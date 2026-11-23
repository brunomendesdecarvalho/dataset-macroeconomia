"""Validação: cross-source, identidades, estacionariedade, quebras e cobertura."""
from __future__ import annotations

import warnings
from dataclasses import dataclass

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller, kpss

from . import settings

warnings.filterwarnings("ignore")

CONCEPTS = {
    "gdp_growth": {"primary": ("annual", "gdp_growth"), "WEO": ("weo", "gdp_growth_weo"),
                   "WDI": ("wdi", "gdp_growth_wdi"), "tol": 1.0, "unit": "p.p."},
    "inflation": {"primary": ("annual", "inflation"), "WEO": ("weo", "inflation_weo"),
                  "WDI": ("wdi", "inflation_wdi"), "tol": 2.0, "unit": "p.p."},
    "unemployment": {"primary": ("annual", "unemployment"), "WEO": ("weo", "unemployment_weo"),
                     "WDI": ("wdi", "unemployment_wdi"), "tol": 1.0, "unit": "p.p."},
    "gov_debt_gdp": {"primary": ("annual", "gov_debt_gdp"), "WEO": ("weo", "gov_debt_gdp_weo"),
                     "WDI": ("wdi", "central_gov_debt_gdp"), "tol": 5.0, "unit": "p.p. do PIB"},
    "gdp_nominal_usd": {"primary": ("annual", "gdp_nominal_usd"),
                        "WEO": ("weo", "gdp_nominal_usd_weo"),
                        "WDI": ("wdi", "gdp_nominal_wdi"), "tol": 0.05, "unit": "%"},
    "primary_balance": {"WEO": ("weo", "primary_balance_gdp"), "BCB": ("bcb", "primary_balance_gdp"),
                        "tol": 2.0, "unit": "p.p. do PIB"},
}


def _load() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, pd.DataFrame]]:
    annual = pd.read_parquet(settings.PROCESSED / "macro_annual_long.parquet")
    quarterly = pd.read_parquet(settings.PROCESSED / "macro_quarterly_long.parquet")
    parsed = {n: pd.read_parquet(settings.RAW / f"parsed_{n}.parquet")
              for n in ("gmd", "wdi", "weo", "pwt", "fred", "bcb", "ibge", "focus")}
    return annual, quarterly, parsed


def _annual_series(annual: pd.DataFrame, var: str) -> pd.DataFrame:
    d = annual[annual.variable == var][["iso3", "year", "value"]].copy()
    return d.groupby(["iso3", "year"], as_index=False)["value"].mean()


def _parsed_series(parsed: dict[str, pd.DataFrame], source: str, var: str) -> pd.DataFrame:
    d = parsed[source]
    d = d[d.variable == var]
    if source == "bcb":
        d = d[d.date.dt.month == 12].copy()
        d["year"] = d.date.dt.year
        d = d.groupby(["iso3", "year"], as_index=False)["value"].mean()
    return d[["iso3", "year", "value"]].copy()


def cross_source(annual: pd.DataFrame, parsed: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    frames = []
    for concept, spec in CONCEPTS.items():
        for src in ("primary", "WEO", "WDI", "BCB"):
            if src not in spec:
                continue
            origin, var = spec[src]
            if src == "primary":
                d = _annual_series(annual, var)
            else:
                d = _parsed_series(parsed, origin, var)
            if d.empty:
                continue
            if concept == "gdp_nominal_usd" and src == "WDI":
                d["value"] = d["value"] / 1e6
            if concept == "gdp_nominal_usd" and src == "WEO":
                d["value"] = d["value"] * 1000.0
            d["concept"] = concept
            d["source"] = src
            frames.append(d)
    comp = pd.concat(frames, ignore_index=True)
    comp = comp.dropna(subset=["value"])

    summary, divs = [], []
    for (concept, iso3), d in comp.groupby(["concept", "iso3"]):
        p = d.pivot_table(index="year", columns="source", values="value", aggfunc="mean")
        srcs = list(p.columns)
        if len(srcs) < 2:
            continue
        diffs = []
        for i, a in enumerate(srcs):
            for b in srcs[i + 1:]:
                diffs.extend((p[a] - p[b]).abs().dropna().tolist())
        diffs = pd.Series(diffs)
        if diffs.empty:
            continue
        tol = CONCEPTS[concept]["tol"]
        if concept == "gdp_nominal_usd":
            scale = p.mean(axis=1).replace(0, np.nan)
            diffs = diffs / scale.mean()
        corr = p.corr().values
        corrs = corr[np.triu_indices_from(corr, k=1)]
        summary.append({
            "concept": concept, "iso3": iso3, "n_years_2plus": int(p.dropna(thresh=2).shape[0]),
            "n_pairs": int(len(diffs)), "mean_abs_diff": diffs.mean(),
            "median_abs_diff": diffs.median(), "p90_abs_diff": diffs.quantile(0.9),
            "max_abs_diff": diffs.max(), "mean_corr": float(np.nanmean(corrs)) if len(corrs) else np.nan,
            "share_within_tol": float((diffs <= tol).mean()), "tolerance": tol,
            "sources": ";".join(srcs),
        })
        spread = (p.max(axis=1) - p.min(axis=1)).dropna()
        metric = spread if concept != "gdp_nominal_usd" else spread / p.mean(axis=1).replace(0, np.nan)
        for year, s in metric[metric > tol].items():
            row = {"concept": concept, "iso3": iso3, "year": int(year), "spread": float(spread.loc[year]),
                   "metric": float(s), "tolerance": tol,
                   "decision": "manter fonte primária; sinalizar divergência"}
            for src in srcs:
                row[src] = p.loc[year, src]
            divs.append(row)
    summ = pd.DataFrame(summary).sort_values(["concept", "mean_abs_diff"], ascending=[True, False])
    div = pd.DataFrame(divs)
    if not div.empty:
        div = div.sort_values("spread", ascending=False).head(400)
    decisions = pd.DataFrame([
        {"concept": "gdp_growth", "primary": "GMD (derivado do PIB real)", "validation": "WEO NGDP_RPCH; WDI NY.GDP.MKTP.KD.ZG",
         "tolerance": "1 p.p.", "decision": "GMD é a espinha dorsal harmonizada; divergências > 1 p.p. sinalizadas e investigadas."},
        {"concept": "inflation", "primary": "BCB/IPCA (Brasil); GMD (demais)", "validation": "WEO PCPIPCH; WDI FP.CPI.TOTL.ZG",
         "tolerance": "2 p.p.", "decision": "Para o Brasil a IPCA é a medida oficial; GMD/WEO/WDI só validam."},
        {"concept": "unemployment", "primary": "GMD", "validation": "WEO LUR; WDI SL.UEM.TOTL.ZS",
         "tolerance": "1 p.p.", "decision": "Definições nacionais diferem; GMD harmoniza; WDI (OIT) é a referência conceitual."},
        {"concept": "gov_debt_gdp", "primary": "GMD (dívida bruta)", "validation": "WEO GGXWDG_NGDP; WDI GC.DOD.TOTL.GD.ZS (governo central)",
         "tolerance": "5 p.p.", "decision": "Perímetros diferentes (governo geral vs central); WDI não é usada como verdade."},
        {"concept": "gdp_nominal_usd", "primary": "GMD (nGDP/USDfx)", "validation": "WEO NGDPD; WDI NY.GDP.MKTP.CD",
         "tolerance": "5%", "decision": "Divergências cambiais explicam a maior parte; mantém-se o cálculo com câmbio médio do GMD."},
        {"concept": "primary_balance", "primary": "WEO pb (governo geral)", "validation": "BCB SGS 5793 (governo central, Brasil)",
         "tolerance": "2 p.p.", "decision": "Perímetros distintos; para o Brasil reportam-se ambos, sem substituição."},
    ])
    return summ, div, decisions


def identities(annual: pd.DataFrame, quarterly: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    p = annual.pivot_table(index=["iso3", "year"], columns="variable", values="value", aggfunc="last")
    p = p.reset_index()
    out = p[["iso3", "year"]].copy()
    out["resid_identity_total_cons"] = 100 - (p.get("consumption_gdp", np.nan)
                                              + p.get("investment_gdp", np.nan)
                                              + p.get("net_exports_gdp", np.nan))
    out["resid_identity_household_plus_gov"] = 100 - (p.get("consumption_gdp", np.nan)
                                                      + p.get("investment_gdp", np.nan)
                                                      + p.get("gov_consumption_gdp", np.nan)
                                                      + p.get("net_exports_gdp", np.nan))
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = p["gdp_nominal"]
        rr = ratio / (p["gdp_real"] * p["gdp_deflator"] / 100)
    out["resid_nominal_real_deflator_pct"] = 100 * (rr - 1)
    out["fisher_gap_pp"] = 100 * ((1 + p.get("policy_rate", np.nan) / 100) /
                                  (1 + p.get("inflation", np.nan) / 100) - 1) \
        - (p.get("policy_rate", np.nan) - p.get("inflation", np.nan))
    # A aproximação linear de Fisher só é informativa fora de hiperinflação
    out.loc[p.get("inflation", np.nan).abs() > 100, "fisher_gap_pp"] = np.nan
    out["debt_residual_pp"] = p.get("debt_dynamics_residual", np.nan)
    out = out.replace([np.inf, -np.inf], np.nan)

    summary_rows = []
    for col, label in [("resid_identity_total_cons", "Y = C + I + NX (C total)"),
                       ("resid_identity_household_plus_gov", "Y = C + I + G + NX (C famílias)"),
                       ("resid_nominal_real_deflator_pct", "Nominal = Real x Deflator"),
                       ("fisher_gap_pp", "Fisher (1+i)=(1+r)(1+pi)"),
                       ("debt_residual_pp", "Dinamica da divida (SFA)")]:
        s = out[col].dropna()
        if col in ("fisher_gap_pp", "debt_residual_pp"):
            s = s[s.abs() < 50]
        summary_rows.append({"identity": label, "n": int(s.size), "mean": s.mean(),
                             "median": s.median(), "p90_abs": s.abs().quantile(0.9),
                             "max_abs": s.abs().max(),
                             "share_abs_gt_1": float((s.abs() > 1).mean()),
                             "share_abs_gt_5": float((s.abs() > 5).mean())})
    summ = pd.DataFrame(summary_rows)

    # Consistência trimestral vs anual
    cons = []
    # (a) crescimento: média anual do crescimento trimestral (SAAR) vs anual
    qg = quarterly[quarterly.variable == "gdp_real_growth"][["iso3", "year", "value"]]
    if not qg.empty:
        qa = qg.groupby(["iso3", "year"], as_index=False)["value"].mean()
        ag = annual[annual.variable == "gdp_growth"][["iso3", "year", "value"]].rename(columns={"value": "annual"})
        mm = qa.merge(ag, on=["iso3", "year"], how="inner")
        mm["quarterly_agg"] = mm["value"]
        mm["diff_pp"] = mm["quarterly_agg"] - mm["annual"]
        mm["rel_diff"] = mm["diff_pp"] / mm["annual"].abs().replace(0, np.nan)
        mm["check"] = "crescimento anual vs media de SAAR trimestral"
        mm["complete_year"] = qg.groupby(["iso3", "year"]).size().reindex(
            pd.MultiIndex.from_frame(mm[["iso3", "year"]])).values == 4
        cons.append(mm[["iso3", "year", "check", "annual", "quarterly_agg", "diff_pp", "rel_diff", "complete_year"]])
    # (b) PIB nominal Brasil: soma dos trimestres vs anual
    if "BRA" in quarterly.iso3.unique():
        qn = quarterly[(quarterly.iso3 == "BRA") & (quarterly.variable == "gdp_nominal")]
        if not qn.empty:
            qy = qn.groupby("year", as_index=False)["value"].sum().rename(columns={"value": "quarterly_agg"})
            an = annual[(annual.iso3 == "BRA") & (annual.variable == "gdp_nominal")][["year", "value"]].rename(columns={"value": "annual"})
            mm = qy.merge(an, on="year", how="inner")
            mm["iso3"] = "BRA"
            mm["diff_pp"] = mm["quarterly_agg"] - mm["annual"]
            mm["rel_diff"] = mm["diff_pp"] / mm["annual"]
            mm["check"] = "soma dos trimestres vs PIB nominal anual (IBGE vs GMD)"
            mm["complete_year"] = qn.groupby("year").size().reindex(mm["year"]).values == 4
            cons.append(mm[["iso3", "year", "check", "annual", "quarterly_agg", "diff_pp", "rel_diff", "complete_year"]])
    con = pd.concat(cons, ignore_index=True) if cons else pd.DataFrame()
    return summ, con


def stationarity(annual: pd.DataFrame) -> pd.DataFrame:
    tests = {
        "gdp_real": "log", "inflation": "level", "policy_rate": "level",
        "exchange_rate_nominal": "log", "reer": "log", "output_gap": "level",
        "gov_debt_gdp": "level", "real_rate_ex_post": "level", "unemployment": "level",
        "investment_real": "log",
    }
    rows = []
    for var, mode in tests.items():
        d = annual[(annual.variable == var) & (annual.year <= 2025)].copy()
        for iso, g in d.groupby("iso3"):
            s = g.sort_values("year").set_index("year")["value"].dropna()
            if len(s) < 20:
                continue
            x = np.log(s) if mode == "log" else s
            try:
                adf_l = adfuller(x, autolag="AIC", regression="c")
                adf_d = adfuller(x.diff().dropna(), autolag="AIC", regression="c")
                kp_l = kpss(x, regression="c", nlags="auto")
                kp_d = kpss(x.diff().dropna(), regression="c", nlags="auto")
            except Exception:
                continue
            i0 = (adf_l[1] < 0.05) and (kp_l[1] > 0.05)
            i1 = (adf_d[1] < 0.05) and (kp_d[1] > 0.05)
            concl = "I(0)" if i0 else ("I(1)" if i1 else "inconclusivo")
            rows.append({"iso3": iso, "variable": var, "transform": mode, "n": len(s),
                         "adf_level_p": adf_l[1], "kpss_level_p": kp_l[1],
                         "adf_diff_p": adf_d[1], "kpss_diff_p": kp_d[1], "conclusion": concl})
    return pd.DataFrame(rows)


def _bai_perron(y: np.ndarray, max_breaks: int = 5, min_size: int = 7) -> tuple[list[int], float, float]:
    n = len(y)
    if n < 2 * min_size + 1:
        return [], float(np.sum((y - y.mean()) ** 2)), -np.inf
    csum = np.concatenate([[0.0], np.cumsum(y)])
    csum2 = np.concatenate([[0.0], np.cumsum(y ** 2)])

    def ssr(i: int, j: int) -> float:
        m = j - i
        s = csum[j] - csum[i]
        s2 = csum2[j] - csum2[i]
        return max(s2 - s * s / m, 1e-12)

    inf = 1e18
    dp = np.full((max_breaks + 1, n + 1), inf)
    prev = np.zeros((max_breaks + 1, n + 1), dtype=int)
    for j in range(min_size, n + 1):
        dp[0, j] = ssr(0, j)
    for k in range(1, max_breaks + 1):
        for j in range((k + 1) * min_size, n + 1):
            best, bi = inf, -1
            for i in range(k * min_size, j - min_size + 1):
                val = dp[k - 1, i] + ssr(i, j)
                if val < best:
                    best, bi = val, i
            dp[k, j], prev[k, j] = best, bi
    bic = np.array([n * np.log(dp[k, n] / n) + (k + 1) * np.log(n) for k in range(max_breaks + 1)])
    kbest = int(np.nanargmin(bic))
    breaks, j = [], n
    for k in range(kbest, 0, -1):
        i = prev[k, j]
        breaks.append(i)
        j = i
    return sorted(breaks), float(dp[kbest, n]), float(bic[kbest])


def breaks(annual: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    for var in ("gdp_growth", "inflation"):
        d = annual[(annual.variable == var) & (annual.year <= 2025)]
        for iso, g in d.groupby("iso3"):
            s = g.sort_values("year").set_index("year")["value"].dropna()
            if len(s) < 25:
                continue
            breaks_idx, ssr, bic = _bai_perron(s.values)
            years = [int(s.index[i]) for i in breaks_idx]
            rows.append({"iso3": iso, "variable": var, "n": len(s), "breaks": ";".join(map(str, years)),
                         "n_breaks": len(years), "ssr": ssr, "bic": bic,
                         "first_year": int(s.index[0]), "last_year": int(s.index[-1])})
    bp = pd.DataFrame(rows)

    # Mapa quebras <-> dummies (ano da quebra +/- 1)
    reg = pd.read_parquet(settings.PROCESSED / "regime_matrix_annual.parquet")
    reg = reg.reset_index()
    mapa = []
    for _, r in bp.iterrows():
        if not r["breaks"]:
            continue
        for y in map(int, r["breaks"].split(";")):
            near = reg[(reg.iso3 == r["iso3"]) & (reg.year.between(y - 1, y + 1))]
            active = [c for c in reg.columns if c not in ("iso3", "year") and near[c].sum() > 0]
            mapa.append({"iso3": r["iso3"], "variable": r["variable"], "break_year": y,
                         "dummies_proximas": ";".join(active), "n_dummies": len(active)})
    return bp, pd.DataFrame(mapa)


def chow(annual: pd.DataFrame) -> pd.DataFrame:
    dates = {
        "BRA": [1994, 1999, 2016, 2020], "USA": [1979, 2008, 2020],
        "ARG": [2001, 2016], "MEX": [1994, 2001], "GBR": [1992, 2016],
        "CHL": [1999], "COL": [1999], "PER": [1990, 2002], "TUR": [2001, 2006],
    }
    rows = []
    for iso, yrs in dates.items():
        for var in ("inflation", "gdp_growth"):
            s = annual[(annual.iso3 == iso) & (annual.variable == var)].sort_values("year")
            s = s[["year", "value"]].dropna()
            if len(s) < 20:
                continue
            s["lag"] = s.value.shift(1)
            s = s.dropna()
            for br in yrs:
                d = s.copy()
                d["D"] = (d.year >= br).astype(float)
                d["Dlag"] = d.D * d.lag
                X = np.column_stack([np.ones(len(d)), d.lag, d.D, d.Dlag])
                y = d.value.values
                beta, *_ = np.linalg.lstsq(X, y, rcond=None)
                resid = y - X @ beta
                ssr_u = float(resid @ resid)
                Xr = np.column_stack([np.ones(len(d)), d.lag])
                betar, *_ = np.linalg.lstsq(Xr, y, rcond=None)
                resr = y - Xr @ betar
                ssr_r = float(resr @ resr)
                q = 2
                df2 = len(d) - 4
                if ssr_u <= 0 or df2 <= 0:
                    continue
                F = ((ssr_r - ssr_u) / q) / (ssr_u / df2)
                from scipy.stats import f as fdist
                p = float(1 - fdist.cdf(F, q, df2))
                rows.append({"iso3": iso, "variable": var, "break_year": br, "n": len(d),
                             "F": F, "p_value": p, "reject_5pct": p < 0.05})
    return pd.DataFrame(rows)


def coverage_and_outliers(annual: pd.DataFrame, quarterly: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    for freq, df, start, end in (("A", annual, 1960, 2026), ("Q", quarterly, 1995, 2026)):
        for (iso, var), d in df.groupby(["iso3", "variable"]):
            d = d.sort_values("date")
            if freq == "A":
                expected = end - start + 1
            else:
                expected = len(pd.period_range(f"{start}Q1", f"{end}Q4", freq="Q"))
            rows.append({"freq": freq, "iso3": iso, "variable": var, "first": d.date.min(),
                         "last": d.date.max(), "n": len(d), "expected": expected,
                         "coverage_pct": 100 * len(d) / expected,
                         "missing_pct": 100 * (1 - len(d) / expected)})
    cov = pd.DataFrame(rows)

    out = []
    for (iso, var), d in annual.groupby(["iso3", "variable"]):
        s = d.value.dropna()
        if len(s) < 10:
            continue
        z = (s - s.mean()) / s.std(ddof=0)
        thr = 4 if var in ("gdp_growth", "inflation") else 5
        out.append({"iso3": iso, "variable": var, "n": len(s), "mean": s.mean(), "sd": s.std(ddof=0),
                    "n_outliers": int((z.abs() > thr).sum()), "pct_outliers": float((z.abs() > thr).mean()),
                    "max_abs_z": float(z.abs().max()), "threshold_z": thr})
    return cov, pd.DataFrame(out)


def run() -> dict[str, pd.DataFrame]:
    annual, quarterly, parsed = _load()
    res = {}
    res["cross_source_summary"], res["cross_source_divergences"], res["source_decisions"] = cross_source(annual, parsed)
    res["identity_summary"], res["quarterly_annual"] = identities(annual, quarterly)
    res["stationarity"] = stationarity(annual)
    bp, mapa = breaks(annual)
    res["bai_perron"] = bp
    res["breaks_regime_map"] = mapa
    res["chow"] = chow(annual)
    res["coverage"], res["outliers"] = coverage_and_outliers(annual, quarterly)
    # matrizes de cobertura variável x país
    cov = res["coverage"]
    for freq, name in (("A", "coverage_matrix_annual.csv"), ("Q", "coverage_matrix_quarterly.csv")):
        cov[cov.freq == freq].pivot_table(index="variable", columns="iso3",
                                          values="coverage_pct").to_csv(
            settings.PROCESSED / name, encoding="utf-8-sig")

    for name, df in res.items():
        if df is None or df.empty:
            continue
        df.to_csv(settings.PROCESSED / f"{name}.csv", index=False, encoding="utf-8-sig")
        df.to_parquet(settings.PROCESSED / f"{name}.parquet", index=False)
        print(f"[validation] {name}: {df.shape}")
    return res


if __name__ == "__main__":
    run()
