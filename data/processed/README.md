# Produtos processados

| Arquivo | Conteúdo |
|---|---|
| `macro_long.parquet` / `.csv` | Dataset longo completo (anual + trimestral), 28 colunas |
| `macro_annual_long.parquet` | Painel anual 1960–2026 |
| `macro_quarterly_long.parquet` | Painel trimestral 1995T1–2026T4 |
| `wide/annual/{ISO3}.csv` | Série wide por país (data × variável) |
| `wide/quarterly/{ISO3}.csv` | Série wide trimestral por país |
| `wide/annual_panel.parquet` | Painel wide (iso3, date) × variável |
| `coverage.csv` / `coverage_matrix_annual.csv` / `coverage_matrix_quarterly.csv` | Cobertura por país-variável e matriz |
| `coverage_panel_annual.csv` | Matriz 0/1 país × variável × ano (131.186 linhas) |
| `coverage_panel_quarterly.csv` | Matriz 0/1 país × variável × trimestre (57.344 linhas) |
| `regime_by_country/` | Matriz país × ano (ou trimestre) × dummy, um CSV por país |
| `regime_matrix_annual.csv` | 1.474 país-ano × 101 dummies (0/1) |
| `regime_matrix_quarterly.csv` | 2.048 país-trimestre × 97 dummies |
| `regime_metadata.csv` | Metadados das dummies |
| `cross_source_*.csv` | Comparação GMD/WEO/WDI/BCB |
| `identity_summary.csv` | Resíduos das identidades |
| `stationarity.csv` | ADF/KPSS por série-país |
| `bai_perron.csv`, `breaks_regime_map.csv`, `chow.csv` | Quebras |
| `quarterly_annual.csv` | Consistência anual-trimestral |
| `outliers.csv` | Outliers por série-país |
| `source_decisions.csv` | Decisões de fonte/tolerância |
| `cross_country_moments.csv` | Médias, desvios-padrão e autocorrelações por país (1995–2025) |
| `empirical_taylor_*` | Regra de Taylor (HAC), com expectativas e robustez pós-metas |
| `empirical_phillips_*` | Curva de Phillips (cheia e núcleo) |
| `empirical_svar_*` | Diagnósticos, IRFs, FEVD e comparação cross-country |
| `empirical_lp_brazil.csv` | Projeções Locais de Jordà (h=0..12, HAC) |
| `empirical_meta.json` | Metadados da rodada empírica |
| `manifest.json` | Proveniência de cada download |
| `refactor_timing.json` | Início e duração da Etapa 3 |
| `dataset_summary.json` | Contagens e período |

**Convenção:** `value` é sempre o valor bruto/construído na unidade de `unit`; a transformação recomendada está em `transformation`. Não há imputação.
