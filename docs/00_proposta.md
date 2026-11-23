# Proposta de desenho — dataset macroeconômico cross-country (âncora: Brasil)

**Versão:** 1.0.0 · **Extração:** 2026-11-23 · **Horizonte:** anual 1960–2026; trimestral 1995T1–2026T4
**Status:** proposta executada. Cada item abaixo traz a decisão tomada e o produto correspondente.

---

## (i) Lista fechada de países e grupos

### Países (22) + agregados (2)

| Região | Países |
|---|---|
| América Latina | ARG, BRA, CHL, COL, MEX, PER |
| América do Norte | CAN, USA |
| Europa | DEU, FRA, GBR, ITA |
| Europa/Ásia | RUS, TUR |
| Ásia-Pacífico | AUS, CHN, IDN, IND, JPN, KOR |
| Oriente Médio | SAU |
| África | ZAF |
| Agregados | **EU** (União Europeia; não é país), **WLD** (mundo; só para PIB mundial) |

**Regra de dupla contagem:** `EU` e `WLD` nunca entram em somas/médias de países. A UE aparece no G20 como agregado e é sinalizada em `config/countries.yml`.

### Grupos (listas fechadas, sobrepostas de propósito)

| Grupo | Membros | Justificativa |
|---|---|---|
| **BRICS** | BRA, RUS, IND, CHN, ZAF | Composição original (2001/2009); expansão de 2024 excluída para manter lista fechada e comparável. |
| **G20** | ARG, AUS, BRA, CAN, CHN, FRA, DEU, IND, IDN, ITA, JPN, KOR, MEX, RUS, SAU, ZAF, TUR, GBR, USA, **EU** | Composição oficial (19 países + UE). UE é agregado, excluída de somas. |
| **G7** | CAN, FRA, DEU, ITA, JPN, GBR, USA | Referência de economias avançadas. |
| **TOP10_NOMINAL** | USA, CHN, DEU, JPN, IND, GBR, FRA, ITA, BRA, CAN | Métrica fixa: PIB nominal em USD, WEO out/2025, estimativa 2025. Inclui o Brasil. |
| **LATAM6** | BRA, MEX, ARG, CHL, COL, PER | Seis maiores da América Latina com cobertura consistente. |
| **EMERG_COMP** | BRA, MEX, IND, IDN, TUR, ZAF | Emergentes de renda média com regimes documentados. |
| **ADVANCED** | USA, DEU, GBR, JPN, CAN, FRA, ITA, AUS, KOR | Fronteira tecnológica e política monetária. |
| **QUARTERLY_CORE** | BRA, USA, DEU, GBR, JPN, CAN, MEX, AUS, FRA, ITA, KOR, ZAF, TUR, IDN, ARG, SAU | PIB trimestral estável (≥ 60 trimestres). CHN, IND, CHL, COL, PER, RUS ficam no anual. |
| **COMMODITY_EXPORTERS** | BRA, ARG, CHL, COL, PER, RUS, SAU, ZAF, IDN, AUS | Choques de termos de troca. |
| **HIGH_INFLATION_HISTORY** | BRA, ARG, PER, TUR, RUS | Inflação > 100% em algum momento pós-1960; justifica amostra DSGE pós-estabilização. |
| **IT_REGIME** | BRA, MEX, CHL, COL, PER, ZAF, TUR, IDN, KOR, GBR, CAN, AUS, DEU, FRA, ITA, EU, USA, JPN, IND, ARG (2016–18) | Dummies monetárias e amostra de estimação. |

Produto: `docs/05_country_groups.md`, `config/countries.yml`.

---

## (ii) Variáveis por modelo e por equação de medida

### Modelos reduzidos — endógenas e exógenas

| Modelo | Endógenas | Exógenas / instrumentos | Observáveis no dataset | Papel |
|---|---|---|---|---|
| **IS-LM** | `gdp_real`, `policy_rate`/`short_rate` | `gov_exp_gdp` (G), `tax_burden_gdp` (T), `m2` (M), `cpi_index` (P), `investment_gdp` (I₀) | Y, i, G, T, M, P, I | reduzido |
| **Mundell-Fleming** | `gdp_real`, `policy_rate`, `exchange_rate_nominal` | `gov_exp_gdp`, `m2`, `world_gdp_real` (Y*), `foreign_policy_rate` (i*), `cpi_index` (P*) | Y, i, E, G, M, Y*, i*, P* | reduzido |
| **AD-AS** | `output_gap` ou `gdp_real`, `inflation` | `commodity_price_index`, `oil_price`, `gov_exp_gdp`, `policy_rate`, `inflation_expectations` | P/π, Y, choques, política, expectativas | reduzido |
| **Curva de Phillips** | `inflation`, `unemployment`/`output_gap` | `inflation_expectations`, `unemployment` (u_n via HP), `oil_price` | π, u/hiato, π^e, u_n, choques | reduzido |
| **Regra de Taylor** | `policy_rate` | `inflation`, `inflation_target` (π*), `output_gap`, `neutral_rate` (r*) | i, π, π*, hiato, r* | reduzido |
| **Solow** | `gdp_real_pc` (y), `capital_stock` (k) | `investment_gdp` (s), `delta` (calibrado), `population` (n), `tfp_growth` (g), `tfp` (A) | y, k, s, δ, n, g, A | reduzido |

### DSGE — equações de medida

Tabela completa (17 linhas) em `docs/02_dsge_observables.md`. Resumo:

| Observável | Transformação | Variável do modelo | Equação de medida | Choque associado |
|---|---|---|---|---|
| `output_gap` | 100·(log y − log y*) | x_t | x_obs = 100·x_t + e_x | demanda |
| `inflation` | 400·Δlog(CPI_SA) | π_t | π_obs = 400·π_t + e_π | markup |
| `policy_rate` | Selic anual / 4 | i_t | i_obs = 400·i_t + e_i | monetário |
| `consumption_real` | 100·HP(log C) | c_t | c_obs = 100·c_t | preferência |
| `investment_real` | 100·HP(log I) | inv_t | inv_obs = 100·inv_t | investimento |
| `gov_exp_real` | 100·HP(log G) | g_t | g_obs = 100·g_t | fiscal |
| `foreign_output` | 100·HP(log Y*) | y*_t | y*_obs = 100·y*_t | externo |
| `credit_spread` | nível | rp_t | rp_obs = rp_t | risco |

**Variáveis latentes:** PIB potencial, hiato, r*, u_n, capital, salário real, markup, expectativas.
**Choques:** tecnologia, preferência, política monetária, política fiscal, markup, prêmio de risco, externo, oferta de trabalho. A correspondência observável→choque e os riscos estão em `docs/02_dsge_observables.md`.

---

## (iii) Fontes e plano de validação cruzada

### Espinha dorsal e complementos

| Fonte | Papel | Cobertura | Uso no dataset |
|---|---|---|---|
| **GMD** | espinha dorsal anual | 1086–2026, 243 países, 46 variáveis | 35 variáveis canônicas + crises |
| **WDI** | complemento/validação | 1960–2026 | participação, crédito, carga tributária, PIB mundial, validação |
| **WEO** | complemento fiscal pós-1980 | 1980–2031 (projeções) | resultado primário, dívida líquida, PPP, validação |
| **PWT 10.01** | capital/PTF | 1950–2019 | capital, PTF, emprego, horas, capital humano, labor share |
| **FRED / OECD-MEI / BIS** | subamostra trimestral | 1995–2026 | PIB, CPI, desemprego, juros, REER, câmbio, commodities, VIX |
| **BCB SGS** | Brasil | 1980–2026 | Selic, IPCA, núcleo, desemprego, câmbio, primário |
| **IBGE SIDRA** | Brasil | 1996–2026 | PIB trimestral e componentes, IPCA |
| **Focus/BCB** | expectativas | 2001–2026 | expectativas de inflação (Brasil) |

### Plano de validação (executado)

| Conceito | Primária | Validação | Tolerância | Decisão |
|---|---|---|---|---|
| Crescimento do PIB | GMD (derivado) | WEO `NGDP_RPCH`; WDI `NY.GDP.MKTP.KD.ZG` | 1 p.p. | GMD prevalece; divergências > 1 p.p. sinalizadas |
| Inflação | BCB/IPCA (Brasil); GMD (demais) | WEO `PCPIPCH`; WDI `FP.CPI.TOTL.ZG` | 2 p.p. | IPCA é a medida oficial do Brasil |
| Desemprego | GMD | WEO `LUR`; WDI `SL.UEM.TOTL.ZS` | 1 p.p. | Definições nacionais; WDI (OIT) é referência conceitual |
| Dívida bruta | GMD (governo geral) | WEO `GGXWDG_NGDP`; WDI `GC.DOD.TOTL.GD.ZS` (central) | 5 p.p. | Perímetros diferentes; WDI não é verdade |
| PIB nominal USD | GMD (nGDP/USDfx) | WEO `NGDPD`; WDI `NY.GDP.MKTP.CD` | 5% | Câmbio médio do GMD prevalece |
| Resultado primário | WEO `pb` (governo geral) | BCB SGS 5793 (governo central, Brasil) | 2 p.p. | Perímetros distintos; ambos reportados |

**Resultados:** crescimento (erro médio absoluto 0,23 p.p.; 95% dentro de 1 p.p.), inflação (3,42 p.p.; 96% dentro de 2 p.p., afetada por hiperinflações), desemprego (0,48 p.p.; 86%), dívida (5,84 p.p.; 74%, por perímetro), PIB USD (2%; 89%). Tabela completa em `data/processed/cross_source_summary.csv`; divergências em `cross_source_divergences.csv`.

---

## (iv) Matriz inicial de dummies de regime

Foram codificadas **101 dummies** país-tempo (30 para o Brasil), em `config/regimes.yml`, com nome, descrição, fonte, URL, início/fim, frequência, variáveis afetadas, modelos e papel no DSGE.

| Família | Exemplos | Nº aprox. |
|---|---|---|
| Crises globais | petróleo 1973, Volcker 1979–82, Ásia 1997, Rússia 1998, GFC 2008–09, euro 2010–12, pandemia 2020–21, energia 2022 | 11 |
| Monetário | metas de inflação (BRA 1999, MEX 2001, GBR 1992…), câmbio fixo/flutuante, ZLB, QE, crises cambiais | 20 |
| Fiscal | LRF 2000, teto 2016, novo arcabouço 2023, metas primárias, Maastricht, Hartz, GST | 16 |
| Crises domésticas | hiperinflação BRA/ARG/PER, planos Cruzado/Bresser/Verão/Collor/Real, default ARG 2001/2020, crises cambiais | 22 |
| Commodities | superciclo 2003–2011, boom mineral AUS, petróleo SAU 2014–16 | 4 |
| Metodológicos | base do PIB BRA 2010, cesta do IPCA 2012, dívida BRA 2008, reunificação DEU | 4 |
| Dummies GMD | crises bancária/cambial/dívida soberana (1800–2025) | 3 |

**Resolução:** anual (ano = 1 se qualquer trimestre do evento o intersecta) e trimestral (trimestre = 1 se o evento o intersecta em ≥ 1 dia). Dummies permanentes são `step` (1 até o fim da amostra).

**Papel no DSGE:** `observed_shock` (GFC, pandemia, commodity), `parameter_break` (IT, LRF, teto, ZLB), `control` (QT, QE), `sample_split` (hiperinflação, câmbio fixo). No DSGE_S, `br_it`, `g_gfc_2008`, `g_pandemic_2020` são quebras de parâmetro/choques observáveis; no DSGE_M, `br_lrf`, `br_ceiling`, `br_new_framework` deslocam a regra fiscal.

Produtos: `regime_matrix_annual.csv` (1.474 × 101), `regime_matrix_quarterly.csv` (2.048 × 97), `regime_metadata.csv`, `docs/03_regime_dummies.md`.

---

## (v) Cronograma (10 semanas) e status

| Fase | Semanas | Entregável | Status |
|---|---|---|---|
| 1. Escopo e listas fechadas | 1 | proposta, grupos, dicionário | **concluído** |
| 2. Coleta e cache | 2–3 | fontes, manifesto, parsing | **concluído** |
| 3. Harmonização anual | 3–4 | painel 1960–2026, unidades, flags | **concluído** |
| 4. Subamostra trimestral | 4–5 | painel 1995–2026, X-13, consistência A-Q | **concluído** |
| 5. Regimes e dummies | 5 | 101 dummies + matriz + metadados | **concluído** |
| 6. Validação | 6–7 | cross-source, identidades, ADF/KPSS, Bai-Perron, Chow | **concluído** |
| 7. DSGE pequeno | 7–8 | estimação bayesiana BRA/EUA, prior/posterior, IRF, FEVD, identificação | **concluído** (com ressalvas) |
| 8. DSGE médio | 8–9 | calibração, solução, momentos, sensibilidade | **concluído** |
| 9. Relatórios e reprodutibilidade | 9–10 | codebook, auditoria, testes, Makefile | **concluído** |

**Decisões que mudaram o plano:**
1. A lista dos 10 maiores usa PIB nominal USD (WEO 2025), não PPP.
2. O DSGE estimado é o pequeno; o médio é calibrado (decisão registrada após diagnóstico de identificação).
3. O núcleo estrutural do DSGE pequeno é calibrado; hábitos, indexação, persistência e choques são estimados.
4. A subamostra trimestral tem 16 países (não 22): CHN, IND, CHL, COL, PER e RUS não têm PIB trimestral estável no FRED/OECD-MEI.
5. A UE é agregado e não entra em somas; cobertura anual da UE é parcial e está sinalizada.

---

## Produtos

| Produto | Arquivo |
|---|---|
| Dataset longo | `data/processed/macro_long.parquet` / `.csv` |
| Dataset wide | `data/processed/wide/` |
| Codebook | `docs/01_codebook.md` |
| DSGE observável→modelo | `docs/02_dsge_observables.md` |
| Dummies de regime | `docs/03_regime_dummies.md` + `regime_matrix_*.csv` |
| Auditoria e validação | `docs/04_audit_report.md` |
| Grupos de países | `docs/05_country_groups.md` |
| Metodologia | `docs/06_metodologia.md` |
| Cobertura | `coverage_matrix_annual.csv`, `coverage.csv` |
| Scripts | `src/macrodata/`, `scripts/`, `Makefile` |
| Diagnósticos DSGE | `data/processed/dsge_*` |
