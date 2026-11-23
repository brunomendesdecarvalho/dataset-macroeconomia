import sys
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from macrodata import settings

a = pd.read_parquet(settings.PROCESSED / "macro_annual_long.parquet")
a = a[(a.year >= 1995) & (a.year <= 2025)]
rows = []
for iso, d in a.groupby("iso3"):
    for var in ("gdp_growth", "inflation", "policy_rate", "gov_debt_gdp", "unemployment"):
        s = d[d.variable == var].sort_values("year")["value"].dropna()
        if len(s) < 10:
            continue
        rows.append({"iso3": iso, "variable": var, "n": len(s), "mean": s.mean(), "sd": s.std(ddof=1),
                     "ac1": np.corrcoef(s[:-1], s[1:])[0, 1] if len(s) > 2 else np.nan})
out = pd.DataFrame(rows)
out.to_csv(settings.PROCESSED / "cross_country_moments.csv", index=False, encoding="utf-8-sig")
print(out.groupby("variable")[["mean", "sd", "ac1"]].median().round(2).to_string())
