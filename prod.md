# proj_aluguel — contexto do projeto

## O que é este projeto

Agente de monitoramento de aluguéis para **São Bento do Sul, SC**.
Roda automaticamente via GitHub Actions a cada 6 horas, raspa anúncios das principais plataformas imobiliárias e publica um dashboard HTML no GitHub Pages.

**Dashboard ao vivo:** https://andrebatistatech.github.io/proj-aluguel

O dono do projeto é **André**, Analytics Engineer. A empresa é de Marketing e usa o padrão **MMM (Marketing Mix Modeling)** para análise de dados.

---

## Objetivo

André está avaliando se muda para São Bento do Sul. O agente monitora automaticamente:
- Novos anúncios de aluguel com preço, área, quartos, banheiros e bairro
- Alertas visuais de anúncios novos desde a última execução
- Ranking de bairros com score interativo por qualidade de vida, custo, saúde e mercados

---

## Stack

| Camada | Tecnologia |
|---|---|
| Linguagem | Python 3.11 |
| Scraping | Playwright (Chromium headless) |
| Parsing | JSON interception + seletores HTML |
| Agendamento | GitHub Actions (cron `0 */6 * * *`) |
| Output | HTML estático gerado por Python |
| Publicação | GitHub Pages |
| Dependências | `requirements.txt` |

---

## Estrutura de arquivos

```
proj_aluguel/
├── scraper/
│   └── scraper.py          # scraping das 4 fontes + deduplicação + filtros
├── dashboard/
│   ├── build_dashboard.py  # gera index.html a partir de data/listings.json
│   └── index.html          # dashboard final (gerado — não editar à mão)
├── data/
│   ├── listings.json       # histórico de anúncios (máx 500)
│   └── seen_ids.json       # IDs já vistos para deduplicação
├── .github/
│   └── workflows/
│       └── monitor.yml     # pipeline GitHub Actions
├── requirements.txt
├── README.md               # passo a passo de deploy
└── prod.md                 # este arquivo
```

---

## Fluxo de execução

```
GitHub Actions (cron 6h)
  └─► scraper/scraper.py
        ├── abre Chromium headless (Playwright)
        ├── navega OLX → ZAP Imóveis → Viva Real → Imovelweb
        ├── filtra APENAS anúncios de São Bento do Sul, SC
        ├── extrai: título, preço, área, quartos, banheiros, bairro, URL, imagem
        ├── aplica filtros (MIN_PRICE / MAX_PRICE / MIN_AREA / BEDROOMS)
        ├── deduplica por hash MD5(source+url) → seen_ids.json
        └── salva data/listings.json (merge com histórico, cap 500)
  └─► dashboard/build_dashboard.py
        ├── lê data/listings.json
        ├── gera dashboard/index.html (HTML puro, sem dependências externas)
        └── inclui ranking de bairros embutido como JSON no HTML
  └─► git pull --rebase origin main
  └─► git commit data/ + dashboard/index.html
  └─► git push
  └─► deploy GitHub Pages
```

---

## Modelo de dados — Listing

```python
@dataclass
class Listing:
    id:           str           # MD5(source+url)[:12]
    source:       str           # "OLX" | "ZAP Imóveis" | "Viva Real" | "Imovelweb"
    title:        str
    price:        Optional[int] # R$ inteiro
    area:         Optional[int] # m²
    bedrooms:     Optional[int]
    bathrooms:    Optional[int]
    neighborhood: Optional[str]
    url:          str
    images:       list          # lista de URLs (primeira imagem)
    scraped_at:   str           # ISO 8601
    is_new:       bool          # True se não estava em seen_ids.json
```

---

## Filtros configuráveis

Definidos via variáveis de ambiente (ou GitHub Actions Variables):

| Variável | Padrão | Descrição |
|---|---|---|
| `MAX_PRICE` | 3000 | Preço máximo em R$ |
| `MIN_PRICE` | 500 | Preço mínimo em R$ |
| `MIN_AREA` | 30 | Área mínima em m² |
| `BEDROOMS` | 0 | Quartos mínimos (0 = qualquer) |

---

## Filtro de cidade — OBRIGATÓRIO

**Todos os anúncios devem ser de São Bento do Sul, SC.**

| Fonte | Mecanismo de filtro |
|---|---|
| OLX | `locationDetails.municipality == "São Bento do Sul"` |
| Imovelweb | `"São Bento do Sul" in location` (campo `data-qa='LOCATION'`) |
| ZAP / Viva Real | URL já é específica para SBS; resultado real é ~0–1 anúncio (cidade pequena) |

---

## Dashboard — abas

### Aba 1: Anúncios
- Grid responsivo de cards com foto, fonte, preço, área, quartos, banheiros, bairro
- Campos sem informação exibem **NA** (chip pontilhado)
- Sem imagem exibe ícone de casa + "Sem imagem"
- Badge **NOVO** em anúncios da última execução
- Filtros: fonte, quartos (mín.), preço máximo (slider), **bairro** (dropdown), somente novos

### Aba 2: Ranking de bairros
- 8 bairros avaliados: Centro, Oxford, Schramm, Cruzeiro, Serra Alta, Colonial, Progresso, Rio Negro
- 4 critérios com scores 0–100: qualidade de vida, custo de vida, hospitais próximos, mercados próximos
- Sliders de peso para personalizar o ranking em tempo real
- Clique no bairro expande detalhes + botão "Ver anúncios em [Bairro]" que filtra a aba 1

---

## Fontes de scraping

| Fonte | Estratégia | Parsing |
|---|---|---|
| OLX | `__NEXT_DATA__` JSON | `props.pageProps.ads[]` — filtra por `locationDetails.municipality` |
| ZAP Imóveis | intercepta `glue-api.zapimoveis.com.br/v2/listings` | `search.result.listings[]` |
| Viva Real | intercepta `glue-api.vivareal.com/v2/listings` | mesmo schema do ZAP |
| Imovelweb | seletores HTML (`data-qa`) | `div[data-qa='posting PROPERTY']` — filtra por location |

Todos usam Playwright com:
- `headless=True`
- User-Agent Chrome 124 real
- `navigator.webdriver = undefined` (anti-bot)
- Locale `pt-BR`, timezone `America/Sao_Paulo`
- Pausa de 3s entre fontes

> **Nota ZAP/Viva Real:** migraram de `__NEXT_DATA__` para Next.js App Router. A estratégia atual intercepta a chamada à API REST que o frontend faz. São Bento do Sul tem ~0–1 anúncio nessas plataformas (cidade pequena).

---

## Ranking de bairros — dados

Bairros baseados em pesquisa de fontes públicas (IBGE censo 2022, ACATS, NSC Total, imobiliárias locais).
Os dados do ranking estão **embutidos diretamente em `build_dashboard.py`** na constante `NEIGHBORHOODS_DATA`.

Para atualizar um score ou adicionar um bairro novo, edite `NEIGHBORHOODS_DATA` em `dashboard/build_dashboard.py` e rode `python dashboard/build_dashboard.py`.

---

## Como rodar localmente

```bash
# instalar dependências
pip install -r requirements.txt
playwright install chromium

# executar scraping
python scraper/scraper.py

# gerar dashboard
python dashboard/build_dashboard.py

# abrir no browser
start dashboard/index.html    # Windows
open dashboard/index.html     # macOS
```

---

## Deploy GitHub Actions

1. Criar repo no GitHub e fazer push
2. Settings → Pages → Source: **GitHub Actions**
3. (Opcional) Settings → Variables → Actions → criar `MAX_PRICE`, `MIN_PRICE`, `MIN_AREA`, `BEDROOMS`
4. Actions → "Monitoramento Aluguel" → **Run workflow** para testar

O workflow roda automaticamente a cada 6h via cron `0 */6 * * *`.
O passo de commit faz `git pull --rebase` antes do push para evitar conflito quando o remote avança.

---

## O que NÃO fazer

- Não editar `dashboard/index.html` à mão — ele é gerado pelo script
- Não commitar `data/listings.json` manualmente — o Actions faz isso
- Não adicionar dependências pesadas (o build no Actions precisa ser rápido)
- Não usar `requests` diretamente nos scrapers — os sites bloqueiam; usar sempre Playwright
- Não remover o filtro de cidade — sem ele OLX retorna anúncios de toda SC

---

## Próximas evoluções sugeridas

- [ ] Notificação por Telegram quando aparecer anúncio novo abaixo de R$ X
- [ ] Gráfico de evolução de preço médio por bairro ao longo do tempo
- [ ] Score de cada anúncio cruzando preço com ranking do bairro (custo-benefício)
- [ ] Suporte a imobiliárias locais de SBS (MGF Imóveis, Imobiliária Oxford, LS House)
- [ ] Filtro por m²/preço (preço por metro quadrado)
