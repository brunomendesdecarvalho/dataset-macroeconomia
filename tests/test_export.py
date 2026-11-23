import pandas as pd
from macrodata import settings


def test_excel_sheets_and_freeze():
    path = settings.DATA / "exports" / "macro_dataset_consolidado.xlsx"
    x = pd.ExcelFile(path)
    assert x.sheet_names == ["Anual_Wide", "Trimestral_Wide", "Regimes_Anual", "Codebook_Fontes"]
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=False)
    assert wb["Anual_Wide"].freeze_panes == "A2"
    assert wb["Trimestral_Wide"].freeze_panes == "A2"


def test_csv_long_schema():
    path = settings.DATA / "exports" / "macro_todos_dados_long.csv"
    d = pd.read_csv(path, nrows=50)
    expected = ["freq", "iso3", "country", "date", "period", "variable", "block",
                "value", "unit", "source", "source_code", "quality_flag",
                "is_forecast", "regime_dummy"]
    assert list(d.columns) == expected
    assert not any("dsge" in c for c in d.columns)
    assert set(d.freq.unique()) <= {"A", "Q"}


def test_wide_files_exist():
    a = pd.read_csv(settings.DATA / "exports" / "macro_anual_wide.csv", nrows=5)
    q = pd.read_csv(settings.DATA / "exports" / "macro_trimestral_wide.csv", nrows=5)
    assert {"iso3", "country", "year", "date"}.issubset(a.columns)
    assert {"iso3", "country", "quarter", "date"}.issubset(q.columns)
    assert "gini_index" in a.columns
    assert "co2_per_capita" in a.columns
