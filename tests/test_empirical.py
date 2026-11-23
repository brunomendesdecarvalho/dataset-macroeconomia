import numpy as np
from macrodata import empirical as emp


def test_taylor_runs():
    out = emp.taylor_rule(use_expectations=False)
    t = out["table"]
    assert np.isfinite(out["phi_pi"])
    assert out["fit"].nobs >= 80
    assert not t["coef"].isna().any()


def test_phillips_runs():
    out = emp.phillips_curve("inflation", use_expectations=True)
    assert out["fit"].nobs >= 80
    assert np.isfinite(out["fit"].params).all()


def test_svar_stable_and_irf():
    s = emp.fit_svar("BRA", n_boot=20)
    assert s.stable
    assert s.irf.shape == (emp.HORIZON + 1, 4, 4)
    assert np.isfinite(s.irf).all()
    assert s.fevd.shape == (4, emp.HORIZON, 4)
    assert s.p >= 1


def test_local_projections():
    s = emp.fit_svar("BRA", n_boot=10)
    lp = emp.local_projections(s)
    assert len(lp) == 3 * (emp.HORIZON + 1)
    assert np.isfinite(lp[["beta", "se_hac", "lo90", "hi90"]]).all().all()


def test_crosscountry_usa():
    s = emp.fit_svar("USA", policy="short_rate", fx="reer", include_foreign=False, n_boot=10)
    assert s.stable
    assert np.isfinite(s.irf).all()


def test_svar_core_robustness():
    s = emp.fit_svar("BRA", inflation_var="core_inflation", n_boot=10)
    assert s.stable
    assert np.isfinite(s.irf).all()
