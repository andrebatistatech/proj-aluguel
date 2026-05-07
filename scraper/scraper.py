"""
Agente de monitoramento de alugueis — São Bento do Sul SC
Usa Playwright (headless browser) para contornar bot protection.
Fontes: OLX, ZAP Imóveis, Viva Real, Imovelweb
IMPORTANTE: Todos os anúncios filtrados para São Bento do Sul, SC.
"""

import json, hashlib, os, time, logging, re
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional
from playwright.sync_api import sync_playwright, Page, TimeoutError as PWTimeout

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s — %(message)s")
log = logging.getLogger("rental_agent")

DATA_DIR  = os.path.join(os.path.dirname(__file__), "..", "data")
DATA_FILE = os.path.join(DATA_DIR, "listings.json")
SEEN_FILE = os.path.join(DATA_DIR, "seen_ids.json")

FILTERS = {
    "max_price": int(os.getenv("MAX_PRICE", 3000)),
    "min_price": int(os.getenv("MIN_PRICE", 500)),
    "min_area":  int(os.getenv("MIN_AREA",  30)),
    "bedrooms":  int(os.getenv("BEDROOMS",  0)),
}

@dataclass
class Listing:
    id: str; source: str; title: str
    price: Optional[int]; area: Optional[int]; bedrooms: Optional[int]
    bathrooms: Optional[int]; neighborhood: Optional[str]; url: str; images: list
    scraped_at: str; is_new: bool = True
    def to_dict(self): return asdict(self)

def make_id(source, url): return hashlib.md5(f"{source}:{url}".encode()).hexdigest()[:12]
def extract_int(text):
    nums = re.findall(r"\d+", str(text).replace(".", "").replace(",", ""))
    return int(nums[0]) if nums else None

def get_next_data(page, url, timeout=30_000):
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=timeout)
        el = page.query_selector("script#__NEXT_DATA__")
        return json.loads(el.inner_text()) if el else {}
    except Exception as exc:
        log.warning("get_next_data falhou (%s): %s", url[:60], exc)
        return {}

def scrape_olx(page):
    log.info("OLX — scraping...")
    url = "https://www.olx.com.br/imoveis/aluguel/casas-e-apartamentos/estado-sc/sao-bento-do-sul"
    data = get_next_data(page, url)
    ads  = data.get("props", {}).get("pageProps", {}).get("ads", [])
    out  = []
    if not ads:
        for card in page.query_selector_all("li[data-lurker-detail='result_card']"):
            t = card.query_selector("h2"); p = card.query_selector("h3"); a = card.query_selector("a")
            link = a.get_attribute("href") if a else ""
            out.append(Listing(make_id("olx",link),"OLX",t.inner_text().strip() if t else "",
                extract_int(p.inner_text() if p else ""),None,None,None,None,link,[],datetime.now().isoformat()))
    else:
        for ad in ads:
            link = ad.get("url", "")
            if not link:
                continue  # pula banners publicitários (sem URL real)
            municipality = ad.get("locationDetails", {}).get("municipality", "")
            muni_norm = municipality.lower().replace("ã","a").replace("é","e")
            if municipality and "sao bento do sul" not in muni_norm:
                continue
            props = {p["name"]: p.get("value") for p in ad.get("properties", []) if isinstance(p, dict)}
            imgs  = ad.get("images", [])
            img   = imgs[0].get("original","") if imgs and isinstance(imgs[0], dict) else ad.get("thumbnail","")
            out.append(Listing(make_id("olx",link),"OLX",ad.get("title",""),
                extract_int(ad.get("price","")), extract_int(str(props.get("size",""))),
                extract_int(str(props.get("rooms",""))),
                extract_int(str(props.get("bathrooms",""))),
                ad.get("locationDetails",{}).get("neighbourhood") or None,
                link,[img],datetime.now().isoformat()))
    log.info("OLX — %d", len(out)); return out

def _scrape_dom_listings(page, page_url, source, url_slug):
    out = []
    try:
        page.goto(page_url, wait_until="domcontentloaded", timeout=30_000)
        page.wait_for_timeout(4_000)
        cards = page.query_selector_all("a[href*='/imovel/']")
        seen_hrefs = set()
        for card in cards:
            href = card.get_attribute("href") or ""
            if not href or href in seen_hrefs:
                continue
            seen_hrefs.add(href)
            href_norm = href.lower().replace("-", " ")
            if url_slug not in href_norm:
                continue
            text = card.inner_text()
            text_norm = text.lower().replace("ã","a").replace("é","e").replace("ô","o")
            if "sao bento do sul" not in text_norm and url_slug not in href_norm:
                continue
            price_m = re.search(r"R\$\s*([\d.,]+)", text)
            price = extract_int(price_m.group(1)) if price_m else None
            area_m = re.search(r"(\d+)\s*m[²2]", text)
            area = int(area_m.group(1)) if area_m else None
            beds_m = re.search(r"(\d+)\s*quarto", text, re.I)
            beds = int(beds_m.group(1)) if beds_m else None
            baths_m = re.search(r"(\d+)\s*banheiro", text, re.I)
            baths = int(baths_m.group(1)) if baths_m else None
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            title = next((l for l in lines if len(l) > 15 and "R$" not in l and "foto" not in l.lower()), "")
            img_el = card.query_selector("img")
            img = img_el.get_attribute("src") or "" if img_el else ""
            out.append(Listing(make_id(source.lower(), href), source, title,
                price, area, beds, baths, None, href, [img] if img else [], datetime.now().isoformat()))
    except Exception as exc:
        log.warning("%s DOM scrape: %s", source, exc)
    return out

def scrape_zapimoveis(page, ctx):
    log.info("ZAP — scraping...")
    out = _scrape_dom_listings(page,
        "https://www.zapimoveis.com.br/aluguel/imoveis/sc+sao-bento-do-sul/",
        "ZAP Imóveis", "sao bento do sul")
    log.info("ZAP — %d", len(out)); return out

def scrape_vivareal(page, ctx):
    log.info("Viva Real — scraping...")
    out = _scrape_dom_listings(page,
        "https://www.vivareal.com.br/aluguel/santa-catarina/sao-bento-do-sul/",
        "Viva Real", "sao bento do sul")
    log.info("Viva Real — %d", len(out)); return out

def _parse_imovelweb_features(text):
    """Parse 'X m² tot.\nN quartos\nN banheiro\nN vaga' → (area, beds, baths)"""
    area = beds = baths = None
    for line in text.split("\n"):
        line = line.strip()
        if "m²" in line or "m2" in line.lower():
            area = extract_int(line)
        elif "quarto" in line.lower():
            beds = extract_int(line)
        elif "ban" in line.lower():
            baths = extract_int(line)
    return area, beds, baths

def scrape_imovelweb(page):
    log.info("Imovelweb — scraping...")
    out = []
    try:
        page.goto("https://www.imovelweb.com.br/imoveis-aluguel-sao-bento-do-sul-sc.html",
                  wait_until="domcontentloaded", timeout=30_000)
        page.wait_for_selector("div[data-qa='posting PROPERTY']", timeout=20_000)
        for card in page.query_selector_all("div[data-qa='posting PROPERTY']"):
            def g(qa): el=card.query_selector(f"[data-qa='{qa}']"); return el.inner_text().strip() if el else ""
            location = g("POSTING_CARD_LOCATION")
            # obrigatório: só aceita se confirmar São Bento do Sul (normalizado por encoding)
            loc_norm = location.lower().replace("ã","a").replace("é","e").replace("ô","o")
            if not location or "sao bento do sul" not in loc_norm:
                continue
            neighborhood = location.split(",")[0].strip() if "," in location else None
            price_txt = g("POSTING_CARD_PRICE")
            features  = g("POSTING_CARD_FEATURES")
            desc      = g("POSTING_CARD_DESCRIPTION")
            area, beds, baths = _parse_imovelweb_features(features)
            link_el = card.query_selector("a")
            link = "https://www.imovelweb.com.br" + (link_el.get_attribute("href") if link_el else "")
            img  = card.query_selector("img")
            out.append(Listing(make_id("imovelweb",link),"Imovelweb",desc,
                extract_int(price_txt), area, beds, baths,
                neighborhood, link,
                [img.get_attribute("src")] if img else [],datetime.now().isoformat()))
    except Exception as exc:
        log.error("Imovelweb: %s", exc)
    log.info("Imovelweb — %d", len(out)); return out

def load_seen():
    return set(json.load(open(SEEN_FILE))) if os.path.exists(SEEN_FILE) else set()

def save_seen(seen):
    os.makedirs(DATA_DIR, exist_ok=True)
    json.dump(list(seen), open(SEEN_FILE,"w"))

def load_existing():
    return json.load(open(DATA_FILE, encoding="utf-8")) if os.path.exists(DATA_FILE) else []

def apply_filters(listings):
    out = []
    for l in listings:
        if l.price and (l.price < FILTERS["min_price"] or l.price > FILTERS["max_price"]): continue
        if l.area and l.area < FILTERS["min_area"]: continue
        if FILTERS["bedrooms"] > 0 and l.bedrooms and l.bedrooms < FILTERS["bedrooms"]: continue
        out.append(l)
    return out

def deduplicate(listings, seen):
    seen2 = set(seen)
    for l in listings:
        l.is_new = l.id not in seen2
        seen2.add(l.id)
    return listings, seen2

def run():
    os.makedirs(DATA_DIR, exist_ok=True)
    log.info("=== Início do ciclo ===")
    all_listings = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, args=["--no-sandbox","--disable-blink-features=AutomationControlled"])
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width":1280,"height":800}, locale="pt-BR", timezone_id="America/Sao_Paulo")
        ctx.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")
        page = ctx.new_page()

        scrapers = [
            (scrape_olx,        (page,)),
            (scrape_zapimoveis, (page, ctx)),
            (scrape_vivareal,   (page, ctx)),
            (scrape_imovelweb,  (page,)),
        ]
        # ctx kept in signature for compatibility but _scrape_dom_listings doesn't use it
        for fn, args in scrapers:
            try: all_listings.extend(fn(*args))
            except Exception as exc: log.error("%s falhou: %s", fn.__name__, exc)
            time.sleep(3)
        browser.close()

    filtered = apply_filters(all_listings)
    seen = load_seen()
    deduped, new_seen = deduplicate(filtered, seen)
    save_seen(new_seen)

    existing     = load_existing()
    existing_ids = {l["id"] for l in existing}
    merged = [l.to_dict() for l in deduped if l.id not in existing_ids] + existing
    merged = merged[:500]

    json.dump(merged, open(DATA_FILE,"w",encoding="utf-8"), ensure_ascii=False, indent=2)

    new_count = sum(1 for l in deduped if l.is_new)
    log.info("Novos: %d | Total: %d", new_count, len(merged))
    log.info("=== Concluído ===")

    summary = os.environ.get("GITHUB_STEP_SUMMARY","")
    if summary:
        with open(summary,"a") as f:
            f.write(f"## Monitoramento — {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
            f.write(f"- Anúncios novos: **{new_count}**\n")
            f.write(f"- Total: {len(merged)}\n")

if __name__ == "__main__":
    run()
