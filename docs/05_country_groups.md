# Grupos de países — listas fechadas e justificativa

A lista de países é **fechada**: 22 países + agregado UE. Grupos se sobrepõem de propósito; a UE é agregado e é excluída de somas/médias para evitar dupla contagem.

| grupo | nome | membros | n | justificativa |
|---|---|---|---|---|
| BRICS | BRICS (composição original) | BRA, RUS, IND, CHN, ZAF | 5 | Composição original do acrônimo (2001) e do bloco formal desde 2009. A expansão de 2024 é deliberadamente excluída para manter a lista fechada e comparável ao longo de todo o período; novos membros entram apenas se já pertencerem a outro grupo do desenho. |
| G20 | G20 (países + UE) | ARG, AUS, BRA, CAN, CHN, FRA, DEU, IND, IDN, ITA, JPN, KOR, MEX, RUS, SAU, ZAF, TUR, GBR, USA, EU | 20 | Composição oficial do G20 (19 países + União Europeia). A UE é agregado e é excluída de qualquer soma/média de países para evitar dupla contagem. |
| G7 | G7 | CAN, FRA, DEU, ITA, JPN, GBR, USA | 7 | Composição oficial do G7; economias avançadas de referência. |
| TOP10_NOMINAL | 10 maiores economias — PIB nominal USD (WEO out/2025) | USA, CHN, DEU, JPN, IND, GBR, FRA, ITA, BRA, CAN | 10 | Métrica FIXA: PIB nominal em USD correntes, estimativa WEO de outubro/2025 para 2025. Inclui o Brasil (âncora). A métrica PPP é reportada apenas como variável (gdp_ppp_usd), nunca para redefinir o grupo. |
| LATAM6 | América Latina (6 maiores) | BRA, MEX, ARG, CHL, COL, PER | 6 | Seis maiores economias da América Latina por PIB nominal e cobertura consistente em GMD/WDI/WEO; bloco solicitado na especificação. |
| EMERG_COMP | Emergentes comparáveis | BRA, MEX, IND, IDN, TUR, ZAF | 6 | Países emergentes de renda média com PIB relevante, regimes monetários documentados e cobertura razoável desde 1980; grupo solicitado. |
| ADVANCED | Economias avançadas | USA, DEU, GBR, JPN, CAN, FRA, ITA, AUS, KOR | 9 | Referência de fronteira tecnológica e de política monetária. |
| QUARTERLY_CORE | Núcleo trimestral | BRA, USA, DEU, GBR, JPN, CAN, MEX, AUS, FRA, ITA, KOR, ZAF, TUR, IND, IDN, CHN | 16 | Países com PIB trimestral encadeado e deflator/CPI trimestral estáveis em FRED/OCDE-MEI, IBGE e BCB. O núcleo mínimo solicitado (BRA, USA, DEU, GBR, JPN, CAN, MEX) é sempre preservado; os demais entram se cumprirem o critério de >= 60 trimestres. |
| COMMODITY_EXPORTERS | Exportadores de commodities | BRA, ARG, CHL, COL, PER, RUS, SAU, ZAF, IDN, AUS | 10 | Para dummies de choque de commodities e termos de troca. |
| HIGH_INFLATION_HISTORY | Histórico de alta inflação | BRA, ARG, PER, TUR, RUS | 5 | Países com inflação anual > 100% em algum momento pós-1960; justifica amostra DSGE pós-estabilização e dummies de hiperinflação/planos. |
| IT_REGIME | Regime de metas de inflação (datas em regimes.yml) | BRA, MEX, CHL, COL, PER, ZAF, TUR, IDN, KOR, GBR, CAN, AUS, DEU, FRA, ITA, EU, USA, JPN, IND, ARG | 20 | Regime explícito ou quasi-explícito de meta; usado para dummies monetárias e para definir a amostra de estimação. ARG entra apenas 2016–2018. |

## Uso nos modelos

- **Painel anual**: todos os 22 países; a UE entra apenas onde há série (WEO), sem uso em somas.
- **Painel trimestral**: 16 países com PIB trimestral estável (BRA, USA, DEU, GBR, JPN, CAN, MEX, AUS, FRA, ITA, KOR, ZAF, TUR, IDN, ARG, SAU); CHN, IND, CHL, COL, PER e RUS ficam no anual.
- **DSGE**: Brasil (âncora) e EUA (validação); demais países entram nos modelos reduzidos e na comparação de momentos.

## Checagem de dupla contagem

- `EU` tem `iso3=EU`, `role=exogenous` e é marcada como agregado em `config/countries.yml`.
- Nenhuma soma cross-country inclui `EU` ou `WLD`; `WLD` só aparece em `world_gdp_real`/`world_gdp_growth`.