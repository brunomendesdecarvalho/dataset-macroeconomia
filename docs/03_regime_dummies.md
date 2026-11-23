# Dummies de regime — metadados e matriz

**101 dummies**, em `config/regimes.yml`, materializadas em `regime_matrix_annual.csv` (1474 país-ano) e `regime_matrix_quarterly.csv` (2048 país-trimestre).

## 1. Cobertura por tipo

| tipo | n |
|---|---|
| commodity | 3 |
| crisis_domestic | 29 |
| crisis_global | 17 |
| fiscal | 14 |
| methodology | 6 |
| monetary | 32 |

## 2. Matriz país × dummy — Brasil

A matriz completa está em `data/processed/regime_matrix_annual.csv`; o recorte abaixo lista as dummies brasileiras.

| dummy | nome | tipo | inicio | fim |
|---|---|---|---|---|
| g_oil_1973 | Primeiro choque do petróleo (embargo da OPEP) | crisis_global | 1973-10-01 | 1975-03-31 |
| g_volcker_1979 | Choque Volcker (aperto monetário dos EUA) | crisis_global | 1979-08-01 | 1982-12-31 |
| br_hyperinflation | Hiperinflação brasileira | crisis_domestic | 1980-01-01 | 1994-06-30 |
| g_latam_debt_1982 | Crise da dívida da América Latina | crisis_global | 1982-08-01 | 1985-12-31 |
| br_cruzado | Plano Cruzado | crisis_domestic | 1986-02-01 | 1987-06-30 |
| br_bresser | Plano Bresser | crisis_domestic | 1987-06-01 | 1989-01-31 |
| br_verao | Plano Verão | crisis_domestic | 1989-01-01 | 1990-03-31 |
| br_collor | Plano Collor | crisis_domestic | 1990-03-01 | 1991-01-31 |
| br_real_plan | Plano Real | crisis_domestic | 1994-07-01 | 1995-06-30 |
| br_crawling_band | Câmbio administrado com bandas (pós-Real) | monetary | 1995-03-01 | 1999-01-31 |
| g_russia_1998 | Default russo e contágio (LTCM) | crisis_global | 1998-08-01 | 1998-12-31 |
| br_primary_targets | Metas de superávit primário | fiscal | 1999-01-01 | 2016-12-31 |
| br_floating | Câmbio flutuante | monetary | 1999-01-01 | permanente |
| br_it | Regime de metas de inflação | monetary | 1999-06-01 | permanente |
| br_lrf | Lei de Responsabilidade Fiscal | fiscal | 2000-05-01 | permanente |
| br_election_2002 | Crise de confiança eleitoral de 2002 | crisis_domestic | 2002-07-01 | 2002-12-31 |
| g_commodity_supercycle | Superciclo das commodities | commodity | 2003-01-01 | 2011-12-31 |
| br_govdebt_method_2008 | Mudança metodológica da dívida pública (2008) | methodology | 2008-01-01 | 2008-01-31 |
| g_gfc_2008 | Crise financeira global (GFC) | crisis_global | 2008-09-01 | 2009-12-31 |
| br_gfc | Crise financeira global no Brasil | crisis_global | 2008-09-01 | 2009-12-31 |
| br_gdp_rebase_2010 | Mudança de base das Contas Nacionais (2010) | methodology | 2010-01-01 | 2010-12-31 |
| br_ipca_rebase_2012 | Nova estrutura de pesos do IPCA (2012) | methodology | 2012-01-01 | 2012-01-31 |
| g_taper_tantrum_2013 | Taper tantrum (choque financeiro externo) | crisis_global | 2013-05-01 | 2013-12-31 |
| br_recession_2014 | Recessão 2014–2016 e crise política | crisis_domestic | 2014-04-01 | 2016-12-31 |
| br_ceiling | Teto de gastos (EC 95/2016) | fiscal | 2016-12-01 | permanente |
| g_pandemic_2020 | Pandemia de COVID-19 | crisis_global | 2020-01-01 | 2021-12-31 |
| br_pandemic | Emergência COVID-19 no Brasil | crisis_global | 2020-03-01 | 2021-12-31 |
| br_tightening_2021 | Ciclo de aperto monetário 2021–2023 | monetary | 2021-03-01 | 2023-08-31 |
| g_inflation_energy_2022 | Choque inflacionário de energia e alimentos (2022) | crisis_global | 2022-01-01 | 2023-12-31 |
| br_new_framework | Novo arcabouço fiscal (LC 200/2023) | fiscal | 2023-08-01 | permanente |

## 3. Como usar

- Controle ou quebra de intercepto/slope em modelos reduzidos; a coluna `regime_dummy` do long lista as ativas.
- No SVAR, `g_gfc_2008` e `g_pandemic_2020` entram como controles exógenos.
- Dummies de método (`br_gdp_rebase_2010`, `br_ipca_rebase_2012`, `ar_indec_2007`) sinalizam quebras de nível, não de ciclo.

## 4. Metadados completos

`data/processed/regime_metadata.csv` (dummy, nome, tipo, escopo, países, início, fim, frequências, fonte, URL, variáveis afetadas, modelos).

| dummy | nome | tipo | inicio | fim | fonte |
|---|---|---|---|---|---|
| g_oil_1973 | Primeiro choque do petróleo (embargo da OPEP) | crisis_global | 1973-10-01 | 1975-03-31 | História econômica; preço do Brent (FRED POILBREUSDM); NBER recessions |
| g_volcker_1979 | Choque Volcker (aperto monetário dos EUA) | crisis_global | 1979-08-01 | 1982-12-31 | Federal Reserve History; FRED FEDFUNDS |
| g_latam_debt_1982 | Crise da dívida da América Latina | crisis_global | 1982-08-01 | 1985-12-31 | Reinhart & Rogoff (2009); GMD (SovDebtCrisis) |
| g_asia_1997 | Crise asiática | crisis_global | 1997-07-01 | 1998-12-31 | IMF; GMD (CurrencyCrisis, BankingCrisis) |
| g_russia_1998 | Default russo e contágio (LTCM) | crisis_global | 1998-08-01 | 1998-12-31 | IMF; GMD (SovDebtCrisis) |
| g_gfc_2008 | Crise financeira global (GFC) | crisis_global | 2008-09-01 | 2009-12-31 | Federal Reserve; IMF; GMD (BankingCrisis) |
| g_euro_crisis_2010 | Crise da dívida soberana da área do euro | crisis_global | 2010-05-01 | 2012-12-31 | ECB; European Commission |
| g_commodity_supercycle | Superciclo das commodities | commodity | 2003-01-01 | 2011-12-31 | IMF Commodity Price Index; FRED PALLFNFINDEXQ |
| g_pandemic_2020 | Pandemia de COVID-19 | crisis_global | 2020-01-01 | 2021-12-31 | OMS; IMF WEO; GMD |
| g_inflation_energy_2022 | Choque inflacionário de energia e alimentos (2022) | crisis_global | 2022-01-01 | 2023-12-31 | FRED; IMF WEO |
| g_taper_tantrum_2013 | Taper tantrum (choque financeiro externo) | crisis_global | 2013-05-01 | 2013-12-31 | Federal Reserve; IMF |
| br_hyperinflation | Hiperinflação brasileira | crisis_domestic | 1980-01-01 | 1994-06-30 | BCB SGS 433; IBGE; Simonsen (1995) |
| br_cruzado | Plano Cruzado | crisis_domestic | 1986-02-01 | 1987-06-30 | BCB; Decreto-Lei 2.283/1986 |
| br_bresser | Plano Bresser | crisis_domestic | 1987-06-01 | 1989-01-31 | BCB; Decreto-Lei 2.335/1987 |
| br_verao | Plano Verão | crisis_domestic | 1989-01-01 | 1990-03-31 | BCB; Lei 7.730/1989 |
| br_collor | Plano Collor | crisis_domestic | 1990-03-01 | 1991-01-31 | BCB; Lei 8.024/1990 |
| br_real_plan | Plano Real | crisis_domestic | 1994-07-01 | 1995-06-30 | BCB; Lei 8.880/1994 |
| br_crawling_band | Câmbio administrado com bandas (pós-Real) | monetary | 1995-03-01 | 1999-01-31 | BCB; IMF AREAER |
| br_floating | Câmbio flutuante | monetary | 1999-01-01 | permanente | BCB; Comunicado 6.565/1999 |
| br_it | Regime de metas de inflação | monetary | 1999-06-01 | permanente | BCB; Decreto 3.088/1999 |
| br_primary_targets | Metas de superávit primário | fiscal | 1999-01-01 | 2016-12-31 | Tesouro Nacional; LDO 2000; IMF |
| br_lrf | Lei de Responsabilidade Fiscal | fiscal | 2000-05-01 | permanente | Lei Complementar 101/2000 |
| br_election_2002 | Crise de confiança eleitoral de 2002 | crisis_domestic | 2002-07-01 | 2002-12-31 | BCB; IMF |
| br_gfc | Crise financeira global no Brasil | crisis_global | 2008-09-01 | 2009-12-31 | BCB; GMD |
| br_recession_2014 | Recessão 2014–2016 e crise política | crisis_domestic | 2014-04-01 | 2016-12-31 | IBGE; BCB |
| br_ceiling | Teto de gastos (EC 95/2016) | fiscal | 2016-12-01 | permanente | Emenda Constitucional 95/2016 |
| br_pandemic | Emergência COVID-19 no Brasil | crisis_global | 2020-03-01 | 2021-12-31 | Ministério da Saúde; BCB; IBGE |
| br_tightening_2021 | Ciclo de aperto monetário 2021–2023 | monetary | 2021-03-01 | 2023-08-31 | BCB; Copom |
| br_new_framework | Novo arcabouço fiscal (LC 200/2023) | fiscal | 2023-08-01 | permanente | Lei Complementar 200/2023 |
| br_gdp_rebase_2010 | Mudança de base das Contas Nacionais (2010) | methodology | 2010-01-01 | 2010-12-31 | IBGE; nota metodológica das Contas Nacionais |

*(tabela completa no CSV; aqui as 30 primeiras)*