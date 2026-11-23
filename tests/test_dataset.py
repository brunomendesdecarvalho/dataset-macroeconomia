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
        for col in ("iso3", "country", "date", "year", "period", "variable", "block",
                    "unit", "source", "source_code", "quality_flag", "is_forecast",
                    "role", "model", "regime_dummy"):
            assert col in df.columns
        assert not any("dsge" in c for c in df.columns)


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


def test_heterodox_blocks():
    a = pd.read_parquet(settings.PROCESSED / "macro_annual_long.parquet")
    expected = {
        "distribuicao": {"profit_share", "gini_index", "income_share_top10",
                         "income_share_bottom20", "vulnerable_employment_pct", "wage_bill_gdp"},
        "restricao_externa": {"terms_of_trade_index", "intl_reserves_usd",
                              "intl_reserves_months_imports", "external_debt_gni",
                              "debt_service_exports", "fdi_net_inflows_gdp"},
        "financeiro": {"lending_rate", "interest_rate_spread", "bank_capital_to_assets",
                       "bank_npl_pct", "market_cap_gdp"},
        "ecologia_estrutura": {"co2_per_capita", "co2_per_gdp", "renewable_electricity_pct",
                               "energy_intensity_gdp", "manufacturing_gdp", "agriculture_gdp",
                               "manufactures_exports_pct", "fuel_ores_exports_pct"},
    }
    for block, vars_ in expected.items():
        assert vars_ <= set(a[a.block == block]["variable"]), block
