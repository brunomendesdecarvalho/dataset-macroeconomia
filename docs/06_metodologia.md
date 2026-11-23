# Metodologia, harmonização e tratamento

**Versão 1.0.0** · extração 2026-11-23 · ver `manifest.json` para URLs, timestamps e SHA-256.

---

## 1. Arquitetura do pipeline

```
config/                 listas fechadas, dicionário, fontes, regimes
src/macrodata/
  settings.py           paths, países, grupos, metas, variáveis
  http.py               cache HTTP, retries, manifesto
  sources.py            GMD, WDI, WEO, PWT, FRED, BCB, IBGE, Focus
  build.py              harmonização anual/trimestral, derivadas, wide
  regimes.py            dummies país-tempo (anual/trimestral)
  validation.py         cross-source, identidades, ADF/KPSS, Bai-Perron, Chow
  report.py             figuras e tabelas
  dsge/                 solver QZ, NK pequeno, estimação, SW-lite médio
scripts/                orquestração e geração de docs
data/raw/               cache bruto (não versionado)
data/processed/         dataset final e diagnósticos
docs/                   codebook, DSGE, regimes, auditoria, metodologia
reports/                figuras e tabelas
```

O pipeline é **idempotente**: cada etapa lê o cache/parquet e regrava os produtos. `MACRO_EXTRACTION_TS` permite congelar o timestamp.

---

## 2. Frequência em duas camadas

### 2.1 Anual, 1960–2026

- **Espinha dorsal:** GMD (`data_final.dta`, release 2026_09). O GMD já harmoniza IMF IFS/WEO/GFS, WDI, OECD MEI/EO/QNA, BIS, PWT, Maddison, Mitchell e fontes históricas; por isso é a base pré-1980.
- **Complementos:** WEO pós-1980 (resultado primário, dívida líquida, PPP), WDI (participação, crédito, carga tributária, PIB mundial), PWT (capital, PTF, emprego, horas, capital humano).
- **Brasil:** IPCA anual (BCB 433) substitui a inflação do GMD; o restante vem do GMD/WEO, com validação contra BCB/IBGE.
- **Corte:** 2026 é ano em curso; 2027+ é descartado. Projeções GMD/WEO para 2026 são marcadas `is_forecast=1` e `quality_flag=preliminary`/`forecast`.

### 2.2 Trimestral, 1995T1–2026T4

- **Países:** 16 com PIB trimestral estável (BRA, USA, DEU, GBR, JPN, CAN, MEX, AUS, FRA, ITA, KOR, ZAF, TUR, IDN, ARG, SAU). CHN, IND, CHL, COL, PER e RUS ficam no anual.
- **PIB real:** FRED/OECD-MEI `NGDPRSAXDC{ISO2}Q`, dessazonalizado.
- **Inflação:** FRED/OECD-MEI `CPALTT01{ISO2}Q659N` (variação 12m); Brasil calculado do IPCA mensal (BCB 433).
- **Desemprego:** `LRHUTTTT{ISO2}Q156S`; Brasil PNAD Contínua (BCB 24369, 2012+).
- **Juros:** Selic meta (BCB 432) para o Brasil; 3m interbancária (`IR3TIB01...`) para os demais; 10 anos (`IRLTLT01...`) para o longo prazo.
- **Câmbio:** FRED `DEX*` (diário → média trimestral); orientação LC por USD, com inversão para EUR/GBP/AUD.
- **REER:** BIS broad via FRED (`RB{ISO2}BIS`), média trimestral.
- **Componentes do PIB (Brasil):** IBGE SIDRA 6612 (consumo, governo, FBCF, exportações, importações) e 1846 (nominal).
- **Expectativas:** Focus/BCB para o Brasil; Michigan (MICH) para os EUA.

---

## 3. Harmonização de unidades e definições

| Dimensão | Regra |
|---|---|
| **Níveis** | Moeda local, milhões; PIB real a preços constantes (base nacional). Não comparar níveis entre países sem `gdp_real_usd`. |
| **Razões** | % do PIB, nominal. |
| **Taxas** | % a.a.; inflação = variação 12m; juros = média do período. |
| **Índices** | `cpi_index` e `reer` 2010=100; `gdp_deflator` na base do PIB real; `gdp_deflator_2010` 2010=100. |
| **Câmbio** | LC por USD; aumento = depreciação. |
| **Sinal fiscal** | Superávit positivo; déficit negativo. |
| **PPPs** | `gdp_ppp_usd` em milhões de int$ (WEO × 1000). |
| **Ouro/commodities** | USD/barril; índice de commodities (2016=100). |

### 3.1 Componentes reais

O GMD fornece consumo, investimento e gasto do governo a preços correntes (exceto `rcons`, que termina em 2023). Para garantir consistência com o PIB real, os componentes foram **deflacionados pelo deflator implícito do PIB** (`nGDP/rGDP`), não pelo deflator 2010=100. Isso preserva a aditividade aproximada e evita misturar bases.

- `consumption_real` = `cons` / (nGDP/rGDP). O GMD `cons` é consumo **total** (famílias + governo); a identidade Y = C + I + NX fecha na mediana.
- `investment_real` = `inv` / (nGDP/rGDP); `fixed_investment_real` = `finv` / fator.
- `gov_exp_real` = `govexp` / fator; **atenção:** `govexp` é despesa total do governo (inclui transferências), não consumo do governo. Para o consumo do governo usar `gov_consumption_gdp` (WDI) × PIB real.

### 3.2 Deflator

O deflator do GMD é um índice cuja base coincide com a base do PIB real do país (ex.: Brasil 1995=100). Mantê-lo é essencial para a identidade:

```
nGDP = rGDP × gdp_deflator / 100
```

O resíduo máximo observado é 6×10⁻⁶%, confirmando a consistência. `gdp_deflator_2010` é uma transformação separada, apenas para comparação internacional; **não** usar com níveis de PIB real.

---

## 4. Tratamento

### 4.1 Sazonalidade

- Séries trimestrais do FRED/OECD-MEI já vêm dessazonalizadas quando indicado (`SA`); o dataset preserva a flag.
- IPCA trimestral (Brasil) é ajustado por **X-13ARIMA-SEATS** (`x13as`, binário ASCII) antes de calcular a variação qoq SAAR usada no DSGE. O dataset público reporta a inflação 12m (NSA) e o DSGE aplica X-13 internamente.
- Fallback documentado: STL robusto se o binário X-13 não estiver disponível.

### 4.2 Deflacionamento

- PIB nominal/real do GMD; componentes deflacionados pelo deflator implícito.
- Para o Brasil trimestral, o deflator é 100 × PIB nominal / PIB real encadeado (IBGE 1846/6612).

### 4.3 Logs, diferenças e hiatos

O dataset **não** aplica log/diferença; ele registra a transformação recomendada em `transformation` e o valor bruto. As derivadas já calculadas são:

- `gdp_growth` = 100·Δlog(PIB real), anual; `gdp_real_growth` = 400·Δlog(PIB real), trimestral (SAAR).
- `output_gap` = 100·(log y − log y*), HP λ=100 (anual) / 1600 (trimestral), bicaudal.
- `potential_gdp` = exp(tendência HP).
- `real_rate_ex_post` = `policy_rate` − `inflation`; `real_rate_ex_ante` = `policy_rate` − `inflation_expectations`.
- `neutral_rate` = HP do juro real ex ante (proxy, **não** estimativa estrutural de r*).
- `debt_dynamics_residual` = Δd − [(r−g)/(1+g)]·d₋₁ + pb (SFA).
- `capital_output_ratio`, `output_per_worker`, `tfp_growth`, `world_gdp_growth`.

### 4.4 Missing e imputação

- **Não há imputação** no dataset final. Lacunas são ausência de linha; a matriz de cobertura mostra onde.
- Interpolação linear é usada **apenas dentro do filtro HP** para lacunas internas; nunca para preencher o dataset.
- Série sem proxy defensável não é criada (ex.: inflação brasileira pré-1980, capital pós-2019, spread trimestral).

### 4.5 Flags de qualidade

| Flag | Significado |
|---|---|
| `ok` | Observação de fonte primária. |
| `preliminary` | 2026 (ano em curso) ou último trimestre. |
| `forecast` | Projeção WEO/GMD para 2026 (marcada). |
| `derived` | Construída por identidade/transformação. |
| `proxy` | Proxy documentada (ex.: r*, produto por trabalhador, PIB mundial). |
| `hp_filter` | Resultado de filtro HP (PIB potencial/hiato). |
| `survey` | Expectativa de survey (Focus/Michigan). |
| `policy` | Meta/regra oficial (inflation_target). |
| `validation` | Série usada apenas em checagem cruzada. |

---

## 5. Regimes e dummies

- 101 eventos em `config/regimes.yml`, com `start`/`end` mensais, `permanent` para step, `freq` A/Q, fonte, URL, variáveis afetadas, modelos e papel no DSGE.
- Resolução anual: ano = 1 se qualquer trimestre do evento o intersecta. Trimestral: trimestre = 1 se o evento o intersecta em ≥ 1 dia; eventos pontuais usam o trimestre do mês.
- `ALL` expande para os 22 países (não para EU/WLD).
- Dummies do GMD (crises bancária/cambial/soberana) entram como colunas adicionais com prefixo `gmd_`.
- O campo `regime_dummy` do dataset longo lista as dummies ativas (separadas por `|`).

---

## 6. Validação

1. **Cross-source:** GMD vs WEO vs WDI para crescimento, inflação, desemprego, dívida, PIB USD; WEO vs BCB para primário. Tolerâncias e decisões em `source_decisions.csv`.
2. **Identidades:** Y = C + I + NX; nominal = real × deflator; Fisher; dinâmica da dívida.
3. **Estacionariedade:** ADF (constante, AIC) e KPSS (constante), nível e primeira diferença; conclusão I(0)/I(1)/inconclusivo.
4. **Quebras:** Bai-Perron (mudança de média, até 5 quebras, mínimo 7 obs) e Chow em datas de regime conhecidas.
5. **Consistência A-Q:** soma dos trimestres vs anual; crescimento anual vs média dos SAAR; flag de ano completo.
6. **Outliers/missing:** z-scores por país-variável; cobertura por país-variável-ano.
7. **DSGE:** prior vs posterior, ESS, SVD do jacobiano de momentos, FEVD, IRFs, momentos dados vs modelo, sensibilidade ±20%.

---

## 7. DSGE

### 7.1 Pequeno (estimado)

- 3 equações (IS com hábitos, NKPC híbrida, Taylor com suavização), 6 estados (3 variáveis + 3 choques AR(1)).
- Solução por QZ (companion quadrático), checagem de Blanchard-Kahn e resíduo da equação matricial.
- Kalman filter, verossimilhança exata, MCMC RW Metropolis em espaço transformado (log/logit) com jacobiano.
- Brasil 1999T3–2025T4; EUA 1995T1–2025T4.
- Núcleo calibrado; hábitos, indexação, ARs e choques estimados. A estimação livre do núcleo foi tentada e convergiu para a fronteira — registrada como risco.

### 7.2 Médio (calibrado)

- 12 variáveis: hiato, inflação, salário real, horas, capital, investimento, consumo, juros, gasto, PIB externo, prêmio de risco, tecnologia.
- 9 choques: demanda, markup, salário, monetário, fiscal, externo, risco, tecnologia, investimento.
- Investimento em forma reduzida (sem Tobin's Q) para garantir determinância.
- Calibração padrão + choques de demanda/markup/monetário calibrados para casar volatilidades.
- Simulação de 40.000 trimestres; momentos, IRFs, FEVD, sensibilidade ±20%.

---

## 8. Reprocessamento

```bash
make fetch       # rede; grava cache + manifesto
make build       # dataset long/wide/coverage/regimes
make validate    # tabelas de validação
make dsge        # estimação + simulação
make reports     # figuras/tabelas
make test        # testes
make all         # tudo
```

Para reproduzir do zero: apagar `data/raw/parsed_*.parquet` e `data/processed/*`; manter `data/raw/` se quiser offline. As fontes SGS/WDI/WEO não têm vintage, então revisões podem alterar o passado — o `manifest.json` registra a data de extração.

---

## 9. Limitações conhecidas

- **Vintage:** SGS não guarda versões; WDI/WEO revisam. Não é possível comparar real-time vs final para toda a amostra.
- **UE:** agregado com cobertura anual parcial; não entra em somas.
- **Perímetros fiscais:** dívida bruta/líquida e primário governo geral/central não são a mesma coisa.
- **Brasil:** inflação pré-1980, desemprego pré-1984, capital pós-2019 e spread trimestral são lacunas.
- **DSGE:** identificação fraca; resultados não estruturais. O médio é calibrado.
- **HP:** bicaudal, com viés de fim de amostra; o hiato é observável construído, não medido.
