"""Configuração central do projeto."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config"
DATA = ROOT / "data"
RAW = DATA / "raw"
PROCESSED = DATA / "processed"
REPORTS = ROOT / "reports"
FIGURES = REPORTS / "figures"
TABLES = REPORTS / "tables"
DOCS = ROOT / "docs"

for _p in (RAW, PROCESSED, REPORTS, FIGURES, TABLES, DOCS, RAW / "gmd", RAW / "wdi",
           RAW / "weo", RAW / "pwt", RAW / "fred", RAW / "bcb", RAW / "ibge", RAW / "focus"):
    _p.mkdir(parents=True, exist_ok=True)

VERSION = "2.0.0"
ANNUAL_START = 1960
ANNUAL_END = 2026          # 2026 = ano em curso; marcado como preliminar
ANNUAL_ACTUAL_END = 2025   # última observação anual consolidada
QUARTERLY_START = "1995-01-01"
QUARTERLY_END = "2026-12-31"
EXTRACTION_TS = os.environ.get("MACRO_EXTRACTION_TS") or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read_yaml(name: str) -> dict[str, Any]:
    with open(CONFIG / name, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


COUNTRIES_YML = _read_yaml("countries.yml")
SOURCES_YML = _read_yaml("sources.yml")
REGIMES_YML = _read_yaml("regimes.yml")

COUNTRIES = [c["iso3"] for c in COUNTRIES_YML["countries"]]
COUNTRY_META = {c["iso3"]: c for c in COUNTRIES_YML["countries"]}
AGGREGATES = [a["iso3"] for a in COUNTRIES_YML.get("aggregates", [])]
COUNTRIES_ALL = COUNTRIES + AGGREGATES
QUARTERLY_COUNTRIES = [c["iso3"] for c in COUNTRIES_YML["countries"] if c.get("quarterly")]
GROUPS = {g: v["members"] for g, v in COUNTRIES_YML["groups"].items()}
GROUP_META = COUNTRIES_YML["groups"]


def load_variables() -> pd.DataFrame:
    """Carrega o dicionário canônico de variáveis (PSV)."""
    df = pd.read_csv(CONFIG / "variables.psv", sep="|", dtype=str, keep_default_na=False)
    df.columns = [c.strip() for c in df.columns]
    for col in ("id", "freq", "label", "unit", "source", "code", "transform", "role",
                "models", "coverage_note", "notes"):
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].astype(str).str.strip()
    return df


VARIABLES = load_variables()

# Metas de inflação (%, a.a.) por país e ano — usadas na dummy de regime e em r*
# Fontes: BCB (Brasil), bancos centrais nacionais, IMF AREAER. None = sem meta explícita.
INFLATION_TARGETS: dict[str, dict[int, float]] = {
    "BRA": {1999: 8.0, 2000: 6.0, 2001: 4.0, 2002: 3.5, 2003: 4.0, 2004: 5.5, 2005: 4.5,
            2006: 4.5, 2007: 4.5, 2008: 4.5, 2009: 4.5, 2010: 4.5, 2011: 4.5, 2012: 4.5,
            2013: 4.5, 2014: 4.5, 2015: 4.5, 2016: 4.5, 2017: 4.5, 2018: 4.5, 2019: 4.25,
            2020: 4.0, 2021: 3.75, 2022: 3.5, 2023: 3.25, 2024: 3.0, 2025: 3.0, 2026: 3.0},
    "MEX": {2001: 8.0, 2002: 4.5, 2003: 3.0, 2004: 3.0, 2005: 3.0, 2006: 3.0, 2007: 3.0,
            2008: 3.0, 2009: 3.0, 2010: 3.0, 2011: 3.0, 2012: 3.0, 2013: 3.0, 2014: 3.0,
            2015: 3.0, 2016: 3.0, 2017: 3.0, 2018: 3.0, 2019: 3.0, 2020: 3.0, 2021: 3.0,
            2022: 3.0, 2023: 3.0, 2024: 3.0, 2025: 3.0, 2026: 3.0},
    "CHL": {1999: 4.5, 2000: 3.5, 2001: 3.5, 2002: 3.0, 2003: 3.0, 2004: 2.5, 2005: 3.0,
            2006: 3.0, 2007: 3.0, 2008: 4.0, 2009: 3.0, 2010: 3.0, 2011: 3.0, 2012: 3.0,
            2013: 3.0, 2014: 3.0, 2015: 3.0, 2016: 3.0, 2017: 3.0, 2018: 3.0, 2019: 3.0,
            2020: 3.0, 2021: 3.0, 2022: 3.0, 2023: 3.0, 2024: 3.0, 2025: 3.0, 2026: 3.0},
    "COL": {1999: 15.0, 2000: 10.0, 2001: 8.0, 2002: 6.0, 2003: 5.5, 2004: 5.5, 2005: 5.0,
            2006: 4.5, 2007: 4.0, 2008: 4.0, 2009: 4.0, 2010: 3.0, 2011: 3.0, 2012: 3.0,
            2013: 3.0, 2014: 3.0, 2015: 3.0, 2016: 3.0, 2017: 3.0, 2018: 3.0, 2019: 3.0,
            2020: 3.0, 2021: 3.0, 2022: 3.0, 2023: 3.0, 2024: 3.0, 2025: 3.0, 2026: 3.0},
    "PER": {2002: 2.5, 2003: 2.5, 2004: 2.5, 2005: 2.5, 2006: 2.5, 2007: 2.0, 2008: 2.0,
            2009: 2.0, 2010: 2.0, 2011: 2.0, 2012: 2.0, 2013: 2.0, 2014: 2.0, 2015: 2.0,
            2016: 2.0, 2017: 2.0, 2018: 2.0, 2019: 2.0, 2020: 2.0, 2021: 2.0, 2022: 2.0,
            2023: 2.0, 2024: 2.0, 2025: 2.0, 2026: 2.0},
    "ZAF": {2000: 3.0, 2001: 3.0, 2002: 3.0, 2003: 3.0, 2004: 3.0, 2005: 3.0, 2006: 3.0,
            2007: 3.0, 2008: 3.0, 2009: 3.0, 2010: 3.0, 2011: 3.0, 2012: 3.0, 2013: 3.0,
            2014: 3.0, 2015: 3.0, 2016: 3.0, 2017: 3.0, 2018: 3.0, 2019: 3.0, 2020: 3.0,
            2021: 3.0, 2022: 3.0, 2023: 3.0, 2024: 3.0, 2025: 3.0, 2026: 3.0},
    "TUR": {2006: 5.0, 2007: 4.0, 2008: 4.0, 2009: 7.5, 2010: 6.5, 2011: 5.5, 2012: 5.0,
            2013: 5.0, 2014: 5.0, 2015: 5.0, 2016: 5.0, 2017: 5.0, 2018: 5.0, 2019: 5.0,
            2020: 5.0, 2021: 5.0, 2022: 5.0, 2023: 5.0, 2024: 5.0, 2025: 5.0, 2026: 5.0},
    "IDN": {2005: 6.0, 2006: 6.0, 2007: 6.0, 2008: 6.0, 2009: 5.0, 2010: 5.0, 2011: 5.0,
            2012: 5.0, 2013: 4.5, 2014: 4.5, 2015: 4.0, 2016: 4.0, 2017: 4.0, 2018: 3.5,
            2019: 3.5, 2020: 3.0, 2021: 3.0, 2022: 3.0, 2023: 3.0, 2024: 2.5, 2025: 2.5,
            2026: 2.5},
    "KOR": {1998: 4.0, 1999: 3.0, 2000: 2.5, 2001: 3.0, 2002: 3.0, 2003: 3.0, 2004: 3.0,
            2005: 3.0, 2006: 3.0, 2007: 3.0, 2008: 3.0, 2009: 3.0, 2010: 3.0, 2011: 3.0,
            2012: 3.0, 2013: 3.0, 2014: 3.0, 2015: 3.0, 2016: 2.0, 2017: 2.0, 2018: 2.0,
            2019: 2.0, 2020: 2.0, 2021: 2.0, 2022: 2.0, 2023: 2.0, 2024: 2.0, 2025: 2.0,
            2026: 2.0},
    "GBR": {1992: 2.5, 1993: 2.5, 1994: 2.5, 1995: 2.5, 1996: 2.5, 1997: 2.5, 1998: 2.5,
            1999: 2.5, 2000: 2.5, 2001: 2.5, 2002: 2.5, 2003: 2.5, 2004: 2.0, 2005: 2.0,
            2006: 2.0, 2007: 2.0, 2008: 2.0, 2009: 2.0, 2010: 2.0, 2011: 2.0, 2012: 2.0,
            2013: 2.0, 2014: 2.0, 2015: 2.0, 2016: 2.0, 2017: 2.0, 2018: 2.0, 2019: 2.0,
            2020: 2.0, 2021: 2.0, 2022: 2.0, 2023: 2.0, 2024: 2.0, 2025: 2.0, 2026: 2.0},
    "CAN": {1991: 3.0, 1992: 3.0, 1993: 3.0, 1994: 3.0, 1995: 3.0, 1996: 3.0, 1997: 3.0,
            1998: 3.0, 1999: 3.0, 2000: 3.0, 2001: 3.0, 2002: 3.0, 2003: 3.0, 2004: 3.0,
            2005: 3.0, 2006: 3.0, 2007: 3.0, 2008: 3.0, 2009: 3.0, 2010: 3.0, 2011: 3.0,
            2012: 3.0, 2013: 3.0, 2014: 3.0, 2015: 3.0, 2016: 3.0, 2017: 3.0, 2018: 3.0,
            2019: 3.0, 2020: 3.0, 2021: 3.0, 2022: 3.0, 2023: 3.0, 2024: 3.0, 2025: 3.0,
            2026: 3.0},
    "AUS": {1993: 3.0, 1994: 3.0, 1995: 3.0, 1996: 3.0, 1997: 3.0, 1998: 3.0, 1999: 3.0,
            2000: 3.0, 2001: 3.0, 2002: 3.0, 2003: 3.0, 2004: 3.0, 2005: 3.0, 2006: 3.0,
            2007: 3.0, 2008: 3.0, 2009: 3.0, 2010: 3.0, 2011: 3.0, 2012: 3.0, 2013: 3.0,
            2014: 3.0, 2015: 3.0, 2016: 3.0, 2017: 3.0, 2018: 3.0, 2019: 3.0, 2020: 3.0,
            2021: 3.0, 2022: 3.0, 2023: 3.0, 2024: 3.0, 2025: 3.0, 2026: 3.0},
    "IND": {2016: 5.0, 2017: 4.0, 2018: 4.0, 2019: 4.0, 2020: 4.0, 2021: 4.0, 2022: 4.0,
            2023: 4.0, 2024: 4.0, 2025: 4.0, 2026: 4.0},
    "USA": {2012: 2.0, 2013: 2.0, 2014: 2.0, 2015: 2.0, 2016: 2.0, 2017: 2.0, 2018: 2.0,
            2019: 2.0, 2020: 2.0, 2021: 2.0, 2022: 2.0, 2023: 2.0, 2024: 2.0, 2025: 2.0,
            2026: 2.0},
    "JPN": {2013: 2.0, 2014: 2.0, 2015: 2.0, 2016: 2.0, 2017: 2.0, 2018: 2.0, 2019: 2.0,
            2020: 2.0, 2021: 2.0, 2022: 2.0, 2023: 2.0, 2024: 2.0, 2025: 2.0, 2026: 2.0},
}
# Área do euro: meta do BCE de 2% (desde 2003); Alemanha/França/Itália herdam.
for _c in ("DEU", "FRA", "ITA", "EU"):
    INFLATION_TARGETS[_c] = {y: 2.0 for y in range(2003, 2027)}
# Argentina: meta 2016–2018 (regime interrompido)
INFLATION_TARGETS["ARG"] = {2016: 25.0, 2017: 17.0, 2018: 15.0}
