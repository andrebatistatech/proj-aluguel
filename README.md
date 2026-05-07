# 🏠 Rental Monitor — São Bento do Sul SC

Agente que raspa anúncios de aluguel das principais plataformas e publica um dashboard HTML atualizado automaticamente via GitHub Actions + GitHub Pages.

## Fontes monitoradas
- OLX
- ZAP Imóveis
- Viva Real
- Imovelweb

## Como fazer o deploy (passo a passo)

### 1. Criar repositório no GitHub
1. Acesse https://github.com/new
2. Nome sugerido: `rental-monitor-sbs`
3. Marque **Private** se quiser manter os dados privados
4. Clique em **Create repository**

### 2. Subir este código
```bash
git init
git add .
git commit -m "feat: rental monitor inicial"
git remote add origin https://github.com/SEU_USUARIO/rental-monitor-sbs.git
git push -u origin main
```

### 3. Ativar GitHub Pages
1. Acesse **Settings → Pages**
2. Em **Source**, selecione **GitHub Actions**
3. Salve

### 4. Personalizar os filtros (opcional)
Acesse **Settings → Variables → Actions** e crie as variáveis:

| Variável    | Padrão | Descrição               |
|-------------|--------|-------------------------|
| `MAX_PRICE` | 3000   | Preço máximo (R$)        |
| `MIN_PRICE` | 500    | Preço mínimo (R$)        |
| `MIN_AREA`  | 30     | Área mínima (m²)         |
| `BEDROOMS`  | 0      | Nº mínimo de quartos (0=qualquer) |

### 5. Rodar manualmente
Acesse a aba **Actions → Monitoramento Aluguel → Run workflow**

### 6. Acessar o dashboard
Após a primeira execução, acesse:
```
https://SEU_USUARIO.github.io/rental-monitor-sbs/
```

## Frequência de execução
O workflow roda automaticamente a cada **6 horas** (configurável no `monitor.yml`).

Para mudar para a cada hora:
```yaml
cron: "0 * * * *"
```

## Estrutura do projeto
```
.
├── .github/
│   └── workflows/
│       └── monitor.yml      # Agendamento GitHub Actions
├── scraper/
│   └── scraper.py           # Scraping das 4 fontes
├── dashboard/
│   ├── build_dashboard.py   # Gerador do HTML
│   └── index.html           # Dashboard gerado (não editar)
├── data/
│   ├── listings.json        # Histórico de anúncios
│   └── seen_ids.json        # IDs já vistos (dedup)
└── requirements.txt
```

## Funcionamento interno
1. O scraper acessa cada fonte e extrai título, preço, área, quartos, bairro e URL
2. Aplica filtros de preço e área
3. Deduplica por hash da URL (evita repetições entre execuções)
4. Salva em `data/listings.json` (últimos 500 anúncios)
5. O gerador lê o JSON e produz `dashboard/index.html`
6. O GitHub Actions faz commit dos dados e publica no Pages

## Rodando localmente
```bash
pip install -r requirements.txt
python scraper/scraper.py
python dashboard/build_dashboard.py
open dashboard/index.html
```
