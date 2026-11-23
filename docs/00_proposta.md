# Proposta e escopo — dataset macroeconômico cross-country v2.0.0

**Extração:** 2026-11-23 · **Âncora:** Brasil · **Anual:** 1960–2026 · **Trimestral:** 1995T1–2026T4

---

## 1. Lista fechada

22 países soberanos + `EU` (agregado, excluído de somas) + `WLD` (PIB mundial): ARG, AUS, BRA, CAN, CHL, CHN, COL, DEU, FRA, GBR, IDN, IND, ITA, JPN, KOR, MEX, PER, RUS, SAU, TUR, USA, ZAF.

Grupos: BRICS (5), G20 (19 + UE), G7 (7), TOP10_NOMINAL (PIB nominal USD, WEO 2025), LATAM6, EMERG_COMP, ADVANCED, QUARTERLY_CORE (16), COMMODITY_EXPORTERS, HIGH_INFLATION_HISTORY, IT_REGIME. A lista `QUARTERLY_CORE` reflete os 16 países efetivamente no trimestral: ARG e SAU dentro; CHN e IND fora.

## 2. Blocos de variáveis

| Bloco | Conteúdo |
|---|---|
| `macro_core` | PIB, consumo, investimento, governo, inflação, juros, câmbio, fiscal, crédito, capital/PTF, externo. |
| `distribuicao` | `profit_share`, `gini_index`, `income_share_top10`, `income_share_bottom20`, `vulnerable_employment_pct`, `wage_bill_gdp`. |
| `restricao_externa` | `terms_of_trade_index`, reservas (USD e meses), dívida externa/RNB, serviço da dívida/exportações, IDE/PIB. |
| `financeiro` | `lending_rate`, `interest_rate_spread`, capital bancário/ativos, NPL, capitalização de mercado/PIB. |
| `ecologia_estrutura` | CO2 per capita e por PIB, renováveis, intensidade energética, manufatura e agricultura (% PIB), manufaturados e combustíveis/minérios (% exportações). |

## 3. Modelos reduzidos

IS-LM, Mundell-Fleming, AD-AS, Curva de Phillips, Regra de Taylor e Solow, com endógenas/exógenas mapeadas no codebook (`model`, `role`).

## 4. Baseline empírico

Taylor e Phillips (OLS/HAC), SVAR recursivo com 4 variáveis no Brasil (1999T1–2025T4), robustez HP vs. log-nível, IRFs bootstrap e FEVD, Projeções Locais de Jordà e comparação EUA/México. Detalhes em `docs/07_empirical_svar.md`.

## 5. Exportação

`data/exports/macro_dataset_consolidado.xlsx` (Anual_Wide, Trimestral_Wide, Regimes_Anual, Codebook_Fontes) e CSVs `macro_anual_wide.csv`, `macro_trimestral_wide.csv`, `macro_todos_dados_long.csv`.

## 6. Cronograma executado

| Fase | Status |
|---|---|
| Coleta e harmonização inicial | concluído |
| Auditoria, identidades e quebras | concluído |
| Remoção do modelo estrutural e limpeza de schema | concluído |
| 4 blocos heterodoxos (WDI + derivadas) | concluído |
| SVAR/LP e robustez HP | concluído |
| Excel/CSV consolidado | concluído |
| Documentação acadêmica e testes | concluído |

## 7. Decisões

- **Sem modelo estrutural** no pipeline ativo; módulo, documentos e saídas correspondentes foram removidos.
- **Sem imputação**: lacunas permanecem como ausência de linha.
- **2026**: `preliminary`/`is_forecast=True`, fora das estimações.
- **WDI heterodoxo**: timeout 20 s, zero retries, fast-fail em 400/403/404.
- **UE**: agregado; nunca somado aos membros.
