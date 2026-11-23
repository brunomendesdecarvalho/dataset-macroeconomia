"""Exportação consolidada: Excel único + CSVs pronto-para-análise."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from . import settings
from .blocks import BLOCK_LABELS, block_of

EXPORTS = settings.DATA / "exports"
EXPORTS.mkdir(parents=True, exist_ok=True)

LONG_COLS = ["freq", "iso3", "country", "date", "period", "variable", "block",
             "value", "unit", "source", "source_code", "quality_flag",
             "is_forecast", "regime_dummy"]


def _load() -> tuple[pd.DataFrame, pd.DataFrame]:
    a = pd.read_parquet(settings.PROCESSED / "macro_annual_long.parquet")
    q = pd.read_parquet(settings.PROCESSED / "macro_quarterly_long.parquet")
    return a, q


def _wide(df: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    # mantém a ordem país-ano/trimestre e uma coluna por variável
    w = df.pivot_table(index=keys, columns="variable", values="value", aggfunc="last")
    w = w.sort_index(level=["iso3", "year" if "year" in keys else "period"])
    w.columns.name = None
    return w.reset_index()


def _format_dates(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    return df


def build_frames(a: pd.DataFrame, q: pd.DataFrame):
    a = a.copy(); q = q.copy()
    a["block"] = a["variable"].map(block_of)
    q["block"] = q["variable"].map(block_of)
    a["is_forecast"] = a["is_forecast"].astype(bool)
    q["is_forecast"] = q["is_forecast"].astype(bool)

    # wide anual: ordem país-ano
    a = a.sort_values(["iso3", "year", "variable"])
    q = q.sort_values(["iso3", "period", "variable"])
    wa = _wide(a, ["iso3", "country", "year", "date"])
    wq = _wide(q, ["iso3", "country", "period", "date"])
    wq = wq.rename(columns={"period": "quarter"})
    wa["date"] = pd.to_datetime(wa["date"]).dt.strftime("%Y-%m-%d")
    wq["date"] = pd.to_datetime(wq["date"]).dt.strftime("%Y-%m-%d")

    # regimes anuais
    reg = pd.read_csv(settings.PROCESSED / "regime_matrix_annual.csv")
    reg = reg.merge(a[["iso3", "country"]].drop_duplicates("iso3"), on="iso3", how="left")
    reg = reg[["iso3", "country", "year"] + [c for c in reg.columns
                                             if c not in ("iso3", "country", "year")]]
    reg = reg.sort_values(["iso3", "year"])

    # codebook de fontes (uma linha por variável)
    cov = pd.read_csv(settings.PROCESSED / "coverage.csv")
    cov = cov.groupby(["freq", "variable"]).agg(
        n_paises=("iso3", "nunique"), cobertura_mediana=("coverage_pct", "median"),
        cobertura_min=("coverage_pct", "min")).reset_index()
    meta = settings.VARIABLES.copy()
    meta["block"] = meta["id"].map(block_of)
    valid = set(a["variable"]) | set(q["variable"])
    meta = meta[meta["id"].isin(valid)].copy()
    cb = meta.merge(cov, left_on=["id", "freq"], right_on=["variable", "freq"], how="left")
    cb = cb[["id", "freq", "label", "block", "unit", "source", "code",
             "n_paises", "cobertura_mediana", "cobertura_min", "coverage_note"]].copy()
    cb.columns = ["variable", "freq", "label", "block", "unit", "source", "source_code",
                  "n_paises", "cobertura_mediana", "cobertura_min", "coverage_note"]
    cb["block_label"] = cb["block"].map(BLOCK_LABELS).fillna(cb["block"])
    cb = cb.sort_values(["block", "freq", "variable"])

    # long consolidado
    long_cols = ["freq", "iso3", "country", "date", "period", "variable", "block",
                 "value", "unit", "source", "source_code", "quality_flag",
                 "is_forecast", "regime_dummy"]
    long = pd.concat([a[long_cols], q[long_cols]], ignore_index=True)
    long["date"] = pd.to_datetime(long["date"]).dt.strftime("%Y-%m-%d")
    long["is_forecast"] = long["is_forecast"].astype(bool)
    long = long.sort_values(["freq", "iso3", "period", "variable"]).reset_index(drop=True)
    return wa, wq, reg, cb, long


def _excel_sheet(writer, df: pd.DataFrame, name: str, freeze: str = "A2") -> None:
    df.to_excel(writer, sheet_name=name, index=False)
    ws = writer.sheets[name]
    ws.freeze_panes = freeze
    ws.auto_filter.ref = ws.dimensions
    for col in ws.columns:
        width = min(42, max(10, max(len(str(c.value)) if c.value is not None else 0
                                     for c in col[:80]) + 2))
        ws.column_dimensions[col[0].column_letter].width = width


def run() -> dict[str, Path]:
    a, q = _load()
    wa, wq, reg, cb, long = build_frames(a, q)
    EXPORTS.mkdir(parents=True, exist_ok=True)
    paths = {
        "anual": EXPORTS / "macro_anual_wide.csv",
        "trimestral": EXPORTS / "macro_trimestral_wide.csv",
        "long": EXPORTS / "macro_todos_dados_long.csv",
        "xlsx": EXPORTS / "macro_dataset_consolidado.xlsx",
    }
    wa.to_csv(paths["anual"], index=False, encoding="utf-8")
    wq.to_csv(paths["trimestral"], index=False, encoding="utf-8")
    long.to_csv(paths["long"], index=False, encoding="utf-8")
    with pd.ExcelWriter(paths["xlsx"], engine="openpyxl") as writer:
        _excel_sheet(writer, wa, "Anual_Wide")
        _excel_sheet(writer, wq, "Trimestral_Wide")
        _excel_sheet(writer, reg, "Regimes_Anual")
        _excel_sheet(writer, cb, "Codebook_Fontes")
    print(f"[export] {paths['xlsx']} | Anual {wa.shape} | Trimestral {wq.shape} | "
          f"Regimes {reg.shape} | Codebook {cb.shape} | Long {long.shape}")
    return paths


if __name__ == "__main__":
    run()
