# Codebook — dataset macroeconômico cross-country (v1.0.0)

Extração: **2026-11-23T16:43:19Z**. Âncora: **Brasil**. Anual 1960–2026; trimestral 1995T1–2026T4.

## 1. Arquivos e grão

| Arquivo | Grão | Linhas | Uso |
|---|---|---|---|
| `data/processed/macro_long.parquet` | país × data × variável | 121,175 | dataset longo completo (anual + trimestral) |
| `data/processed/macro_annual_long.parquet` | país × ano × variável | 101,818 | painel anual |
| `data/processed/macro_quarterly_long.parquet` | país × trimestre × variável | 19,357 | subamostra trimestral |
| `data/processed/wide/annual/{ISO3}.csv` | data × variável | 22+2 países | série wide por país |
| `data/processed/wide/quarterly/{ISO3}.csv` | data × variável | 16 países | série wide trimestral |
| `data/processed/regime_matrix_annual.csv` | país × ano × dummy | 1,474 × 101 | matriz 0/1 de regimes |
| `data/processed/regime_matrix_quarterly.csv` | país × trimestre × dummy | 2,048 × 97 | matriz 0/1 trimestral |
| `data/processed/coverage_matrix_annual.csv` | variável × país | 89 × 24 | % de cobertura |
| `data/processed/coverage_panel_annual.csv` | país × variável × ano | 131.186 | matriz 0/1 de presença |

## 2. Dicionário de campos

| campo | tipo | descrição |
|---|---|---|
| iso3 | string | Código ISO3 do país; `WLD` = mundo (agregado); `EU` = União Europeia (agregado, excluído de somas). |
| country | string | Nome em português. |
| date | date | Fim do período: 31/12 do ano (anual) ou último dia do trimestre (trimestral). |
| year | int | Ano do período (facilita merges anuais). |
| variable | string | Identificador canônico (ver seção 5). |
| value | float | Valor na unidade declarada; nunca em log (a transformação recomendada está em `transformation`). |
| unit | string | Unidade nativa (%, % do PIB, milhões de LC, índice etc.). |
| freq | string | `A` (anual) ou `Q` (trimestral). |
| source | string | Fonte efetiva da linha (GMD, WDI, WEO, PWT, FRED, BCB, IBGE, BCB_FOCUS, derived, hardcoded). |
| source_code | string | Código original (coluna GMD, indicador WDI/WEO, ID FRED, código SGS/SIDRA). |
| source_detail | string | Descrição legível da série original. |
| source_url | string | URL da fonte. |
| vintage | string | Versão/vintage da fonte (quando disponível). |
| transformation | string | Transformação recomendada para estimação: level, log, yoy, diff, hp_gap, hp_trend, fisher, pct_gdp, index, dummy, derived. |
| transform_applied | string | Sempre `none` neste arquivo: o valor é bruto/construído, não transformado. A pipeline DSGE aplica as transformações. |
| role | string | endogenous, exogenous, latent, shock, regime, validation. |
| model | string | Modelos em que a variável entra: ISLM, MF, ADAS, PC, TR, SOLOW, DSGE_S, DSGE_M. |
| dsge_var | string | Nome da variável no DSGE (quando aplicável). |
| measurement_equation | string | Equação de medida do DSGE (quando observável). |
| shock | string | Choque associado (quando a variável identifica um choque). |
| coverage_note | string | Nota de cobertura temporal. |
| notes | string | Definição, ressalvas e decisões. |
| is_forecast | bool | True para projeções (GMD/WEO > 2025) ou anos preliminares. |
| quality_flag | string | ok, preliminary, forecast, derived, proxy, hp_filter, survey, policy, validation. |
| seasonal_adjustment | string | SA, NSA ou n/a. |
| imputation | string | none (não há imputação no dataset final; lacunas são preservadas). |
| extraction_date | string | Timestamp UTC da extração. |
| regime_dummy | string | Lista separada por `\|` das dummies ativas naquele país-data. |

## 3. Convenções

- **Sinal fiscal**: resultado primário e balanço fiscal positivos = superávit; negativos = déficit.
- **Câmbio nominal**: unidades de moeda local por 1 USD (aumento = depreciação). Para EUR/GBP/AUD, a série do FRED (USD por LC) foi invertida.
- **Deflator**: `gdp_deflator` tem base igual ao ano-base do PIB real do país (identidade nominal = real × deflator/100). `gdp_deflator_2010` é a versão 2010=100 para comparação.
- **Juros**: % a.a. no anual; % a.a. no trimestral (média do período). A taxa trimestral usada no DSGE é i/4.
- **Inflação**: % a.a. (variação 12 meses). No Brasil, `inflation` anual e trimestral vem do IPCA (BCB/IBGE), não do GMD; nos demais países, do GMD/OECD-MEI.
- **Spread de crédito**: não há série trimestral harmonizada; a variável foi removida do dataset e a lacuna está registrada na auditoria.
- **PIB real**: milhões de LC a preços constantes; a base varia por país. Não comparar níveis entre países sem `gdp_real_usd`.
- **PPPs**: `gdp_ppp_usd` em milhões de int$ (WEO PPPGDP × 1000).
- **FRED**: os templates usam `{ISO2}` (código de 2 letras); o ID exato de cada país/série está em `source_code`. Para EUA/MEX, o SVAR empírico usa `short_rate` e `reer`.
- **Capital**: `capital_stock` usa `rnna` (PWT, capital a preços nacionais constantes, milhões USD 2017), não `rkna` (índice 2017=1).
- **Forecast**: 2026 é ano em curso (preliminary); 2027+ não entra. Projeções WEO/GMD para 2026 são marcadas.

## 4. Registro de fontes

| id | fonte | versão | cobertura | papel |
|---|---|---|---|---|
| GMD | Global Macro Database (GMD) | 2026_09 (release notes de set/2026) | 243 países, anual, 1086–2025/26; foco pós-1950; 46 variáveis | espinha dorsal anual |
| WDI | World Development Indicators | API v2, lastupdated variável por indicador (gravado no manifesto) | 217 economias + agregados, anual, 1960–2025/26 | complemento e validação cruzada |
| WEO | World Economic Outlook Database | outubro/2025 (DataMapper API; campo lastupdated no manifesto) | 1980–2031 (projeções); anual | complemento fiscal (resultado primário, dívida líquida) e validação |
| PWT | Penn World Table 10.01 | 10.01 (2019 como último ano) | 183 países, anual, 1950–2019 | capital, PTF, emprego, horas, capital humano e participação do trabalho |
| FRED | Federal Reserve Economic Data | extração via fredgraph.csv (sem chave); vintage = data de extração | anual/trimestral/mensal/diária; cobertura por série | subamostra trimestral; commodities; VIX; juros dos EUA |
| OECD_MEI | OECD Main Economic Indicators (via FRED) | vintage FRED na data de extração | trimestral, países OCDE e alguns não membros | fonte original das séries trimestrais de CPI, desemprego e juros |
| BIS | BIS Effective Exchange Rate (via FRED) | vintage FRED na data de extração | mensal, 1994–presente | câmbio real efetivo |
| BCB | Banco Central do Brasil — Sistema Gerenciador de Séries Temporais (SGS) | vintage na data de extração (SGS não guarda vintages) | diário/mensal/trimestral/anual; 1980–presente (por série) | Brasil: juros, câmbio, IPCA, núcleo, desemprego, crédito, fiscal |
| IBGE | IBGE — SIDRA / Contas Nacionais Trimestrais e IPCA | SIDRA v3, período final 2026T2 (na extração) | trimestral 1996–2026 (CNT); mensal 1980–2026 (IPCA) | Brasil: PIB trimestral e componentes da despesa; IPCA |
| IMF_IFS | IMF International Financial Statistics | via GMD (2026_09) | anual/mensal; histórico longo | fonte primária histórica incorporada pelo GMD |
| OECD_EO | OECD Economic Outlook | via GMD (2026_09) | anual/semestral, 1960–presente | complemento histórico pós-1980 incorporado pelo GMD |
| BACEN_FOCUS | BCB — Relatório Focus (expectativas de mercado) | vintage na data de extração | Brasil, mensal, 2001–presente (IPCA 12 meses); séries adicionais por indicador | expectativas de inflação (survey) para o Brasil |
| MICH | University of Michigan — Inflation Expectations | vintage FRED | EUA, mensal, 1978–presente | expectativas de inflação (survey) para os EUA |

## 5. Dicionário de variáveis

| variável | freq | rótulo | unidade | fonte | código | transformação | papel | modelos | n_países | cobertura_mediana_% | cobertura |
|---|---|---|---|---|---|---|---|---|---|---|---|
| gdp_nominal | A | PIB nominal | milhões de LC correntes | GMD | nGDP | level | endogenous | ISLM,MF,ADAS,DSGE_S,DSGE_M | 22.0 | 100.0 | 1950–2025/26 |
| gdp_real | A | PIB real | milhões de LC, preços constantes | GMD | rGDP | log | endogenous | ISLM,ADAS,SOLOW,DSGE_S,DSGE_M | 22.0 | 100.0 | 1950–2025/26 |
| gdp_real_usd | A | PIB real em USD | milhões de USD constantes | GMD | rGDP_USD | log | exogenous | SOLOW,DSGE_M | 22.0 | 97.01492537313432 | 1950–2025/26 |
| gdp_nominal_usd | A | PIB nominal em USD | milhões de USD correntes | derived | nGDP/USDfx | level | exogenous | MF,DSGE_M | 22.0 | 98.50746268656717 | Calculado como nGDP dividido pela taxa de câmbio média do ano. |
| gdp_real_pc | A | PIB real per capita | LC constantes per capita | GMD | rGDP_pc | log | endogenous | SOLOW | 22.0 | 100.0 | Usado no modelo de Solow e em convergência. |
| gdp_deflator | A | Deflator implícito do PIB | índice (ano-base do PIB real = 100) | GMD | deflator | index | endogenous | ADAS,DSGE_S,DSGE_M | 22.0 | 100.0 | 1950–2025/26 |
| gdp_ppp_usd | A | PIB em paridade de poder de compra | milhões de int$ correntes | WEO | PPPGDP | level | exogenous | SOLOW,DSGE_M | 23.0 | 70.14925373134328 | Apenas para comparação de níveis; não entra na lista TOP10_NOMINAL. |
| gdp_growth | A | Crescimento real do PIB | % a.a. | derived | dlog(gdp_real) | yoy | endogenous | ADAS,PC,SOLOW,DSGE_S,DSGE_M | 22.0 | 98.50746268656717 | 1960–2025/26 |
| potential_gdp | A | PIB potencial | milhões de LC constantes | derived | HP(log(gdp_real), λ=100) | hp_trend | latent | ADAS,DSGE_S,DSGE_M | 22.0 | 98.50746268656717 | 1960–2025/26 |
| output_gap | A | Hiato do produto | % do PIB potencial | derived | 100*(log(gdp_real)-log(potential_gdp)) | hp_gap | latent | ADAS,PC,TR,DSGE_S,DSGE_M | 22.0 | 98.50746268656717 | 1960–2025/26 |
| consumption_real | A | Consumo final real | milhões de LC constantes | GMD | cons | log | endogenous | ISLM,ADAS,DSGE_M | 22.0 | 98.50746268656717 | 1950–2025/26 |
| consumption_gdp | A | Consumo final (% do PIB) | % do PIB | GMD | cons_GDP | pct_gdp | endogenous | ISLM,ADAS,DSGE_M | 22.0 | 98.50746268656717 | Razão nominal. |
| investment_real | A | Formação bruta de capital real | milhões de LC constantes | GMD | inv | log | endogenous | ISLM,ADAS,DSGE_M | 22.0 | 100.0 | 1950–2025/26 |
| investment_gdp | A | Investimento (% do PIB) | % do PIB | GMD | inv_GDP | pct_gdp | endogenous | ISLM,DSGE_M | 22.0 | 100.0 | Razão nominal. |
| fixed_investment_real | A | Formação bruta de capital fixo real | milhões de LC constantes | GMD | finv | log | endogenous | DSGE_M | 22.0 | 98.50746268656717 | 1950–2025/26 |
| fixed_investment_gdp | A | Formação bruta de capital fixo (% do PIB) | % do PIB | GMD | finv_GDP | pct_gdp | endogenous | DSGE_M | 22.0 | 98.50746268656717 | Razão nominal. |
| gov_exp_real | A | Despesa do governo real | milhões de LC constantes | GMD | govexp | log | exogenous | ISLM,MF,ADAS,DSGE_M | 22.0 | 100.0 | 1950–2025/26 |
| gov_exp_gdp | A | Despesa do governo (% do PIB) | % do PIB | GMD | govexp_GDP | pct_gdp | exogenous | ISLM,MF,ADAS,DSGE_M | 22.0 | 100.0 | Razão nominal. |
| gov_revenue_gdp | A | Receita do governo (% do PIB) | % do PIB | GMD | govrev_GDP | pct_gdp | exogenous | ISLM,DSGE_M | 22.0 | 100.0 | 1950–2025/26 |
| tax_burden_gdp | A | Carga tributária (% do PIB) | % do PIB | GMD | govtax_GDP | pct_gdp | exogenous | ISLM,DSGE_M | 22.0 | 94.02985074626864 | Tributos sobre produção e importação; não é receita total. |
| gov_balance_gdp | A | Resultado fiscal (% do PIB) | % do PIB | GMD | govdef_GDP | pct_gdp | exogenous | ISLM,DSGE_M | 22.0 | 100.0 | 1950–2025/26 |
| gov_debt_gdp | A | Dívida bruta do governo (% do PIB) | % do PIB | GMD | govdebt_GDP | pct_gdp | exogenous | DSGE_M | 22.0 | 100.0 | 1950–2025/26 |
| exports_gdp | A | Exportações (% do PIB) | % do PIB | GMD | exports_GDP | pct_gdp | exogenous | ISLM,MF,DSGE_M | 22.0 | 100.0 | Bens e serviços, preços correntes. |
| imports_gdp | A | Importações (% do PIB) | % do PIB | GMD | imports_GDP | pct_gdp | exogenous | ISLM,MF,DSGE_M | 22.0 | 100.0 | Bens e serviços, preços correntes. |
| net_exports_gdp | A | Exportações líquidas (% do PIB) | % do PIB | derived | exports_GDP - imports_GDP | pct_gdp | endogenous | ISLM,MF,ADAS,DSGE_M | 22.0 | 100.0 | 1950–2025/26 |
| current_account_gdp | A | Conta corrente (% do PIB) | % do PIB | GMD | CA_GDP | pct_gdp | exogenous | MF,DSGE_M | 22.0 | 100.0 | Inclui renda de fatores e transferências. |
| cpi_index | A | Índice de preços ao consumidor | índice 2010=100 | GMD | CPI | index | endogenous | PC,ADAS | 22.0 | 100.0 | 1950–2025/26 |
| inflation | A | Inflação ao consumidor | % a.a. | GMD | infl | yoy | endogenous | ADAS,PC,TR,DSGE_S,DSGE_M | 22.0 | 100.0 | 1950–2025/26 |
| population | A | População | milhões | GMD | pop | log | exogenous | SOLOW | 22.0 | 100.0 | Usada em n e em per capita. |
| unemployment | A | Taxa de desemprego | % da força de trabalho | GMD | unemp | level | endogenous | PC,DSGE_M | 22.0 | 93.28358208955224 | 1950–2025/26 |
| short_rate | A | Juro de curto prazo | % a.a. | GMD | strate | level | endogenous | ISLM,MF,TR,DSGE_S | 22.0 | 95.52238805970148 | 1950–2025/26 |
| long_rate | A | Juro de longo prazo | % a.a. | GMD | ltrate | level | endogenous | ISLM,DSGE_M | 21.0 | 67.16417910447761 | Título soberano de longo prazo; usado na curva de juros e na dívida. |
| policy_rate | A | Taxa de política monetária | % a.a. | GMD | cbrate | level | exogenous | TR,DSGE_S,DSGE_M | 22.0 | 98.50746268656717 | 1950–2025/26 |
| m0 | A | Base monetária | milhões de LC | GMD | M0 | log | exogenous | ISLM,MF | 21.0 | 94.02985074626864 | Agregado monetário restrito. |
| m1 | A | M1 | milhões de LC | GMD | M1 | log | exogenous | ISLM,MF | 22.0 | 94.02985074626864 | Papel-moeda + depósitos à vista. |
| m2 | A | M2 | milhões de LC | GMD | M2 | log | exogenous | ISLM,MF | 21.0 | 92.53731343283582 | M1 + depósitos de poupança e a prazo. |
| m3 | A | M3 | milhões de LC | GMD | M3 | log | exogenous | ISLM,MF | 19.0 | 64.17910447761194 | M2 + títulos e outros passivos. |
| exchange_rate_nominal | A | Taxa de câmbio nominal | LC por USD (média anual) | GMD | USDfx | log | endogenous | MF,DSGE_M | 22.0 | 98.50746268656717 | 1950–2025/26 |
| reer | A | Câmbio real efetivo | índice 2010=100 | GMD | REER | log | endogenous | MF,DSGE_M | 22.0 | 98.50746268656717 | 1950–2025/26 |
| hpi | A | Índice de preços de imóveis | índice 2010=100 | GMD | HPI | log | exogenous | DSGE_M | 21.0 | 74.6268656716418 | Onde disponível; usado como controle de riqueza. |
| primary_balance_gdp | A | Resultado primário (% do PIB) | % do PIB | WEO | pb | pct_gdp | exogenous | ISLM,DSGE_M | 22.0 | 67.16417910447761 | 1980–2031 |
| net_debt_gdp | A | Dívida líquida do governo (% do PIB) | % do PIB | WEO | GGXWDN_G01_GDP_PT | pct_gdp | exogenous | DSGE_M | 18.0 | 47.76119402985075 | Dívida líquida; cobertura menor que a bruta. |
| inflation_weo | A | Inflação (WEO) | % a.a. | WEO | PCPIPCH | yoy | validation | ADAS,PC | 23.0 | 70.14925373134328 | Série de validação/forecast; is_forecast=1 para anos > 2025. |
| gov_debt_gdp_weo | A | Dívida bruta (WEO) | % do PIB | WEO | GGXWDG_NGDP | pct_gdp | validation | DSGE_M | 23.0 | 47.76119402985075 | Validação cruzada da dívida. |
| gdp_growth_weo | A | Crescimento do PIB (WEO) | % a.a. | WEO | NGDP_RPCH | yoy | validation | ADAS | 23.0 | 70.14925373134328 | Validação cruzada do crescimento. |
| gdp_nominal_usd_weo | A | PIB nominal USD (WEO) | milhões de USD | WEO | NGDPD | level | validation | MF | 23.0 | 70.14925373134328 | Validação cruzada do PIB nominal. |
| unemployment_weo | A | Desemprego (WEO) | % | WEO | LUR | level | validation | PC | 22.0 | 70.14925373134328 | Validação cruzada do desemprego. |
| participation_rate | A | Taxa de participação | % da população em idade ativa | WDI | SL.TLF.CACT.ZS | level | endogenous | DSGE_M | 23.0 | 53.73134328358209 | Força de trabalho / população 15+. |
| credit_private_gdp | A | Crédito ao setor privado (% do PIB) | % do PIB | WDI | FS.AST.PRVT.GD.ZS | pct_gdp | exogenous | DSGE_M | 23.0 | 83.58208955223881 | Crédito doméstico ao setor privado; fricção financeira. |
| gov_consumption_gdp | A | Consumo do governo (% do PIB) | % do PIB | WDI | NE.CON.GOVT.ZS | pct_gdp | validation | ISLM,DSGE_M | 23.0 | 98.50746268656717 | Validação/complemento de gov_exp_gdp. |
| gross_capital_formation_gdp | A | Formação bruta de capital (% do PIB) | % do PIB | WDI | NE.GDI.TOTL.ZS | pct_gdp | validation | ISLM,DSGE_M | 23.0 | 98.50746268656717 | Validação/complemento de investment_gdp. |
| tax_revenue_gdp_wdi | A | Receita tributária (% do PIB) | % do PIB | WDI | GC.TAX.TOTL.GD.ZS | pct_gdp | validation | DSGE_M | 23.0 | 68.65671641791045 | Validação da carga tributária. |
| central_gov_debt_gdp | A | Dívida do governo central (% do PIB) | % do PIB | WDI | GC.DOD.TOTL.GD.ZS | pct_gdp | validation | DSGE_M | 17.0 | 31.34328358208955 | Validação/complemento da dívida bruta. |
| real_gdp_wdi | A | PIB real (WDI) | USD constantes de 2015 | WDI | NY.GDP.MKTP.KD | log | validation | ADAS,SOLOW |  |  | Validação cruzada do nível de PIB real. |
| inflation_wdi | A | Inflação (WDI) | % a.a. | WDI | FP.CPI.TOTL.ZG | yoy | validation | ADAS,PC | 23.0 | 98.50746268656717 | Validação cruzada da inflação. |
| unemployment_wdi | A | Desemprego (WDI) | % | WDI | SL.UEM.TOTL.ZS | level | validation | PC | 23.0 | 52.23880597014925 | Validação cruzada do desemprego (OIT). |
| population_wdi | A | População (WDI) | pessoas | WDI | SP.POP.TOTL | log | validation | SOLOW | 23.0 | 98.50746268656717 | Validação da população. |
| world_gdp_real | A | PIB real mundial | USD constantes de 2015 | WDI | NY.GDP.MKTP.KD | log | exogenous | MF,DSGE_M | 23.0 | 98.50746268656717 | 1960–2025/26 |
| world_gdp_growth | A | Crescimento do PIB mundial | % a.a. | derived | dlog(world_gdp_real) | yoy | exogenous | MF,DSGE_M | 1.0 | 97.01492537313432 | Choque externo comum. |
| capital_stock | A | Estoque de capital | milhões de USD constantes de 2017 | PWT | rnna | log | endogenous | SOLOW,DSGE_M | 22.0 | 89.55223880597015 | 1950–2019 |
| tfp | A | PTF (TFP) | índice 2017=1 | PWT | rtfpna | log | endogenous | SOLOW,DSGE_M | 22.0 | 89.55223880597015 | 1950–2019 |
| employment | A | Emprego | milhões de trabalhadores | PWT | emp | log | endogenous | SOLOW,DSGE_M | 22.0 | 89.55223880597015 | 1950–2019 |
| hours_worked | A | Horas trabalhadas por trabalhador | horas/ano | PWT | avh | log | endogenous | DSGE_M | 21.0 | 89.55223880597015 | 1950–2019 |
| labor_share | A | Participação do trabalho na renda | fração (0–1) | PWT | labsh | level | endogenous | DSGE_M | 22.0 | 89.55223880597015 | PWT labsh; usado para calibrar salário/markup. |
| human_capital | A | Capital humano | índice | PWT | hc | log | exogenous | SOLOW | 22.0 | 89.55223880597015 | PWT hc. |
| capital_output_ratio | A | Razão capital-produto | razão | derived | capital_stock/gdp_real | level | endogenous | SOLOW | 22.0 | 89.55223880597015 | Unidades compatíveis (ambas em USD constantes de 2017). |
| tfp_growth | A | Crescimento da PTF | % a.a. | derived | dlog(tfp) | yoy | endogenous | SOLOW,DSGE_M |  |  | Choque de tecnologia. |
| commodity_price_index | A | Índice de preços de commodities | índice (2016=100) | FRED | PALLFNFINDEXQ | log | exogenous | PC,DSGE_M | 1.0 | 52.23880597014925 | 1960–2025/26 |
| oil_price | A | Preço do petróleo Brent | USD/barril | FRED | POILBREUSDM | log | exogenous | ADAS,PC,DSGE_M | 1.0 | 52.23880597014925 | Média anual; choque de oferta. |
| vix | A | Índice de volatilidade VIX | índice | FRED | VIXCLS | log | exogenous | MF,DSGE_M | 1.0 | 55.223880597014926 | Proxy de prêmio de risco global. |
| foreign_policy_rate | A | Juro de política dos EUA | % a.a. | FRED | IR3TIB01USQ156N | level | exogenous | MF,DSGE_M | 1.0 | 100.0 | 1960–2025/26 |
| us_gdp_real | A | PIB real dos EUA | bilhões de USD encadeados de 2017 | FRED | GDPC1 | log | exogenous | MF,DSGE_M |  |  | 1947–2025/26 |
| real_rate_ex_post | A | Juro real ex post | % a.a. | derived | policy_rate - inflation | fisher | endogenous | ISLM,TR,DSGE_S | 22.0 | 98.50746268656717 | Aproximação de Fisher; usa inflação contemporânea. |
| real_rate_ex_ante | A | Juro real ex ante | % a.a. | derived | policy_rate - inflation_expectations | fisher | endogenous | TR,DSGE_S | 1.0 | 71.64179104477611 | 2001–2025/26 |
| neutral_rate | A | Taxa de juros neutra (r*) | % a.a. | derived | HP(real_rate_ex_ante, λ=100) | hp_trend | latent | TR,DSGE_S,DSGE_M | 1.0 | 71.64179104477611 | 2001–2025/26 |
| inflation_expectations | A | Expectativas de inflação (survey) | % a.a. 12 meses à frente | BCB_FOCUS | ExpectativasMercadoInflacao12Meses | level | exogenous | PC,TR,DSGE_S | 1.0 | 73.13432835820896 | 2001–2025/26 |
| inflation_target | A | Meta de inflação | % a.a. | hardcoded | metas por país | level | regime | TR,DSGE_S | 20.0 | 36.56716417910448 | Tabela em regimes.yml; ausente onde não há regime explícito. |
| debt_dynamics_residual | A | Resíduo da dinâmica da dívida | % do PIB | derived | identidade da dívida | derived | validation | DSGE_M | 22.0 | 65.67164179104478 | SFA (stock-flow adjustment); ver validação de identidades. |
| banking_crisis | A | Crise bancária (dummy) | 0/1 | GMD | BankingCrisis | dummy | regime | ADAS,DSGE_M | 21.0 | 86.56716417910448 | Dummy anual do GMD; complementa regimes.yml. |
| currency_crisis | A | Crise cambial (dummy) | 0/1 | GMD | CurrencyCrisis | dummy | regime | MF,DSGE_M | 21.0 | 86.56716417910448 | Dummy anual do GMD. |
| sovereign_debt_crisis | A | Crise de dívida soberana (dummy) | 0/1 | GMD | SovDebtCrisis | dummy | regime | DSGE_M | 21.0 | 86.56716417910448 | Dummy anual do GMD. |
| output_per_worker | A | Produto por trabalhador | LC constantes por trabalhador | derived | gdp_real/employment | log | endogenous | SOLOW,DSGE_M | 22.0 | 89.55223880597015 | Produtividade média do trabalho. |
| gdp_real | Q | PIB real trimestral | milhões de LC, preços constantes, SA | FRED | NGDPRSAXDC{ISO2}Q | log | endogenous | ADAS,DSGE_S,DSGE_M | 16.0 | 98.4375 | 1996–2026T2 |
| gdp_real_growth | Q | Crescimento trimestral do PIB | % a.a. (SAAR) | derived | 400*dlog(gdp_real) | yoy | endogenous | ADAS,DSGE_S,DSGE_M | 16.0 | 97.65625 | 1996–2026T2 |
| potential_gdp | Q | PIB potencial trimestral | milhões de LC constantes | derived | HP(log(gdp_real), λ=1600) | hp_trend | latent | ADAS,DSGE_S,DSGE_M | 16.0 | 98.4375 | 1996–2026T2 |
| output_gap | Q | Hiato do produto trimestral | % do PIB potencial | derived | 100*(log(gdp_real)-log(potential_gdp)) | hp_gap | latent | ADAS,PC,TR,DSGE_S,DSGE_M | 16.0 | 98.4375 | 1996–2026T2 |
| inflation | Q | Inflação ao consumidor trimestral | % a.a. (variação 4 trimestres) | FRED | CPALTT01{ISO2}Q659N | yoy | endogenous | ADAS,PC,TR,DSGE_S,DSGE_M | 14.0 | 94.53125 | 1996–2026T2 |
| core_inflation | Q | Núcleo da inflação | % a.a. | BCB | 11427 | yoy | endogenous | PC,DSGE_S | 2.0 | 100.0 | 2001–2026 |
| unemployment | Q | Taxa de desemprego trimestral | % | FRED | LRHUTTTT{ISO2}Q156S | level | endogenous | PC,DSGE_M | 12.0 | 99.21875 | 1996–2026T2 |
| policy_rate | Q | Taxa de política monetária trimestral | % a.a. | BCB | 432 | level | exogenous | TR,DSGE_S,DSGE_M | 1.0 | 87.5 | 1996–2026T2 |
| short_rate | Q | Juro de curto prazo trimestral | % a.a. | FRED | IR3TIB01{ISO2}Q156N | level | endogenous | ISLM,MF,DSGE_S | 13.0 | 99.21875 | Taxa de 3 meses interbancária. |
| long_rate | Q | Juro de longo prazo trimestral | % a.a. | FRED | IRLTLT01{ISO2}Q156N | level | endogenous | ISLM,DSGE_M | 11.0 | 99.21875 | Título soberano de 10 anos. |
| exchange_rate_nominal | Q | Taxa de câmbio nominal trimestral | LC por USD | FRED | DEX{ISO2} | log | endogenous | MF,DSGE_M | 12.0 | 100.0 | 1996–2026T2 |
| reer | Q | Câmbio real efetivo trimestral | índice 2010=100 | FRED | RB{ISO2}BIS | log | endogenous | MF,DSGE_M | 16.0 | 100.0 | 1994–2026T3 |
| inflation_expectations | Q | Expectativas de inflação (survey) | % a.a. 12 meses à frente | BCB_FOCUS | ExpectativasMercadoInflacao12Meses | level | exogenous | PC,TR,DSGE_S | 2.0 | 89.453125 | 2001–2026 |
| consumption_real | Q | Consumo das famílias real | milhões de BRL, preços de 1995 | IBGE | 6612/93404 | log | endogenous | DSGE_M | 1.0 | 95.3125 | 1996–2026T2 |
| gov_exp_real | Q | Consumo do governo real | milhões de BRL, preços de 1995 | IBGE | 6612/93405 | log | exogenous | DSGE_M | 1.0 | 95.3125 | 1996–2026T2 |
| investment_real | Q | Formação bruta de capital fixo real | milhões de BRL, preços de 1995 | IBGE | 6612/93406 | log | endogenous | DSGE_M | 1.0 | 95.3125 | 1996–2026T2 |
| exports_real | Q | Exportações reais | milhões de BRL, preços de 1995 | IBGE | 6612/93407 | log | exogenous | DSGE_M | 1.0 | 95.3125 | 1996–2026T2 |
| imports_real | Q | Importações reais | milhões de BRL, preços de 1995 | IBGE | 6612/93408 | log | exogenous | DSGE_M | 1.0 | 95.3125 | 1996–2026T2 |
| gdp_nominal | Q | PIB nominal trimestral | milhões de BRL correntes | IBGE | 1846/90707 | level | endogenous | DSGE_M | 1.0 | 95.3125 | 1996–2026T2 |
| gdp_deflator | Q | Deflator implícito trimestral | índice 1995=100 | derived | 100*gdp_nominal/gdp_real | index | endogenous | DSGE_M | 1.0 | 95.3125 | 1996–2026T2 |
| real_rate_ex_ante | Q | Juro real ex ante trimestral | % a.a. | derived | policy_rate - inflation_expectations | fisher | endogenous | TR,DSGE_S | 1.0 | 78.90625 | 2001–2026 |
| oil_price | Q | Preço do petróleo Brent | USD/barril | FRED | POILBREUSDM | log | exogenous | PC,DSGE_M | 1.0 | 99.21875 | Média trimestral. |
| foreign_output | Q | PIB real dos EUA | bilhões de USD encadeados de 2017 | FRED | GDPC1 | log | exogenous | MF,DSGE_M | 1.0 | 99.21875 | 1947–2026T2 |
| foreign_policy_rate | Q | Juro de política dos EUA | % a.a. | FRED | DFF | level | exogenous | MF,DSGE_M | 1.0 | 100.0 | 1954–2026 |
| gdp_deflator_2010 | A | Deflator implícito do PIB (2010=100) | índice 2010=100 | derived | deflator reescalado | index | exogenous | ADAS,DSGE_S,DSGE_M | 22.0 | 100.0 | 1950–2026 |
| primary_balance_brl | Q | Resultado primário do governo central | milhões de BRL | BCB | 4649 | level | exogenous | ISLM,DSGE_M | 1.0 | 78.125 | Fluxo mensal somado no trimestre; perímetro do governo central, distinto do WEO (governo geral). |

## 6. Lacunas explícitas por país

- **Brasil**: IPCA começa em 1980 (cobertura anual de inflação ~67%); PNAD Contínua trimestral começa em 2012; crédito/spread trimestral não têm série harmonizada; salário real trimestral não é usado.
- **Argentina**: PIB trimestral começa em 2004; inflação oficial tem quebras metodológicas (INDEC 2007–2015); câmbio paralelo não é usado.
- **Alemanha**: PIB trimestral do FRED começa em 1991 (pré-reunificação não coberto).
- **Japão**: CPI trimestral do OECD-MEI termina em 2021T2; usar fontes nacionais para o período recente.
- **China/Índia/Chile/Colômbia/Peru/Rússia**: sem PIB trimestral estável no FRED/OECD-MEI; entram apenas no painel anual.
- **Arábia Saudita**: PIB trimestral começa em 2010.
- **União Europeia**: agregado presente no G20, mas sem cobertura anual harmonizada para todas as variáveis; não entra em somas cross-country.
- **Capital/PTF**: PWT termina em 2019; não extrapolamos.

## 7. Reprodutibilidade

Ver `README.md` e `Makefile`. O manifesto `data/processed/manifest.json` registra URL, timestamp, tamanho e SHA-256 de cada download. O cache fica em `data/raw/`.