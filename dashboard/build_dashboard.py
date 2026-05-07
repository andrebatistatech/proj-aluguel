"""
Gera dashboard/index.html com duas abas:
  1. Anúncios  — grid filtrável de aluguéis raspados
  2. Bairros   — ranking interativo com pesos ajustáveis
"""

import json, os
from datetime import datetime

DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "listings.json")
OUT_FILE  = os.path.join(os.path.dirname(__file__), "..", "dashboard", "index.html")

NEIGHBORHOODS_DATA = [
    {
        "name": "Centro",
        "scores": {"vida": 82, "custo": 52, "hosp": 100, "merc": 100},
        "aluguel": "R$ 2.100–2.400",
        "badges": [["Principal hospital","bt"],["Fort + Komprão","bg"],["Comércio completo","bb"]],
        "detail": {
            "Aluguel médio 2 qtos": "R$ 2.100–2.400",
            "Hospital Sagrada Família": "< 1 km",
            "Fort Atacadista": "< 2 km",
            "Komprão Koch": "< 2 km",
            "Posto de saúde": "no bairro",
            "Transporte": "ótimo",
            "Lazer/comércio": "abundante",
            "Trânsito": "moderado",
        },
        "tip": "Melhor infraestrutura de saúde e mercados. Aluguel mais alto, mas tudo na porta.",
    },
    {
        "name": "Oxford",
        "scores": {"vida": 80, "custo": 68, "hosp": 82, "merc": 100},
        "aluguel": "R$ 1.700–2.000",
        "badges": [["Fort + Komprão no bairro","bg"],["Expansão rápida","bb"],["Rodovia dos Móveis","ba"]],
        "detail": {
            "Aluguel médio 2 qtos": "R$ 1.700–2.000",
            "Fort Atacadista Oxford": "no bairro",
            "Komprão Koch Oxford": "no bairro",
            "Hospital Sagrada Família": "~5 km",
            "Infraestrutura": "moderna",
            "Transporte": "bom",
            "Crescimento": "alto",
            "Trânsito": "leve",
        },
        "tip": "Bairro em expansão com as duas principais redes de atacarejo. Ótimo custo-benefício.",
    },
    {
        "name": "Schramm",
        "scores": {"vida": 76, "custo": 70, "hosp": 80, "merc": 90},
        "aluguel": "R$ 1.700–2.000",
        "badges": [["Fort próximo","bg"],["Delegacia no bairro","bt"],["Novos prédios","bb"]],
        "detail": {
            "Aluguel médio 2 qtos": "R$ 1.700–2.000",
            "Fort Atacadista": "< 1 km",
            "Bertovan Supermercado": "no bairro",
            "Hospital Sagrada Família": "~4 km",
            "Delegacia": "no bairro",
            "Transporte": "bom",
            "Perfil": "residencial moderno",
            "Novos condomínios": "sim",
        },
        "tip": "Residencial seguro com supermercado na porta. Prédios novos com boa relação preço/qualidade.",
    },
    {
        "name": "Cruzeiro",
        "scores": {"vida": 75, "custo": 74, "hosp": 85, "merc": 82},
        "aluguel": "R$ 1.500–1.900",
        "badges": [["2° mais populoso","bb"],["UBS no bairro","bt"],["Farmácias e padarias","bg"]],
        "detail": {
            "Aluguel médio 2 qtos": "R$ 1.500–1.900",
            "Hospital Sagrada Família": "~3 km",
            "UBS Cruzeiro": "no bairro",
            "Mercados locais": "vários",
            "Escola": "no bairro",
            "Transporte": "bom",
            "Perfil": "residencial consolidado",
            "Segurança": "boa",
        },
        "tip": "Bairro consolidado com boa rede de saúde básica. Aluguel acessível e ampla oferta de imóveis.",
    },
    {
        "name": "Serra Alta",
        "scores": {"vida": 72, "custo": 80, "hosp": 70, "merc": 72},
        "aluguel": "R$ 1.400–1.800",
        "badges": [["Maior bairro","bb"],["Aluguel barato","bg"],["Komprão em 2026","ba"]],
        "detail": {
            "Aluguel médio 2 qtos": "R$ 1.400–1.800",
            "Komprão (previsto 2026)": "no bairro",
            "Mercados locais": "médio porte",
            "Hospital Sagrada Família": "~6 km",
            "Posto de saúde": "no bairro",
            "Transporte": "razoável",
            "Perfil": "popular/familiar",
            "Pop. censo 2022": "12.167",
        },
        "tip": "Maior bairro com custo acessível. Komprão previsto para 2026 vai melhorar muito o acesso a mercados.",
    },
    {
        "name": "Colonial",
        "scores": {"vida": 74, "custo": 76, "hosp": 72, "merc": 70},
        "aluguel": "R$ 1.500–1.900",
        "badges": [["UNIVILLE ao lado","bb"],["Tranquilo e familiar","bt"],["UPA próxima","bg"]],
        "detail": {
            "Aluguel médio 2 qtos": "R$ 1.500–1.900",
            "UNIVILLE campus": "< 1 km",
            "UPA (nova)": "< 2 km",
            "Mercados locais": "bom",
            "Hospital Sagrada Família": "~5 km",
            "Perfil": "familiar tranquilo",
            "Acesso SC-301": "fácil",
            "Lazer": "bom",
        },
        "tip": "Ideal para quem tem filhos na UNIVILLE ou busca ambiente tranquilo. Nova UPA próxima valoriza o bairro.",
    },
    {
        "name": "Progresso",
        "scores": {"vida": 68, "custo": 82, "hosp": 68, "merc": 65},
        "aluguel": "R$ 1.300–1.700",
        "badges": [["Menor aluguel","bg"],["Imóveis espaçosos","ba"],["Mais afastado","br"]],
        "detail": {
            "Aluguel médio 2 qtos": "R$ 1.300–1.700",
            "Mercados locais": "básico",
            "Hospital Sagrada Família": "~7 km",
            "Transporte": "limitado",
            "Perfil": "residencial popular",
            "Espaço imóveis": "grande",
            "Segurança": "boa",
            "Lazer": "limitado",
        },
        "tip": "Melhor custo de vida da lista. Bom para quem tem carro e quer mais espaço por menos dinheiro.",
    },
    {
        "name": "Rio Negro",
        "scores": {"vida": 70, "custo": 74, "hosp": 65, "merc": 68},
        "aluguel": "R$ 1.500–1.900",
        "badges": [["Rio e natureza","bt"],["Quieto e arborizado","bg"],["Menor infraestrutura","br"]],
        "detail": {
            "Aluguel médio 2 qtos": "R$ 1.500–1.900",
            "Mercados locais": "básico",
            "Hospital Sagrada Família": "~8 km",
            "Acesso à natureza": "excelente",
            "Transporte": "limitado",
            "Perfil": "tranquilo/natureza",
            "Lazer natural": "alto",
            "Comércio": "básico",
        },
        "tip": "Para quem valoriza contato com a natureza e tranquilidade absoluta. Carro é indispensável.",
    },
]


def load_listings():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)


def fmt_price(p):
    if p is None:
        return "—"
    return f"R$ {p:,.0f}".replace(",", ".")


def fmt_area(a):
    return f"{a} m²" if a else "—"


def source_color(src):
    return {
        "OLX":         "#6d28d9",
        "ZAP Imóveis": "#0ea5e9",
        "Viva Real":   "#10b981",
        "Imovelweb":   "#f59e0b",
    }.get(src, "#6b7280")


def build_listing_card(l):
    img_tag   = f'<img src="{l["images"][0]}" alt="foto" onerror="this.style.display=\'none\'">' if l.get("images") else ""
    new_badge = '<span class="badge-new">NOVO</span>' if l.get("is_new") else ""
    neigh     = l.get("neighborhood") or ""
    area      = fmt_area(l.get("area"))
    beds_n    = l.get("bedrooms") or 0
    beds      = f'{beds_n} qto{"s" if beds_n > 1 else ""}' if beds_n else ""
    scraped   = l.get("scraped_at", "")[:10]
    neigh_attr = neigh.lower().strip()

    return f"""<div class="listing-card"
     data-price="{l.get('price') or 0}"
     data-source="{l.get('source','')}"
     data-bedrooms="{beds_n}"
     data-new="{str(l.get('is_new', False)).lower()}"
     data-neighborhood="{neigh_attr}">
  <div class="lc-img">{img_tag}</div>
  <div class="lc-body">
    <div class="lc-top">
      <span class="src-badge" style="background:{source_color(l.get('source',''))}">{l.get('source','')}</span>
      {new_badge}
    </div>
    <div class="lc-title">{l.get('title','Sem título')}</div>
    <div class="lc-price">{fmt_price(l.get('price'))}<span class="per-mo">/mês</span></div>
    <div class="lc-meta">
      {"<span>"+area+"</span>" if area != "—" else ""}
      {"<span>"+beds+"</span>" if beds else ""}
      {"<span>"+neigh+"</span>" if neigh else ""}
    </div>
    <div class="lc-footer">
      <span class="lc-date">{scraped}</span>
      <a href="{l.get('url','#')}" target="_blank" rel="noopener">Ver anúncio →</a>
    </div>
  </div>
</div>"""


def build_html(listings):
    total     = len(listings)
    new_count = sum(1 for l in listings if l.get("is_new"))
    prices    = [l["price"] for l in listings if l.get("price")]
    avg_price = int(sum(prices) / len(prices)) if prices else 0
    min_price = min(prices) if prices else 0
    updated   = datetime.now().strftime("%d/%m/%Y %H:%M")

    sources     = sorted({l.get("source", "") for l in listings})
    src_options = "\n".join(f'<option value="{s}">{s}</option>' for s in sources)
    cards_html  = "\n".join(build_listing_card(l) for l in listings)

    neigh_json = json.dumps(NEIGHBORHOODS_DATA, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Aluguel Monitor — São Bento do Sul SC</title>
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:system-ui,-apple-system,sans-serif;background:#f4f4f5;color:#18181b;min-height:100vh}}
/* ── header ── */
header{{background:#18181b;color:#fff;padding:1rem 2rem;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:.5rem}}
header h1{{font-size:1.05rem;font-weight:600}}
.updated{{font-size:.72rem;color:#a1a1aa}}
/* ── tabs ── */
.tabs{{display:flex;gap:0;padding:0 2rem;background:#18181b;border-bottom:1px solid #27272a}}
.tab{{padding:.6rem 1.2rem;font-size:.85rem;color:#a1a1aa;cursor:pointer;border-bottom:2px solid transparent;transition:color .15s,border-color .15s}}
.tab.active{{color:#fff;border-bottom-color:#6d28d9}}
.tab-panel{{display:none}}
.tab-panel.active{{display:block}}
/* ── stats ── */
.stats{{display:flex;gap:.75rem;padding:1.1rem 2rem;flex-wrap:wrap}}
.stat{{background:#fff;border-radius:10px;padding:.75rem 1.1rem;min-width:120px;box-shadow:0 1px 3px rgba(0,0,0,.07)}}
.stat-label{{font-size:.68rem;color:#71717a;text-transform:uppercase;letter-spacing:.05em}}
.stat-value{{font-size:1.4rem;font-weight:600;margin-top:2px}}
.stat-value.green{{color:#16a34a}}
/* ── filters ── */
.filters{{padding:0 2rem .9rem;display:flex;gap:.6rem;flex-wrap:wrap;align-items:flex-end}}
.fg{{display:flex;flex-direction:column;gap:3px}}
.fg label{{font-size:.75rem;color:#52525b}}
select,input[type=range]{{border:1px solid #d4d4d8;border-radius:6px;padding:.3rem .55rem;font-size:.82rem;background:#fff;color:#18181b}}
#price-out{{font-size:.78rem;color:#3f3f46;font-weight:500}}
.filter-badge{{display:none;align-items:center;gap:6px;background:#ede9fe;color:#4c1d95;padding:3px 10px;border-radius:20px;font-size:.75rem;font-weight:500}}
.filter-badge button{{background:none;border:none;color:#4c1d95;cursor:pointer;font-size:14px;line-height:1;padding:0}}
#reset-btn{{padding:.3rem .8rem;border:1px solid #d4d4d8;border-radius:6px;background:#fff;cursor:pointer;font-size:.78rem}}
#reset-btn:hover{{background:#f4f4f5}}
/* ── listings grid ── */
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:.9rem;padding:0 2rem 2rem}}
.listing-card{{background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.08);transition:transform .15s,box-shadow .15s}}
.listing-card:hover{{transform:translateY(-2px);box-shadow:0 4px 12px rgba(0,0,0,.12)}}
.lc-img{{height:150px;background:#e4e4e7;overflow:hidden}}
.lc-img img{{width:100%;height:100%;object-fit:cover}}
.lc-body{{padding:.85rem .95rem}}
.lc-top{{display:flex;align-items:center;gap:5px;margin-bottom:5px}}
.src-badge{{font-size:.62rem;font-weight:600;color:#fff;padding:2px 7px;border-radius:20px;text-transform:uppercase;letter-spacing:.04em}}
.badge-new{{font-size:.62rem;font-weight:700;color:#fff;background:#ef4444;padding:2px 7px;border-radius:20px}}
.lc-title{{font-size:.82rem;font-weight:500;color:#27272a;line-height:1.4;margin-bottom:5px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}}
.lc-price{{font-size:1.15rem;font-weight:700;color:#18181b}}
.per-mo{{font-size:.68rem;font-weight:400;color:#71717a;margin-left:2px}}
.lc-meta{{display:flex;gap:6px;flex-wrap:wrap;margin-top:5px}}
.lc-meta span{{font-size:.72rem;color:#52525b;background:#f4f4f5;padding:2px 7px;border-radius:20px}}
.lc-footer{{display:flex;justify-content:space-between;align-items:center;margin-top:9px;padding-top:7px;border-top:1px solid #f4f4f5}}
.lc-date{{font-size:.68rem;color:#a1a1aa}}
.lc-footer a{{font-size:.77rem;color:#6d28d9;text-decoration:none;font-weight:500}}
.lc-footer a:hover{{text-decoration:underline}}
.empty-msg{{grid-column:1/-1;text-align:center;color:#71717a;padding:3rem;font-size:.9rem}}
/* ── ranking tab ── */
.rank-wrap{{padding:1.25rem 2rem 2rem}}
.rank-intro{{font-size:.8rem;color:#71717a;margin-bottom:1rem}}
.weight-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:.6rem;margin-bottom:1.25rem}}
.wctrl{{background:#fff;border-radius:8px;padding:.65rem .9rem;border:1px solid #e4e4e7}}
.wctrl-label{{font-size:.7rem;color:#71717a;margin-bottom:5px;display:flex;justify-content:space-between}}
.wctrl-label span{{font-weight:600;color:#18181b}}
.rank-list{{display:flex;flex-direction:column;gap:.65rem}}
.nbcard{{background:#fff;border-radius:12px;border:1px solid #e4e4e7;padding:.9rem 1rem;cursor:pointer;transition:border-color .15s}}
.nbcard.winner{{border:2px solid #1D9E75}}
.nbcard:hover{{border-color:#a1a1aa}}
.nbc-top{{display:flex;align-items:center;gap:9px;margin-bottom:8px}}
.nbc-rank{{width:26px;height:26px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:600;flex-shrink:0}}
.r1{{background:#dcfce7;color:#14532d}}
.r2{{background:#dbeafe;color:#1e3a8a}}
.r3{{background:#fef3c7;color:#78350f}}
.rn{{background:#f4f4f5;color:#71717a}}
.nbc-name{{font-size:.95rem;font-weight:500;flex:1}}
.nbc-score{{text-align:right}}
.nbc-score-val{{font-size:1.3rem;font-weight:600}}
.nbc-score-lbl{{font-size:.65rem;color:#71717a}}
.nbc-badges{{display:flex;gap:4px;flex-wrap:wrap;margin-bottom:8px}}
.nbadge{{font-size:.68rem;padding:2px 7px;border-radius:20px;font-weight:500}}
.bg{{background:#dcfce7;color:#14532d}}
.bb{{background:#dbeafe;color:#1e3a8a}}
.bt{{background:#d1fae5;color:#064e3b}}
.ba{{background:#fef3c7;color:#78350f}}
.br{{background:#fee2e2;color:#7f1d1d}}
.nbc-bars{{display:grid;grid-template-columns:1fr 1fr;gap:5px 14px;margin-bottom:6px}}
.bar-row{{display:flex;flex-direction:column;gap:2px}}
.bar-lbl{{font-size:.67rem;color:#71717a;display:flex;justify-content:space-between}}
.bar-track{{height:4px;background:#f4f4f5;border-radius:3px;overflow:hidden}}
.bar-fill{{height:100%;border-radius:3px;transition:width .35s}}
.nbc-detail{{display:none;margin-top:8px;padding-top:8px;border-top:1px solid #f4f4f5}}
.detail-grid{{display:grid;grid-template-columns:1fr 1fr;gap:3px 14px;font-size:.72rem}}
.dr{{display:flex;justify-content:space-between;padding:2px 0;border-bottom:.5px solid #f9f9f9}}
.dk{{color:#71717a}}
.dv{{font-weight:500}}
.nbc-tip{{font-size:.75rem;color:#52525b;margin-top:7px;line-height:1.5;background:#f9f9f9;border-radius:6px;padding:.45rem .7rem}}
.filter-link{{display:inline-flex;align-items:center;gap:4px;margin-top:.6rem;font-size:.75rem;color:#6d28d9;background:#ede9fe;padding:3px 10px;border-radius:20px;cursor:pointer;border:none;font-family:inherit}}
.filter-link:hover{{background:#ddd6fe}}
@media(max-width:600px){{.stats,.filters,.grid,.rank-wrap{{padding-left:1rem;padding-right:1rem}}}}
</style>
</head>
<body>

<header>
  <h1>Aluguel Monitor — São Bento do Sul, SC</h1>
  <span class="updated">Atualizado: {updated}</span>
</header>

<div class="tabs">
  <div class="tab active" data-tab="listings">Anúncios</div>
  <div class="tab" data-tab="ranking">Ranking de bairros</div>
</div>

<!-- ═══════════════ ABA ANÚNCIOS ═══════════════ -->
<div class="tab-panel active" id="panel-listings">

  <div class="stats">
    <div class="stat"><div class="stat-label">Total</div><div class="stat-value">{total}</div></div>
    <div class="stat"><div class="stat-label">Novos</div><div class="stat-value green">{new_count}</div></div>
    <div class="stat"><div class="stat-label">Preço médio</div><div class="stat-value">{fmt_price(avg_price)}</div></div>
    <div class="stat"><div class="stat-label">Menor preço</div><div class="stat-value">{fmt_price(min_price)}</div></div>
  </div>

  <div class="filters">
    <div class="fg">
      <label>Fonte</label>
      <select id="f-source"><option value="">Todas</option>{src_options}</select>
    </div>
    <div class="fg">
      <label>Quartos (mín.)</label>
      <select id="f-beds">
        <option value="0">Qualquer</option>
        <option value="1">1+</option>
        <option value="2">2+</option>
        <option value="3">3+</option>
      </select>
    </div>
    <div class="fg">
      <label>Preço máx — <span id="price-out">R$ 3.000</span></label>
      <input type="range" id="f-price" min="500" max="5000" step="100" value="5000">
    </div>
    <div class="fg">
      <label>Apenas novos</label>
      <select id="f-new"><option value="">Todos</option><option value="true">Somente novos</option></select>
    </div>
    <span class="filter-badge" id="neigh-badge">
      <span id="neigh-badge-text"></span>
      <button id="neigh-clear" title="Remover filtro">×</button>
    </span>
    <button id="reset-btn">Limpar filtros</button>
  </div>

  <div class="grid" id="grid">
    {cards_html}
    <div class="empty-msg" id="empty-msg" style="display:none">Nenhum anúncio encontrado com esses filtros.</div>
  </div>
</div>

<!-- ═══════════════ ABA RANKING ═══════════════ -->
<div class="tab-panel" id="panel-ranking">
  <div class="rank-wrap">
    <p class="rank-intro">Ajuste os pesos para personalizar o ranking. Clique em um bairro para expandir detalhes ou filtrar os anúncios.</p>
    <div class="weight-grid">
      <div class="wctrl">
        <div class="wctrl-label">Qualidade de vida <span id="lv">30%</span></div>
        <input type="range" id="wv" min="0" max="100" step="5" value="30" style="width:100%">
      </div>
      <div class="wctrl">
        <div class="wctrl-label">Custo de vida <span id="lc">25%</span></div>
        <input type="range" id="wc" min="0" max="100" step="5" value="25" style="width:100%">
      </div>
      <div class="wctrl">
        <div class="wctrl-label">Hospitais próximos <span id="lh">25%</span></div>
        <input type="range" id="wh" min="0" max="100" step="5" value="25" style="width:100%">
      </div>
      <div class="wctrl">
        <div class="wctrl-label">Mercados próximos <span id="lm">20%</span></div>
        <input type="range" id="wm" min="0" max="100" step="5" value="20" style="width:100%">
      </div>
    </div>
    <div class="rank-list" id="rank-list"></div>
  </div>
</div>

<script>
const NEIGHBORHOODS = {neigh_json};
const barColors = {{vida:"#1D9E75",custo:"#378ADD",hosp:"#D85A30",merc:"#BA7517"}};
const barLabels = {{vida:"Qualidade de vida",custo:"Custo",hosp:"Saúde",merc:"Mercados"}};

/* ── tabs ── */
document.querySelectorAll('.tab').forEach(tab => {{
  tab.addEventListener('click', () => {{
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    tab.classList.add('active');
    document.getElementById('panel-' + tab.dataset.tab).classList.add('active');
  }});
}});

/* ── listings filter ── */
const grid     = document.getElementById('grid');
const allCards = Array.from(grid.querySelectorAll('.listing-card'));
const emptyMsg = document.getElementById('empty-msg');
const neighBadge = document.getElementById('neigh-badge');
const neighBadgeTxt = document.getElementById('neigh-badge-text');
let activeNeigh = '';

function fmt(v) {{ return 'R$ ' + Number(v).toLocaleString('pt-BR'); }}

function applyFilters() {{
  const src  = document.getElementById('f-source').value;
  const beds = parseInt(document.getElementById('f-beds').value);
  const price = parseInt(document.getElementById('f-price').value);
  const onlyNew = document.getElementById('f-new').value;
  document.getElementById('price-out').textContent = price >= 5000 ? 'Sem limite' : fmt(price);

  let vis = 0;
  allCards.forEach(c => {{
    const ok =
      (!src      || c.dataset.source    === src) &&
      (!beds     || parseInt(c.dataset.bedrooms) >= beds) &&
      (price>=5000 || !parseInt(c.dataset.price) || parseInt(c.dataset.price) <= price) &&
      (!onlyNew  || c.dataset.new === 'true') &&
      (!activeNeigh || c.dataset.neighborhood.includes(activeNeigh.toLowerCase()));
    c.style.display = ok ? '' : 'none';
    if (ok) vis++;
  }});
  emptyMsg.style.display = vis === 0 ? '' : 'none';
}}

['f-source','f-beds','f-price','f-new'].forEach(id => {{
  document.getElementById(id).addEventListener('input', applyFilters);
}});

document.getElementById('reset-btn').addEventListener('click', () => {{
  document.getElementById('f-source').value = '';
  document.getElementById('f-beds').value   = '0';
  document.getElementById('f-price').value  = '5000';
  document.getElementById('f-new').value    = '';
  clearNeighFilter();
}});

document.getElementById('neigh-clear').addEventListener('click', clearNeighFilter);

function clearNeighFilter() {{
  activeNeigh = '';
  neighBadge.style.display = 'none';
  applyFilters();
}}

function filterByNeigh(name) {{
  activeNeigh = name.toLowerCase();
  neighBadgeTxt.textContent = name;
  neighBadge.style.display = 'inline-flex';
  document.querySelector('[data-tab="listings"]').click();
  applyFilters();
}}

/* ── ranking ── */
function getW() {{
  const wv = parseInt(document.getElementById('wv').value);
  const wc = parseInt(document.getElementById('wc').value);
  const wh = parseInt(document.getElementById('wh').value);
  const wm = parseInt(document.getElementById('wm').value);
  const tot = (wv+wc+wh+wm) || 1;
  return {{vida:wv/tot, custo:wc/tot, hosp:wh/tot, merc:wm/tot}};
}}

function calcScore(d, w) {{
  return Math.round(d.scores.vida*w.vida + d.scores.custo*w.custo +
                    d.scores.hosp*w.hosp + d.scores.merc*w.merc);
}}

function renderRanking() {{
  const w = getW();
  const sorted = NEIGHBORHOODS.map(d => ({{...d, total: calcScore(d,w)}}))
                              .sort((a,b) => b.total - a.total);
  const list = document.getElementById('rank-list');
  list.innerHTML = '';

  ['lv','lc','lh','lm'].forEach((id,i) => {{
    const keys = ['vida','custo','hosp','merc'];
    document.getElementById(id).textContent = Math.round(w[keys[i]]*100) + '%';
  }});

  sorted.forEach((d, i) => {{
    const rankCls = i===0?'r1':i===1?'r2':i===2?'r3':'rn';
    const winCls  = i===0 ? ' winner' : '';

    const barsHtml = Object.entries(barLabels).map(([k,lbl]) =>
      `<div class="bar-row">
         <div class="bar-lbl"><span>${{lbl}}</span><span>${{d.scores[k]}}</span></div>
         <div class="bar-track"><div class="bar-fill" style="width:${{d.scores[k]}}%;background:${{barColors[k]}}"></div></div>
       </div>`).join('');

    const badgesHtml = d.badges.map(([t,c]) =>
      `<span class="nbadge ${{c}}">${{t}}</span>`).join('');

    const detailRows = Object.entries(d.detail).map(([k,v]) =>
      `<div class="dr"><span class="dk">${{k}}</span><span class="dv">${{v}}</span></div>`).join('');

    const card = document.createElement('div');
    card.className = `nbcard${{winCls}}`;
    card.innerHTML = `
      <div class="nbc-top">
        <div class="nbc-rank ${{rankCls}}">${{i+1}}</div>
        <div class="nbc-name">${{d.name}}</div>
        <div class="nbc-score">
          <div class="nbc-score-val">${{d.total}}</div>
          <div class="nbc-score-lbl">score</div>
        </div>
      </div>
      <div class="nbc-badges">${{badgesHtml}}</div>
      <div class="nbc-bars">${{barsHtml}}</div>
      <div class="nbc-detail" id="det-${{i}}">
        <div class="detail-grid">${{detailRows}}</div>
        <p class="nbc-tip">${{d.tip}}</p>
        <button class="filter-link" data-neigh="${{d.name}}">
          Ver anúncios em ${{d.name}} →
        </button>
      </div>`;

    card.querySelector('.nbc-top').addEventListener('click', () => {{
      const det = document.getElementById(`det-${{i}}`);
      det.style.display = det.style.display === 'block' ? 'none' : 'block';
    }});

    card.querySelector('.filter-link').addEventListener('click', (e) => {{
      e.stopPropagation();
      filterByNeigh(d.name);
    }});

    list.appendChild(card);
  }});
}}

['wv','wc','wh','wm'].forEach(id => {{
  document.getElementById(id).addEventListener('input', renderRanking);
}});

renderRanking();
applyFilters();
</script>
</body>
</html>"""


def run():
    listings = load_listings()
    html = build_html(listings)
    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Dashboard gerado: {OUT_FILE} ({len(listings)} anúncios)")


if __name__ == "__main__":
    run()
