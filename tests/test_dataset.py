import pandas as pd
from macrodata import settings


def test_schema_and_duplicates():
    a = pd.read_parquet(settings.PROCESSED / "macro_annual_long.parquet")
    q = pd.read_parquet(settings.PROCESSED / "macro_quarterly_long.parquet")
    for df, freq in ((a, "A"), (q, "Q")):
        assert df.freq.unique().tolist() == [freq]
        assert not df.duplicated(["iso3", "date", "variable"]).any()
        assert df.value.notna().all()
        assert df.date.notna().all()
        for col in ("iso3", "variable", "unit", "source", "role", "regime_dummy"):
            assert col in df.columns


def test_annual_dates():
    a = pd.read_parquet(settings.PROCESSED / "macro_annual_long.parquet")
    assert (a.date.dt.month == 12).all()
    assert (a.date.dt.day == 31).all()


def test_regime_matrices():
    r = pd.read_csv(settings.PROCESSED / "regime_matrix_annual.csv")
    assert r.shape[0] == 1474
    assert r.shape[1] >= 90
    assert set(r.drop(columns=["iso3", "year"]).stack().unique()).issubset({0, 1})
    q = pd.read_csv(settings.PROCESSED / "regime_matrix_quarterly.csv")
    assert q.shape[0] == 2048


def test_capital_stock_uses_rnna():
    a = pd.read_parquet(settings.PROCESSED / "macro_annual_long.parquet")
    v = a[(a.iso3 == "BRA") & (a.year == 2019) & (a.variable == "capital_stock")]["value"].iloc[0]
    # rnna (milhões USD 2017) ~ 12,7 milhões; rkna (índice 2017=1) ~ 1,02
    assert v > 1_000_000
