# Metodologia, harmonização e tratamento — v2.0.0

**Extração:** 2026-11-23 · cache em `data/raw/` · manifesto com SHA-256 em `data/processed/manifest.json`.

---

## 1. Arquitetura

```
config/                 países, grupos, dicionário, fontes, regimes, metas
src/macrodata/
  settings.py           paths, países, grupos, metas
  http.py               cache HTTP, manifesto, fast-fail
  sources.py            GMD, WDI (core + heterodoxo), WEO, PWT, FRED, BCB, IBGE, Focus
  blocks.py             mapa variável -> bloco temático
  build.py              harmonização anual/trimestral e derivadas
  regimes.py            dummies país-tempo
  validation.py         cross-source, identidades, ADF/KPSS, Bai-Perron, Chow
  empirical.py          Taylor, Phillips, SVAR, Projeções Locais
  export.py             Excel único + CSVs consolidados
  report.py             figuras e tabelas
scripts/                orquestração e docs
data/raw/               cache bruto (não versionado)
data/processed/         dataset e diagnósticos
data/exports/           Excel e CSVs finais
docs/                   codebook, regimes, grupos, auditoria, metodologia, empírico
reports/                figuras e tabelas
```

Pipeline sem modelo estrutural ativo. O pipeline é idempotente e o cache permite modo offline.

---

## 2. Frequência

### 2.1 Anual, 1960–2026

- **Espinha dorsal:** GMD (`data_final.dta`, release 2026_09), que harmoniza IMF IFS/WEO/GFS, WDI, OECD MEI/EO/QNA, BIS, PWT, Maddison e Mitchell.
- **Complementos:** WEO pós-1980; WDI para participação, crédito, carga tributária e validação; PWT para capital, PTF, emprego, horas, capital humano e labor share.
- **Brasil:** IPCA anual (BCB 433) substitui a inflação do GMD.
- **2026:** ano em curso, `preliminary`/`is_forecast=True`; 2027+ é descartado.

### 2.2 Trimestral, 1995T1–2026T4

- **16 países:** BRA, USA, DEU, GBR, JPN, CAN, MEX, AUS, FRA, ITA, KOR, ZAF, TUR, IDN, ARG, SAU. China, Índia, Chile, Colômbia, Peru e Rússia ficam no anual.
- **PIB real:** FRED/OECD-MEI `NGDPRSAXDC{ISO2}Q` (SA).
- **Inflação:** FRED/OECD-MEI `CPALTT01{ISO2}Q659N`; Brasil do IPCA mensal (BCB 433).
- **Desemprego:** `LRHUTTTT{ISO2}Q156S`; Brasil PNAD Contínua (BCB 24369, 2012+).
- **Juros:** Selic meta (BCB 432); 3m interbancária e 10 anos para os demais.
- **Câmbio:** FRED `DEX*`; REER BIS. Componentes do PIB (Brasil): IBGE SIDRA 6612/1846.
- **Expectativas:** Focus (Brasil) e Michigan (EUA).

---

## 3. Blocos heterodoxos (novos)

Todos os indicadores novos vêm da **API WDI**, com timeout de 20 s, zero retries e fast-fail em 400/403/404. Se a série não existe para um país/ano, não há linha (sem imputação).

| Bloco | Variáveis | Códigos WDI |
|---|---|---|
| Distribuição e classe | `gini_index`, `income_share_top10`, `income_share_bottom20`, `vulnerable_employment_pct` | `SI.POV.GINI`, `SI.DST.10TH.10`, `SI.DST.FRST.20`, `SL.EMP.VULN.ZS` |
| Restrição externa | `terms_of_trade_index`, `intl_reserves_usd`, `intl_reserves_months_imports`, `external_debt_gni`, `debt_service_exports`, `fdi_net_inflows_gdp` | `TT.PRI.MRCH.XD.WD`, `FI.RES.TOTL.CD`, `FI.RES.TOTL.MO`, `DT.DOD.DECT.GN.ZS`, `DT.TDS.DECT.EX.ZS`, `BX.KLT.DINV.WD.GD.ZS` |
| Financeiro | `lending_rate`, `interest_rate_spread`, `bank_capital_to_assets`, `bank_npl_pct`, `market_cap_gdp` | `FR.INR.LEND`, `FR.INR.LNDP`, `FB.BNK.CAPA.ZS`, `FB.AST.NPER.ZS`, `CM.MKT.LCAP.GD.ZS` |
| Ecologia e estrutura | `co2_per_capita`, `renewable_electricity_pct`, `energy_intensity_gdp`, `manufacturing_gdp`, `agriculture_gdp`, `manufactures_exports_pct` | `EN.GHG.CO2.PC.CE.AR5`, `EG.ELC.RNEW.ZS`, `EG.EGY.PRIM.PP.KD`, `NV.IND.MANF.ZS`, `NV.AGR.TOTL.ZS`, `TX.VAL.MANF.ZS.UN` |

**Derivadas:**
- `profit_share = 1 − labor_share` (PWT, fração 0–1).
- `wage_bill_gdp = 100 × labor_share` (% do PIB).
- `co2_per_gdp = co2_total_mt × 1000 / gdp_nominal_usd` (kg CO2e por USD corrente; total CO2 = `EN.GHG.CO2.MT.CE.AR5`).
- `fuel_ores_exports_pct = TX.VAL.FUEL.ZS.UN + TX.VAL.MMTL.ZS.UN` (soma estrita; NaN se um componente faltar).

Cada variável recebe um `block`: `macro_core`, `distribuicao`, `restricao_externa`, `financeiro`, `ecologia_estrutura`.

---

## 4. Harmonização

| Dimensão | Regra |
|---|---|
| Níveis | Moeda local, milhões; PIB real a preços constantes (base nacional). |
| Razões | % do PIB, nominal. |
| Taxas | % a.a.; inflação 12m; juros médios do período. |
| Índices | CPI/REER 2010=100; deflator na base do PIB real; `gdp_deflator_2010` 2010=100. |
| Câmbio | LC por USD; aumento = depreciação. |
| Sinal fiscal | Superávit positivo; déficit negativo. |
| PPPs | milhões de int$ (WEO × 1000). |

**Componentes reais:** consumo, investimento e gasto do governo do GMD são correntes; foram deflacionados pelo deflator implícito do PIB (`nGDP/rGDP`). `cons` é consumo total (famílias + governo), o que faz Y = C + I + NX fechar na mediana.

**Deflator:** mantido na base do PIB real para preservar `nGDP = rGDP × deflator/100`; a versão 2010=100 é separada.

---

## 5. Tratamento e flags

- **Sazonalidade:** séries FRED/OECD-MEI já vêm SA quando indicado; IPCA trimestral é ajustado por X-13ARIMA-SEATS no cálculo qoq do SVAR.
- **Sem imputação:** lacunas são ausência de linha. Interpolação linear só no filtro HP interno.
- **Logs/diferenças:** o dataset guarda o valor bruto e a transformação recomendada; as derivadas já calculadas são `gdp_growth`, `output_gap`, `potential_gdp`, juros reais, `neutral_rate`, `debt_dynamics_residual`, `capital_output_ratio`, `output_per_worker`, `profit_share`, `wage_bill_gdp`, `co2_per_gdp`, `fuel_ores_exports_pct`.
- **Flags:** `ok`, `preliminary`, `forecast`, `derived`, `proxy`, `hp_filter`, `survey`, `policy`, `validation`.
- **`is_forecast`:** 2026 ou projeções; não entra nas estimações.

---

## 6. Regimes

- 101 eventos em `config/regimes.yml`, com início/fim mensal, `permanent` para step, frequência A/Q, fonte, URL, variáveis afetadas e modelos.
- Resolução anual: ano = 1 se qualquer trimestre do evento o intersecta. Trimestral: trimestre = 1 se o evento o intersecta em ≥ 1 dia.
- `ALL` expande para os 22 países; `EU`/`WLD` não entram.
- Dummies GMD (crise bancária/cambial/soberana) têm prefixo `gmd_`.
- `regime_dummy` no long lista as dummies ativas.

---

## 7. Baseline empírico

- **Taylor:** OLS/HAC, Brasil 1999T1–2025T4, com dummies `br_recession_2014` e `br_pandemic`; coeficientes de curto e longo prazo.
- **Phillips:** OLS/HAC, inflação cheia e núcleo, expectativas Focus, hiato, petróleo e câmbio em log-diff.
- **SVAR recursivo:** ordem `[atividade, inflação, Selic, 100·Δlog(câmbio)]`, controles `foreign_policy_rate`, `100·Δlog(oil)`, `g_gfc_2008`, `g_pandemic_2020`; lags por AIC/BIC (máx. 4), estabilidade, brancura, IRFs bootstrap 68%/90% e FEVD.
- **Robustez HP:** SVAR com `output_gap` e com `100·log(gdp_real)` em nível com tendência linear.
- **Projeções Locais:** h=0..12, HAC, mesmas defasagens/controles; SVAR vs. LP.
- **Cross-country:** USA e MEX com `short_rate`; Brasil com `policy_rate`.

---

## 8. Exportação

`data/exports/macro_dataset_consolidado.xlsx` com abas `Anual_Wide`, `Trimestral_Wide`, `Regimes_Anual`, `Codebook_Fontes` (cabeçalho congelado). CSVs: `macro_anual_wide.csv`, `macro_trimestral_wide.csv`, `macro_todos_dados_long.csv` (UTF-8, vírgula). Colunas do long: `freq, iso3, country, date, period, variable, block, value, unit, source, source_code, quality_flag, is_forecast, regime_dummy`.

---

## 9. Limitações

- **Vintage:** SGS não guarda versões; WDI/WEO revisam. O `manifest.json` registra a extração.
- **UE:** agregado com cobertura anual parcial; não entra em somas.
- **Perímetros fiscais:** dívida bruta vs. líquida; primário geral vs. central.
- **Heterodoxos:** cobertura esparsa (Gini ~37% mediano; termos de troca 2005+); sem imputação.
- **SVAR:** identificação recursiva; price puzzle no Brasil e output puzzle nos EUA.
- **2026:** preliminar, fora das estimações.
