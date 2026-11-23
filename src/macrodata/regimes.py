"""Construção das dummies de regime país-tempo (anual e trimestral)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd

from . import settings


@dataclass
class Event:
    id: str
    name: str
    kind: str
    scope: str
    countries: list[str]
    start: pd.Timestamp
    end: pd.Timestamp
    permanent: bool
    point: bool
    freq: list[str]
    source: str
    url: str
    variables: list[str]
    models: list[str]
    description: str


def _ts(value: str, end: bool = False) -> pd.Timestamp:
    ts = pd.to_datetime(value, format="%Y-%m", errors="coerce")
    if pd.isna(ts):
        ts = pd.to_datetime(value, errors="coerce")
    if pd.isna(ts):
        raise ValueError(f"data inválida em regimes.yml: {value}")
    if end:
        return ts + pd.offsets.MonthEnd(0)
    return ts


def load_events() -> list[Event]:
    events: list[Event] = []
    for raw in settings.REGIMES_YML["events"]:
        countries = raw.get("countries", [])
        if countries == ["ALL"] or countries == "ALL":
            countries = list(settings.COUNTRIES)
        countries = list(dict.fromkeys(countries))
        start = _ts(str(raw["start"]))
        permanent = bool(raw.get("permanent", False))
        end = pd.Timestamp("2026-12-31") if permanent else _ts(str(raw.get("end", raw["start"])), end=True)
        if end < start:
            raise ValueError(f"evento {raw['id']} com fim antes do início")
        events.append(Event(
            id=raw["id"], name=raw.get("name", raw["id"]), kind=raw.get("kind", "other"),
            scope=raw.get("scope", "country"), countries=countries, start=start, end=end,
            permanent=permanent, point=bool(raw.get("point", False)),
            freq=[f.upper() for f in raw.get("freq", ["A", "Q"])],
            source=raw.get("source", ""), url=raw.get("url", ""),
            variables=raw.get("variables", []),
            models=raw.get("models", []),
            description=raw.get("name", raw["id"]),
        ))
    return events


def annual_matrix(start: int = 1960, end: int = 2026) -> pd.DataFrame:
    events = [e for e in load_events() if "A" in e.freq]
    years = list(range(start, end + 1))
    idx = pd.MultiIndex.from_product([settings.COUNTRIES, years], names=["iso3", "year"])
    mat = pd.DataFrame(0, index=idx, columns=[e.id for e in events], dtype="int8")
    for e in events:
        y0, y1 = max(e.start.year, start), min(e.end.year, end)
        if y1 < y0:
            continue
        for iso in e.countries:
            if iso not in settings.COUNTRIES:
                continue
            mat.loc[(iso, slice(y0, y1)), e.id] = 1
    return mat


def quarterly_matrix(start: str = "1995Q1", end: str = "2026Q4") -> pd.DataFrame:
    events = [e for e in load_events() if "Q" in e.freq]
    periods = pd.period_range(start=start, end=end, freq="Q")
    qends = periods.to_timestamp(how="end").normalize()
    idx = pd.MultiIndex.from_product([settings.QUARTERLY_COUNTRIES, periods.astype(str)],
                                     names=["iso3", "quarter"])
    mat = pd.DataFrame(0, index=idx, columns=[e.id for e in events], dtype="int8")
    for e in events:
        # um trimestre conta se o evento o intersecta em pelo menos 1 dia
        active = [str(p) for p, qs, qe in
                  zip(periods, periods.to_timestamp(how="start"), qends)
                  if (qe >= e.start.normalize()) and (qs <= e.end.normalize())]
        if not active:
            continue
        for iso in e.countries:
            if iso not in settings.QUARTERLY_COUNTRIES:
                continue
            mat.loc[(iso, active), e.id] = 1
    return mat


def metadata() -> pd.DataFrame:
    rows = []
    for e in load_events():
        rows.append({
            "dummy": e.id, "nome": e.name, "tipo": e.kind, "escopo": e.scope,
            "paises": ";".join(e.countries), "inicio": e.start.strftime("%Y-%m-%d"),
            "fim": ("permanente" if e.permanent else e.end.strftime("%Y-%m-%d")),
            "frequencias": ";".join(e.freq), "fonte": e.source, "url": e.url,
            "variaveis_afetadas": ";".join(e.variables),
            "modelos": ";".join(e.models),
        })
    return pd.DataFrame(rows)


def add_gmd_crises(annual: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Acrescenta as dummies de crise do GMD (cobertura histórica longa)."""
    g = pd.read_parquet(settings.RAW / "parsed_gmd.parquet")
    g = g[g.variable.isin(["banking_crisis", "currency_crisis", "sovereign_debt_crisis"])]
    g = g[(g.year >= 1960) & (g.year <= 2026)]
    wide = g.pivot_table(index=["iso3", "year"], columns="variable", values="value", aggfunc="max")
    wide = wide.reindex(annual.index).fillna(0).astype("int8")
    wide.columns = [f"gmd_{c}" for c in wide.columns]
    meta = pd.DataFrame([
        {"dummy": "gmd_banking_crisis", "nome": "Crise bancária (GMD)", "tipo": "crisis_domestic",
         "escopo": "país", "paises": "todos", "inicio": "1800", "fim": "2025",
         "frequencias": "A", "fonte": "GMD", "url": "https://www.globalmacrodb.org",
         "variaveis_afetadas": "credit_spread;gdp_real;policy_rate", "modelos": ""},
        {"dummy": "gmd_currency_crisis", "nome": "Crise cambial (GMD)", "tipo": "crisis_domestic",
         "escopo": "país", "paises": "todos", "inicio": "1800", "fim": "2025",
         "frequencias": "A", "fonte": "GMD", "url": "https://www.globalmacrodb.org",
         "variaveis_afetadas": "exchange_rate_nominal;reer", "modelos": "MF"},
        {"dummy": "gmd_sovereign_debt_crisis", "nome": "Crise de dívida soberana (GMD)", "tipo": "crisis_domestic",
         "escopo": "país", "paises": "todos", "inicio": "1800", "fim": "2025",
         "frequencias": "A", "fonte": "GMD", "url": "https://www.globalmacrodb.org",
         "variaveis_afetadas": "gov_debt_gdp;credit_spread", "modelos": ""},
    ])
    return pd.concat([annual, wide], axis=1), meta


def build_all() -> dict[str, pd.DataFrame]:
    ann = annual_matrix()
    ann, gmd_meta = add_gmd_crises(ann)
    qtr = quarterly_matrix()
    meta = pd.concat([metadata(), gmd_meta], ignore_index=True)
    return {"annual": ann, "quarterly": qtr, "metadata": meta}


def active_strings(wide: pd.DataFrame, level: str) -> pd.Series:
    """Série de strings 'd1|d2|...' por (iso3, year/quarter)."""
    def _join(row):
        return "|".join([c for c, v in row.items() if v == 1])
    return wide.apply(_join, axis=1)


if __name__ == "__main__":
    out = build_all()
    out["annual"].to_parquet(settings.PROCESSED / "regime_matrix_annual.parquet")
    out["quarterly"].to_parquet(settings.PROCESSED / "regime_matrix_quarterly.parquet")
    out["annual"].reset_index().to_csv(settings.PROCESSED / "regime_matrix_annual.csv", index=False, encoding="utf-8-sig")
    out["quarterly"].reset_index().to_csv(settings.PROCESSED / "regime_matrix_quarterly.csv", index=False, encoding="utf-8-sig")
    out["metadata"].to_csv(settings.PROCESSED / "regime_metadata.csv", index=False, encoding="utf-8-sig")
    print(out["annual"].shape, out["quarterly"].shape, out["metadata"].shape)
