# Codebook — dataset macroeconômico cross-country (v1.0.0)

Extração: **2026-11-23T18:27:25Z**. Âncora: **Brasil**. Anual 1960–2026; trimestral 1995T1–2026T4.

## 1. Arquivos e grão

| Arquivo | Grão | Linhas | Uso |
|---|---|---|---|
| `data/processed/macro_long.parquet` | país × data × variável | 142,744 | dataset longo completo (anual + trimestral) |
| `data/processed/macro_annual_long.parquet` | país × ano × variável | 123,387 | painel anual |
| `data/processed/macro_quarterly_long.parquet` | país × trimestre × variável | 19,357 | subamostra trimestral |
| `data/exports/macro_dataset_consolidado.xlsx` | 4 abas | — | Excel consolidado |
| `data/exports/macro_anual_wide.csv` | país × ano | — | wide anual |
| `data/exports/macro_trimestral_wide.csv` | país × trimestre | — | wide trimestral |
| `data/exports/macro_todos_dados_long.csv` | país × período × variável | — | long consolidado |
| `data/processed/regime_matrix_annual.csv` | país × ano × dummy | 1,474 × 101 | matriz 0/1 |
| `data/processed/regime_matrix_quarterly.csv` | país × trimestre × dummy | 2,048 × 97 | matriz 0/1 |

## 2. Dicionário de campos

| campo | tipo | descrição |
|---|---|---|
| iso3 | string | Código ISO3; `WLD` = mundo (agregado); `EU` = União Europeia (agregado, excluído de somas). |
| country | string | Nome em português. |
| date | date | Fim do período: 31/12 do ano ou último dia do trimestre. |
| year | int | Ano do período. |
| period | string | `YYYY` (anual) ou `YYYYQn` (trimestral). |
| variable | string | Identificador canônico. |
| block | string | macro_core, distribuicao, restricao_externa, financeiro, ecologia_estrutura. |
| value | float | Valor na unidade declarada; nunca em log. |
| unit | string | Unidade nativa. |
| freq | string | `A` ou `Q`. |
| source | string | Fonte efetiva (GMD, WDI, WEO, PWT, FRED, BCB, IBGE, derived, hardcoded). |
| source_code | string | Código original (coluna, indicador, ID FRED, SGS/SIDRA). |
| source_detail | string | Descrição legível da série. |
| source_url | string | URL da fonte. |
| vintage | string | Versão/vintage da fonte. |
| transformation | string | Transformação recomendada: level, log, yoy, diff, hp_gap, hp_trend, fisher, pct_gdp, index, dummy, derived. |
| transform_applied | string | Sempre `none`: o valor é bruto/construído. |
| role | string | endogenous, exogenous, latent, shock, regime, validation. |
| model | string | Modelos reduzidos: ISLM, MF, ADAS, PC, TR, SOLOW. |
| coverage_note | string | Nota de cobertura temporal. |
| notes | string | Definição e ressalvas. |
| is_forecast | bool | Projeção ou ano preliminar. |
| quality_flag | string | ok, preliminary, forecast, derived, proxy, hp_filter, survey, policy, validation. |
| seasonal_adjustment | string | SA, NSA ou n/a. |
| imputation | string | none (sem imputação). |
| extraction_date | string | Timestamp UTC da extração. |
| regime_dummy | string | Dummies ativas, separadas por `\|`. |

## 3. Convenções

- **Sinal fiscal**: resultado primário/balanço positivos = superávit.
- **Câmbio**: moeda local por USD (aumento = depreciação); EUR/GBP/AUD invertidos.
- **Deflator**: `gdp_deflator` na base do PIB real; `gdp_deflator_2010` 2010=100.
- **Juros**: % a.a.; inflação % a.a. (12 meses); no Brasil, IPCA (BCB/IBGE).
- **PIB real**: milhões de LC a preços constantes; base nacional; não comparar níveis sem `gdp_real_usd`.
- **PPPs**: `gdp_ppp_usd` em milhões de int$ (WEO × 1000).
- **FRED**: templates `{ISO2}`; o ID exato está em `source_code`.
- **Capital**: `capital_stock` usa `rnna` (PWT, milhões USD 2017), não `rkna` (índice 2017=1).
- **2026**: ano em curso, `preliminary`/`is_forecast=True`; não entra nas estimações.

## 4. Blocos e cobertura

| bloco | freq | variaveis | observacoes |
|---|---|---|---|
| Distribuição e classe | A | 6 | 5170 |
| Ecologia e estrutura produtiva | A | 8 | 8364 |
| Financiarização e crédito | A | 5 | 2823 |
| Macro core (ortodoxo) | A | 89 | 101818 |
| Macro core (ortodoxo) | Q | 28 | 19357 |
| Restrição externa e hierarquia monetária | A | 6 | 5212 |

## 5. Registro de fontes

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

## 6. Dicionário de variáveis

| variável | freq | rótulo | unidade | fonte | código | transformação | papel | modelos | bloco | n_países | cobertura_% | notas |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gdp_nominal | A | PIB nominal | milhões de LC correntes | GMD | nGDP | level | endogenous | ISLM,MF,ADAS | Macro core (ortodoxo) | 22 | 100.0 | Base do deflator e das razões % do PIB. |
| gdp_real | A | PIB real | milhões de LC, preços constantes | GMD | rGDP | log | endogenous | ISLM,ADAS,SOLOW | Macro core (ortodoxo) | 22 | 100.0 | Série encadeada; ano-base varia por país no GMD (documentado por país). |
| gdp_real_usd | A | PIB real em USD | milhões de USD constantes | GMD | rGDP_USD | log | exogenous | SOLOW | Macro core (ortodoxo) | 22 | 97.01492537313432 | Comparação de níveis reais entre países. |
| gdp_nominal_usd | A | PIB nominal em USD | milhões de USD correntes | derived | nGDP/USDfx | level | exogenous | MF | Macro core (ortodoxo) | 22 | 98.50746268656717 | Calculado como nGDP dividido pela taxa de câmbio média do ano. |
| gdp_real_pc | A | PIB real per capita | LC constantes per capita | GMD | rGDP_pc | log | endogenous | SOLOW | Macro core (ortodoxo) | 22 | 100.0 | Usado no modelo de Solow e em convergência. |
| gdp_deflator | A | Deflator implícito do PIB | índice (ano-base do PIB real = 100) | GMD | deflator | index | endogenous | ADAS | Macro core (ortodoxo) | 22 | 100.0 | GMD fornece a razão nominal/real; base coincide com a do PIB real do país. A versão 2010=100 está em gdp_deflator_2010. |
| gdp_ppp_usd | A | PIB em paridade de poder de compra | milhões de int$ correntes | WEO | PPPGDP | level | exogenous | SOLOW | Macro core (ortodoxo) | 23 | 70.14925373134328 | Apenas para comparação de níveis; não entra na lista TOP10_NOMINAL. |
| gdp_growth | A | Crescimento real do PIB | % a.a. | derived | dlog(gdp_real) | yoy | endogenous | ADAS,PC,SOLOW | Macro core (ortodoxo) | 22 | 98.50746268656717 | Calculado por diferença de log; não usa a série de crescimento do GMD. |
| potential_gdp | A | PIB potencial | milhões de LC constantes | derived | HP(log(gdp_real), λ=100) | hp_trend | latent | ADAS | Macro core (ortodoxo) | 22 | 98.50746268656717 | Filtro HP bicaudal com λ=100 (anual); risco de viés de fim de amostra documentado. |
| output_gap | A | Hiato do produto | % do PIB potencial | derived | 100*(log(gdp_real)-log(potential_gdp)) | hp_gap | latent | ADAS,PC,TR | Macro core (ortodoxo) | 22 | 98.50746268656717 | Hiato construído por HP; usado no SVAR e nas Projeções Locais. |
| consumption_real | A | Consumo final real | milhões de LC constantes | GMD | cons | log | endogenous | ISLM,ADAS | Macro core (ortodoxo) | 22 | 98.50746268656717 | Consumo final das famílias + governo quando a fonte não separa; ver nota por país. |
| consumption_gdp | A | Consumo final (% do PIB) | % do PIB | GMD | cons_GDP | pct_gdp | endogenous | ISLM,ADAS | Macro core (ortodoxo) | 22 | 98.50746268656717 | Razão nominal. |
| investment_real | A | Formação bruta de capital real | milhões de LC constantes | GMD | inv | log | endogenous | ISLM,ADAS | Macro core (ortodoxo) | 22 | 100.0 | Inclui variação de estoques quando disponível. |
| investment_gdp | A | Investimento (% do PIB) | % do PIB | GMD | inv_GDP | pct_gdp | endogenous | ISLM | Macro core (ortodoxo) | 22 | 100.0 | Razão nominal. |
| fixed_investment_real | A | Formação bruta de capital fixo real | milhões de LC constantes | GMD | finv | log | endogenous |  | Macro core (ortodoxo) | 22 | 98.50746268656717 | Proxy de investimento das firmas. |
| fixed_investment_gdp | A | Formação bruta de capital fixo (% do PIB) | % do PIB | GMD | finv_GDP | pct_gdp | endogenous |  | Macro core (ortodoxo) | 22 | 98.50746268656717 | Razão nominal. |
| gov_exp_real | A | Despesa do governo real | milhões de LC constantes | GMD | govexp | log | exogenous | ISLM,MF,ADAS | Macro core (ortodoxo) | 22 | 100.0 | Consumo + investimento do governo; definição fiscal detalhada em gov_revenue. |
| gov_exp_gdp | A | Despesa do governo (% do PIB) | % do PIB | GMD | govexp_GDP | pct_gdp | exogenous | ISLM,MF,ADAS | Macro core (ortodoxo) | 22 | 100.0 | Razão nominal. |
| gov_revenue_gdp | A | Receita do governo (% do PIB) | % do PIB | GMD | govrev_GDP | pct_gdp | exogenous | ISLM | Macro core (ortodoxo) | 22 | 100.0 | Receita total; inclui contribuições sociais quando a fonte reporta. |
| tax_burden_gdp | A | Carga tributária (% do PIB) | % do PIB | GMD | govtax_GDP | pct_gdp | exogenous | ISLM | Macro core (ortodoxo) | 22 | 94.02985074626864 | Tributos sobre produção e importação; não é receita total. |
| gov_balance_gdp | A | Resultado fiscal (% do PIB) | % do PIB | GMD | govdef_GDP | pct_gdp | exogenous | ISLM | Macro core (ortodoxo) | 22 | 100.0 | Sinal: positivo = superávit; ver normalize_sinal no build. |
| gov_debt_gdp | A | Dívida bruta do governo (% do PIB) | % do PIB | GMD | govdebt_GDP | pct_gdp | exogenous |  | Macro core (ortodoxo) | 22 | 100.0 | Dívida bruta; comparação com WDI/WEO na validação. |
| exports_gdp | A | Exportações (% do PIB) | % do PIB | GMD | exports_GDP | pct_gdp | exogenous | ISLM,MF | Macro core (ortodoxo) | 22 | 100.0 | Bens e serviços, preços correntes. |
| imports_gdp | A | Importações (% do PIB) | % do PIB | GMD | imports_GDP | pct_gdp | exogenous | ISLM,MF | Macro core (ortodoxo) | 22 | 100.0 | Bens e serviços, preços correntes. |
| net_exports_gdp | A | Exportações líquidas (% do PIB) | % do PIB | derived | exports_GDP - imports_GDP | pct_gdp | endogenous | ISLM,MF,ADAS | Macro core (ortodoxo) | 22 | 100.0 | Identidade Y=C+I+G+NX; resíduo reportado na validação. |
| current_account_gdp | A | Conta corrente (% do PIB) | % do PIB | GMD | CA_GDP | pct_gdp | exogenous | MF | Macro core (ortodoxo) | 22 | 100.0 | Inclui renda de fatores e transferências. |
| cpi_index | A | Índice de preços ao consumidor | índice 2010=100 | GMD | CPI | index | endogenous | PC,ADAS | Macro core (ortodoxo) | 22 | 100.0 | GMD padroniza 2010=100. |
| inflation | A | Inflação ao consumidor | % a.a. | GMD | infl | yoy | endogenous | ADAS,PC,TR | Macro core (ortodoxo) | 22 | 100.0 | Variação anual do CPI; núcleo apenas onde existe (Brasil/EUA). |
| population | A | População | milhões | GMD | pop | log | exogenous | SOLOW | Macro core (ortodoxo) | 22 | 100.0 | Usada em n e em per capita. |
| unemployment | A | Taxa de desemprego | % da força de trabalho | GMD | unemp | level | endogenous | PC | Macro core (ortodoxo) | 22 | 93.28358208955224 | Definições nacionais harmonizadas pelo GMD; ver notas por país. |
| short_rate | A | Juro de curto prazo | % a.a. | GMD | strate | level | endogenous | ISLM,MF,TR | Macro core (ortodoxo) | 22 | 95.52238805970148 | Taxa de mercado de curto prazo; instrumento da regra de Taylor. |
| long_rate | A | Juro de longo prazo | % a.a. | GMD | ltrate | level | endogenous | ISLM | Macro core (ortodoxo) | 21 | 67.16417910447761 | Título soberano de longo prazo; usado na curva de juros e na dívida. |
| policy_rate | A | Taxa de política monetária | % a.a. | GMD | cbrate | level | exogenous | TR | Macro core (ortodoxo) | 22 | 98.50746268656717 | Taxa básica; para o Brasil vem do SGS 432 no trimestral. |
| m0 | A | Base monetária | milhões de LC | GMD | M0 | log | exogenous | ISLM,MF | Macro core (ortodoxo) | 21 | 94.02985074626864 | Agregado monetário restrito. |
| m1 | A | M1 | milhões de LC | GMD | M1 | log | exogenous | ISLM,MF | Macro core (ortodoxo) | 22 | 94.02985074626864 | Papel-moeda + depósitos à vista. |
| m2 | A | M2 | milhões de LC | GMD | M2 | log | exogenous | ISLM,MF | Macro core (ortodoxo) | 21 | 92.53731343283582 | M1 + depósitos de poupança e a prazo. |
| m3 | A | M3 | milhões de LC | GMD | M3 | log | exogenous | ISLM,MF | Macro core (ortodoxo) | 19 | 64.17910447761194 | M2 + títulos e outros passivos. |
| exchange_rate_nominal | A | Taxa de câmbio nominal | LC por USD (média anual) | GMD | USDfx | log | endogenous | MF | Macro core (ortodoxo) | 22 | 98.50746268656717 | Orientación: unidades de moeda local por 1 USD; aumento = depreciação. |
| reer | A | Câmbio real efetivo | índice 2010=100 | GMD | REER | log | endogenous | MF | Macro core (ortodoxo) | 22 | 98.50746268656717 | BIS/bruto; aumento = apreciação real. |
| hpi | A | Índice de preços de imóveis | índice 2010=100 | GMD | HPI | log | exogenous |  | Macro core (ortodoxo) | 21 | 74.6268656716418 | Onde disponível; usado como controle de riqueza. |
| primary_balance_gdp | A | Resultado primário (% do PIB) | % do PIB | WEO | pb | pct_gdp | exogenous | ISLM | Macro core (ortodoxo) | 22 | 67.16417910447761 | WEO pós-1980; sinal positivo = superávit primário. |
| net_debt_gdp | A | Dívida líquida do governo (% do PIB) | % do PIB | WEO | GGXWDN_G01_GDP_PT | pct_gdp | exogenous |  | Macro core (ortodoxo) | 18 | 47.76119402985075 | Dívida líquida; cobertura menor que a bruta. |
| inflation_weo | A | Inflação (WEO) | % a.a. | WEO | PCPIPCH | yoy | validation | ADAS,PC | Macro core (ortodoxo) | 23 | 70.14925373134328 | Série de validação/forecast; is_forecast=1 para anos > 2025. |
| gov_debt_gdp_weo | A | Dívida bruta (WEO) | % do PIB | WEO | GGXWDG_NGDP | pct_gdp | validation |  | Macro core (ortodoxo) | 23 | 47.76119402985075 | Validação cruzada da dívida. |
| gdp_growth_weo | A | Crescimento do PIB (WEO) | % a.a. | WEO | NGDP_RPCH | yoy | validation | ADAS | Macro core (ortodoxo) | 23 | 70.14925373134328 | Validação cruzada do crescimento. |
| gdp_nominal_usd_weo | A | PIB nominal USD (WEO) | milhões de USD | WEO | NGDPD | level | validation | MF | Macro core (ortodoxo) | 23 | 70.14925373134328 | Validação cruzada do PIB nominal. |
| unemployment_weo | A | Desemprego (WEO) | % | WEO | LUR | level | validation | PC | Macro core (ortodoxo) | 22 | 70.14925373134328 | Validação cruzada do desemprego. |
| participation_rate | A | Taxa de participação | % da população em idade ativa | WDI | SL.TLF.CACT.ZS | level | endogenous |  | Macro core (ortodoxo) | 23 | 53.73134328358209 | Força de trabalho / população 15+. |
| credit_private_gdp | A | Crédito ao setor privado (% do PIB) | % do PIB | WDI | FS.AST.PRVT.GD.ZS | pct_gdp | exogenous |  | Macro core (ortodoxo) | 23 | 83.58208955223881 | Crédito doméstico ao setor privado; fricção financeira. |
| gov_consumption_gdp | A | Consumo do governo (% do PIB) | % do PIB | WDI | NE.CON.GOVT.ZS | pct_gdp | validation | ISLM | Macro core (ortodoxo) | 23 | 98.50746268656717 | Validação/complemento de gov_exp_gdp. |
| gross_capital_formation_gdp | A | Formação bruta de capital (% do PIB) | % do PIB | WDI | NE.GDI.TOTL.ZS | pct_gdp | validation | ISLM | Macro core (ortodoxo) | 23 | 98.50746268656717 | Validação/complemento de investment_gdp. |
| tax_revenue_gdp_wdi | A | Receita tributária (% do PIB) | % do PIB | WDI | GC.TAX.TOTL.GD.ZS | pct_gdp | validation |  | Macro core (ortodoxo) | 23 | 68.65671641791045 | Validação da carga tributária. |
| central_gov_debt_gdp | A | Dívida do governo central (% do PIB) | % do PIB | WDI | GC.DOD.TOTL.GD.ZS | pct_gdp | validation |  | Macro core (ortodoxo) | 17 | 31.34328358208955 | Validação/complemento da dívida bruta. |
| inflation_wdi | A | Inflação (WDI) | % a.a. | WDI | FP.CPI.TOTL.ZG | yoy | validation | ADAS,PC | Macro core (ortodoxo) | 23 | 98.50746268656717 | Validação cruzada da inflação. |
| unemployment_wdi | A | Desemprego (WDI) | % | WDI | SL.UEM.TOTL.ZS | level | validation | PC | Macro core (ortodoxo) | 23 | 52.23880597014925 | Validação cruzada do desemprego (OIT). |
| population_wdi | A | População (WDI) | pessoas | WDI | SP.POP.TOTL | log | validation | SOLOW | Macro core (ortodoxo) | 23 | 98.50746268656717 | Validação da população. |
| world_gdp_real | A | PIB real mundial | USD constantes de 2015 | WDI | NY.GDP.MKTP.KD | log | exogenous | MF | Macro core (ortodoxo) | 23 | 98.50746268656717 | Agregado WLD do Banco Mundial; proxy de Y*. |
| world_gdp_growth | A | Crescimento do PIB mundial | % a.a. | derived | dlog(world_gdp_real) | yoy | exogenous | MF | Macro core (ortodoxo) | 1 | 97.01492537313432 | Choque externo comum. |
| capital_stock | A | Estoque de capital | milhões de USD constantes de 2017 | PWT | rnna | log | endogenous | SOLOW | Macro core (ortodoxo) | 22 | 89.55223880597015 | PWT 10.01, variável rnna (capital a preços nacionais constantes); após 2019 não extrapolado. |
| tfp | A | PTF (TFP) | índice 2017=1 | PWT | rtfpna | log | endogenous | SOLOW | Macro core (ortodoxo) | 22 | 89.55223880597015 | PTF de Solow ajustada por capital humano. |
| employment | A | Emprego | milhões de trabalhadores | PWT | emp | log | endogenous | SOLOW | Macro core (ortodoxo) | 22 | 89.55223880597015 | PWT emp; complementado por WDI/ILO quando necessário. |
| hours_worked | A | Horas trabalhadas por trabalhador | horas/ano | PWT | avh | log | endogenous |  | Macro core (ortodoxo) | 21 | 89.55223880597015 | PWT avh. |
| labor_share | A | Participação do trabalho na renda | fração (0–1) | PWT | labsh | level | endogenous |  | Macro core (ortodoxo) | 22 | 89.55223880597015 | PWT labsh; usado para calibrar salário/markup. |
| human_capital | A | Capital humano | índice | PWT | hc | log | exogenous | SOLOW | Macro core (ortodoxo) | 22 | 89.55223880597015 | PWT hc. |
| capital_output_ratio | A | Razão capital-produto | razão | derived | capital_stock/gdp_real | level | endogenous | SOLOW | Macro core (ortodoxo) | 22 | 89.55223880597015 | Unidades compatíveis (ambas em USD constantes de 2017). |
| commodity_price_index | A | Índice de preços de commodities | índice (2016=100) | FRED | PALLFNFINDEXQ | log | exogenous | PC | Macro core (ortodoxo) | 1 | 52.23880597014925 | Índice amplo de commodities do FMI, média anual. |
| oil_price | A | Preço do petróleo Brent | USD/barril | FRED | POILBREUSDM | log | exogenous | ADAS,PC | Macro core (ortodoxo) | 1 | 52.23880597014925 | Média anual; choque de oferta. |
| vix | A | Índice de volatilidade VIX | índice | FRED | VIXCLS | log | exogenous | MF | Macro core (ortodoxo) | 1 | 55.223880597014926 | Proxy de prêmio de risco global. |
| foreign_policy_rate | A | Juro de política dos EUA | % a.a. | FRED | IR3TIB01USQ156N | level | exogenous | MF | Macro core (ortodoxo) | 1 | 100.0 | Média anual da taxa de 3 meses dos EUA. |
| real_rate_ex_post | A | Juro real ex post | % a.a. | derived | policy_rate - inflation | fisher | endogenous | ISLM,TR | Macro core (ortodoxo) | 22 | 98.50746268656717 | Aproximação de Fisher; usa inflação contemporânea. |
| real_rate_ex_ante | A | Juro real ex ante | % a.a. | derived | policy_rate - inflation_expectations | fisher | endogenous | TR | Macro core (ortodoxo) | 1 | 71.64179104477611 | Só para Brasil (Focus) e EUA (Michigan). |
| neutral_rate | A | Taxa de juros neutra (r*) | % a.a. | derived | HP(real_rate_ex_ante, λ=100) | hp_trend | latent | TR | Macro core (ortodoxo) | 1 | 71.64179104477611 | Proxy por filtro HP; não é estimativa estrutural de r*. |
| inflation_expectations | A | Expectativas de inflação (survey) | % a.a. 12 meses à frente | BCB_FOCUS | ExpectativasMercadoInflacao12Meses | level | exogenous | PC,TR | Macro core (ortodoxo) | 1 | 73.13432835820896 | Focus (Brasil) e Michigan (EUA); demais países sem survey homogêneo. |
| inflation_target | A | Meta de inflação | % a.a. | hardcoded | metas por país | level | regime | TR | Macro core (ortodoxo) | 20 | 36.56716417910448 | Tabela em regimes.yml; ausente onde não há regime explícito. |
| debt_dynamics_residual | A | Resíduo da dinâmica da dívida | % do PIB | derived | identidade da dívida | derived | validation |  | Macro core (ortodoxo) | 22 | 65.67164179104478 | SFA (stock-flow adjustment); ver validação de identidades. |
| banking_crisis | A | Crise bancária (dummy) | 0/1 | GMD | BankingCrisis | dummy | regime | ADAS | Macro core (ortodoxo) | 21 | 86.56716417910448 | Dummy anual do GMD; complementa regimes.yml. |
| currency_crisis | A | Crise cambial (dummy) | 0/1 | GMD | CurrencyCrisis | dummy | regime | MF | Macro core (ortodoxo) | 21 | 86.56716417910448 | Dummy anual do GMD. |
| sovereign_debt_crisis | A | Crise de dívida soberana (dummy) | 0/1 | GMD | SovDebtCrisis | dummy | regime |  | Macro core (ortodoxo) | 21 | 86.56716417910448 | Dummy anual do GMD. |
| output_per_worker | A | Produto por trabalhador | LC constantes por trabalhador | derived | gdp_real/employment | log | endogenous | SOLOW | Macro core (ortodoxo) | 22 | 89.55223880597015 | Produtividade média do trabalho. |
| gdp_real | Q | PIB real trimestral | milhões de LC, preços constantes, SA | FRED | NGDPRSAXDC{ISO2}Q | log | endogenous | ADAS | Macro core (ortodoxo) | 16 | 98.4375 | Série OECD-MEI dessazonalizada; Brasil também validado contra IBGE. |
| gdp_real_growth | Q | Crescimento trimestral do PIB | % a.a. (SAAR) | derived | 400*dlog(gdp_real) | yoy | endogenous | ADAS | Macro core (ortodoxo) | 16 | 97.65625 | Taxa anualizada da variação trimestral. |
| potential_gdp | Q | PIB potencial trimestral | milhões de LC constantes | derived | HP(log(gdp_real), λ=1600) | hp_trend | latent | ADAS | Macro core (ortodoxo) | 16 | 98.4375 | HP bicaudal λ=1600. |
| output_gap | Q | Hiato do produto trimestral | % do PIB potencial | derived | 100*(log(gdp_real)-log(potential_gdp)) | hp_gap | latent | ADAS,PC,TR | Macro core (ortodoxo) | 16 | 98.4375 | Usado no SVAR e nas Projeções Locais; robustez com log-nível. |
| inflation | Q | Inflação ao consumidor trimestral | % a.a. (variação 4 trimestres) | FRED | CPALTT01{ISO2}Q659N | yoy | endogenous | ADAS,PC,TR | Macro core (ortodoxo) | 14 | 94.53125 | Brasil: calculada do IPCA mensal (SGS 433); demais: OECD-MEI. |
| core_inflation | Q | Núcleo da inflação | % a.a. | BCB | 11427 | yoy | endogenous | PC | Macro core (ortodoxo) | 2 | 100.0 | Brasil: núcleo de médias aparadas com suavização; EUA: CPILFESL. Demais: ausente. |
| unemployment | Q | Taxa de desemprego trimestral | % | FRED | LRHUTTTT{ISO2}Q156S | level | endogenous | PC | Macro core (ortodoxo) | 12 | 99.21875 | OECD-MEI, dessazonalizada. |
| policy_rate | Q | Taxa de política monetária trimestral | % a.a. | BCB | 432 | level | exogenous | TR | Macro core (ortodoxo) | 1 | 87.5 | Brasil: Selic meta (média do trimestre); EUA: fed funds efetivo; demais: 3m interbancária. |
| short_rate | Q | Juro de curto prazo trimestral | % a.a. | FRED | IR3TIB01{ISO2}Q156N | level | endogenous | ISLM,MF | Macro core (ortodoxo) | 13 | 99.21875 | Taxa de 3 meses interbancária. |
| long_rate | Q | Juro de longo prazo trimestral | % a.a. | FRED | IRLTLT01{ISO2}Q156N | level | endogenous | ISLM | Macro core (ortodoxo) | 11 | 99.21875 | Título soberano de 10 anos. |
| exchange_rate_nominal | Q | Taxa de câmbio nominal trimestral | LC por USD | FRED | DEX{ISO2} | log | endogenous | MF | Macro core (ortodoxo) | 12 | 100.0 | Média do trimestre; orientação LC por USD; EUR/GBP/AUD invertidos. |
| reer | Q | Câmbio real efetivo trimestral | índice 2010=100 | FRED | RB{ISO2}BIS | log | endogenous | MF | Macro core (ortodoxo) | 16 | 100.0 | BIS broad, média trimestral. |
| inflation_expectations | Q | Expectativas de inflação (survey) | % a.a. 12 meses à frente | BCB_FOCUS | ExpectativasMercadoInflacao12Meses | level | exogenous | PC,TR | Macro core (ortodoxo) | 2 | 89.453125 | Brasil: Focus (média do trimestre); EUA: MICH. |
| consumption_real | Q | Consumo das famílias real | milhões de BRL, preços de 1995 | IBGE | 6612/93404 | log | endogenous |  | Macro core (ortodoxo) | 1 | 95.3125 | Brasil apenas; valores encadeados. |
| gov_exp_real | Q | Consumo do governo real | milhões de BRL, preços de 1995 | IBGE | 6612/93405 | log | exogenous |  | Macro core (ortodoxo) | 1 | 95.3125 | Brasil apenas; administração pública. |
| investment_real | Q | Formação bruta de capital fixo real | milhões de BRL, preços de 1995 | IBGE | 6612/93406 | log | endogenous |  | Macro core (ortodoxo) | 1 | 95.3125 | Brasil apenas. |
| exports_real | Q | Exportações reais | milhões de BRL, preços de 1995 | IBGE | 6612/93407 | log | exogenous |  | Macro core (ortodoxo) | 1 | 95.3125 | Brasil apenas. |
| imports_real | Q | Importações reais | milhões de BRL, preços de 1995 | IBGE | 6612/93408 | log | exogenous |  | Macro core (ortodoxo) | 1 | 95.3125 | Brasil apenas; sinal positivo (importação). |
| gdp_nominal | Q | PIB nominal trimestral | milhões de BRL correntes | IBGE | 1846/90707 | level | endogenous |  | Macro core (ortodoxo) | 1 | 95.3125 | Brasil apenas. |
| gdp_deflator | Q | Deflator implícito trimestral | índice 1995=100 | derived | 100*gdp_nominal/gdp_real | index | endogenous |  | Macro core (ortodoxo) | 1 | 95.3125 | Brasil apenas; base 1995. |
| real_rate_ex_ante | Q | Juro real ex ante trimestral | % a.a. | derived | policy_rate - inflation_expectations | fisher | endogenous | TR | Macro core (ortodoxo) | 1 | 78.90625 | Brasil. |
| oil_price | Q | Preço do petróleo Brent | USD/barril | FRED | POILBREUSDM | log | exogenous | PC | Macro core (ortodoxo) | 1 | 99.21875 | Média trimestral. |
| foreign_output | Q | PIB real dos EUA | bilhões de USD encadeados de 2017 | FRED | GDPC1 | log | exogenous | MF | Macro core (ortodoxo) | 1 | 99.21875 | Proxy de demanda externa. |
| foreign_policy_rate | Q | Juro de política dos EUA | % a.a. | FRED | DFF | level | exogenous | MF | Macro core (ortodoxo) | 1 | 100.0 | Média trimestral do fed funds efetivo. |
| gdp_deflator_2010 | A | Deflator implícito do PIB (2010=100) | índice 2010=100 | derived | deflator reescalado | index | exogenous | ADAS | Macro core (ortodoxo) | 22 | 100.0 | Versão comparável entre países; NÃO usar com níveis de PIB real (base nacional). Para a identidade nominal/real usar gdp_deflator. |
| primary_balance_brl | Q | Resultado primário do governo central | milhões de BRL | BCB | 4649 | level | exogenous | ISLM | Macro core (ortodoxo) | 1 | 78.125 | Fluxo mensal somado no trimestre; perímetro do governo central, distinto do WEO (governo geral). |
| profit_share | A | Parcela dos lucros na renda | fração (0–1) | derived | 1 - labor_share | level | endogenous | ISLM,PC,SOLOW | Distribuição e classe | 22 | 89.55223880597015 | Derivada do PWT (1 - labsh); não é lucro contábil, é resíduo da renda do trabalho. |
| gini_index | A | Índice de Gini | índice 0–100 | WDI | SI.POV.GINI | level | exogenous | PC,SOLOW | Distribuição e classe | 21 | 44.776119402985074 | Desigualdade de renda; cobertura esparsa e comparações entre países requerem cautela. |
| income_share_top10 | A | Parcela da renda do topo 10% | % da renda total | WDI | SI.DST.10TH.10 | level | exogenous | PC,SOLOW | Distribuição e classe | 21 | 44.776119402985074 | Share of income held by highest 10%. |
| income_share_bottom20 | A | Parcela da renda dos 20% mais pobres | % da renda total | WDI | SI.DST.FRST.20 | level | exogenous | PC,SOLOW | Distribuição e classe | 21 | 44.776119402985074 | Share of income held by lowest 20%. |
| vulnerable_employment_pct | A | Emprego vulnerável | % do emprego total | WDI | SL.EMP.VULN.ZS | level | exogenous | PC,SOLOW | Distribuição e classe | 22 | 52.23880597014925 | Proxy de informalidade/trabalho vulnerável (OIT). |
| wage_bill_gdp | A | Massa salarial | % do PIB | derived | labor_share * 100 | level | endogenous | ISLM,PC,SOLOW | Distribuição e classe | 22 | 89.55223880597015 | Derivada do PWT (labsh × 100). |
| terms_of_trade_index | A | Termos de troca | índice (2015=100) | WDI | TT.PRI.MRCH.XD.WD | level | exogenous | MF,PC | Restrição externa e hierarquia monetária | 22 | 29.85074626865672 | Net barter terms of trade; exportações/importações. |
| intl_reserves_usd | A | Reservas internacionais | USD correntes | WDI | FI.RES.TOTL.CD | level | exogenous | MF | Restrição externa e hierarquia monetária | 22 | 98.50746268656717 | Reservas totais, excluindo ouro. |
| intl_reserves_months_imports | A | Reservas em meses de importação | meses | WDI | FI.RES.TOTL.MO | level | exogenous | MF | Restrição externa e hierarquia monetária | 22 | 76.11940298507463 | Reservas / importações mensais. |
| external_debt_gni | A | Dívida externa total | % do RNB | WDI | DT.DOD.DECT.GN.ZS | level | exogenous | MF | Restrição externa e hierarquia monetária | 11 | 83.58208955223881 | Dívida externa total, pública e privada. |
| debt_service_exports | A | Serviço da dívida externa | % das exportações | WDI | DT.TDS.DECT.EX.ZS | level | exogenous | MF | Restrição externa e hierarquia monetária | 11 | 73.13432835820896 | Principal + juros / exportações. |
| fdi_net_inflows_gdp | A | IDE líquido | % do PIB | WDI | BX.KLT.DINV.WD.GD.ZS | level | exogenous | MF,SOLOW | Restrição externa e hierarquia monetária | 22 | 83.58208955223881 | Investimento direto estrangeiro líquido. |
| lending_rate | A | Taxa de empréstimo | % a.a. | WDI | FR.INR.LEND | level | exogenous | ISLM,MF | Financiarização e crédito | 18 | 58.2089552238806 | Taxa média de empréstimos bancários. |
| interest_rate_spread | A | Spread bancário | p.p. | WDI | FR.INR.LNDP | level | exogenous | ISLM,MF | Financiarização e crédito | 15 | 49.25373134328358 | Spread entre empréstimo e depósito. |
| bank_capital_to_assets | A | Capital bancário sobre ativos | % | WDI | FB.BNK.CAPA.ZS | level | exogenous | MF | Financiarização e crédito | 22 | 26.865671641791046 | Capital e reservas / ativos totais. |
| bank_npl_pct | A | Inadimplência bancária | % dos empréstimos | WDI | FB.AST.NPER.ZS | level | exogenous | MF | Financiarização e crédito | 22 | 26.865671641791046 | Non-performing loans / total gross loans. |
| market_cap_gdp | A | Capitalização de mercado | % do PIB | WDI | CM.MKT.LCAP.GD.ZS | level | exogenous | MF | Financiarização e crédito | 22 | 60.44776119402985 | Empresas domésticas listadas. |
| co2_per_capita | A | Emissões de CO2 per capita | t CO2e per capita | WDI | EN.GHG.CO2.PC.CE.AR5 | level | exogenous | SOLOW | Ecologia e estrutura produtiva | 22 | 82.08955223880596 | Emissões de CO2 equivalentes, AR5. |
| co2_per_gdp | A | Intensidade de carbono do PIB | kg CO2e por USD corrente | derived | co2_total_mt * 1000 / gdp_nominal_usd | level | exogenous | SOLOW | Ecologia e estrutura produtiva | 22 | 82.08955223880596 | Derivada de EN.GHG.CO2.MT.CE.AR5 / PIB nominal USD. |
| renewable_electricity_pct | A | Eletricidade renovável | % da matriz elétrica | WDI | EG.ELC.RNEW.ZS | level | exogenous | SOLOW | Ecologia e estrutura produtiva | 22 | 47.76119402985075 | Participação de renováveis na geração elétrica. |
| energy_intensity_gdp | A | Intensidade energética | MJ por 2017 PPP USD | WDI | EG.EGY.PRIM.PP.KD | level | exogenous | SOLOW | Ecologia e estrutura produtiva | 22 | 34.32835820895522 | Energia primária por PIB PPP. |
| manufacturing_gdp | A | Indústria de transformação | % do PIB | WDI | NV.IND.MANF.ZS | level | exogenous | SOLOW | Ecologia e estrutura produtiva | 22 | 83.58208955223881 | Valor adicionado da manufatura. |
| agriculture_gdp | A | Agricultura | % do PIB | WDI | NV.AGR.TOTL.ZS | level | exogenous | SOLOW | Ecologia e estrutura produtiva | 22 | 88.80597014925374 | Valor adicionado da agricultura. |
| manufactures_exports_pct | A | Exportações de manufaturados | % das exportações de mercadorias | WDI | TX.VAL.MANF.ZS.UN | level | exogenous | MF,SOLOW | Ecologia e estrutura produtiva | 22 | 94.02985074626864 | Diversificação exportadora. |
| fuel_ores_exports_pct | A | Exportações de combustíveis e minérios | % das exportações de mercadorias | derived | TX.VAL.FUEL.ZS.UN + TX.VAL.MMTL.ZS.UN | level | exogenous | MF,SOLOW | Ecologia e estrutura produtiva | 22 | 94.02985074626864 | Soma estrita dos dois componentes; NaN se um faltar. |
| gdp_real_wdi | A | PIB real (WDI, validação) | USD constantes de 2015 | WDI | NY.GDP.MKTP.KD | log | validation | ADAS,SOLOW | Macro core (ortodoxo) | 23 | 98.50746268656717 | Série de validação; não é a fonte primária do PIB real. |
| gdp_nominal_wdi | A | PIB nominal (WDI, validação) | USD correntes | WDI | NY.GDP.MKTP.CD | level | validation | MF | Macro core (ortodoxo) | 23 | 98.50746268656717 | Série de validação. |
| gdp_deflator_wdi | A | Deflator do PIB (WDI, validação) | índice 2015=100 | WDI | NY.GDP.DEFL.ZS | index | validation | ADAS | Macro core (ortodoxo) | 22 | 98.50746268656717 | Série de validação. |
| gdp_growth_wdi | A | Crescimento do PIB (WDI, validação) | % a.a. | WDI | NY.GDP.MKTP.KD.ZG | yoy | validation | ADAS | Macro core (ortodoxo) | 23 | 97.01492537313432 | Série de validação. |
| consumption_gdp_wdi | A | Consumo total (WDI, validação) | % do PIB | WDI | NE.CON.TOTL.ZS | pct_gdp | validation | ISLM,ADAS | Macro core (ortodoxo) | 22 | 98.50746268656717 | Série de validação. |
| exports_gdp_wdi | A | Exportações (WDI, validação) | % do PIB | WDI | NE.EXP.GNFS.ZS | pct_gdp | validation | MF | Macro core (ortodoxo) | 23 | 98.50746268656717 | Série de validação. |
| imports_gdp_wdi | A | Importações (WDI, validação) | % do PIB | WDI | NE.IMP.GNFS.ZS | pct_gdp | validation | MF | Macro core (ortodoxo) | 23 | 98.50746268656717 | Série de validação. |
| gov_balance_gdp_weo | A | Resultado fiscal (WEO, validação) | % do PIB | WEO | GGXCNL_G01_GDP_PT | pct_gdp | validation | ISLM | Macro core (ortodoxo) | 22 | 54.47761194029851 | Série de validação; sinal positivo = superávit. |
| rgdpna_pwt | A | PIB real PWT (validação) | milhões de USD 2017 | PWT | rgdpna | log | validation | SOLOW | Macro core (ortodoxo) | 22 | 89.55223880597015 | Usado para capital/produto e validação. |
| commodity_price_index | Q | Índice de preços de commodities | índice (2016=100) | FRED | PALLFNFINDEXQ | log | exogenous | PC | Macro core (ortodoxo) | 1 | 99.21875 | Média trimestral do índice amplo de commodities do FMI. |
| vix | Q | Índice de volatilidade VIX | índice | FRED | VIXCLS | log | exogenous | MF | Macro core (ortodoxo) | 1 | 100.0 | Média trimestral; proxy de risco global. |
| primary_balance_gdp | Q | Resultado primário (% do PIB) | % do PIB | BCB | 5793 | level | exogenous | ISLM | Macro core (ortodoxo) | 1 | 75.0 | Média trimestral do resultado primário acumulado em 12 meses (governo central). |

## 7. Lacunas explícitas

- **Brasil**: IPCA começa em 1980 (série anual de 12m em 1981); PNAD Contínua trimestral em 2012; spread trimestral não harmonizado; salário real trimestral não usado.
- **Argentina**: PIB trimestral em 2004; inflação com quebras INDEC 2007–2015.
- **Alemanha**: PIB trimestral em 1991 (pré-reunificação não coberto).
- **Japão**: CPI trimestral do OECD-MEI termina em 2021T2.
- **China/Índia/Chile/Colômbia/Peru/Rússia**: sem PIB trimestral estável; apenas anual.
- **Arábia Saudita**: PIB trimestral em 2010.
- **UE**: agregado do G20 com cobertura anual parcial; não entra em somas.
- **Capital/PTF**: PWT termina em 2019; não extrapolado.
- **Blocos heterodoxos**: Gini/top10/bottom20 ~1990+ e cobertura esparsa; termos de troca ~2005+; CO2/energia ~1970+; capital bancário/NPL ~2000+. Ver `cobertura_%`.

## 8. Reprodutibilidade

`make all` (fetch → build → validate → empirical → export → reports → test). Manifesto com URL/timestamp/SHA-256 em `data/processed/manifest.json`.