# Rental Monitor — São Bento do Sul SC

Agente de monitoramento de aluguéis para **São Bento do Sul, SC**.
Raspa anúncios das principais plataformas a cada 6h e publica dashboard HTML via GitHub Actions + GitHub Pages.

**Dashboard:** https://andrebatistatech.github.io/proj-aluguel

---

## Fontes monitoradas

| Fonte | Estratégia | Status |
|---|---|---|
| OLX | `__NEXT_DATA__` JSON | ativo |
| Imovelweb | seletores HTML `data-qa` | ativo |
| ZAP Imóveis | interceptação `glue-api` | ativo (SBS tem ~0–1 anúncio) |
| Viva Real | interceptação `glue-api` | ativo (SBS tem ~0–1 anúncio) |

Todos os anúncios filtrados para **São Bento do Sul, SC** — sem resultados de outras cidades.

---

## Dashboard

### Aba Anúncios
- Grid responsivo com foto, fonte, preço, área, quartos, banheiros, bairro
- Badge **NOVO** em anúncios da última execução
- Campos sem informação exibem **NA** (pontilhado)
- Sem imagem exibe ícone de casa + "Sem imagem"
- Filtros: fonte, quartos (mín.), preço máx (slider), **bairro**, apenas novos

### Aba Ranking de Bairros
- 8 bairros avaliados com scores 0–100 em 4 critérios
- Sliders de peso para personalizar em tempo real
- Clique no bairro filtra anúncios da Aba 1

---

## Deploy

### 1. Fork / clone e push
```bash
git clone https://github.com/andrebatistatech/proj-aluguel.git
cd proj-aluguel
git remote set-url origin https://github.com/SEU_USUARIO/SEU_REPO.git
git push -u origin main
```

### 2. Ativar GitHub Pages
Settings → Pages → Source: **GitHub Actions**

### 3. Filtros opcionais
Settings → Variables → Actions:

| Variável | Padrão | Descrição |
|---|---|---|
| `MAX_PRICE` | 3000 | Preço máximo (R$) |
| `MIN_PRICE` | 500 | Preço mínimo (R$) |
| `MIN_AREA` | 30 | Área mínima (m²) |
| `BEDROOMS` | 0 | Quartos mínimos (0 = qualquer) |

### 4. Rodar manualmente
Actions → Monitoramento Aluguel → **Run workflow**

---

## Executar localmente

```bash
# instalar dependências
pip install -r requirements.txt
playwright install chromium

# scraping
python scraper/scraper.py

# gerar dashboard
python dashboard/build_dashboard.py

# abrir
start dashboard/index.html    # Windows
open dashboard/index.html     # macOS
```

---

## Estrutura

```
proj-aluguel/
├── .github/workflows/monitor.yml   # cron 6h + deploy Pages
├── scraper/scraper.py              # scraping 4 fontes + filtros + dedup
├── dashboard/
│   ├── build_dashboard.py          # gera index.html a partir do JSON
│   └── index.html                  # dashboard final (gerado — não editar)
├── data/
│   ├── listings.json               # histórico (máx 500)
│   └── seen_ids.json               # IDs vistos para dedup
├── requirements.txt
├── prod.md                         # contexto técnico completo
└── README.md
```

---

## Frequência

Cron: `0 */6 * * *` — roda às 00h, 06h, 12h, 18h UTC.

Para rodar de hora em hora: `cron: "0 * * * *"`
