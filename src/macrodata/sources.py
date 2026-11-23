"""Coletores das fontes primárias. Cada função retorna dados em formato longo
(tidy) com no mínimo: iso3, date/period, variable, value, source, source_code,
source_detail. Nenhuma transformação econômica é feita aqui — apenas parsing.
"""
from __future__ import annotations

import json
import re
from io import BytesIO
from urllib.parse import quote

import numpy as np
import pandas as pd

from . import settings
from .http import CachedFetcher, to_num

# -----------------------------------------------------------------------------
# 1. GMD — espinha dorsal anual
# -----------------------------------------------------------------------------
GMD_MAP: dict[str, str] = {
    "gdp_nominal": "nGDP",
    "gdp_real": "rGDP",
    "gdp_real_usd": "rGDP_USD",
    "gdp_real_pc": "rGDP_pc",
    "gdp_deflator": "deflator",
    "consumption_real": "cons",
    "consumption_gdp": "cons_GDP",
    "investment_real": "inv",
    "investment_gdp": "inv_GDP",
    "fixed_investment_real": "finv",
    "fixed_investment_gdp": "finv_GDP",
    "gov_exp_real": "govexp",
    "gov_exp_gdp": "govexp_GDP",
    "gov_revenue_gdp": "govrev_GDP",
    "tax_burden_gdp": "govtax_GDP",
    "gov_balance_gdp": "govdef_GDP",
    "gov_debt_gdp": "govdebt_GDP",
    "exports_gdp": "exports_GDP",
    "imports_gdp": "imports_GDP",
    "current_account_gdp": "CA_GDP",
    "cpi_index": "CPI",
    "inflation": "infl",
    "population": "pop",
    "unemployment": "unemp",
    "short_rate": "strate",
    "long_rate": "ltrate",
    "policy_rate": "cbrate",
    "m0": "M0",
    "m1": "M1",
    "m2": "M2",
    "m3": "M3",
    "exchange_rate_nominal": "USDfx",
    "reer": "REER",
    "hpi": "HPI",
    "banking_crisis": "BankingCrisis",
    "currency_crisis": "CurrencyCrisis",
    "sovereign_debt_crisis": "SovDebtCrisis",
}


def fetch_gmd() -> pd.DataFrame:
    path = settings.RAW / "gmd" / "data_final.parquet"
    if not path.exists():
        dta = settings.RAW / "gmd" / "data_final.dta"
        df = pd.read_stata(dta, convert_categoricals=False)
        df.to_parquet(path, index=False)
    df = pd.read_parquet(path)
    df = df.rename(columns={"ISO3": "iso3", "year": "year"})
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df = df[df["iso3"].isin(settings.COUNTRIES_ALL) & df["year"].notna()].copy()
    df["year"] = df["year"].astype(int)
    long = df.melt(id_vars=["iso3", "year"], value_vars=list(GMD_MAP.values()),
                   var_name="gmd_code", value_name="value")
    inv = {v: k for k, v in GMD_MAP.items()}
    long["variable"] = long["gmd_code"].map(inv)
    long["source"] = "GMD"
    long["source_code"] = long["gmd_code"]
    long["source_detail"] = "Global Macro Database 2026_09"
    long["freq"] = "A"
    long["value"] = pd.to_numeric(long["value"], errors="coerce")
    return long[["iso3", "year", "variable", "value", "source", "source_code",
                 "source_detail", "freq"]].dropna(subset=["value"])


# -----------------------------------------------------------------------------
# 2. WDI — complemento e validação
# -----------------------------------------------------------------------------
WDI_INDICATORS: dict[str, str] = {
    "gdp_real_wdi": "NY.GDP.MKTP.KD",
    "gdp_nominal_wdi": "NY.GDP.MKTP.CD",
    "gdp_deflator_wdi": "NY.GDP.DEFL.ZS",
    "gdp_growth_wdi": "NY.GDP.MKTP.KD.ZG",
    "inflation_wdi": "FP.CPI.TOTL.ZG",
    "unemployment_wdi": "SL.UEM.TOTL.ZS",
    "participation_rate": "SL.TLF.CACT.ZS",
    "population_wdi": "SP.POP.TOTL",
    "credit_private_gdp": "FS.AST.PRVT.GD.ZS",
    "gov_consumption_gdp": "NE.CON.GOVT.ZS",
    "gross_capital_formation_gdp": "NE.GDI.TOTL.ZS",
    "tax_revenue_gdp_wdi": "GC.TAX.TOTL.GD.ZS",
    "central_gov_debt_gdp": "GC.DOD.TOTL.GD.ZS",
    "consumption_gdp_wdi": "NE.CON.TOTL.ZS",
    "exports_gdp_wdi": "NE.EXP.GNFS.ZS",
    "imports_gdp_wdi": "NE.IMP.GNFS.ZS",
    "world_gdp_real": "NY.GDP.MKTP.KD",
}


def fetch_wdi(force: bool = False) -> pd.DataFrame:
    fetcher = CachedFetcher(force=force)
    frames = []
    for var, code in WDI_INDICATORS.items():
        url = (f"https://api.worldbank.org/v2/country/all/indicator/{code}"
               f"?format=json&per_page=20000&date=1960:2026")
        rel = f"wdi/{code}.json"
        try:
            payload = fetcher.get_json(url, rel)
        except Exception as exc:  # noqa: BLE001
            print(f"[WDI] falha {code}: {exc}")
            continue
        if not isinstance(payload, list) or len(payload) < 2 or payload[1] is None:
            print(f"[WDI] sem dados {code}")
            continue
        rows = payload[1]
        df = pd.DataFrame(rows)
        if df.empty:
            continue
        df["iso3"] = df["countryiso3code"].replace("", np.nan)
        df["iso3"] = df["iso3"].fillna(df["country"].apply(lambda x: x.get("id") if isinstance(x, dict) else None))
        df["year"] = pd.to_numeric(df["date"], errors="coerce")
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df = df[df["iso3"].isin(settings.COUNTRIES_ALL + ["WLD"]) & df["year"].notna()]
        df["variable"] = var
        df["source"] = "WDI"
        df["source_code"] = code
        df["source_detail"] = f"World Bank WDI {code}"
        df["freq"] = "A"
        frames.append(df[["iso3", "year", "variable", "value", "source", "source_code",
                          "source_detail", "freq"]])
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True).dropna(subset=["value"])


# -----------------------------------------------------------------------------
# 3. WEO — FMI DataMapper (pós-1980; projeções sinalizadas)
# -----------------------------------------------------------------------------
WEO_INDICATORS: dict[str, str] = {
    "gdp_growth_weo": "NGDP_RPCH",
    "gdp_nominal_usd_weo": "NGDPD",
    "inflation_weo": "PCPIPCH",
    "unemployment_weo": "LUR",
    "gov_debt_gdp_weo": "GGXWDG_NGDP",
    "primary_balance_gdp": "pb",
    "net_debt_gdp": "GGXWDN_G01_GDP_PT",
    "gdp_ppp_usd": "PPPGDP",
    "gov_balance_gdp_weo": "GGXCNL_G01_GDP_PT",
}


def fetch_weo(force: bool = False) -> pd.DataFrame:
    fetcher = CachedFetcher(force=force)
    frames = []
    for var, code in WEO_INDICATORS.items():
        url = f"https://www.imf.org/external/datamapper/api/v1/{code}"
        rel = f"weo/{code}.json"
        try:
            payload = fetcher.get_json(url, rel)
        except Exception as exc:  # noqa: BLE001
            print(f"[WEO] falha {code}: {exc}")
            continue
        values = payload.get("values", {}).get(code, {})
        rows = []
        for iso3, series in values.items():
            if iso3 not in settings.COUNTRIES_ALL:
                continue
            for year, value in series.items():
                try:
                    y = int(year)
                except (TypeError, ValueError):
                    continue
                if value is None:
                    continue
                rows.append((iso3, y, float(value)))
        df = pd.DataFrame(rows, columns=["iso3", "year", "value"])
        df["variable"] = var
        df["source"] = "WEO"
        df["source_code"] = code
        df["source_detail"] = f"IMF DataMapper {code}"
        df["freq"] = "A"
        frames.append(df)
    if not frames:
        return pd.DataFrame(columns=["iso3", "year", "variable", "value", "source",
                                     "source_code", "source_detail", "freq"])
    return pd.concat(frames, ignore_index=True)


# -----------------------------------------------------------------------------
# 4. PWT — capital, PTF, emprego, horas
# -----------------------------------------------------------------------------
PWT_MAP = {
    "capital_stock": "rnna",
    "tfp": "rtfpna",
    "employment": "emp",
    "hours_worked": "avh",
    "labor_share": "labsh",
    "human_capital": "hc",
    "rgdpna_pwt": "rgdpna",
}


def fetch_pwt() -> pd.DataFrame:
    df = pd.read_stata(settings.RAW / "gmd" / "pwt1001.dta", convert_categoricals=False)
    df = df.rename(columns={"countrycode": "iso3"})
    df = df[df["iso3"].isin(settings.COUNTRIES_ALL) & df["year"].between(1950, 2019)]
    long = df.melt(id_vars=["iso3", "year"], value_vars=list(PWT_MAP.values()),
                   var_name="pwt_code", value_name="value")
    inv = {v: k for k, v in PWT_MAP.items()}
    long["variable"] = long["pwt_code"].map(inv)
    long["source"] = "PWT"
    long["source_code"] = long["pwt_code"]
    long["source_detail"] = "Penn World Table 10.01"
    long["freq"] = "A"
    long["value"] = pd.to_numeric(long["value"], errors="coerce")
    return long[["iso3", "year", "variable", "value", "source", "source_code",
                 "source_detail", "freq"]].dropna(subset=["value"])


# -----------------------------------------------------------------------------
# 5. FRED — subamostra trimestral, commodities, VIX
# -----------------------------------------------------------------------------
FRED_QUARTERLY = [
    "BRA", "USA", "DEU", "GBR", "JPN", "CAN", "MEX", "AUS", "FRA", "ITA",
    "KOR", "ZAF", "TUR", "IDN", "ARG", "SAU",
]
FRED_FX = {
    "BRA": "DEXBZUS", "DEU": "DEXUSEU", "FRA": "DEXUSEU", "ITA": "DEXUSEU",
    "GBR": "DEXUSUK", "JPN": "DEXJPUS", "CAN": "DEXCAUS", "MEX": "DEXMXUS",
    "AUS": "DEXUSAL", "KOR": "DEXKOUS", "ZAF": "DEXSFUS", "TUR": "DEXTAUS",
    "IND": "DEXINUS", "CHN": "DEXCHUS",
}
FRED_INVERT = {"DEU", "FRA", "ITA", "GBR", "AUS"}  # séries cotadas em USD por LC
ISO2 = {"ARG": "AR", "AUS": "AU", "BRA": "BR", "CAN": "CA", "CHL": "CL", "CHN": "CN",
        "COL": "CO", "DEU": "DE", "FRA": "FR", "GBR": "GB", "IDN": "ID", "IND": "IN",
        "ITA": "IT", "JPN": "JP", "KOR": "KR", "MEX": "MX", "PER": "PE", "RUS": "RU",
        "SAU": "SA", "TUR": "TR", "USA": "US", "ZAF": "ZA", "EU": "EA"}


def fred_series_map() -> dict[str, dict[str, str]]:
    """Mapeia variável -> {iso3: series_id}."""
    m: dict[str, dict[str, str]] = {k: {} for k in
        ["gdp_real", "inflation", "unemployment", "short_rate", "long_rate",
         "reer", "exchange_rate_nominal", "gdp_nominal", "core_inflation"]}
    for iso in FRED_QUARTERLY:
        c2 = ISO2[iso]
        m["gdp_real"][iso] = f"NGDPRSAXDC{c2}Q"
        m["inflation"][iso] = f"CPALTT01{c2}Q659N"
        m["unemployment"][iso] = f"LRHUTTTT{c2}Q156S"
        m["short_rate"][iso] = f"IR3TIB01{c2}Q156N"
        m["long_rate"][iso] = f"IRLTLT01{c2}Q156N"
        m["reer"][iso] = f"RB{c2}BIS"
    m["exchange_rate_nominal"] = {iso: sid for iso, sid in FRED_FX.items()}
    m["core_inflation"] = {"USA": "CPILFESL"}
    # Brasil: IPCA cheio e núcleo vêm do BCB; não usar CPALTT01BRQ659N.
    m["inflation"].pop("BRA", None)
    return m


FRED_GLOBAL = {
    "commodity_price_index": "PALLFNFINDEXQ",
    "oil_price": "POILBREUSDM",
    "vix": "VIXCLS",
    "foreign_policy_rate": "DFF",
    "foreign_output": "GDPC1",
}


def fetch_fred(force: bool = False) -> pd.DataFrame:
    fetcher = CachedFetcher(force=force)
    frames = []

    def add(series_id: str, variable: str, iso3: str | None, freq: str, invert: bool = False):
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
        rel = f"fred/{series_id}.csv"
        try:
            df = fetcher.get_csv(url, rel)
        except Exception as exc:  # noqa: BLE001
            print(f"[FRED] falha {series_id}: {exc}")
            return
        date_col = "observation_date" if "observation_date" in df.columns else df.columns[0]
        val_col = series_id if series_id in df.columns else df.columns[1]
        out = pd.DataFrame({
            "date": pd.to_datetime(df[date_col], errors="coerce"),
            "value": to_num(df[val_col]),
        }).dropna()
        if out.empty:
            return
        if invert:
            out["value"] = 1.0 / out["value"].replace(0, np.nan)
        out["iso3"] = iso3 or "WLD"
        out["variable"] = variable
        out["source"] = "FRED"
        out["source_code"] = series_id
        out["source_detail"] = f"FRED {series_id}"
        out["freq"] = freq
        frames.append(out)

    for var, mapping in fred_series_map().items():
        for iso, sid in mapping.items():
            add(sid, var, iso, "Q", invert=(var == "exchange_rate_nominal" and iso in FRED_INVERT))
    for var, sid in FRED_GLOBAL.items():
        add(sid, var, None, "Q" if var in ("commodity_price_index", "foreign_output") else "M")
    add("MICH", "inflation_expectations", "USA", "M")
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True)
    df["year"] = df["date"].dt.year
    df["quarter"] = df["date"].dt.quarter
    return df


# -----------------------------------------------------------------------------
# 6. BCB — Brasil (SGS)
# -----------------------------------------------------------------------------
BCB_SERIES = {
    432: ("policy_rate", "daily", "% a.a."),
    1: ("exchange_rate_nominal", "daily", "BRL/USD"),
    433: ("inflation", "monthly", "% m.m."),
    11427: ("core_inflation", "monthly", "% m.m."),
    24369: ("unemployment", "monthly", "%"),
    5793: ("primary_balance_gdp", "monthly", "% do PIB (12m)"),
    4649: ("primary_balance_brl", "monthly", "R$ milhões"),
}


def fetch_bcb(force: bool = False) -> pd.DataFrame:
    fetcher = CachedFetcher(force=force)
    frames = []
    for code, (var, freq, unit) in BCB_SERIES.items():
        payload: list = []
        if freq == "daily":
            # SGS limita séries diárias a janelas de 10 anos
            windows = [(y, min(y + 9, 2026)) for y in range(1980, 2027, 10)]
            for (y0, y1) in windows:
                url = (f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{code}/dados"
                       f"?formato=json&dataInicial=01/01/{y0}&dataFinal=31/12/{y1}")
                rel = f"bcb/{code}_{y0}_{y1}.json"
                try:
                    part = fetcher.get_json(url, rel)
                except Exception as exc:  # noqa: BLE001
                    print(f"[BCB] falha {code} {y0}-{y1}: {exc}")
                    continue
                if isinstance(part, list):
                    payload.extend(part)
        else:
            url = (f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{code}/dados"
                   f"?formato=json&dataInicial=01/01/1980")
            rel = f"bcb/{code}.json"
            try:
                part = fetcher.get_json(url, rel)
                payload = part if isinstance(part, list) else []
            except Exception as exc:  # noqa: BLE001
                print(f"[BCB] falha {code}: {exc}")
                continue
        if not payload:
            print(f"[BCB] sem dados {code}")
            continue
        df = pd.DataFrame(payload)
        df["date"] = pd.to_datetime(df["data"], format="%d/%m/%Y", errors="coerce")
        df["value"] = to_num(df["valor"])
        df = df.dropna(subset=["date", "value"])
        df["iso3"] = "BRA"
        df["variable"] = var
        df["source"] = "BCB"
        df["source_code"] = str(code)
        df["source_detail"] = f"BCB SGS {code}"
        df["freq"] = freq
        df["unit_native"] = unit
        frames.append(df[["iso3", "date", "variable", "value", "source", "source_code",
                          "source_detail", "freq", "unit_native"]])
    return pd.concat(frames, ignore_index=True)


# -----------------------------------------------------------------------------
# 7. IBGE — Contas Nacionais Trimestrais e IPCA
# -----------------------------------------------------------------------------
IBGE_CNT = {
    "gdp_real": (6612, "9318", "90707"),
    "consumption_real": (6612, "9318", "93404"),
    "gov_exp_real": (6612, "9318", "93405"),
    "investment_real": (6612, "9318", "93406"),
    "exports_real": (6612, "9318", "93407"),
    "imports_real": (6612, "9318", "93408"),
    "gdp_nominal": (1846, "585", "90707"),
}


def _sidra_url(table: int, variable: str, category: str, periods: str = "-220") -> str:
    cls = quote(f"11255[{category}]", safe="")
    return (f"https://servicodados.ibge.gov.br/api/v3/agregados/{table}/periodos/{periods}"
            f"/variaveis/{variable}?localidades=N1[all]&classificacao={cls}")


def fetch_ibge(force: bool = False) -> pd.DataFrame:
    fetcher = CachedFetcher(force=force)
    frames = []
    for var, (table, variable, category) in IBGE_CNT.items():
        url = _sidra_url(table, variable, category)
        rel = f"ibge/{table}_{variable}_{category}.json"
        try:
            payload = fetcher.get_json(url, rel)
        except Exception as exc:  # noqa: BLE001
            print(f"[IBGE] falha {var}: {exc}")
            continue
        if not payload:
            continue
        serie = payload[0]["resultados"][0]["series"][0]["serie"]
        rows = []
        for period, value in serie.items():
            if value in ("...", "..", "-", ""):
                continue
            try:
                y, q = int(str(period)[:4]), int(str(period)[4:6])
            except (TypeError, ValueError):
                continue
            rows.append((pd.Timestamp(year=y, month=3 * q, day=1) + pd.offsets.MonthEnd(0),
                         float(value)))
        df = pd.DataFrame(rows, columns=["date", "value"])
        df["iso3"] = "BRA"
        df["variable"] = var
        df["source"] = "IBGE"
        df["source_code"] = f"SIDRA {table}/{variable}/{category}"
        df["source_detail"] = f"IBGE SIDRA tabela {table}"
        df["freq"] = "quarterly"
        frames.append(df)
    # IPCA mensal (número-índice, dez/1993=100)
    url = ("https://servicodados.ibge.gov.br/api/v3/agregados/1737/periodos/-600"
           "/variaveis/2266?localidades=N1[all]")
    try:
        payload = fetcher.get_json(url, "ibge/ipca_2266.json")
        serie = payload[0]["resultados"][0]["series"][0]["serie"]
        rows = []
        for period, value in serie.items():
            if value in ("...", "..", "-", ""):
                continue
            rows.append((pd.to_datetime(str(period), format="%Y%m"), float(value)))
        df = pd.DataFrame(rows, columns=["date", "value"])
        df["iso3"] = "BRA"
        df["variable"] = "cpi_index"
        df["source"] = "IBGE"
        df["source_code"] = "SIDRA 1737/2266"
        df["source_detail"] = "IBGE IPCA número-índice (dez/1993=100)"
        df["freq"] = "M"
        frames.append(df)
    except Exception as exc:  # noqa: BLE001
        print(f"[IBGE] falha IPCA: {exc}")
    return pd.concat(frames, ignore_index=True)


# -----------------------------------------------------------------------------
# 8. Focus — expectativas (Brasil)
# -----------------------------------------------------------------------------
def fetch_focus(force: bool = False) -> pd.DataFrame:
    fetcher = CachedFetcher(force=force)
    base = "https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/odata"
    frames = []
    endpoints = {
        "inflation_expectations": "ExpectativasMercadoInflacao12Meses",
        "policy_rate_expectations": "ExpectativasMercadoSelic",
        "exchange_rate_expectations": "ExpectativasMercadoCambio",
        "gdp_expectations": "ExpectativasMercadoPIB",
    }
    for var, ep in endpoints.items():
        url = (f"{base}/{ep}?$filter=Indicador%20eq%20%27IPCA%27&$orderby=Data%20asc"
               f"&$top=100000&$format=json") if var == "inflation_expectations" else \
              (f"{base}/{ep}?$orderby=Data%20asc&$top=100000&$format=json")
        rel = f"focus/{ep}.json"
        try:
            payload = fetcher.get_json(url, rel)
        except Exception as exc:  # noqa: BLE001
            print(f"[Focus] falha {ep}: {exc}")
            continue
        rows = payload.get("value", [])
        if not rows:
            continue
        df = pd.DataFrame(rows)
        date_col = next((c for c in ("Data", "data") if c in df.columns), None)
        value_col = next((c for c in ("Mediana", "Media", "media", "mediana") if c in df.columns), None)
        if not date_col or not value_col:
            continue
        out = pd.DataFrame({
            "date": pd.to_datetime(df[date_col], errors="coerce"),
            "value": pd.to_numeric(df[value_col], errors="coerce"),
        })
        if "Indicador" in df.columns:
            out["indicador"] = df["Indicador"].values
        if "Suavizada" in df.columns:
            out["suavizada"] = df["Suavizada"].values
        if "baseCalculo" in df.columns:
            out["base_calculo"] = df["baseCalculo"].values
        out = out.dropna(subset=["date", "value"])
        out["iso3"] = "BRA"
        out["variable"] = var
        out["source"] = "BCB_FOCUS"
        out["source_code"] = ep
        out["source_detail"] = f"BCB Focus {ep}"
        out["freq"] = "M"
        frames.append(out)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def fetch_all(force: bool = False) -> dict[str, pd.DataFrame]:
    out = {
        "gmd": fetch_gmd(),
        "wdi": fetch_wdi(force=force),
        "weo": fetch_weo(force=force),
        "pwt": fetch_pwt(),
        "fred": fetch_fred(force=force),
        "bcb": fetch_bcb(force=force),
        "ibge": fetch_ibge(force=force),
        "focus": fetch_focus(force=force),
    }
    for name, df in out.items():
        if df is None or df.empty:
            print(f"[fetch_all] {name}: VAZIO")
            continue
        path = settings.RAW / f"parsed_{name}.parquet"
        df.to_parquet(path, index=False)
        print(f"[fetch_all] {name}: {len(df):,} linhas -> {path.relative_to(settings.ROOT)}")
    return out


if __name__ == "__main__":
    fetch_all(force=False)
