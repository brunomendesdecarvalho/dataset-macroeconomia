import numpy as np
import pandas as pd
from macrodata import settings


def test_nominal_real_deflator():
    a = pd.read_parquet(settings.PROCESSED / "macro_annual_long.parquet")
    p = a.pivot_table(index=["iso3", "year"], columns="variable", values="value", aggfunc="last")
    r = p.gdp_nominal / (p.gdp_real * p.gdp_deflator / 100) - 1
    assert np.nanmax(np.abs(r)) < 1e-4


def test_components_identity_median():
    a = pd.read_parquet(settings.PROCESSED / "macro_annual_long.parquet")
    p = a.pivot_table(index=["iso3", "year"], columns="variable", values="value", aggfunc="last")
    resid = 100 - (p.consumption_gdp + p.investment_gdp + p.net_exports_gdp)
    assert abs(np.nanmedian(resid)) < 2.0


def test_dsge_measurement_table():
    m = pd.read_csv(settings.CONFIG / "dsge_measurement.psv", sep="|")
    assert {"observable", "model_variable", "measurement_equation", "shock"}.issubset(m.columns)
    assert len(m) >= 10
