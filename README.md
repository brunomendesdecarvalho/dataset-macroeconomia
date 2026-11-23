# MacroData Brasil — dataset macroeconômico cross-country com variáveis heterodoxas e baseline SVAR

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24480760.svg)](https://doi.org/10.5281/zenodo.24480760)

**Versão 1.0.0** · **Início da execução:** 2026-11-23T18:13:37Z (15:13:37 −03) · **Duração total:** `03h33min26s`

## Resumo

Dataset macroeconômico cross-country com o **Brasil como âncora**, cobrindo **22 países soberanos** (mais o agregado `EU` e o agregado mundial `WLD`), em duas frequências: **anual 1960–2026** e **trimestral 1995T1–2026T4**. O núcleo ortodoxo é combinado com **quatro blocos heterodoxos** — distribuição e classe, restrição externa e hierarquia monetária, financiarização e crédito, ecologia e estrutura produtiva — e com um **baseline empírico reproduzível** (Regra de Taylor, Curva de Phillips, SVAR recursivo com robustez ao filtro HP, Projeções Locais de Jordà e comparação Brasil–EUA–México). O modelo estrutural foi removido do pipeline ativo.

O dataset é _research-ready_: inclui codebook, manifesto de proveniência com SHA-256, matriz de cobertura, 101 dummies de regime, relatório de auditoria, testes automatizados e uma planilha Excel única com abas limpas e cabeçalho congelado.

## Escopo e grupos

- **Países:** ARG, AUS, BRA, CAN, CHL, CHN, COL, DEU, FRA, GBR, IDN, IND, ITA, JPN, KOR, MEX, PER, RUS, SAU, TUR, USA, ZAF.
- **Agregados:** `EU` (União Europeia; nunca somada aos membros) e `WLD` (PIB mundial).
- **Grupos fechados:** BRICS, G20 (19 + UE), G7, TOP10_NOMINAL (PIB nominal USD, WEO 2025), LATAM6, EMERG_COMP, ADVANCED, QUARTERLY_CORE (16), COMMODITY_EXPORTERS, HIGH_INFLATION_HISTORY, IT_REGIME.
- **Trimestral:** 16 países (BRA, USA, DEU, GBR, JPN, CAN, MEX, AUS, FRA, ITA, KOR, ZAF, TUR, IDN, ARG, SAU). China, Índia, Chile, Colômbia, Peru e Rússia ficam no anual.

## Estrutura dos arquivos entregues

| Arquivo | Conteúdo |
|---|---|
| [data/exports/macro_dataset_consolidado.xlsx](data/exports/macro_dataset_consolidado.xlsx) | **Planilha única**: `Anual_Wide`, `Trimestral_Wide`, `Regimes_Anual`, `Codebook_Fontes`; cabeçalho congelado e autofiltro. |
| [data/exports/macro_anual_wide.csv](data/exports/macro_anual_wide.csv) | Wide anual: uma linha por `(iso3, country, year, date)`, todas as variáveis. |
| [data/exports/macro_trimestral_wide.csv](data/exports/macro_trimestral_wide.csv) | Wide trimestral: uma linha por `(iso3, country, quarter, date)`. |
| [data/exports/macro_todos_dados_long.csv](data/exports/macro_todos_dados_long.csv) | Long único: `freq, iso3, country, date, period, variable, block, value, unit, source, source_code, quality_flag, is_forecast, regime_dummy`. |
| [data/processed/macro_long.parquet](data/processed/macro_long.parquet) | Dataset interno completo (anual + trimestral). |
| [docs/01_codebook.md](docs/01_codebook.md) | Codebook, dicionário de campos, blocos, fontes e lacunas. |
| [docs/04_audit_report.md](docs/04_audit_report.md) | Auditoria: cobertura, identidades, divergências, estacionariedade, quebras e riscos. |
| [docs/06_metodologia.md](docs/06_metodologia.md) | Metodologia, harmonização, tratamento e exportação. |
| [docs/07_empirical_svar.md](docs/07_empirical_svar.md) | Taylor, Phillips, SVAR, Projeções Locais e cross-country. |
| [reports/figures/](reports/figures/) | `fig_svar_lp_brazil.png`, `fig_svar_crosscountry.png`, `fig_svar_hp_vs_level.png` e demais figuras. |

## Resultados e auditoria

| Dimensão | Número final |
|---|---|
| Linhas anuais / trimestrais / totais | **123.387 / 19.357 / 142.744** |
| Variáveis anuais / trimestrais | **114 / 28** |
| Cobertura mediana — `macro_core` | **97,0%** (média 85,0%) |
| Cobertura mediana — distribuição | **52,2%** (média 59,8%) |
| Cobertura mediana — restrição externa | **82,1%** (média 70,7%) |
| Cobertura mediana — financiarização | **37,3%** (média 42,6%) |
| Cobertura mediana — ecologia/estrutura | **82,1%** (média 70,9%) |
| Dummies de regime | **101** (30 para o Brasil; 1.474 país-ano × 101 e 2.048 país-trimestre × 97) |
| Identidade nominal = real × deflator | resíduo máximo **6×10⁻⁶%** |
| Identidade Y = C + I + NX | mediana **0,0002% do PIB** |
| Cross-source — crescimento | erro médio **0,23 p.p.**; 95% dentro de 1 p.p. |
| Cross-source — inflação | erro médio **3,42 p.p.**; 96% dentro de 2 p.p. |
| SVAR Brasil | 108 obs; **2 lags** (BIC), estável; brancura rejeitada (p=0,002) |
| FEVD do choque monetário (12T) | **15,0% do hiato**, **7,4% da inflação** |
| IRF +100 pb | hiato **−0,32 p.p.** (h=5); inflação **+0,38 p.p.** (h=2); câmbio **−1,26 p.p.** (h=1) |
| Robustez HP vs. nível | pico acumulado **−2,68 p.p.** (hiato) vs. **−6,17%** (log-nível com tendência) |
| Taylor | φπ de longo prazo **1,576** (s.e. 0,345; p unilateral 0,047); pós-metas 2,588 (s.e. 1,152; p=0,084) |

**Limitações explícitas:** zero imputação (lacunas = ausência de linha); perímetros fiscais distintos (dívida bruta vs. líquida; primário governo geral vs. central); 2026 é preliminar e `is_forecast=True`; vintage limitado (SGS não guarda versões; WDI/WEO revisam); a robustez HP vs. log-nível não elimina o *price puzzle* brasileiro; o SVAR recursivo tem identificação por Cholesky e não resolve todos os problemas; a UE é agregada e não entra em somas.

## Transparência metodológica, fluxo assistido por IA e tempos

**Fluxo de construção e validação:**

- **Ideia inicial:** Deepseek Flash 4.1
- **Revisão dos prompts:** Gemini Neon
- **Refinamento com base na literatura científica:** LeapSpace
- **Aplicação do refinamento final:** Gemini Neon
- **Agente de execução e engenharia de dados:** Deepseek Harness utilizando `deepseek-flash`

| Etapa | Duração |
|---|---|
| Etapa 1 — Construção inicial crua (coleta, harmonização, auditoria e protótipo DSGE) | `2h28min38s` |
| Etapa 2 — Macroeconometria empírica (SVAR, Projeções Locais, Taylor e Phillips) | `10min36s` |
| Etapa 3 — Refinamento pela literatura via LeapSpace (remoção do DSGE, 4 blocos heterodoxos, exportação consolidada e documentação) | `00h54min12s` |
| **Total** | **`03h33min26s`** |

A Etapa 3 foi medida a partir do timestamp `2026-11-23T18:13:37Z`; o cálculo usa o relógio do sistema e está registrado em `data/processed/refactor_timing.json`.

## Reprodutibilidade

```bash
python3 -m venv --system-site-packages .venv
.venv/bin/pip install -r requirements.txt

make all        # fetch -> build -> validate -> empirical -> export -> reports -> tests
make empirical  # apenas Taylor, Phillips, SVAR (gap/núcleo/nível), LP e cross-country
make export     # apenas Excel + CSVs consolidados
make test       # pytest
```

- O cache em `data/raw/` é reutilizado; os novos indicadores WDI usam timeout de 20 s, **zero retries** e fast-fail em 400/403/404.
- `data/processed/manifest.json` registra URL, timestamp, tamanho e **SHA-256** de cada download.
- `data/processed/refactor_timing.json` registra o início e a duração da Etapa 3.
- Versões fixadas em `requirements.txt`.

## Autoria e afiliação

**Bruno Mendes de Carvalho Castelo Branco** — projeto independente. Doutorando na Universidade Federal do Piauí (UFPI); este dataset não faz parte da pesquisa de doutorado. ORCID: https://orcid.org/0009-0005-8188-9001.

## Como citar

### BibTeX

```bibtex
@dataset{castelo_branco_macrodata_2026,
  author       = {CASTELO BRANCO, Bruno Mendes de Carvalho},
  title        = {MacroData Brasil: dataset macroeconômico cross-country com variáveis heterodoxas e baseline SVAR},
  year         = {2026},
  publisher    = {Zenodo},
  version      = {1.0.0},
  doi          = {10.5281/zenodo.24480760},
  url          = {https://doi.org/10.5281/zenodo.24480760},
  license      = {CC-BY-4.0}
}
```

### APA

CASTELO BRANCO, Bruno Mendes de Carvalho. (2026). *MacroData Brasil: dataset macroeconômico cross-country com variáveis heterodoxas e baseline SVAR* (Versão 1.0.0) [Data set]. Zenodo. https://doi.org/10.5281/zenodo.24480760

## Licenças

- **Código:** MIT — ver [LICENSE](LICENSE).
- **Dados:** CC-BY-4.0, preservando as licenças das fontes originais (GMD/WDI/PWT CC BY 4.0; FRED/OCDE/BIS/FMI/BCB/IBGE conforme termos) — ver [LICENSE-DATA.md](LICENSE-DATA.md).
- **Citação:** `CITATION.cff` na raiz, compatível com GitHub/Zenodo.
