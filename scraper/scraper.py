"""
Agente de monitoramento de alugueis — São Bento do Sul SC
Usa Playwright (headless browser) para contornar bot protection.
Fontes: OLX, ZAP Imóveis, Viva Real, Imovelweb
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
    neighborhood: Optional[str]; url: str; images: list
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
                extract_int(p.inner_text() if p else ""),None,None,None,link,[],datetime.now().isoformat()))
    else:
        for ad in ads:
            props = {p["name"]: p.get("value") for p in ad.get("properties", []) if isinstance(p, dict)}
            link  = ad.get("url","")
            imgs  = ad.get("images", [])
            img   = imgs[0].get("original","") if imgs and isinstance(imgs[0], dict) else ad.get("thumbnail","")
            out.append(Listing(make_id("olx",link),"OLX",ad.get("title",""),
                extract_int(ad.get("price","")), extract_int(str(props.get("size",""))),
                extract_int(str(props.get("rooms",""))),
                ad.get("locationDetails",{}).get("neighbourhood") or ad.get("location","").split(",")[0].strip() or None,
                link,[img],datetime.now().isoformat()))
    log.info("OLX — %d", len(out)); return out

def _parse_zap_api(data, base, source):
    out = []
    listings = data.get("search", {}).get("result", {}).get("listings", [])
    for item in listings:
        ld = item.get("listing", {})
        pinfo = ld.get("pricingInfos", [{}])
        price = extract_int(str(next((p.get("price") for p in pinfo if p.get("businessType") == "RENTAL"), None) or ""))
        beds  = ld.get("bedrooms", [None]); beds = int(beds[0]) if beds else None
        link  = base + ld.get("href", "")
        out.append(Listing(make_id(source.lower(), link), source, ld.get("title", ""),
            price, extract_int(str(ld.get("usableArea", ""))), beds,
            ld.get("address", {}).get("neighborhood"), link,
            ld.get("images", [])[:1], datetime.now().isoformat()))
    return out

def _scrape_glue_api(ctx, page, page_url, api_host, base, source):
    captured = {}

    def on_response(response):
        if f"{api_host}/v2/listings" in response.url:
            try: captured["data"] = response.json()
            except: pass

    ctx.on("response", on_response)
    try:
        page.goto(page_url, wait_until="domcontentloaded", timeout=30_000)
        page.wait_for_timeout(5_000)
    except Exception as exc:
        log.warning("%s page load: %s", source, exc)
    ctx.remove_listener("response", on_response)
    return _parse_zap_api(captured.get("data", {}), base, source)

def scrape_zapimoveis(page, ctx):
    log.info("ZAP — scraping...")
    out = _scrape_glue_api(ctx, page,
        "https://www.zapimoveis.com.br/aluguel/imoveis/sc+sao-bento-do-sul/",
        "glue-api.zapimoveis.com.br", "https://www.zapimoveis.com.br", "ZAP Imóveis")
    log.info("ZAP — %d", len(out)); return out

def scrape_vivareal(page, ctx):
    log.info("Viva Real — scraping...")
    out = _scrape_glue_api(ctx, page,
        "https://www.vivareal.com.br/aluguel/santa-catarina/sao-bento-do-sul/",
        "glue-api.vivareal.com", "https://www.vivareal.com.br", "Viva Real")
    log.info("Viva Real — %d", len(out)); return out

def scrape_imovelweb(page):
    log.info("Imovelweb — scraping...")
    out = []
    try:
        page.goto("https://www.imovelweb.com.br/imoveis-aluguel-sao-bento-do-sul-sc.html",
                  wait_until="domcontentloaded", timeout=30_000)
        page.wait_for_selector("div[data-qa='posting PROPERTY']", timeout=20_000)
        for card in page.query_selector_all("div[data-qa='posting PROPERTY']"):
            def g(sel): el=card.query_selector(sel); return el.inner_text().strip() if el else ""
            link_el = card.query_selector("a")
            link = "https://www.imovelweb.com.br" + (link_el.get_attribute("href") if link_el else "")
            img  = card.query_selector("img")
            out.append(Listing(make_id("imovelweb",link),"Imovelweb",g("h2"),
                extract_int(g("div[data-qa='PRICE']")),
                extract_int(g("span[data-qa='SURFACE_COVERED']")),
                extract_int(g("span[data-qa='BEDROOMS']")),
                g("div[data-qa='LOCATION']") or None,link,
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
    return json.load(open(DATA_FILE)) if os.path.exists(DATA_FILE) else []

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
