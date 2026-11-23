"""Construção do dataset harmonizado (long e wide), anual e trimestral."""
from __future__ import annotations

import numpy as np
import pandas as pd
from statsmodels.tsa.filters.hp_filter import hpfilter

from . import blocks, regimes, settings
from .http import quarter_end

CFG = settings.VARIABLES.set_index(["id", "freq"])
SOURCE_URL = {k: v.get("url", "") for k, v in settings.SOURCES_YML["sources"].items()}
SOURCE_VINTAGE = {k: v.get("version", "") for k, v in settings.SOURCES_YML["sources"].items()}
COUNTRY_NAME = {**{c["iso3"]: c["name_pt"] for c in settings.COUNTRIES_YML["countries"]},
                **{a["iso3"]: a["name_pt"] for a in settings.COUNTRIES_YML.get("aggregates", [])},
                "WLD": "Mundo (agregado)"}

BASE_COLS = ["iso3", "country", "date", "year", "period", "variable", "block",
             "value", "unit", "freq", "source", "source_code", "source_detail",
             "source_url", "vintage", "transformation", "transform_applied", "role",
             "model", "coverage_note", "notes", "is_forecast", "quality_flag",
             "seasonal_adjustment", "imputation", "extraction_date", "regime_dummy"]


def _cfg(var: str, freq: str) -> pd.Series | None:
    try:
        return CFG.loc[(var, freq)]
    except KeyError:
        return None


def _attach(df: pd.DataFrame, freq: str) -> pd.DataFrame:
    """Acrescenta metadados do dicionário canônico e colunas de proveniência."""
    df = df.copy()
    df["freq"] = freq
    for col in ("source", "source_code", "source_detail"):
        if col not in df.columns:
            df[col] = ""
    rows = []
    for var, g in df.groupby("variable", sort=False):
        c = _cfg(var, freq)
        g = g.copy()
        if c is None:
            fallback = {
                "gdp_nominal_wdi": "USD correntes", "gdp_real_wdi": "USD constantes de 2015",
                "gdp_growth_wdi": "% a.a.", "inflation_wdi": "% a.a.", "unemployment_wdi": "%",
                "population_wdi": "pessoas", "world_gdp_real": "USD constantes de 2015",
                "gdp_deflator_wdi": "índice (2015=100)", "consumption_gdp_wdi": "% do PIB",
                "exports_gdp_wdi": "% do PIB", "imports_gdp_wdi": "% do PIB",
                "gov_consumption_gdp": "% do PIB", "gross_capital_formation_gdp": "% do PIB",
                "tax_revenue_gdp_wdi": "% do PIB", "central_gov_debt_gdp": "% do PIB",
                "inflation_weo": "% a.a.", "gdp_growth_weo": "% a.a.", "unemployment_weo": "%",
                "gov_debt_gdp_weo": "% do PIB", "gdp_nominal_usd_weo": "milhões de USD",
                "gov_balance_gdp_weo": "% do PIB", "net_debt_gdp": "% do PIB",
                "gdp_ppp_usd": "milhões de int$", "primary_balance_gdp": "% do PIB",
                "rgdpna_pwt": "milhões de USD 2017", "commodity_price_index": "índice",
                "oil_price": "USD/barril", "vix": "índice", "foreign_policy_rate": "% a.a.",
                "inflation_expectations": "% a.a.",
            }
            g["unit"] = g["unit"].fillna("") if "unit" in g else ""
            g.loc[g["unit"].astype(str).str.strip() == "", "unit"] = fallback.get(var, "")
            if "unit" not in g:
                g["unit"] = fallback.get(var, "")
            g["transformation"] = "level"
            g["role"] = "exogenous"
            g["model"] = ""
            g["coverage_note"] = ""
            g["notes"] = "Variável sem entrada no dicionário canônico; verificar."
        else:
            g["unit"] = c["unit"]
            g["transformation"] = c["transform"]
            g["role"] = c["role"]
            g["model"] = c["models"]
            g["coverage_note"] = c["coverage_note"]
            g["notes"] = c["notes"]
        g["block"] = blocks.block_of(var)
        rows.append(g)
    df = pd.concat(rows, ignore_index=True) if rows else df
    df["country"] = df["iso3"].map(COUNTRY_NAME).fillna(df["iso3"])
    df["source_url"] = df["source"].map(SOURCE_URL).fillna("")
    df["vintage"] = df["source"].map(SOURCE_VINTAGE).fillna("")
    df["extraction_date"] = settings.EXTRACTION_TS
    df["transform_applied"] = "none"
    df["imputation"] = "none"
    df["seasonal_adjustment"] = "n/a"
    if "quality_flag" not in df.columns:
        df["quality_flag"] = "ok"
    return df


def _finalize(df: pd.DataFrame) -> pd.DataFrame:
    for col in BASE_COLS:
        if col not in df.columns:
            df[col] = ""
    df["year"] = pd.to_datetime(df["date"], errors="coerce").dt.year
    df["period"] = np.where(df["freq"] == "A", df["year"].astype("Int64").astype(str),
                            pd.to_datetime(df["date"]).dt.to_period("Q").astype(str))
    if "block" not in df.columns:
        df["block"] = "macro_core"
    df["block"] = df["block"].fillna("macro_core")
    df = df[BASE_COLS].copy()
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["value"])
    df = df.drop_duplicates(["iso3", "date", "variable", "freq"], keep="last")
    df["is_forecast"] = df["is_forecast"].fillna(False).astype(bool)
    return df.sort_values(["freq", "iso3", "variable", "date"]).reset_index(drop=True)


# -----------------------------------------------------------------------------
# ANUAL
# -----------------------------------------------------------------------------
def _gmd_annual(parsed: dict[str, pd.DataFrame]) -> pd.DataFrame:
    g = parsed["gmd"].copy()
    g = g[(g.year >= settings.ANNUAL_START) & (g.year <= settings.ANNUAL_END)]
    # Deflator: reescala para 2010=100 por país (o GMD usa bases nacionais distintas)
    # O deflator do GMD é um índice cuja base coincide com a base do PIB real
    # de cada país; mantemos essa série (necessária para a identidade
    # nGDP = rGDP * deflator/100) e criamos uma versão 2010=100 comparável.
    defl = g[g.variable == "gdp_deflator"].copy()
    norm = []
    for iso, d in defl.groupby("iso3"):
        d = d.sort_values("year").dropna(subset=["value"]).copy()
        if d.empty:
            continue
        base = d.loc[d.year == 2010, "value"]
        if base.empty:
            base = d.loc[d.year <= 2010, "value"].tail(1)
        if base.empty:
            base = d["value"].iloc[0]
        b = float(base.iloc[0])
        if b != 0:
            d["value"] = 100.0 * d["value"] / b
        d["variable"] = "gdp_deflator_2010"
        norm.append(d)
    if norm:
        g = pd.concat([g, *norm], ignore_index=True)

    # Componentes reais: o GMD fornece consumo, investimento e gasto do governo
    # a preços correntes. Deflacionamos pelo deflator implícito do PIB
    # (nGDP/rGDP), garantindo a mesma base do PIB real e aditividade aproximada.
    ngdp = g[g.variable == "gdp_nominal"][["iso3", "year", "value"]].rename(columns={"value": "ngdp"})
    rgdp = g[g.variable == "gdp_real"][["iso3", "year", "value"]].rename(columns={"value": "rgdp"})
    factor = ngdp.merge(rgdp, on=["iso3", "year"], how="inner")
    factor["factor"] = factor["ngdp"] / factor["rgdp"].replace(0, np.nan)
    factor = factor[["iso3", "year", "factor"]]
    real_vars = ["consumption_real", "investment_real", "gov_exp_real", "fixed_investment_real"]
    real_parts = []
    for var in real_vars:
        m = g[g.variable == var].merge(factor, on=["iso3", "year"], how="left")
        m["value"] = m["value"] / m["factor"]
        real_parts.append(m)
    g = pd.concat([g[~g.variable.isin(real_vars)], *real_parts], ignore_index=True)

    g["date"] = pd.to_datetime(dict(year=g["year"], month=12, day=31))
    g["is_forecast"] = g["year"] > settings.ANNUAL_ACTUAL_END
    g["quality_flag"] = np.where(g["year"] == 2026, "preliminary",
                                 np.where(g["year"] > 2026, "forecast", "ok"))
    return g


def _pwt_annual(parsed: dict[str, pd.DataFrame]) -> pd.DataFrame:
    p = parsed["pwt"].copy()
    p = p[(p.year >= settings.ANNUAL_START) & (p.year <= 2019)]
    p["date"] = pd.to_datetime(dict(year=p["year"], month=12, day=31))
    p["is_forecast"] = False
    p["quality_flag"] = "ok"
    return p


def _hp_annual(gdp: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    pot_rows, gap_rows = [], []
    for iso, d in gdp.groupby("iso3"):
        s = d.set_index("year")["value"].sort_index()
        s = s[~s.index.duplicated()]
        full = pd.Series(index=range(settings.ANNUAL_START, settings.ANNUAL_ACTUAL_END + 1), dtype=float)
        full.loc[s.index.intersection(full.index)] = s
        if full.notna().sum() < 10:
            continue
        first = full.first_valid_index()
        full = full.loc[first:]
        full = full.interpolate(limit_area="inside")
        obs = full.dropna()
        if len(obs) < 10:
            continue
        cycle, trend = hpfilter(np.log(obs), lamb=100)
        for y in obs.index:
            pot_rows.append((iso, y, float(np.exp(trend.loc[y]))))
            gap_rows.append((iso, y, float(100 * (np.log(obs.loc[y]) - trend.loc[y]))))
    pot = pd.DataFrame(pot_rows, columns=["iso3", "year", "value"])
    gap = pd.DataFrame(gap_rows, columns=["iso3", "year", "value"])
    for df in (pot, gap):
        df["date"] = pd.to_datetime(dict(year=df["year"], month=12, day=31))
        df["is_forecast"] = False
        df["quality_flag"] = "hp_filter"
    return pot, gap


def _annual_fred(parsed: dict[str, pd.DataFrame]) -> pd.DataFrame:
    f = parsed["fred"].copy()
    f["year"] = f["date"].dt.year
    f = f[f.year.between(1960, 2026)]
    agg = f.groupby(["iso3", "variable", "year"], as_index=False)["value"].mean()
    return agg


def _focus_annual(parsed: dict[str, pd.DataFrame]) -> pd.DataFrame:
    f = parsed["focus"].copy()
    if f.empty:
        return pd.DataFrame(columns=["iso3", "year", "value"])
    f = f[f.variable == "inflation_expectations"]
    if "indicador" in f.columns:
        f = f[f.indicador == "IPCA"]
    if "suavizada" in f.columns:
        f = f[f.suavizada == "N"]
    if "base_calculo" in f.columns:
        f = f[f.base_calculo == 0]
    f = f.dropna(subset=["date", "value"])
    # média mensal -> média anual (a expectativa é 12 meses à frente)
    f["year"] = f.date.dt.year
    monthly = f.groupby(["iso3", "year", "date"], as_index=False)["value"].median()
    out = monthly.groupby(["iso3", "year"], as_index=False)["value"].mean()
    return out


def build_annual(parsed: dict[str, pd.DataFrame]) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []

    gmd = _gmd_annual(parsed)
    frames.append(gmd)

    # PIB nominal em USD (milhões) = nGDP (milhões LC) / (LC por USD)
    ng = gmd[gmd.variable == "gdp_nominal"][["iso3", "year", "value"]].rename(columns={"value": "ngdp"})
    fx = gmd[gmd.variable == "exchange_rate_nominal"][["iso3", "year", "value"]].rename(columns={"value": "fx"})
    usd = ng.merge(fx, on=["iso3", "year"], how="inner")
    usd["value"] = usd["ngdp"] / usd["fx"].replace(0, np.nan)
    usd["variable"] = "gdp_nominal_usd"
    usd["date"] = pd.to_datetime(dict(year=usd["year"], month=12, day=31))
    usd["source"] = "derived"
    usd["source_code"] = "nGDP/USDfx"
    usd["source_detail"] = "GMD nGDP dividido por GMD USDfx"
    usd["is_forecast"] = usd["year"] > settings.ANNUAL_ACTUAL_END
    usd["quality_flag"] = "derived"
    frames.append(usd[["iso3", "year", "date", "variable", "value", "source",
                       "source_code", "source_detail", "is_forecast", "quality_flag"]])

    # Saldo comercial em % do PIB
    exp = gmd[gmd.variable == "exports_gdp"][["iso3", "year", "value"]].rename(columns={"value": "x"})
    imp = gmd[gmd.variable == "imports_gdp"][["iso3", "year", "value"]].rename(columns={"value": "m"})
    nx = exp.merge(imp, on=["iso3", "year"], how="inner")
    nx["value"] = nx["x"] - nx["m"]
    nx["variable"] = "net_exports_gdp"
    nx["date"] = pd.to_datetime(dict(year=nx["year"], month=12, day=31))
    nx["source"] = "derived"
    nx["source_code"] = "exports_GDP-imports_GDP"
    nx["source_detail"] = "GMD"
    nx["is_forecast"] = nx["year"] > settings.ANNUAL_ACTUAL_END
    nx["quality_flag"] = "derived"
    frames.append(nx[["iso3", "year", "date", "variable", "value", "source",
                      "source_code", "source_detail", "is_forecast", "quality_flag"]])

    # Crescimento real e PIB potencial/hiato
    gdp = gmd[gmd.variable == "gdp_real"][["iso3", "year", "value"]].copy()
    growth_rows = []
    for iso, d in gdp.groupby("iso3"):
        d = d.sort_values("year")
        d["g"] = 100 * np.log(d["value"]).diff()
        d["value"] = d["g"]
        d["variable"] = "gdp_growth"
        d["date"] = pd.to_datetime(dict(year=d["year"], month=12, day=31))
        d["source"] = "derived"
        d["source_code"] = "100*dlog(rGDP)"
        d["source_detail"] = "GMD rGDP"
        d["is_forecast"] = d["year"] > settings.ANNUAL_ACTUAL_END
        d["quality_flag"] = "derived"
        growth_rows.append(d[["iso3", "year", "date", "variable", "value", "source",
                              "source_code", "source_detail", "is_forecast", "quality_flag"]])
    if growth_rows:
        frames.append(pd.concat(growth_rows, ignore_index=True))

    pot, gap = _hp_annual(gdp)
    for df, var in ((pot, "potential_gdp"), (gap, "output_gap")):
        df = df.copy()
        df["variable"] = var
        df["source"] = "derived"
        df["source_code"] = "HP(log(rGDP), lambda=100)"
        df["source_detail"] = "Filtro Hodrick-Prescott bicaudal"
        frames.append(df[["iso3", "year", "date", "variable", "value", "source",
                          "source_code", "source_detail", "is_forecast", "quality_flag"]])

    # WEO
    weo = parsed["weo"].copy()
    weo = weo[(weo.year >= 1980) & (weo.year <= settings.ANNUAL_END)]
    weo["date"] = pd.to_datetime(dict(year=weo["year"], month=12, day=31))
    weo["is_forecast"] = weo["year"] > settings.ANNUAL_ACTUAL_END
    weo["quality_flag"] = np.where(weo["year"] == 2026, "preliminary", "ok")
    for var in ("gdp_nominal_usd_weo", "gdp_ppp_usd"):
        m = weo.variable == var
        weo.loc[m, "value"] = weo.loc[m, "value"] * 1000.0  # bilhões -> milhões
    frames.append(weo)

    # WDI
    wdi = parsed["wdi"].copy()
    wdi = wdi[(wdi.year >= settings.ANNUAL_START) & (wdi.year <= settings.ANNUAL_END)]
    wdi["date"] = pd.to_datetime(dict(year=wdi["year"], month=12, day=31))
    wdi["is_forecast"] = wdi["year"] > settings.ANNUAL_ACTUAL_END
    wdi["quality_flag"] = np.where(wdi["year"] == 2026, "preliminary", "ok")
    frames.append(wdi)

    # PWT
    frames.append(_pwt_annual(parsed))

    # FRED (médias anuais)
    fa = _annual_fred(parsed)
    fa["date"] = pd.to_datetime(dict(year=fa["year"], month=12, day=31))
    fa["is_forecast"] = False
    fa["quality_flag"] = "ok"
    # Apenas séries globais (commodities, VIX, juros dos EUA, Michigan).
    # As séries país-específicas do FRED entram só no painel trimestral; no anual
    # a fonte primária é o GMD (evita duplicação de conceito).
    fa = fa[fa.variable.isin(["commodity_price_index", "oil_price", "vix",
                              "foreign_policy_rate", "inflation_expectations"])]
    fa = fa[fa.iso3.isin(["WLD", "USA"])]
    fa.loc[fa.variable == "foreign_policy_rate", "iso3"] = "WLD"
    fa["variable"] = fa["variable"].replace({"inflation_expectations": "inflation_expectations"})
    frames.append(fa)

    # Focus (expectativas anuais, Brasil)
    foc = _focus_annual(parsed)
    if not foc.empty:
        foc["date"] = pd.to_datetime(dict(year=foc["year"], month=12, day=31))
        foc["source"] = "BCB_FOCUS"
        foc["source_code"] = "ExpectativasMercadoInflacao12Meses"
        foc["source_detail"] = "BCB Focus, mediana IPCA 12m"
        foc["is_forecast"] = False
        foc["quality_flag"] = "survey"
        frames.append(foc)

    ann = pd.concat(frames, ignore_index=True)

    # Brasil: IPCA (BCB/IBGE) é a medida oficial de inflação; o GMD pode usar
    # outra série de preços. Substituímos a inflação anual do Brasil pela IPCA
    # acumulada em 12 meses (dezembro), mantendo o GMD apenas na validação.
    bcb = parsed["bcb"]
    bi = bcb[(bcb.iso3 == "BRA") & (bcb.variable == "inflation")].copy()
    if not bi.empty:
        m = bi.groupby("date")["value"].mean().sort_index()
        idx = (1 + m / 100).cumprod() * 100
        dec = idx[idx.index.month == 12]
        yoy = 100 * (dec / dec.shift(1) - 1)
        br_inf = yoy.dropna().rename("value").reset_index()
        br_inf.columns = ["date", "value"]
        br_inf["iso3"] = "BRA"
        br_inf["year"] = br_inf.date.dt.year
        br_inf["date"] = pd.to_datetime(dict(year=br_inf["year"], month=12, day=31))
        br_inf["variable"] = "inflation"
        br_inf["source"] = "BCB"
        br_inf["source_code"] = "433 (IPCA)"
        br_inf["source_detail"] = "IBGE IPCA via BCB SGS 433, 12m em dezembro"
        br_inf["is_forecast"] = False
        br_inf["quality_flag"] = "ok"
        ann = ann[~((ann.iso3 == "BRA") & (ann.variable == "inflation"))]
        ann = pd.concat([ann, br_inf], ignore_index=True)

    ann = _attach(ann, "A")
    ann = _add_heterodox(ann, parsed)

    # Metas de inflação
    tgt_rows = []
    for iso, targets in settings.INFLATION_TARGETS.items():
        for y, v in targets.items():
            tgt_rows.append((iso, y, float(v)))
    tgt = pd.DataFrame(tgt_rows, columns=["iso3", "year", "value"])
    tgt["date"] = pd.to_datetime(dict(year=tgt["year"], month=12, day=31))
    tgt["variable"] = "inflation_target"
    tgt["source"] = "hardcoded"
    tgt["source_code"] = "INFLATION_TARGETS"
    tgt["source_detail"] = "Metas oficiais (BCB/bancos centrais/AREAER)"
    tgt["is_forecast"] = False
    tgt["quality_flag"] = "policy"
    tgt = _attach(tgt, "A")
    ann = pd.concat([ann, tgt], ignore_index=True)

    # Juro real ex post e ex ante, r* e resíduos
    def pivot(var: str) -> pd.DataFrame:
        return ann[ann.variable == var][["iso3", "year", "value"]].rename(columns={"value": var})

    base = pivot("policy_rate")
    for var in ("inflation", "long_rate", "primary_balance_gdp",
                "gov_debt_gdp", "gdp_growth", "inflation_expectations"):
        base = base.merge(pivot(var), on=["iso3", "year"], how="left")
    base["real_rate_ex_post"] = base["policy_rate"] - base["inflation"]
    base["real_rate_ex_ante"] = base["policy_rate"] - base["inflation_expectations"]
    deriv = []
    for var in ("real_rate_ex_post", "real_rate_ex_ante"):
        d = base[["iso3", "year", var]].dropna().rename(columns={var: "value"})
        d["variable"] = var
        d["date"] = pd.to_datetime(dict(year=d["year"], month=12, day=31))
        d["source"] = "derived"
        d["source_code"] = "policy_rate - inflation(_expectations)"
        d["source_detail"] = "Aproximação de Fisher"
        d["is_forecast"] = False
        d["quality_flag"] = "derived"
        deriv.append(d)
    # r*: HP do juro real ex ante (proxy, não estrutural)
    ra = base[["iso3", "year", "real_rate_ex_ante"]].dropna()
    for iso, d in ra.groupby("iso3"):
        d = d.sort_values("year").set_index("year")["real_rate_ex_ante"]
        if len(d) < 10:
            continue
        cyc, tr = hpfilter(d, lamb=100)
        out = pd.DataFrame({"iso3": iso, "year": d.index, "value": tr.values})
        out["variable"] = "neutral_rate"
        out["date"] = pd.to_datetime(dict(year=out["year"], month=12, day=31))
        out["source"] = "derived"
        out["source_code"] = "HP(real_rate_ex_ante, lambda=100)"
        out["source_detail"] = "Proxy de r* por filtro HP"
        out["is_forecast"] = False
        out["quality_flag"] = "proxy"
        deriv.append(out)
    if deriv:
        d = pd.concat(deriv, ignore_index=True)
        d = _attach(d, "A")
        ann = pd.concat([ann, d], ignore_index=True)

    # Dinâmica da dívida: resíduo SFA
    dd = base.dropna(subset=["gov_debt_gdp", "primary_balance_gdp", "gdp_growth"]).copy()
    dd = dd.sort_values(["iso3", "year"])
    dd["d_lag"] = dd.groupby("iso3")["gov_debt_gdp"].shift(1)
    dd["i"] = dd["long_rate"].fillna(dd["policy_rate"]) / 100.0
    dd["pi"] = dd["inflation"] / 100.0
    dd["r"] = (1 + dd["i"]) / (1 + dd["pi"]) - 1
    dd["g"] = dd["gdp_growth"] / 100.0
    dd["delta_d"] = dd["gov_debt_gdp"] - dd["d_lag"]
    dd["sfa"] = dd["delta_d"] - ((dd["r"] - dd["g"]) / (1 + dd["g"])) * dd["d_lag"] + dd["primary_balance_gdp"]
    sfa = dd[["iso3", "year", "sfa"]].dropna().rename(columns={"sfa": "value"})
    sfa["variable"] = "debt_dynamics_residual"
    sfa["date"] = pd.to_datetime(dict(year=sfa["year"], month=12, day=31))
    sfa["source"] = "derived"
    sfa["source_code"] = "SFA = dD - ((r-g)/(1+g))D(-1) + pb"
    sfa["source_detail"] = "Resíduo stock-flow adjustment"
    sfa["is_forecast"] = False
    sfa["quality_flag"] = "validation"
    sfa = _attach(sfa, "A")
    ann = pd.concat([ann, sfa], ignore_index=True)

    # Capital/produto e produto por trabalhador
    pwt = ann[ann.variable.isin(["capital_stock", "employment", "tfp"])]
    k = pwt[pwt.variable == "capital_stock"][["iso3", "year", "value"]].rename(columns={"value": "k"})
    rg = parsed["pwt"][parsed["pwt"].variable == "rgdpna_pwt"][["iso3", "year", "value"]].rename(columns={"value": "rgdpna"})
    kor = k.merge(rg, on=["iso3", "year"], how="inner")
    kor["value"] = kor["k"] / kor["rgdpna"]
    kor["variable"] = "capital_output_ratio"
    kor["date"] = pd.to_datetime(dict(year=kor["year"], month=12, day=31))
    kor["source"] = "derived"
    kor["source_code"] = "rnna/rgdpna"
    kor["source_detail"] = "PWT 10.01, ambos em USD 2017"
    kor["is_forecast"] = False
    kor["quality_flag"] = "derived"
    kor = _attach(kor, "A")
    ann = pd.concat([ann, kor], ignore_index=True)

    y = ann[ann.variable == "gdp_real"][["iso3", "year", "value"]].rename(columns={"value": "y"})
    emp = ann[ann.variable == "employment"][["iso3", "year", "value"]].rename(columns={"value": "n"})
    yw = y.merge(emp, on=["iso3", "year"], how="inner")
    yw["value"] = yw["y"] / yw["n"]
    yw["variable"] = "output_per_worker"
    yw["date"] = pd.to_datetime(dict(year=yw["year"], month=12, day=31))
    yw["source"] = "derived"
    yw["source_code"] = "rGDP/emp"
    yw["source_detail"] = "GMD/PWT; unidades nacionais por trabalhador"
    yw["is_forecast"] = False
    yw["quality_flag"] = "proxy"
    yw = _attach(yw, "A")
    ann = pd.concat([ann, yw], ignore_index=True)

    # PIB mundial em crescimento
    wg = ann[(ann.variable == "world_gdp_real") & (ann.iso3 == "WLD")][["year", "value"]].sort_values("year")
    wg["value"] = 100 * np.log(wg["value"]).diff()
    wg["variable"] = "world_gdp_growth"
    wg["iso3"] = "WLD"
    wg["date"] = pd.to_datetime(dict(year=wg["year"], month=12, day=31))
    wg["source"] = "derived"
    wg["source_code"] = "100*dlog(world_gdp_real)"
    wg["source_detail"] = "WDI WLD"
    wg["is_forecast"] = False
    wg["quality_flag"] = "derived"
    wg = _attach(wg, "A")
    ann = pd.concat([ann, wg], ignore_index=True)

    return _finalize(ann)


def _add_heterodox(ann: pd.DataFrame, parsed: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Incorpora os 4 blocos heterodoxos e as derivadas de PWT/GMD."""
    e = parsed.get("wdi_extra", pd.DataFrame()).copy()
    if e.empty:
        return ann
    e = e[(e.year >= settings.ANNUAL_START) & (e.year <= settings.ANNUAL_END)].copy()
    e["date"] = pd.to_datetime(dict(year=e["year"], month=12, day=31))
    e["is_forecast"] = e["year"] > settings.ANNUAL_ACTUAL_END
    e["quality_flag"] = np.where(e["year"] == 2026, "preliminary", "ok")
    e = _attach(e, "A")

    def base_frame(var: str) -> pd.DataFrame:
        return e[e.variable == var][["iso3", "year", "date", "value"]].rename(
            columns={"value": var})

    # co2_per_gdp = CO2 total (Mt) / PIB nominal USD (milhões) * 1000 -> kg/USD
    co2 = base_frame("co2_total_mt")
    gdp = ann[ann.variable == "gdp_nominal_usd"][["iso3", "year", "value"]].rename(
        columns={"value": "gdp_usd_mm"})
    m = co2.merge(gdp, on=["iso3", "year"], how="inner")
    m["value"] = m["co2_total_mt"] * 1000.0 / m["gdp_usd_mm"].replace(0, np.nan)
    co2_gdp = m[["iso3", "year", "date", "value"]].dropna()
    co2_gdp["variable"] = "co2_per_gdp"
    co2_gdp["source"] = "derived"
    co2_gdp["source_code"] = "co2_total_mt*1000/gdp_nominal_usd"
    co2_gdp["source_detail"] = "WDI EN.GHG.CO2.MT.CE.AR5 / GMD nGDP/USDfx"
    co2_gdp["is_forecast"] = False
    co2_gdp["quality_flag"] = "derived"

    # profit_share = 1 - labor_share; wage_bill_gdp = 100 * labor_share
    ls = ann[ann.variable == "labor_share"][["iso3", "year", "date", "value"]].rename(
        columns={"value": "labor_share"})
    profit = ls.copy(); profit["value"] = 1.0 - profit["labor_share"]
    profit["variable"] = "profit_share"; profit["source"] = "derived"
    profit["source_code"] = "1 - labor_share"; profit["source_detail"] = "PWT 10.01 (labsh)"
    profit["is_forecast"] = False; profit["quality_flag"] = "derived"
    wage = ls.copy(); wage["value"] = 100.0 * wage["labor_share"]
    wage["variable"] = "wage_bill_gdp"; wage["source"] = "derived"
    wage["source_code"] = "100 * labor_share"; wage["source_detail"] = "PWT 10.01 (labsh)"
    wage["is_forecast"] = False; wage["quality_flag"] = "derived"

    # fuel_ores_exports_pct = fuel + ores/metals (soma estrita)
    fuel = base_frame("fuel_exports_pct")
    ores = base_frame("ores_metals_exports_pct")
    fo = fuel.merge(ores, on=["iso3", "year", "date"], suffixes=("_fuel", "_ores"))
    fo["value"] = fo["fuel_exports_pct"] + fo["ores_metals_exports_pct"]
    fo = fo[["iso3", "year", "date", "value"]].dropna()
    fo["variable"] = "fuel_ores_exports_pct"
    fo["source"] = "derived"
    fo["source_code"] = "TX.VAL.FUEL.ZS.UN + TX.VAL.MMTL.ZS.UN"
    fo["source_detail"] = "WDI; soma dos dois componentes"
    fo["is_forecast"] = False; fo["quality_flag"] = "derived"

    keep = e[~e.variable.isin(["co2_total_mt", "fuel_exports_pct", "ores_metals_exports_pct"])]
    derived = pd.concat([co2_gdp, profit, wage, fo], ignore_index=True)
    derived = _attach(derived, "A")
    return pd.concat([ann, keep, derived], ignore_index=True)


# -----------------------------------------------------------------------------
# TRIMESTRAL
# -----------------------------------------------------------------------------
def _quarter(dates: pd.Series) -> pd.Series:
    return pd.to_datetime(dates).dt.to_period("Q").dt.end_time.dt.normalize()


def _fred_quarterly(parsed: dict[str, pd.DataFrame]) -> pd.DataFrame:
    f = parsed["fred"].copy()
    f = f[f.iso3.isin(settings.QUARTERLY_COUNTRIES) | (f.iso3 == "WLD")]
    f["quarter"] = _quarter(f["date"])
    out = []
    for (iso, var), d in f.groupby(["iso3", "variable"]):
        if var == "core_inflation" and iso == "USA":
            # CPILFESL é índice: converter para variação 12 meses
            s = d.groupby("quarter")["value"].mean().sort_index()
            s = 100 * (s / s.shift(4) - 1)
            g = s.dropna().reset_index()
            g.columns = ["quarter", "value"]
        else:
            g = d.groupby("quarter", as_index=False)["value"].mean()
        g["iso3"] = iso
        g["variable"] = var
        out.append(g)
    df = pd.concat(out, ignore_index=True)
    df["date"] = df["quarter"]
    df["year"] = df["date"].dt.year
    df["source"] = "FRED"
    df["source_code"] = "FRED/OECD-MEI/BIS"
    df["source_detail"] = "Séries trimestrais OECD-MEI e BIS distribuídas pelo FRED"
    return df


def _bcb_quarterly(parsed: dict[str, pd.DataFrame]) -> pd.DataFrame:
    b = parsed["bcb"].copy()
    b = b[b.iso3 == "BRA"]
    b["quarter"] = _quarter(b["date"])
    out = []
    for var, d in b.groupby("variable"):
        if var in ("inflation", "core_inflation"):
            # % mensal -> índice -> variação 12 meses no trimestre
            m = d.groupby("date")["value"].mean().sort_index()
            idx = (1 + m / 100).cumprod() * 100
            q = idx.groupby(idx.index.to_period("Q")).last()
            q.index = q.index.to_timestamp(how="end").normalize()
            s = 100 * (q / q.shift(4) - 1)
            g = s.dropna().rename("value").reset_index()
            g.columns = ["quarter", "value"]
        elif var == "primary_balance_brl":
            g = d.groupby("quarter", as_index=False)["value"].sum()
        else:
            g = d.groupby("quarter", as_index=False)["value"].mean()
        g["iso3"] = "BRA"
        g["variable"] = var
        out.append(g)
    df = pd.concat(out, ignore_index=True)
    df["date"] = df["quarter"]
    df["year"] = df["date"].dt.year
    df["source"] = "BCB"
    df["source_code"] = "BCB SGS"
    df["source_detail"] = "Banco Central do Brasil, SGS"
    return df


def _ibge_quarterly(parsed: dict[str, pd.DataFrame]) -> pd.DataFrame:
    i = parsed["ibge"].copy()
    i = i[i.variable.isin(["consumption_real", "gov_exp_real", "investment_real",
                           "exports_real", "imports_real", "gdp_nominal"])]
    i["quarter"] = _quarter(i["date"])
    out = i.groupby(["iso3", "variable", "quarter"], as_index=False)["value"].mean()
    out["date"] = out["quarter"]
    out["year"] = out["date"].dt.year
    # deflator implícito = 100 * nominal / real (real encadeado 1995)
    nom = out[out.variable == "gdp_nominal"][["quarter", "value"]].rename(columns={"value": "nom"})
    real = parsed["ibge"][parsed["ibge"].variable == "gdp_real"].copy()
    real["quarter"] = _quarter(real["date"])
    real = real.groupby("quarter", as_index=False)["value"].mean().rename(columns={"value": "real"})
    m = nom.merge(real, on="quarter")
    m["value"] = 100 * m["nom"] / m["real"]
    m["iso3"] = "BRA"
    m["variable"] = "gdp_deflator"
    m["date"] = m["quarter"]
    m["year"] = m["date"].dt.year
    out = pd.concat([out, m[["iso3", "variable", "date", "year", "value"]]], ignore_index=True)
    out["source"] = "IBGE"
    out["source_code"] = "IBGE SIDRA 6612/1846"
    out["source_detail"] = "Contas Nacionais Trimestrais"
    return out


def _focus_quarterly(parsed: dict[str, pd.DataFrame]) -> pd.DataFrame:
    f = parsed["focus"].copy()
    if f.empty:
        return pd.DataFrame()
    f = f[(f.variable == "inflation_expectations")]
    if "indicador" in f.columns:
        f = f[f.indicador == "IPCA"]
    if "suavizada" in f.columns:
        f = f[f.suavizada == "N"]
    if "base_calculo" in f.columns:
        f = f[f.base_calculo == 0]
    f["quarter"] = _quarter(f["date"])
    monthly = f.groupby(["quarter", "date"], as_index=False)["value"].median()
    out = monthly.groupby("quarter", as_index=False)["value"].mean()
    out["iso3"] = "BRA"
    out["variable"] = "inflation_expectations"
    out["date"] = out["quarter"]
    out["year"] = out["date"].dt.year
    out["source"] = "BCB_FOCUS"
    out["source_code"] = "ExpectativasMercadoInflacao12Meses"
    out["source_detail"] = "BCB Focus"
    return out


def _hp_quarterly(df: pd.DataFrame, var: str = "gdp_real") -> tuple[pd.DataFrame, pd.DataFrame]:
    pot, gap = [], []
    for iso, d in df[df.variable == var].groupby("iso3"):
        s = d.set_index("date")["value"].sort_index()
        s = s[~s.index.duplicated()]
        if len(s) < 20:
            continue
        s = s.asfreq("QE")
        s = s.interpolate(limit_area="inside").dropna()
        if len(s) < 20:
            continue
        cycle, trend = hpfilter(np.log(s), lamb=1600)
        for dt in s.index:
            pot.append((iso, dt, float(np.exp(trend.loc[dt]))))
            gap.append((iso, dt, float(100 * (np.log(s.loc[dt]) - trend.loc[dt]))))
    p = pd.DataFrame(pot, columns=["iso3", "date", "value"])
    g = pd.DataFrame(gap, columns=["iso3", "date", "value"])
    for x in (p, g):
        x["year"] = x["date"].dt.year
    return p, g


def build_quarterly(parsed: dict[str, pd.DataFrame]) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    fred = _fred_quarterly(parsed)
    frames.append(fred)
    frames.append(_bcb_quarterly(parsed))
    frames.append(_ibge_quarterly(parsed))
    foc = _focus_quarterly(parsed)
    if not foc.empty:
        frames.append(foc)
    q = pd.concat(frames, ignore_index=True)
    q = q[q.date.between(pd.Timestamp("1995-03-31"), pd.Timestamp("2026-12-31"))]

    # PIB real do Brasil: usar FRED (SA) e não a série do IBGE (NSA)
    q = q[~((q.iso3 == "BRA") & (q.variable == "gdp_real") & (q.source == "IBGE"))]

    q = _attach(q, "Q")
    q["seasonal_adjustment"] = np.where(
        q.variable.isin(["gdp_real", "unemployment", "consumption_real", "investment_real",
                         "gov_exp_real", "exports_real", "imports_real"]), "SA", "NSA")

    # Crescimento trimestral (SAAR)
    growth = []
    for iso, d in q[q.variable == "gdp_real"].groupby("iso3"):
        d = d.sort_values("date")
        d["value"] = 400 * np.log(d["value"]).diff()
        d["variable"] = "gdp_real_growth"
        d["source"] = "derived"
        d["source_code"] = "400*dlog(gdp_real)"
        d["source_detail"] = "OECD-MEI via FRED"
        growth.append(d)
    if growth:
        g = pd.concat(growth, ignore_index=True)
        g = _attach(g, "Q")
        g["seasonal_adjustment"] = "SA"
        q = pd.concat([q, g], ignore_index=True)

    pot, gap = _hp_quarterly(q)
    for df, var in ((pot, "potential_gdp"), (gap, "output_gap")):
        df = df.copy()
        df["variable"] = var
        df["source"] = "derived"
        df["source_code"] = "HP(log(gdp_real), lambda=1600)"
        df["source_detail"] = "Filtro HP bicaudal"
        df["quality_flag"] = "hp_filter"
        df = _attach(df, "Q")
        df["seasonal_adjustment"] = "SA"
        q = pd.concat([q, df], ignore_index=True)

    # Juro real ex ante Brasil
    pol = q[(q.iso3 == "BRA") & (q.variable == "policy_rate")][["date", "value"]].rename(columns={"value": "i"})
    exp = q[(q.iso3 == "BRA") & (q.variable == "inflation_expectations")][["date", "value"]].rename(columns={"value": "e"})
    rr = pol.merge(exp, on="date", how="inner")
    if not rr.empty:
        rr["value"] = rr["i"] - rr["e"]
        rr["iso3"] = "BRA"
        rr["variable"] = "real_rate_ex_ante"
        rr["year"] = rr.date.dt.year
        rr["source"] = "derived"
        rr["source_code"] = "policy_rate - inflation_expectations"
        rr["source_detail"] = "Fisher ex ante"
        rr["quality_flag"] = "derived"
        rr = _attach(rr, "Q")
        rr["seasonal_adjustment"] = "NSA"
        q = pd.concat([q, rr], ignore_index=True)

    # Metas anuais aplicadas aos trimestres
    tgt = q[q.variable == "inflation_target"]
    q = q[q.variable != "inflation_target"]

    q["is_forecast"] = False
    q["quality_flag"] = np.where(q["date"] > pd.Timestamp("2025-12-31"), "preliminary",
                                 q.get("quality_flag", "ok"))
    q.loc[q.variable.isin(["potential_gdp", "output_gap"]), "quality_flag"] = "hp_filter"
    q = _finalize(q)
    return q


# -----------------------------------------------------------------------------
# REGIMES E SAÍDAS
# -----------------------------------------------------------------------------
def attach_regimes(df: pd.DataFrame) -> pd.DataFrame:
    r = regimes.build_all()
    meta = r["metadata"]
    df = df.drop(columns=["regime_dummy"], errors="ignore")
    if df.freq.iloc[0] == "A":
        wide = r["annual"]
        mapping = regimes.active_strings(wide, "annual")
        mapping.index.names = ["iso3", "year"]
        df = df.merge(mapping.rename("regime_dummy"), left_on=["iso3", "year"],
                      right_index=True, how="left")
    else:
        # trimestral: a coluna `quarter` não existe no df final; usar period
        wide = r["quarterly"]
        mapping = regimes.active_strings(wide, "quarterly")
        mapping.index.names = ["iso3", "quarter"]
        q = pd.PeriodIndex(df["date"], freq="Q").astype(str)
        df = df.assign(_q=q).merge(mapping.rename("regime_dummy"),
                                   left_on=["iso3", "_q"], right_index=True, how="left").drop(columns="_q")
    df["regime_dummy"] = df["regime_dummy"].fillna("")
    return df


def write_outputs(annual: pd.DataFrame, quarterly: pd.DataFrame) -> None:
    long = pd.concat([annual, quarterly], ignore_index=True)
    long.to_parquet(settings.PROCESSED / "macro_long.parquet", index=False)
    long.to_csv(settings.PROCESSED / "macro_long.csv", index=False, encoding="utf-8-sig")
    annual.to_parquet(settings.PROCESSED / "macro_annual_long.parquet", index=False)
    quarterly.to_parquet(settings.PROCESSED / "macro_quarterly_long.parquet", index=False)
    # wide por país
    for freq, df in (("annual", annual), ("quarterly", quarterly)):
        folder = settings.PROCESSED / "wide" / freq
        folder.mkdir(parents=True, exist_ok=True)
        for iso, d in df.groupby("iso3"):
            w = d.pivot_table(index="date", columns="variable", values="value", aggfunc="last").sort_index()
            w.to_csv(folder / f"{iso}.csv", encoding="utf-8-sig")
    # painel wide combinado
    annual.pivot_table(index=["iso3", "date"], columns="variable", values="value", aggfunc="last") \
        .to_parquet(settings.PROCESSED / "wide" / "annual_panel.parquet")
    quarterly.pivot_table(index=["iso3", "date"], columns="variable", values="value", aggfunc="last") \
        .to_parquet(settings.PROCESSED / "wide" / "quarterly_panel.parquet")


if __name__ == "__main__":
    parsed = {n: pd.read_parquet(settings.RAW / f"parsed_{n}.parquet")
              for n in ("gmd", "wdi", "wdi_extra", "weo", "pwt", "fred", "bcb", "ibge", "focus")}
    a = build_annual(parsed)
    q = build_quarterly(parsed)
    a = attach_regimes(a)
    q = attach_regimes(q)
    write_outputs(a, q)
    print("anual", a.shape, "trimestral", q.shape)
    print(a.groupby("freq").variable.nunique(), q.groupby("freq").variable.nunique())
