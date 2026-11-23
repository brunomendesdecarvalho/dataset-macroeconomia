# Dataset macroeconômico cross-country — âncora Brasil

Dataset anual (1960–2026) e trimestral (1995T1–2026T4) para **22 países + agregado UE**, com o Brasil como âncora, desenhado para modelos reduzidos (IS-LM, Mundell-Fleming, AD-AS, Curva de Phillips, Regra de Taylor, Solow) e para um DSGE pequeno (estimado) e médio (calibrado).

**Versão:** 1.0.0 · **Extração:** 2026-11-23 · **Licença dos dados:** depende da fonte (GMD/WDI/PWT CC BY 4.0; FRED/BCB/IBGE/OCDE/FMI conforme termos originais). O código é MIT.

---

## O que está pronto

| Produto | Onde |
|---|---|
| Dataset longo (121.175 linhas) | `data/processed/macro_long.parquet` / `.csv` |
| Painel anual (101.818 linhas, 89 variáveis) | `data/processed/macro_annual_long.parquet` |
| Painel trimestral (19.357 linhas, 28 variáveis) | `data/processed/macro_quarterly_long.parquet` |
| Wide por país | `data/processed/wide/annual/`, `wide/quarterly/` |
| Codebook | `docs/01_codebook.md` |
| DSGE observável → modelo, latentes e choques | `docs/02_dsge_observables.md` |
| 101 dummies de regime + matriz 0/1 | `docs/03_regime_dummies.md`, `data/processed/regime_matrix_*.csv` |
| Auditoria e validação | `docs/04_audit_report.md` |
| Grupos de países | `docs/05_country_groups.md` |
| Metodologia | `docs/06_metodologia.md` |
| Proposta inicial (i–v) | `docs/00_proposta.md` |
| Cobertura país × variável | `data/processed/coverage_matrix_annual.csv`, `coverage.csv` |
| DSGE pequeno (posterior, IRF, FEVD, identificação) | `data/processed/dsge_small_*` |
| DSGE médio (calibração, momentos, sensibilidade) | `data/processed/dsge_medium_*` |

### Números-chave

- **22 países** + **EU** (agregado, excluído de somas) + **WLD** (PIB mundial).
- **89 variáveis anuais**, **28 trimestrais**, **101 dummies** de regime (30 para o Brasil).
- Cobertura anual mediana **97%**; erro médio cross-source de **0,23 p.p.** no crescimento e **3,42 p.p.** na inflação.
- Identidade nominal = real × deflator com resíduo máximo **6×10⁻⁶%**.
- DSGE pequeno: 106 obs (Brasil, 1999T3–2025T4) e 124 (EUA); **identificação fraca** — ver auditoria.

---

## Quickstart

Requisitos: Python 3.11+ (testado em 3.14), ~1 GB de disco, rede para a primeira extração.

```bash
python3 -m venv --system-site-packages .venv
.venv/bin/pip install -r requirements.txt

# pipeline completo
make all

# ou etapas
make fetch      # baixa/cacheia GMD, WDI, WEO, PWT, FRED, BCB, IBGE, Focus
make build      # harmoniza e grava o dataset
make validate   # cross-source, identidades, ADF/KPSS, Bai-Perron, Chow
make dsge       # estima NK pequeno (BRA/EUA) + simula SW-lite
make reports    # figuras, tabelas e docs
make test       # pytest
```

Tempo aproximado: fetch 3–8 min (rede), build 1–2 min, validação 2–3 min, DSGE 4–6 min, relatórios <1 min.

### Uso mínimo

```python
import pandas as pd
df = pd.read_parquet("data/processed/macro_long.parquet")
bra = df[(df.iso3 == "BRA") & (df.variable == "inflation") & (df.freq == "A")]
print(bra[["date", "value", "unit", "source"]].tail())

wide = pd.read_csv("data/processed/wide/annual/BRA.csv", index_col=0, parse_dates=True)
print(wide[["gdp_real", "inflation", "policy_rate", "gov_debt_gdp"]].tail())
```

---

## Estrutura

```
config/                 países, grupos, dicionário, fontes, regimes, metas
src/macrodata/          pipeline (fetch → build → validate → dsge → report)
scripts/                orquestração e geração de docs
data/raw/               cache bruto + manifesto (não versionado)
data/processed/         dataset final, matrizes, diagnósticos, wide
docs/                   proposta, codebook, DSGE, regimes, auditoria, metodologia
reports/                figuras e tabelas
tests/                  solver, schema, identidades, tabela DSGE
```

---

## Fontes

- **GMD** (Global Macro Database 2026_09) — espinha dorsal anual.
- **WDI** (Banco Mundial) — complemento/validação.
- **WEO** (FMI, out/2025) — fiscal pós-1980, PPP, validação.
- **PWT 10.01** — capital, PTF, emprego, horas (até 2019).
- **FRED / OECD-MEI / BIS** — subamostra trimestral, commodities, VIX.
- **BCB SGS / IBGE SIDRA / Focus** — Brasil: IPCA, Selic, PIB trimestral, componentes, expectativas.
- **Michigan (MICH)** — expectativas dos EUA.

Cada linha do dataset tem `source`, `source_code`, `source_url`, `vintage` e `extraction_date`. O manifesto `data/processed/manifest.json` registra URL, timestamp, tamanho e SHA-256 de cada download.

---

## Decisões e ressalvas importantes

1. **10 maiores economias:** PIB nominal USD (WEO 2025), não PPP.
2. **UE é agregado:** nunca entra em somas/médias de países.
3. **Dívida:** GMD/WEO governo geral; WDI governo central é apenas validação — divergências de até 47 p.p. são de perímetro.
4. **Primário:** WEO governo geral vs BCB governo central; ambos reportados.
5. **Trimestral:** 16 países com PIB estável; China, Índia, Chile, Colômbia, Peru e Rússia ficam no anual.
6. **DSGE pequeno:** núcleo calibrado (σ=1; κ=0,08; φπ=1,5; ρ=0,8); hábitos/indexação/choques estimados. A estimação livre do núcleo converge para a fronteira — **não usar para inferência estrutural**.
7. **DSGE médio:** calibrado, não estimado; serve para cenários/IRFs qualitativos.
8. **Sem imputação:** lacunas são preservadas e sinalizadas.

Leia `docs/04_audit_report.md` antes de usar o DSGE para política ou publicação.

---

## Reprodutibilidade

- `requirements.txt` com versões fixas; `pyproject.toml` para instalação.
- `manifest.json` com data/hora e hash de cada download.
- `MACRO_EXTRACTION_TS` permite congelar o timestamp.
- `make all` refaz do zero; cache em `data/raw/` permite modo offline.
- Testes: `make test` (solver QZ, schema, datas, identidades, tabela DSGE).

---

## Citação

Se usar o dataset, cite as fontes originais (GMD, WDI, WEO, PWT, FRED, BCB, IBGE) e este repositório:

```
Dataset macroeconômico cross-country (v1.0.0), âncora Brasil, 2026.
```
