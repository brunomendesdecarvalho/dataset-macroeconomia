# Relatório de auditoria e validação — v2.0.0

**Dataset:** macroeconômico cross-country, âncora Brasil · **Extração:** 2026-11-23
**Escopo:** 22 países + `EU` (agregado) + `WLD` (PIB mundial) · anual 1960–2026 · trimestral 1995T1–2026T4

---

## 1. Sumário executivo

| Dimensão | Resultado | Leitura |
|---|---|---|
| Cobertura anual | **123.387** linhas, **114** variáveis, 24 entidades | 89 variáveis *macro_core* + 25 heterodoxas em 4 blocos |
| Cobertura trimestral | **19.357** linhas, **28** variáveis, 16 países + WLD | Núcleo original preservado |
| Blocos heterodoxos | 5.170 obs (distribuição), 5.212 (externa), 2.823 (financeiro), 8.364 (ecologia/estrutura) | Cobertura mediana de 37% a 82%; sem imputação |
| Cross-source | Crescimento: 0,23 p.p.; inflação: 3,42 p.p.; dívida: 5,84 p.p. | Divergências de dívida são de perímetro |
| Identidade nominal = real × deflator | resíduo máximo **6×10⁻⁶%** | Fecha por construção |
| Identidade Y = C + I + NX | mediana **0,0002% do PIB** | Confirma que `cons` do GMD é consumo total |
| Estacionariedade | 125 I(1), 49 I(0), 42 inconclusivas | Hiato I(0) em 22/22 |
| Quebras | 41/44 séries com ao menos 1 quebra | Datas globais 1967/1974/1982/1992/2008 |
| Dummies de regime | **101** dummies (30 Brasil) | Matriz 1.474 × 101 e 2.048 × 97 |
| SVAR Brasil | 108 obs, 2 lags (BIC), estável | FEVD monetária: 15% do hiato, 7,4% da inflação |
| SVAR nível (robustez HP) | 108 obs, 2 lags, estável | Pico acumulado da atividade −6,17% vs −2,68 p.p. no hiato |

**Mensagem central:** o dataset agora combina a espinha dorsal macroeconômica com quatro blocos heterodoxos e um baseline empírico transparente (Taylor, Phillips, SVAR recursivo e Projeções Locais). Não há modelo estrutural no pipeline ativo. A identificação do SVAR é recursiva e tem limites explícitos (price puzzle no Brasil; output puzzle nos EUA), documentados abaixo.

---

## 2. Cobertura e blocos

### 2.1 Visão por frequência

| Frequência | Linhas | Entidades | Variáveis | Início | Fim | Observações |
|---|---:|---:|---:|---|---|---|
| Anual | 123.387 | 24 | 114 | 1960-12-31 | 2026-12-31 | 635 linhas `is_forecast`/preliminares |
| Trimestral | 19.357 | 17 | 28 | 1995-03-31 | 2026-12-31 | 16 países + WLD |

### 2.2 Cobertura dos blocos heterodoxos

| Bloco | Variáveis | Obs. | Cobertura média | Cobertura mediana |
|---|---:|---:|---:|---:|
| Distribuição e classe | 6 | 5.170 | 59,8% | 52,2% |
| Restrição externa | 6 | 5.212 | 70,7% | 82,1% |
| Financiarização e crédito | 5 | 2.823 | 42,6% | 37,3% |
| Ecologia e estrutura produtiva | 8 | 8.364 | 70,9% | 82,1% |
| **Macro core** | 89 | 101.818 | 85,0% | 97,0% |

**Lacunas:** Gini/top10/bottom20 têm cobertura esparsa e começam nos anos 1990; termos de troca só a partir de ~2005; capital bancário/NPL ~2000+; CO2/energia ~1970+. Não houve imputação: ausência de linha = ausência de dado.

### 2.3 Cobertura Brasil (variáveis críticas)

| Variável | Início | Fim | n | Cobertura 1960–2026 |
|---|---|---|---:|---:|
| `gdp_real` | 1960 | 2026 | 67 | 100% |
| `gov_debt_gdp` | 1960 | 2026 | 67 | 100% |
| `policy_rate` | 1960 | 2025 | 66 | 99% |
| `credit_private_gdp` | 1960 | 2025 | 64 | 96% |
| `capital_stock` / `tfp` | 1960 | 2019 | 60 | 90% |
| `inflation` | 1981 | 2025 | 45 | 67% |
| `unemployment` | 1984 | 2026 | 43 | 64% |

---

## 3. Checagem cruzada entre fontes

| Conceito | Países | Erro médio absoluto | % dentro da tolerância | Tolerância | Fontes |
|---|---:|---:|---:|---:|---|
| Crescimento do PIB | 22 | 0,23 p.p. | 95% | 1 p.p. | GMD, WEO, WDI |
| Inflação | 22 | 3,42 p.p. | 96% | 2 p.p. | BCB/GMD, WEO, WDI |
| Desemprego | 22 | 0,48 p.p. | 86% | 1 p.p. | GMD, WEO, WDI |
| Dívida bruta | 22 | 5,84 p.p. | 74% | 5 p.p. | GMD, WEO, WDI (central) |
| PIB nominal USD | 22 | 2,0% | 89% | 5% | GMD, WEO, WDI |
| Resultado primário (BRA) | 1 | 5,41 p.p. | 35% | 2 p.p. | WEO (geral) vs BCB (central) |

**Divergências de perímetro, não de medida:** dívida JPN/CAN/AUS (WDI é governo central), primário BRA (WEO geral vs BCB central). Nenhuma série foi substituída sem regra; ver `source_decisions.csv` e `cross_source_divergences.csv`.

---

## 4. Identidades

| Identidade | n | Média | Mediana | p90 \|res.\| | Máx. \|res.\| | >1 p.p. |
|---|---:|---:|---:|---:|---:|---:|
| Y = C + I + NX (C total) | 1.397 | -0,11 | **0,0002** | 5,81 | 72,12 | 41,9% |
| Y = C + I + G + NX (C famílias) | 1.349 | -15,24 | -15,40 | 22,80 | 81,45 | 99,1% |
| Nominal = Real × Deflator | 1.474 | -1,2×10⁻⁸ | 2,6×10⁻⁸ | 4×10⁻⁶ | 6×10⁻⁶ | 0% |
| Fisher | 1.179 | 0,23 | -0,03 | 1,09 | 45,5 | 10,5% |
| Dinâmica da dívida (SFA) | 862 | 1,63 | 1,18 | 6,47 | 47,1 | 72,4% |

A segunda identidade fica em −15,4% do PIB (consumo do governo), confirmando que `cons` é consumo total. O SFA mediano de 1,18% do PIB inclui reconhecimento de dívidas, revisões e diferenças de perímetro; **não** é erro da identidade.

---

## 5. Estacionariedade e quebras

- **ADF/KPSS:** 125 séries I(1), 49 I(0), 42 inconclusivas. `output_gap` é I(0) em 22/22; PIB real, REER, desemprego e dívida são majoritariamente I(1). Modelos reduzidos usam diferenças/hiatos; o SVAR usa hiato e, como robustez, log-nível com tendência.
- **Bai-Perron:** 41 de 44 séries com quebra; 18 com 2 quebras; datas recorrentes 1967, 1974, 1982, 1992, 2008.
- **Chow:** 23,7% de rejeição; rejeições fazem sentido (BRA 1994, MEX 1994/2001, GBR 1992/2016, COL 1999, PER 1990/2002, USA 2008).
- **Mapa quebra ↔ dummy:** 103 pares em `breaks_regime_map.csv`; a maioria das quebras tem dummy próxima.

---

## 6. Outliers e missing

- **Sem NaN no dataset final:** lacunas são ausência de linha. Cobertura mediana de 97% no macro core; 37%–82% nos blocos heterodoxos.
- **Outliers:** 102 sinalizações (|z|>4 para crescimento/inflação; |z|>5 para demais). A maioria são dummies binárias de crise e hiperinflações; os casos não binários mais relevantes são inflação ARG/SAU, câmbio ARG e juro PER.
- **Zero imputação:** nenhuma série foi interpolada no dataset final. Interpolação linear só é usada internamente no filtro HP de lacunas internas.

---

## 7. Consistência anual ↔ trimestral

- Soma dos 4 trimestres do PIB nominal (IBGE) vs anual (GMD), Brasil: 0,0% em 2019–2022; +0,8% em 2023; +1,4% em 2024; +3,6% em 2025 (revisões IBGE vs GMD).
- Crescimento anual vs média dos SAAR trimestrais: mediana 0,004 p.p.; caudas em 2020–21 e 2026 incompleto.
- Níveis de PIB real têm bases distintas; comparamos crescimento, não nível. `complete_year` marca anos incompletos.

---

## 8. Baseline empírico (1999T1–2025T4)

### 8.1 Regra de Taylor e Curva de Phillips

| Modelo | Resultado principal |
|---|---|
| Taylor (inflação) | φπ de longo prazo **1,576** (s.e. 0,345; p unilateral 0,047); φx 0,183 (n.s.) |
| Taylor pós-metas (1999T3+) | φπ **2,588** (s.e. 1,152; p=0,084) — sensível à janela |
| Taylor (expectativas Focus) | φπ 6,60 (s.e. 8,03) — impreciso |
| Phillips (cheia) | expectativas 0,855***; hiato −0,017 (n.s.); petróleo 0,025** |
| Phillips (núcleo) | hiato +0,054* (p=0,060); expectativas 0,484*** |

### 8.2 SVAR recursivo — Brasil

Ordem: **hiato → inflação → Selic → 100·Δlog(câmbio)**. Controles: `foreign_policy_rate`, `100·Δlog(oil)`, `g_gfc_2008`, `g_pandemic_2020`.
Lags: AIC 4, **BIC 2 (usado)**; n=108; estável (módulo inverso 0,808); brancura rejeitada (p=0,002).

| Choque monetário (+100 pb) | Pico | Horizonte | Acumulado 12T |
|---|---:|---:|---:|
| Hiato | −0,321 p.p. | 5 | −2,680 p.p. |
| Inflação | +0,380 p.p. | 2 | +2,547 p.p. |
| Câmbio | −1,263 p.p. | 1 | −2,831 p.p. |

**FEVD (12T):** monetário explica **15,0% do hiato**, **7,4% da inflação**, 46,3% da Selic e 4,9% do câmbio.

**Robustez:** núcleo da inflação reduz o *price puzzle* (pico +0,24 p.p. em h=3), mas não o elimina. Nível `100·log(PIB)` com tendência linear mantém atividade negativa (pico acumulado −6,17%) e VAR estável (raiz inversa 0,985); ver `fig_svar_hp_vs_level.png`.

### 8.3 Projeções Locais e cross-country

As LP (HAC) mostram atividade negativa a partir de h=4, mas com bandas muito mais largas e magnitudes menores que o SVAR; para inflação, o *price puzzle* também aparece. No cross-country, o México reproduz o sinal teórico (atividade −0,31; inflação −0,03); os EUA exibem *output puzzle* (+0,08) e inflação −0,23; o Brasil exibe *price puzzle*.

---

## 9. Riscos, decisões e limitações

| Risco | Evidência | Mitigação / decisão |
|---|---|---|
| Dupla contagem UE + membros | `EU` é agregado | Excluída de somas; flag em `countries.yml` |
| Perímetro da dívida | divergência até 47 p.p. | GMD/WEO governo geral; WDI central só validação |
| Primário geral vs central | 5,4 p.p. no Brasil | Ambos reportados |
| Cobertura heterodoxa esparsa | Gini 37% mediano; ToT 2005+ | Sem imputação; cobertura explícita |
| 2026 preliminar | ano incompleto | `preliminary`/`is_forecast=True`; fora das estimações |
| Identificação SVAR | price/output puzzles | Cholesky documentado; robustez HP vs nível; LP como contraponto |
| Amostra trimestral | 16 países, não 22 | China/Índia/Chile/Colômbia/Peru/Rússia só anual |
| Vintages | SGS sem vintage; WDI/WEO revisam | `manifest.json` com data/hora e SHA-256 |
| Zero imputação | lacunas preservadas | Documentado no codebook |

**Não foi feito:** modelo estrutural (removido), imputação de lacunas, nowcasting, dados em tempo real, séries não documentadas.

---

## 10. Reprodutibilidade

1. `make fetch` — cacheia fontes existentes e baixa apenas os novos indicadores WDI (fast-fail, timeout 20 s, sem retry).
2. `make build` — harmoniza anual/trimestral, blocos heterodoxos e derivadas.
3. `make validate` — cross-source, identidades, ADF/KPSS, Bai-Perron, Chow.
4. `make empirical` — Taylor, Phillips, SVAR (gap/núcleo/nível), LP e cross-country.
5. `make export` — Excel + CSVs consolidados.
6. `make reports` — figuras, tabelas e docs.
7. `make test` — schema, exportação e estabilidade do SVAR.

`manifest.json` registra URL, timestamp e SHA-256 de cada download; o cache em `data/raw/` permite reprodução offline.
