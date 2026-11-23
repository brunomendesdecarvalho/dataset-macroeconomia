"""Geração de figuras, tabelas e números-chave para os relatórios."""
from __future__ import annotations

import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from . import settings

plt.rcParams.update({"figure.dpi": 130, "font.size": 8, "axes.titlesize": 9,
                     "axes.grid": True, "grid.alpha": 0.25, "axes.spines.top": False,
                     "axes.spines.right": False})
FIG = settings.FIGURES
TAB = settings.TABLES
FIG.mkdir(parents=True, exist_ok=True)
TAB.mkdir(parents=True, exist_ok=True)


def _save(fig, name: str) -> None:
    fig.tight_layout()
    fig.savefig(FIG / name, bbox_inches="tight")
    plt.close(fig)


def fig_coverage(annual: pd.DataFrame) -> None:
    cov = pd.read_csv(settings.PROCESSED / "coverage_matrix_annual.csv", index_col=0)
    keys = ["gdp_real", "gdp_nominal", "inflation", "unemployment", "policy_rate", "long_rate",
            "exchange_rate_nominal", "reer", "gov_debt_gdp", "primary_balance_gdp",
            "credit_private_gdp", "capital_stock", "tfp", "current_account_gdp",
            "consumption_gdp", "investment_gdp", "inflation_expectations", "output_gap",
            "gini_index", "income_share_top10", "vulnerable_employment_pct",
            "terms_of_trade_index", "intl_reserves_months_imports", "external_debt_gni",
            "lending_rate", "interest_rate_spread", "market_cap_gdp",
            "co2_per_capita", "renewable_electricity_pct", "manufacturing_gdp"]
    keys = [k for k in keys if k in cov.index]
    d = cov.loc[keys].drop(columns=[c for c in ["EU", "WLD"] if c in cov.columns])
    fig, ax = plt.subplots(figsize=(11, 5))
    im = ax.imshow(d.values, aspect="auto", cmap="YlGnBu", vmin=0, vmax=100)
    ax.set_xticks(range(d.shape[1])); ax.set_xticklabels(d.columns, rotation=90)
    ax.set_yticks(range(d.shape[0])); ax.set_yticklabels(d.index)
    ax.set_title("Cobertura anual por país e variável (% de anos com observação, 1960–2026)")
    fig.colorbar(im, ax=ax, shrink=0.7, label="%")
    _save(fig, "fig_coverage_annual.png")


def fig_brazil(annual: pd.DataFrame) -> None:
    b = annual[annual.iso3 == "BRA"]
    def s(v):
        d = b[b.variable == v].set_index("year")["value"].sort_index()
        return d[~d.index.duplicated()]
    fig, axes = plt.subplots(3, 2, figsize=(11, 8))
    ax = axes[0, 0]
    ax.plot(s("gdp_growth").index, s("gdp_growth").values, color="#1f4e79")
    ax.axhline(0, color="k", lw=0.6); ax.set_title("Crescimento real do PIB (%)")
    ax = axes[0, 1]
    ax.plot(s("inflation").index, s("inflation").values, label="IPCA", color="#c00000")
    t = s("inflation_target")
    ax.plot(t.index, t.values, label="Meta", color="k", ls="--")
    ax.set_yscale("symlog"); ax.set_title("Inflação e meta (% a.a., escala symlog)"); ax.legend()
    ax = axes[1, 0]
    ax.plot(s("policy_rate").index, s("policy_rate").values, label="Selic", color="#1f4e79")
    ax.plot(s("real_rate_ex_post").index, s("real_rate_ex_post").values, label="Juro real ex post", color="#c55a11")
    ax.set_yscale("symlog", linthresh=1.0)
    ax.set_title("Juros (% a.a., escala symlog)"); ax.legend()
    ax = axes[1, 1]
    ax.plot(s("gov_debt_gdp").index, s("gov_debt_gdp").values, label="Dívida bruta", color="#7030a0")
    ax.plot(s("primary_balance_gdp").index, s("primary_balance_gdp").values, label="Resultado primário", color="#548235")
    ax.set_title("Fiscal (% do PIB)"); ax.legend()
    ax = axes[2, 0]
    ax.plot(s("output_gap").index, s("output_gap").values, color="#c00000")
    ax.axhline(0, color="k", lw=0.6); ax.set_title("Hiato do produto (%)")
    ax = axes[2, 1]
    ax.plot(s("reer").index, s("reer").values, color="#2e75b6")
    ax.set_title("Câmbio real efetivo (2010=100)")
    _save(fig, "fig_brazil_panel.png")


def fig_regimes() -> None:
    reg = pd.read_parquet(settings.PROCESSED / "regime_matrix_annual.parquet").reset_index()
    b = reg[reg.iso3 == "BRA"].set_index("year").drop(columns=["iso3"])
    b = b.loc[:, b.sum() > 0]
    fig, ax = plt.subplots(figsize=(12, max(4, 0.18 * b.shape[1])))
    ax.imshow(b.T.values, aspect="auto", cmap="Greys", interpolation="nearest")
    ax.set_yticks(range(b.shape[1])); ax.set_yticklabels(b.columns, fontsize=6)
    ax.set_xticks(range(0, len(b.index), 5)); ax.set_xticklabels(b.index[::5], rotation=90)
    ax.set_title("Dummies de regime ativas — Brasil (1960–2026)")
    _save(fig, "fig_regime_timeline_bra.png")


def coverage_panel(annual: pd.DataFrame, quarterly: pd.DataFrame) -> None:
    """Matriz país × variável × período (1 = presente, 0 = ausente)."""
    for freq, df, years, iso_list in (
        ("annual", annual, range(1960, 2027), settings.COUNTRIES),
        ("quarterly", quarterly, None, settings.QUARTERLY_COUNTRIES),
    ):
        variables = sorted(df.variable.unique())
        if freq == "annual":
            idx = pd.MultiIndex.from_product([iso_list, variables, years],
                                             names=["iso3", "variable", "year"])
        else:
            periods = pd.period_range("1995Q1", "2026Q4", freq="Q").astype(str)
            idx = pd.MultiIndex.from_product([iso_list, variables, periods],
                                             names=["iso3", "variable", "quarter"])
        grid = pd.DataFrame(index=idx).reset_index()
        key = "year" if freq == "annual" else "quarter"
        if freq == "annual":
            keys = df[["iso3", "variable", "year"]].drop_duplicates().assign(present=1)
        else:
            keys = df[["iso3", "variable", "date"]].copy()
            keys["quarter"] = pd.PeriodIndex(keys["date"], freq="Q").astype(str)
            keys = keys.drop_duplicates(["iso3", "variable", "quarter"]).assign(present=1)
        grid = grid.merge(keys[["iso3", "variable", key, "present"]],
                          on=["iso3", "variable", key], how="left")
        grid["present"] = grid["present"].fillna(0).astype("int8")
        grid.to_parquet(settings.PROCESSED / f"coverage_panel_{freq}.parquet", index=False)
        grid.to_csv(settings.PROCESSED / f"coverage_panel_{freq}.csv", index=False, encoding="utf-8-sig")


def regime_by_country() -> None:
    folder = settings.PROCESSED / "regime_by_country"
    folder.mkdir(exist_ok=True)
    for freq, fname, key in (("annual", "regime_matrix_annual.csv", "year"),
                             ("quarterly", "regime_matrix_quarterly.csv", "quarter")):
        d = pd.read_csv(settings.PROCESSED / fname)
        for iso, g in d.groupby("iso3"):
            g.to_csv(folder / f"{iso}_{freq}.csv", index=False, encoding="utf-8-sig")


def tables(annual: pd.DataFrame, quarterly: pd.DataFrame) -> None:
    # grupos
    rows = []
    for g, meta in settings.GROUP_META.items():
        for iso in meta["members"]:
            rows.append({"grupo": g, "iso3": iso, "pais": settings.COUNTRY_META.get(iso, {}).get("name_pt", iso),
                         "justificativa": meta["justification"]})
    pd.DataFrame(rows).to_csv(TAB / "table_country_groups.csv", index=False, encoding="utf-8-sig")
    # dicionário
    settings.VARIABLES.to_csv(TAB / "table_variable_dictionary.csv", index=False, encoding="utf-8-sig")
    # regimes
    pd.read_csv(settings.PROCESSED / "regime_metadata.csv").to_csv(
        TAB / "table_regime_metadata.csv", index=False, encoding="utf-8-sig")
    # cobertura agregada
    cov = pd.read_csv(settings.PROCESSED / "coverage.csv")
    from .blocks import block_of
    cov["block"] = cov["variable"].map(block_of)
    cov.groupby(["block", "freq"]).agg(
        n_variaveis=("variable", "nunique"), cobertura_media=("coverage_pct", "mean"),
        cobertura_mediana=("coverage_pct", "median")).reset_index().to_csv(
        TAB / "table_heterodox_coverage.csv", index=False, encoding="utf-8-sig")
    pd.read_csv(settings.PROCESSED / "cross_source_summary.csv").to_csv(
        TAB / "table_cross_source_summary.csv", index=False, encoding="utf-8-sig")
    pd.read_csv(settings.PROCESSED / "identity_summary.csv").to_csv(
        TAB / "table_identity_summary.csv", index=False, encoding="utf-8-sig")
    pd.read_csv(settings.PROCESSED / "stationarity.csv").to_csv(
        TAB / "table_stationarity.csv", index=False, encoding="utf-8-sig")
    pd.read_csv(settings.PROCESSED / "bai_perron.csv").to_csv(
        TAB / "table_bai_perron.csv", index=False, encoding="utf-8-sig")
    pd.read_csv(settings.PROCESSED / "chow.csv").to_csv(
        TAB / "table_chow.csv", index=False, encoding="utf-8-sig")
    summary = {
        "annual_rows": int(len(annual)), "quarterly_rows": int(len(quarterly)),
        "annual_countries": int(annual.iso3.nunique()), "quarterly_countries": int(quarterly.iso3.nunique()),
        "annual_variables": int(annual.variable.nunique()), "quarterly_variables": int(quarterly.variable.nunique()),
        "annual_start": str(annual.date.min().date()), "annual_end": str(annual.date.max().date()),
        "quarterly_start": str(quarterly.date.min().date()), "quarterly_end": str(quarterly.date.max().date()),
        "regime_dummies": int(pd.read_csv(settings.PROCESSED / "regime_metadata.csv").shape[0]),
    }
    with open(settings.PROCESSED / "dataset_summary.json", "w", encoding="utf-8") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=2)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def run() -> None:
    annual = pd.read_parquet(settings.PROCESSED / "macro_annual_long.parquet")
    quarterly = pd.read_parquet(settings.PROCESSED / "macro_quarterly_long.parquet")
    fig_coverage(annual)
    fig_brazil(annual)
    fig_regimes()
    tables(annual, quarterly)
    coverage_panel(annual, quarterly)
    regime_by_country()
    print("figuras e tabelas geradas")


if __name__ == "__main__":
    run()
