# Dummies de regime — metadados, matriz e papel no DSGE

**101 dummies**, codificadas em `config/regimes.yml` e materializadas em `regime_matrix_annual.csv` (1474 país-ano) e `regime_matrix_quarterly.csv` (2048 país-trimestre).

## 1. Cobertura por tipo

| tipo | n |
|---|---|
| commodity | 3 |
| crisis_domestic | 29 |
| crisis_global | 17 |
| fiscal | 14 |
| methodology | 6 |
| monetary | 32 |

## 2. Papel no DSGE

| papel_dsge | n |
|---|---|
| control | 5 |
| observed_shock | 42 |
| parameter_break | 50 |
| sample_split | 4 |

- `observed_shock`: entra como regressor exógeno/choque observável (ex.: GFC, pandemia, commodity).
- `parameter_break`: quebra de parâmetro (ex.: metas de inflação, teto de gastos, ZLB).
- `control`: controle em modelos reduzidos, sem papel estrutural.
- `sample_split`: define amostra (hiperinflação, câmbio fixo).

## 3. Matriz país × dummy — Brasil (recorte)

A matriz completa (0/1 para todos os 22 países e 1960–2026) está em `data/processed/regime_matrix_annual.csv`. O recorte abaixo mostra as dummies brasileiras mais relevantes e os anos de ativação.

| dummy | nome | tipo | inicio | fim | papel_dsge |
|---|---|---|---|---|---|
| g_oil_1973 | Primeiro choque do petróleo (embargo da OPEP) | crisis_global | 1973-10-01 | 1975-03-31 | observed_shock |
| g_volcker_1979 | Choque Volcker (aperto monetário dos EUA) | crisis_global | 1979-08-01 | 1982-12-31 | observed_shock |
| br_hyperinflation | Hiperinflação brasileira | crisis_domestic | 1980-01-01 | 1994-06-30 | sample_split |
| g_latam_debt_1982 | Crise da dívida da América Latina | crisis_global | 1982-08-01 | 1985-12-31 | observed_shock |
| br_cruzado | Plano Cruzado | crisis_domestic | 1986-02-01 | 1987-06-30 | parameter_break |
| br_bresser | Plano Bresser | crisis_domestic | 1987-06-01 | 1989-01-31 | parameter_break |
| br_verao | Plano Verão | crisis_domestic | 1989-01-01 | 1990-03-31 | parameter_break |
| br_collor | Plano Collor | crisis_domestic | 1990-03-01 | 1991-01-31 | parameter_break |
| br_real_plan | Plano Real | crisis_domestic | 1994-07-01 | 1995-06-30 | parameter_break |
| br_crawling_band | Câmbio administrado com bandas (pós-Real) | monetary | 1995-03-01 | 1999-01-31 | parameter_break |
| g_russia_1998 | Default russo e contágio (LTCM) | crisis_global | 1998-08-01 | 1998-12-31 | observed_shock |
| br_primary_targets | Metas de superávit primário | fiscal | 1999-01-01 | 2016-12-31 | parameter_break |
| br_floating | Câmbio flutuante | monetary | 1999-01-01 | permanente | sample_split |
| br_it | Regime de metas de inflação | monetary | 1999-06-01 | permanente | parameter_break |
| br_lrf | Lei de Responsabilidade Fiscal | fiscal | 2000-05-01 | permanente | parameter_break |
| br_election_2002 | Crise de confiança eleitoral de 2002 | crisis_domestic | 2002-07-01 | 2002-12-31 | observed_shock |
| g_commodity_supercycle | Superciclo das commodities | commodity | 2003-01-01 | 2011-12-31 | observed_shock |
| br_govdebt_method_2008 | Mudança metodológica da dívida pública (2008) | methodology | 2008-01-01 | 2008-01-31 | parameter_break |
| g_gfc_2008 | Crise financeira global (GFC) | crisis_global | 2008-09-01 | 2009-12-31 | observed_shock |
| br_gfc | Crise financeira global no Brasil | crisis_global | 2008-09-01 | 2009-12-31 | observed_shock |
| br_gdp_rebase_2010 | Mudança de base das Contas Nacionais (2010) | methodology | 2010-01-01 | 2010-12-31 | parameter_break |
| br_ipca_rebase_2012 | Nova estrutura de pesos do IPCA (2012) | methodology | 2012-01-01 | 2012-01-31 | parameter_break |
| g_taper_tantrum_2013 | Taper tantrum (choque financeiro externo) | crisis_global | 2013-05-01 | 2013-12-31 | observed_shock |
| br_recession_2014 | Recessão 2014–2016 e crise política | crisis_domestic | 2014-04-01 | 2016-12-31 | observed_shock |
| br_ceiling | Teto de gastos (EC 95/2016) | fiscal | 2016-12-01 | permanente | parameter_break |
| g_pandemic_2020 | Pandemia de COVID-19 | crisis_global | 2020-01-01 | 2021-12-31 | observed_shock |
| br_pandemic | Emergência COVID-19 no Brasil | crisis_global | 2020-03-01 | 2021-12-31 | observed_shock |
| br_tightening_2021 | Ciclo de aperto monetário 2021–2023 | monetary | 2021-03-01 | 2023-08-31 | observed_shock |
| g_inflation_energy_2022 | Choque inflacionário de energia e alimentos (2022) | crisis_global | 2022-01-01 | 2023-12-31 | observed_shock |
| br_new_framework | Novo arcabouço fiscal (LC 200/2023) | fiscal | 2023-08-01 | permanente | parameter_break |

## 4. Como usar

- Em modelos reduzidos: incluir a dummy como controle ou quebra de intercepto/slope; a coluna `regime_dummy` do dataset longo lista as dummies ativas.
- No DSGE_S: `br_it`, `us_zlb_2008`, `g_gfc_2008`, `g_pandemic_2020` entram como quebras de parâmetro ou choques observáveis; ver `docs/02_dsge_observables.md`.
- No DSGE_M: `br_ceiling`, `br_new_framework`, `br_lrf` deslocam a regra fiscal; `g_commodity_supercycle` desloca o prêmio de risco/termos de troca.

## 5. Metadados completos

Arquivo: `data/processed/regime_metadata.csv` (colunas: dummy, nome, tipo, escopo, países, início, fim, frequências, fonte, URL, variáveis afetadas, modelos, papel no DSGE, justificativa).

| dummy | nome | tipo | inicio | fim | fonte | papel_dsge |
|---|---|---|---|---|---|---|
| g_oil_1973 | Primeiro choque do petróleo (embargo da OPEP) | crisis_global | 1973-10-01 | 1975-03-31 | História econômica; preço do Brent (FRED POILBREUSDM); NBER recessions | observed_shock |
| g_volcker_1979 | Choque Volcker (aperto monetário dos EUA) | crisis_global | 1979-08-01 | 1982-12-31 | Federal Reserve History; FRED FEDFUNDS | observed_shock |
| g_latam_debt_1982 | Crise da dívida da América Latina | crisis_global | 1982-08-01 | 1985-12-31 | Reinhart & Rogoff (2009); GMD (SovDebtCrisis) | observed_shock |
| g_asia_1997 | Crise asiática | crisis_global | 1997-07-01 | 1998-12-31 | IMF; GMD (CurrencyCrisis, BankingCrisis) | observed_shock |
| g_russia_1998 | Default russo e contágio (LTCM) | crisis_global | 1998-08-01 | 1998-12-31 | IMF; GMD (SovDebtCrisis) | observed_shock |
| g_gfc_2008 | Crise financeira global (GFC) | crisis_global | 2008-09-01 | 2009-12-31 | Federal Reserve; IMF; GMD (BankingCrisis) | observed_shock |
| g_euro_crisis_2010 | Crise da dívida soberana da área do euro | crisis_global | 2010-05-01 | 2012-12-31 | ECB; European Commission | observed_shock |
| g_commodity_supercycle | Superciclo das commodities | commodity | 2003-01-01 | 2011-12-31 | IMF Commodity Price Index; FRED PALLFNFINDEXQ | observed_shock |
| g_pandemic_2020 | Pandemia de COVID-19 | crisis_global | 2020-01-01 | 2021-12-31 | OMS; IMF WEO; GMD | observed_shock |
| g_inflation_energy_2022 | Choque inflacionário de energia e alimentos (2022) | crisis_global | 2022-01-01 | 2023-12-31 | FRED; IMF WEO | observed_shock |
| g_taper_tantrum_2013 | Taper tantrum (choque financeiro externo) | crisis_global | 2013-05-01 | 2013-12-31 | Federal Reserve; IMF | observed_shock |
| br_hyperinflation | Hiperinflação brasileira | crisis_domestic | 1980-01-01 | 1994-06-30 | BCB SGS 433; IBGE; Simonsen (1995) | sample_split |
| br_cruzado | Plano Cruzado | crisis_domestic | 1986-02-01 | 1987-06-30 | BCB; Decreto-Lei 2.283/1986 | parameter_break |
| br_bresser | Plano Bresser | crisis_domestic | 1987-06-01 | 1989-01-31 | BCB; Decreto-Lei 2.335/1987 | parameter_break |
| br_verao | Plano Verão | crisis_domestic | 1989-01-01 | 1990-03-31 | BCB; Lei 7.730/1989 | parameter_break |
| br_collor | Plano Collor | crisis_domestic | 1990-03-01 | 1991-01-31 | BCB; Lei 8.024/1990 | parameter_break |
| br_real_plan | Plano Real | crisis_domestic | 1994-07-01 | 1995-06-30 | BCB; Lei 8.880/1994 | parameter_break |
| br_crawling_band | Câmbio administrado com bandas (pós-Real) | monetary | 1995-03-01 | 1999-01-31 | BCB; IMF AREAER | parameter_break |
| br_floating | Câmbio flutuante | monetary | 1999-01-01 | permanente | BCB; Comunicado 6.565/1999 | sample_split |
| br_it | Regime de metas de inflação | monetary | 1999-06-01 | permanente | BCB; Decreto 3.088/1999 | parameter_break |
| br_primary_targets | Metas de superávit primário | fiscal | 1999-01-01 | 2016-12-31 | Tesouro Nacional; LDO 2000; IMF | parameter_break |
| br_lrf | Lei de Responsabilidade Fiscal | fiscal | 2000-05-01 | permanente | Lei Complementar 101/2000 | parameter_break |
| br_election_2002 | Crise de confiança eleitoral de 2002 | crisis_domestic | 2002-07-01 | 2002-12-31 | BCB; IMF | observed_shock |
| br_gfc | Crise financeira global no Brasil | crisis_global | 2008-09-01 | 2009-12-31 | BCB; GMD | observed_shock |
| br_recession_2014 | Recessão 2014–2016 e crise política | crisis_domestic | 2014-04-01 | 2016-12-31 | IBGE; BCB | observed_shock |
| br_ceiling | Teto de gastos (EC 95/2016) | fiscal | 2016-12-01 | permanente | Emenda Constitucional 95/2016 | parameter_break |
| br_pandemic | Emergência COVID-19 no Brasil | crisis_global | 2020-03-01 | 2021-12-31 | Ministério da Saúde; BCB; IBGE | observed_shock |
| br_tightening_2021 | Ciclo de aperto monetário 2021–2023 | monetary | 2021-03-01 | 2023-08-31 | BCB; Copom | observed_shock |
| br_new_framework | Novo arcabouço fiscal (LC 200/2023) | fiscal | 2023-08-01 | permanente | Lei Complementar 200/2023 | parameter_break |
| br_gdp_rebase_2010 | Mudança de base das Contas Nacionais (2010) | methodology | 2010-01-01 | 2010-12-31 | IBGE; nota metodológica das Contas Nacionais | parameter_break |

*(tabela completa no CSV; aqui listamos as 30 primeiras para legibilidade)*