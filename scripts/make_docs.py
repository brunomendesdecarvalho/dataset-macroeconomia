"""Gera codebook, documento de regimes e grupos a partir dos dados processados."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from macrodata import settings  # noqa: E402
from macrodata.blocks import BLOCK_LABELS, block_of  # noqa: E402


def md(df: pd.DataFrame, cols: list[str] | None = None, max_rows: int | None = None) -> str:
    if cols:
        df = df[cols]
    if max_rows:
        df = df.head(max_rows)
    df = df.fillna("")
    out = ["| " + " | ".join(map(str, df.columns)) + " |",
           "|" + "|".join(["---"] * len(df.columns)) + "|"]
    for _, row in df.iterrows():
        vals = [str(v).replace("|", "\\|").replace("\n", " ") for v in row.tolist()]
        out.append("| " + " | ".join(vals) + " |")
    return "\n".join(out)


def _load():
    ann = pd.read_parquet(settings.PROCESSED / "macro_annual_long.parquet")
    qtr = pd.read_parquet(settings.PROCESSED / "macro_quarterly_long.parquet")
    long = pd.read_parquet(settings.PROCESSED / "macro_long.parquet")
    reg_a = pd.read_csv(settings.PROCESSED / "regime_matrix_annual.csv")
    reg_q = pd.read_csv(settings.PROCESSED / "regime_matrix_quarterly.csv")
    cov = pd.read_csv(settings.PROCESSED / "coverage.csv")
    return ann, qtr, long, reg_a, reg_q, cov


def codebook() -> None:
    ann, qtr, long, reg_a, reg_q, cov = _load()
    valid = set(ann["variable"]) | set(qtr["variable"])
    v = settings.VARIABLES.copy()
    v = v[v["id"].isin(valid)].copy()
    v["block"] = v["id"].map(block_of)
    ext = ann.extraction_date.iloc[0]
    agg = cov.groupby(["freq", "variable"]).agg(
        n_paises=("iso3", "nunique"), cobertura_min=("coverage_pct", "min"),
        cobertura_mediana=("coverage_pct", "median")).reset_index()
    v = v.merge(agg, left_on=["id", "freq"], right_on=["variable", "freq"], how="left")
    v["block_label"] = v["block"].map(BLOCK_LABELS).fillna(v["block"])
    n_a, n_q, n_long = len(ann), len(qtr), len(long)
    n_ra, n_ca = reg_a.shape[0], reg_a.shape[1] - 2
    n_rq, n_cq = reg_q.shape[0], reg_q.shape[1] - 2

    blocks = (v.groupby(["block", "freq"]).agg(variaveis=("id", "nunique")).reset_index())
    blocks["bloco"] = blocks["block"].map(BLOCK_LABELS).fillna(blocks["block"])
    obs = long.groupby(["block", "freq"]).size().rename("observacoes").reset_index()
    blocks = blocks.merge(obs, on=["block", "freq"], how="left")

    lines = [
        "# Codebook — dataset macroeconômico cross-country (v1.0.0)",
        "",
        f"Extração: **{ext}**. Âncora: **Brasil**. "
        f"Anual {settings.ANNUAL_START}–{settings.ANNUAL_END}; trimestral 1995T1–2026T4.",
        "",
        "## 1. Arquivos e grão",
        "",
        "| Arquivo | Grão | Linhas | Uso |",
        "|---|---|---|---|",
        f"| `data/processed/macro_long.parquet` | país × data × variável | {n_long:,} | dataset longo completo (anual + trimestral) |",
        f"| `data/processed/macro_annual_long.parquet` | país × ano × variável | {n_a:,} | painel anual |",
        f"| `data/processed/macro_quarterly_long.parquet` | país × trimestre × variável | {n_q:,} | subamostra trimestral |",
        "| `data/exports/macro_dataset_consolidado.xlsx` | 4 abas | — | Excel consolidado |",
        "| `data/exports/macro_anual_wide.csv` | país × ano | — | wide anual |",
        "| `data/exports/macro_trimestral_wide.csv` | país × trimestre | — | wide trimestral |",
        "| `data/exports/macro_todos_dados_long.csv` | país × período × variável | — | long consolidado |",
        f"| `data/processed/regime_matrix_annual.csv` | país × ano × dummy | {n_ra:,} × {n_ca} | matriz 0/1 |",
        f"| `data/processed/regime_matrix_quarterly.csv` | país × trimestre × dummy | {n_rq:,} × {n_cq} | matriz 0/1 |",
        "",
        "## 2. Dicionário de campos",
        "",
        md(pd.DataFrame([
            ["iso3", "string", "Código ISO3; `WLD` = mundo (agregado); `EU` = União Europeia (agregado, excluído de somas)."],
            ["country", "string", "Nome em português."],
            ["date", "date", "Fim do período: 31/12 do ano ou último dia do trimestre."],
            ["year", "int", "Ano do período."],
            ["period", "string", "`YYYY` (anual) ou `YYYYQn` (trimestral)."],
            ["variable", "string", "Identificador canônico."],
            ["block", "string", "macro_core, distribuicao, restricao_externa, financeiro, ecologia_estrutura."],
            ["value", "float", "Valor na unidade declarada; nunca em log."],
            ["unit", "string", "Unidade nativa."],
            ["freq", "string", "`A` ou `Q`."],
            ["source", "string", "Fonte efetiva (GMD, WDI, WEO, PWT, FRED, BCB, IBGE, derived, hardcoded)."],
            ["source_code", "string", "Código original (coluna, indicador, ID FRED, SGS/SIDRA)."],
            ["source_detail", "string", "Descrição legível da série."],
            ["source_url", "string", "URL da fonte."],
            ["vintage", "string", "Versão/vintage da fonte."],
            ["transformation", "string", "Transformação recomendada: level, log, yoy, diff, hp_gap, hp_trend, fisher, pct_gdp, index, dummy, derived."],
            ["transform_applied", "string", "Sempre `none`: o valor é bruto/construído."],
            ["role", "string", "endogenous, exogenous, latent, shock, regime, validation."],
            ["model", "string", "Modelos reduzidos: ISLM, MF, ADAS, PC, TR, SOLOW."],
            ["coverage_note", "string", "Nota de cobertura temporal."],
            ["notes", "string", "Definição e ressalvas."],
            ["is_forecast", "bool", "Projeção ou ano preliminar."],
            ["quality_flag", "string", "ok, preliminary, forecast, derived, proxy, hp_filter, survey, policy, validation."],
            ["seasonal_adjustment", "string", "SA, NSA ou n/a."],
            ["imputation", "string", "none (sem imputação)."],
            ["extraction_date", "string", "Timestamp UTC da extração."],
            ["regime_dummy", "string", "Dummies ativas, separadas por `|`."],
        ], columns=["campo", "tipo", "descrição"])),
        "",
        "## 3. Convenções",
        "",
        "- **Sinal fiscal**: resultado primário/balanço positivos = superávit.",
        "- **Câmbio**: moeda local por USD (aumento = depreciação); EUR/GBP/AUD invertidos.",
        "- **Deflator**: `gdp_deflator` na base do PIB real; `gdp_deflator_2010` 2010=100.",
        "- **Juros**: % a.a.; inflação % a.a. (12 meses); no Brasil, IPCA (BCB/IBGE).",
        "- **PIB real**: milhões de LC a preços constantes; base nacional; não comparar níveis sem `gdp_real_usd`.",
        "- **PPPs**: `gdp_ppp_usd` em milhões de int$ (WEO × 1000).",
        "- **FRED**: templates `{ISO2}`; o ID exato está em `source_code`.",
        "- **Capital**: `capital_stock` usa `rnna` (PWT, milhões USD 2017), não `rkna` (índice 2017=1).",
        "- **2026**: ano em curso, `preliminary`/`is_forecast=True`; não entra nas estimações.",
        "",
        "## 4. Blocos e cobertura",
        "",
        md(blocks[["bloco", "freq", "variaveis", "observacoes"]]),
        "",
        "## 5. Registro de fontes",
        "",
        md(pd.DataFrame([
            [k, v.get("name", ""), v.get("version", ""), v.get("coverage", ""), v.get("role", "")]
            for k, v in settings.SOURCES_YML["sources"].items()
        ], columns=["id", "fonte", "versão", "cobertura", "papel"])),
        "",
        "## 6. Dicionário de variáveis",
        "",
        md(v[["id", "freq", "label", "unit", "source", "code", "transform", "role",
              "models", "block_label", "n_paises", "cobertura_mediana", "notes"]]
           .rename(columns={"id": "variável", "freq": "freq", "label": "rótulo",
                            "unit": "unidade", "source": "fonte", "code": "código",
                            "transform": "transformação", "role": "papel",
                            "models": "modelos", "block_label": "bloco",
                            "n_paises": "n_países", "cobertura_mediana": "cobertura_%",
                            "notes": "notas"})),
        "",
        "## 7. Lacunas explícitas",
        "",
        "- **Brasil**: IPCA começa em 1980 (série anual de 12m em 1981); PNAD Contínua trimestral em 2012; spread trimestral não harmonizado; salário real trimestral não usado.",
        "- **Argentina**: PIB trimestral em 2004; inflação com quebras INDEC 2007–2015.",
        "- **Alemanha**: PIB trimestral em 1991 (pré-reunificação não coberto).",
        "- **Japão**: CPI trimestral do OECD-MEI termina em 2021T2.",
        "- **China/Índia/Chile/Colômbia/Peru/Rússia**: sem PIB trimestral estável; apenas anual.",
        "- **Arábia Saudita**: PIB trimestral em 2010.",
        "- **UE**: agregado do G20 com cobertura anual parcial; não entra em somas.",
        "- **Capital/PTF**: PWT termina em 2019; não extrapolado.",
        "- **Blocos heterodoxos**: Gini/top10/bottom20 ~1990+ e cobertura esparsa; termos de troca ~2005+; CO2/energia ~1970+; capital bancário/NPL ~2000+. Ver `cobertura_%`.",
        "",
        "## 8. Reprodutibilidade",
        "",
        "`make all` (fetch → build → validate → empirical → export → reports → test). "
        "Manifesto com URL/timestamp/SHA-256 em `data/processed/manifest.json`.",
    ]
    (ROOT / "docs" / "01_codebook.md").write_text("\n".join(lines), encoding="utf-8")


def regime_doc() -> None:
    meta = pd.read_csv(settings.PROCESSED / "regime_metadata.csv")
    ann = pd.read_csv(settings.PROCESSED / "regime_matrix_annual.csv")
    q = pd.read_csv(settings.PROCESSED / "regime_matrix_quarterly.csv")
    by_kind = meta.groupby("tipo").size().rename("n").reset_index()
    lines = [
        "# Dummies de regime — metadados e matriz",
        "",
        f"**{len(meta)} dummies**, em `config/regimes.yml`, materializadas em "
        f"`regime_matrix_annual.csv` ({ann.shape[0]} país-ano) e "
        f"`regime_matrix_quarterly.csv` ({q.shape[0]} país-trimestre).",
        "",
        "## 1. Cobertura por tipo",
        "",
        md(by_kind),
        "",
        "## 2. Matriz país × dummy — Brasil",
        "",
        "A matriz completa está em `data/processed/regime_matrix_annual.csv`; "
        "o recorte abaixo lista as dummies brasileiras.",
        "",
        md(meta[meta.paises.str.contains("BRA")][["dummy", "nome", "tipo", "inicio", "fim"]]
           .sort_values("inicio")),
        "",
        "## 3. Como usar",
        "",
        "- Controle ou quebra de intercepto/slope em modelos reduzidos; a coluna `regime_dummy` do long lista as ativas.",
        "- No SVAR, `g_gfc_2008` e `g_pandemic_2020` entram como controles exógenos.",
        "- Dummies de método (`br_gdp_rebase_2010`, `br_ipca_rebase_2012`, `ar_indec_2007`) sinalizam quebras de nível, não de ciclo.",
        "",
        "## 4. Metadados completos",
        "",
        "`data/processed/regime_metadata.csv` (dummy, nome, tipo, escopo, países, início, fim, "
        "frequências, fonte, URL, variáveis afetadas, modelos).",
        "",
        md(meta[["dummy", "nome", "tipo", "inicio", "fim", "fonte"]].head(30)),
        "",
        "*(tabela completa no CSV; aqui as 30 primeiras)*",
    ]
    (ROOT / "docs" / "03_regime_dummies.md").write_text("\n".join(lines), encoding="utf-8")


def groups_doc() -> None:
    rows = []
    for g, meta in settings.GROUP_META.items():
        rows.append([g, meta["name"], ", ".join(meta["members"]), len(meta["members"]),
                     meta["justification"]])
    lines = [
        "# Grupos de países — listas fechadas e justificativa",
        "",
        "22 países + agregado UE. Grupos se sobrepõem; a UE é agregada e excluída de somas.",
        "",
        md(pd.DataFrame(rows, columns=["grupo", "nome", "membros", "n", "justificativa"])),
        "",
        "## Uso",
        "",
        "- **Anual**: 22 países; UE apenas onde há série, sem somas.",
        "- **Trimestral**: 16 países com PIB estável (BRA, USA, DEU, GBR, JPN, CAN, MEX, AUS, FRA, ITA, KOR, ZAF, TUR, IDN, ARG, SAU); CHN, IND, CHL, COL, PER e RUS ficam no anual.",
        "- **SVAR**: Brasil, EUA e México.",
    ]
    (ROOT / "docs" / "05_country_groups.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    codebook()
    regime_doc()
    groups_doc()
    print("docs gerados")
