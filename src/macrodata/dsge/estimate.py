"""Estimação bayesiana do NK pequeno (Brasil e EUA) + diagnósticos."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats
from scipy.linalg import solve_discrete_lyapunov
from scipy.optimize import minimize
from statsmodels.tsa.stattools import acf

from .. import settings
from . import small_nk as nk
from .solver import IndeterminacyError, solve

# ---------------------------------------------------------------------------
# Priors
# ---------------------------------------------------------------------------
# Núcleo calibrado (padrões da literatura; NÃO estimado livremente)
CALIBRATED = dict(sigma=1.0, kappa=0.08, phi_pi=1.50, phi_x=0.125, rho=0.80,
                  beta=0.9925)

# Parâmetros efetivamente estimados (choques, hábitos e indexação)
PRIORS = {
    "a": ("beta", 5.0, 5.0),            # hábito, média 0.5, sd 0.15
    "b": ("beta", 5.0, 5.0),            # indexação, média 0.5, sd 0.15
    "rho_x": ("beta", 5.0, 5.0),
    "rho_pi": ("beta", 5.0, 5.0),
    "rho_i": ("beta", 5.0, 5.0),
    "sd_x": ("halfnorm", 0.01),
    "sd_pi": ("halfnorm", 0.005),
    "sd_i": ("halfnorm", 0.003),
    "me_x": ("halfnorm", 0.005),
}
POSITIVE = {"sd_x", "sd_pi", "sd_i", "me_x"}
BOUNDED = {"a", "b", "rho_x", "rho_pi", "rho_i"}
PARAM_NAMES = list(PRIORS)
BETA_FIXED = 0.9925
BOUNDS = {
    "a": (0.01, 0.99), "b": (0.01, 0.99),
    "rho_x": (0.01, 0.99), "rho_pi": (0.01, 0.99), "rho_i": (0.01, 0.99),
    "sd_x": (1e-5, 0.10), "sd_pi": (1e-5, 0.10), "sd_i": (1e-5, 0.10),
    "me_x": (1e-5, 0.10),
}
ME_PI = 0.10  # erro de medida em p.p. anualizados
ME_I = 0.10


def prior_mean(name: str) -> float:
    kind, *args = PRIORS[name]
    if kind == "gamma":
        k, theta = args
        return k * theta
    if kind == "beta":
        a, b = args
        return a / (a + b)
    if kind == "halfnorm":
        return args[0] * np.sqrt(2 / np.pi)
    raise ValueError(kind)


def log_prior(p: dict) -> float:
    lp = 0.0
    for name, spec in PRIORS.items():
        x = p[name]
        lo, hi = BOUNDS[name]
        if not (lo <= x <= hi):
            return -np.inf
        kind, *args = spec
        if kind == "gamma":
            k, theta = args
            if x <= 0:
                return -np.inf
            lp += (k - 1) * np.log(x) - x / theta - stats.gamma.logpdf(1, k, scale=theta)
        elif kind == "beta":
            a, b = args
            if not (0 < x < 1):
                return -np.inf
            lp += (a - 1) * np.log(x) + (b - 1) * np.log(1 - x) - stats.beta.logpdf(0.5, a, b)
        elif kind == "halfnorm":
            s = args[0]
            if x <= 0:
                return -np.inf
            lp += stats.halfnorm.logpdf(x, scale=s)
    return float(lp)


def to_z(p: dict) -> np.ndarray:
    z = []
    for name in PARAM_NAMES:
        x = p[name]
        if name in POSITIVE:
            z.append(np.log(max(x, 1e-10)))
        else:
            z.append(np.log(max(min(x, 1 - 1e-10), 1e-10) / (1 - min(max(x, 1e-10), 1 - 1e-10))))
    return np.array(z)


def from_z(z: np.ndarray) -> dict:
    p = {}
    for name, zi in zip(PARAM_NAMES, z):
        if name in POSITIVE:
            p[name] = float(np.exp(zi))
        else:
            p[name] = float(1 / (1 + np.exp(-zi)))
    return p


def log_jac(z: np.ndarray) -> float:
    j = 0.0
    for name, zi in zip(PARAM_NAMES, z):
        if name in POSITIVE:
            j += zi
        else:
            s = 1 / (1 + np.exp(-zi))
            j += np.log(s * (1 - s))
    return float(j)


# ---------------------------------------------------------------------------
# Kalman
# ---------------------------------------------------------------------------
def kalman_loglik(y: np.ndarray, P: np.ndarray, Q: np.ndarray, H: np.ndarray,
                  R: np.ndarray) -> float:
    n = P.shape[0]
    Sigma = solve_discrete_lyapunov(P, Q @ Q.T)
    s = np.zeros(n)
    ll = 0.0
    for t in range(y.shape[0]):
        s_pred = P @ s
        Sig_pred = P @ Sigma @ P.T + Q @ Q.T
        v = y[t] - H @ s_pred
        F = H @ Sig_pred @ H.T + R
        sign, logdet = np.linalg.slogdet(F)
        if sign <= 0:
            return -np.inf
        ll += -0.5 * (logdet + v @ np.linalg.solve(F, v) + y.shape[1] * np.log(2 * np.pi))
        K = np.linalg.solve(F, H @ Sig_pred).T
        s = s_pred + K @ v
        Sigma = Sig_pred - K @ H @ Sig_pred
    return float(ll)


def data_moments(y: np.ndarray) -> dict:
    out = {}
    names = ["gap", "pi", "i"]
    for j, nm in enumerate(names):
        out[f"sd_{nm}"] = float(np.std(y[:, j], ddof=1))
        out[f"ac1_{nm}"] = float(np.corrcoef(y[:-1, j], y[1:, j])[0, 1])
    out["corr_gap_pi"] = float(np.corrcoef(y[:, 0], y[:, 1])[0, 1])
    out["corr_gap_i"] = float(np.corrcoef(y[:, 0], y[:, 2])[0, 1])
    out["corr_pi_i"] = float(np.corrcoef(y[:, 1], y[:, 2])[0, 1])
    return out


def model_moments(p: dict, T: int = 60000, seed: int = 7) -> dict:
    sol, H = nk.solve_model({**p, "beta": BETA_FIXED})
    y = nk.simulate({**p, "beta": BETA_FIXED}, sol, T=T, seed=seed)
    obs = y @ H.T
    return data_moments(obs)


# ---------------------------------------------------------------------------
# Dados
# ---------------------------------------------------------------------------
def _x13_sa(series: pd.Series) -> pd.Series:
    """Ajuste sazonal X-13ARIMA-SEATS; fallback STL documentado."""
    try:
        import x13as
        from statsmodels.tsa.x13 import x13_arima_analysis
        binpath = os.path.join(os.path.dirname(x13as.__file__), "_bin", "x13as")
        s = series.dropna().astype(float)
        s.index = pd.PeriodIndex(s.index, freq="Q")
        res = x13_arima_analysis(s, x12path=binpath, trading=False, outlier=True,
                                 tempdir=str(settings.ROOT / ".cache" / "x13"))
        out = res.seasadj.copy()
        out.index = out.index.to_timestamp(how="end").normalize()
        return out
    except Exception as exc:  # noqa: BLE001
        from statsmodels.tsa.seasonal import STL
        s = series.dropna().astype(float).asfreq("QE")
        res = STL(s, period=4, robust=True).fit()
        return res.seasonal + res.resid


def _brazil_data() -> pd.DataFrame:
    q = pd.read_parquet(settings.PROCESSED / "macro_quarterly_long.parquet")
    gap = q[(q.iso3 == "BRA") & (q.variable == "output_gap")].set_index("date")["value"]
    pol = q[(q.iso3 == "BRA") & (q.variable == "policy_rate")].set_index("date")["value"]
    # IPCA: índice mensal -> trimestre -> X-13 -> qoq SAAR
    b = pd.read_parquet(settings.RAW / "parsed_bcb.parquet")
    ipca = b[(b.variable == "inflation")].set_index("date")["value"].sort_index()
    idx = (1 + ipca / 100).cumprod() * 100
    qidx = idx.groupby(idx.index.to_period("Q")).last()
    qidx.index = qidx.index.to_timestamp(how="end").normalize()
    sa = _x13_sa(qidx)
    pi = 400 * np.log(sa).diff()
    df = pd.DataFrame({"gap": gap, "pi": pi, "i": pol}).dropna()
    df = df[(df.index >= "1999-09-30") & (df.index <= "2025-12-31")]
    return df


def _usa_data() -> pd.DataFrame:
    q = pd.read_parquet(settings.PROCESSED / "macro_quarterly_long.parquet")
    gap = q[(q.iso3 == "USA") & (q.variable == "output_gap")].set_index("date")["value"]
    pol = q[(q.iso3 == "USA") & (q.variable == "short_rate")].set_index("date")["value"]
    # núcleo do CPI (CPILFESL) índice mensal -> trimestre -> X-13 -> qoq SAAR
    f = pd.read_parquet(settings.RAW / "parsed_fred.parquet")
    core = f[(f.iso3 == "USA") & (f.variable == "core_inflation")].set_index("date")["value"].sort_index()
    core = core[core.index >= "1980-01-01"]
    qidx = core.groupby(core.index.to_period("Q")).last()
    qidx.index = qidx.index.to_timestamp(how="end").normalize()
    sa = _x13_sa(qidx)
    pi = 400 * np.log(sa).diff()
    df = pd.DataFrame({"gap": gap, "pi": pi, "i": pol}).dropna()
    df = df[(df.index >= "1995-03-31") & (df.index <= "2025-12-31")]
    return df


def prepare_data(country: str = "BRA") -> tuple[pd.DataFrame, pd.Series]:
    df = _brazil_data() if country == "BRA" else _usa_data()
    means = df.mean()
    y = (df - means).values
    return df, means


# ---------------------------------------------------------------------------
# MCMC
# ---------------------------------------------------------------------------
@dataclass
class Posterior:
    draws: pd.DataFrame
    logpost: np.ndarray
    acceptance: float
    means: pd.Series
    data: pd.DataFrame
    solution: object

    def full_params(self) -> dict:
        return {**CALIBRATED, **self.draws.mean().to_dict()}

    def summary(self) -> pd.DataFrame:
        rows = []
        for name in PARAM_NAMES:
            s = self.draws[name]
            q05, q50, q95 = s.quantile([0.05, 0.5, 0.95])
            rows.append({"parameter": name, "prior_mean": prior_mean(name),
                         "prior_sd": _prior_sd(name), "post_mean": s.mean(), "post_sd": s.std(),
                         "q05": q05, "median": q50, "q95": q95,
                         "ess": _ess(s.values)})
        return pd.DataFrame(rows)


def _prior_sd(name: str) -> float:
    kind, *args = PRIORS[name]
    if kind == "gamma":
        k, theta = args
        return float(np.sqrt(k) * theta)
    if kind == "beta":
        a, b = args
        return float(np.sqrt(a * b / ((a + b) ** 2 * (a + b + 1))))
    if kind == "halfnorm":
        s = args[0]
        return float(s * np.sqrt(1 - 2 / np.pi))
    return np.nan


def _ess(x: np.ndarray, maxlag: int = 100) -> float:
    x = np.asarray(x, float)
    n = len(x)
    if n < 20:
        return np.nan
    r = acf(x, nlags=min(maxlag, n // 2), fft=True)
    r = r[1:]
    r = np.where(r < 0, 0, r)
    return float(n / (1 + 2 * r.sum()))


def _logpost(z: np.ndarray, y: np.ndarray) -> float:
    p = {**CALIBRATED, **from_z(z)}
    lp = log_prior(p)
    if not np.isfinite(lp):
        return -np.inf
    try:
        sol, H = nk.solve_model({**p, "beta": BETA_FIXED})
    except IndeterminacyError:
        return -np.inf
    R = np.diag([p["me_x"] ** 2 + 1e-10, ME_PI ** 2, ME_I ** 2])
    ll = kalman_loglik(y, sol.P, sol.Q, H, R)
    if not np.isfinite(ll):
        return -np.inf
    return float(lp + ll + log_jac(z))


def estimate(country: str = "BRA", ndraws: int = 22000, burn: int = 6000,
             seed: int = 123) -> Posterior:
    df, means = prepare_data(country)
    y = (df - means).values
    start = {k: prior_mean(k) for k in PARAM_NAMES}
    z = to_z(start)
    lp = _logpost(z, y)
    if not np.isfinite(lp):
        # busca um ponto determinístico com maior verossimilhança
        best, best_lp = z.copy(), lp
        rng0 = np.random.default_rng(0)
        for _ in range(2000):
            cand = z + rng0.normal(0, 0.5, len(z))
            lc = _logpost(cand, y)
            if lc > best_lp:
                best, best_lp = cand, lc
        z, lp = best, best_lp
    rng = np.random.default_rng(seed)
    nparams = len(z)
    chol = np.eye(nparams) * 0.05
    draws, lps = [], []
    acc = 0
    total = ndraws + burn
    for i in range(total):
        prop = z + chol @ rng.standard_normal(nparams)
        lprop = _logpost(prop, y)
        if np.log(rng.random()) < (lprop - lp):
            z, lp = prop, lprop
            acc += 1
        if i >= burn and (i - burn) % 5 == 0:
            draws.append(from_z(z))
            lps.append(lp)
        if i == burn:
            chol = np.eye(nparams) * 0.02
        if i > burn and i % 500 == 0:
            # adaptação durante o burn-in extendido (Haario)
            recent = np.array([to_z(d) for d in draws[-200:]])
            if len(recent) > 50:
                chol = np.linalg.cholesky(np.cov(recent.T) + 1e-8 * np.eye(nparams))
    draws_df = pd.DataFrame(draws)
    post_mean = draws_df.mean()
    sol, H = nk.solve_model({**CALIBRATED, **post_mean.to_dict()})
    return Posterior(draws=draws_df, logpost=np.array(lps),
                     acceptance=acc / total, means=means, data=df, solution=sol)


# ---------------------------------------------------------------------------
# Diagnósticos
# ---------------------------------------------------------------------------
def identification(post: Posterior) -> tuple[pd.DataFrame, pd.DataFrame]:
    p = post.full_params()
    z0 = to_z({k: p[k] for k in PARAM_NAMES})
    base = model_moments(p, T=30000)
    keys = list(base.keys())
    J = np.zeros((len(keys), len(z0)))
    for j in range(len(z0)):
        h = 1e-3
        zp, zm = z0.copy(), z0.copy()
        zp[j] += h; zm[j] -= h
        mp = model_moments({**p, **from_z(zp)}, T=30000, seed=11)
        mm = model_moments({**p, **from_z(zm)}, T=30000, seed=11)
        J[:, j] = [(mp[k] - mm[k]) / (2 * h) for k in keys]
    # normalização por escala dos momentos e dos parâmetros
    scale_m = np.maximum(np.abs(J).mean(axis=1, keepdims=True), 1e-12)
    Jn = J / scale_m
    U, S, Vt = np.linalg.svd(Jn, full_matrices=False)
    sv = pd.DataFrame({"singular_value": S, "ratio_to_max": S / S[0] if S[0] else S,
                       "cum_share": np.cumsum(S ** 2) / np.sum(S ** 2)})
    importance = np.sqrt((Jn ** 2).sum(axis=0))
    importance = importance / importance.max() if importance.max() > 0 else importance
    sens = pd.DataFrame({"parameter": PARAM_NAMES,
                         "importance": importance,
                         "max_abs_loading": np.abs(Vt).max(axis=0)})
    return sv, sens


def irfs(post: Posterior, horizon: int = 16) -> pd.DataFrame:
    p = post.full_params()
    sol, H = nk.solve_model(p)
    rows = []
    for j, shock in enumerate(nk.SHOCKS):
        size = p[["sd_x", "sd_pi", "sd_i"][j]]
        ir = nk.irf(p, sol, horizon=horizon, shock=j, size=size) @ H.T
        for h in range(horizon):
            for k, obs in enumerate(["output_gap", "inflation", "policy_rate"]):
                rows.append({"shock": shock, "horizon": h, "observable": obs, "response": ir[h, k]})
    return pd.DataFrame(rows)


def fevd(post: Posterior, T: int = 40000, seed: int = 3) -> pd.DataFrame:
    p = post.full_params()
    sol, H = nk.solve_model(p)
    full = nk.simulate(p, sol, T=T, seed=seed) @ H.T
    rows = []
    for j, shock in enumerate(nk.SHOCKS):
        pj = {**p, "sd_x": 0.0, "sd_pi": 0.0, "sd_i": 0.0}
        pj[["sd_x", "sd_pi", "sd_i"][j]] = p[["sd_x", "sd_pi", "sd_i"][j]]
        solj, _ = nk.solve_model(pj)
        yj = nk.simulate(pj, solj, T=T, seed=seed) @ H.T
        for k, obs in enumerate(["output_gap", "inflation", "policy_rate"]):
            rows.append({"shock": shock, "observable": obs,
                         "share": float(np.var(yj[:, k]) / np.var(full[:, k]))})
    return pd.DataFrame(rows)


def smoothed_shocks(post: Posterior) -> pd.DataFrame:
    """Suavização RTS e decomposição histórica dos choques."""
    p = post.full_params()
    sol, H = nk.solve_model(p)
    y = (post.data - post.means).values
    P, Q = sol.P, sol.Q
    R = np.diag([p["me_x"] ** 2 + 1e-10, ME_PI ** 2, ME_I ** 2])
    n = P.shape[0]
    s_f, P_f, s_p, P_p = [], [], [], []
    Sigma = solve_discrete_lyapunov(P, Q @ Q.T)
    s = np.zeros(n)
    for t in range(y.shape[0]):
        s_pred = P @ s
        Sig_pred = P @ Sigma @ P.T + Q @ Q.T
        v = y[t] - H @ s_pred
        F = H @ Sig_pred @ H.T + R
        K = np.linalg.solve(F, H @ Sig_pred).T
        s = s_pred + K @ v
        Sigma = Sig_pred - K @ H @ Sig_pred
        s_p.append(s_pred); P_p.append(Sig_pred); s_f.append(s); P_f.append(Sigma)
    s_s = np.array(s_f); P_s = np.array(P_f)
    for t in range(y.shape[0] - 2, -1, -1):
        J = P_f[t] @ P.T @ np.linalg.pinv(P_p[t + 1])
        s_s[t] = s_f[t] + J @ (s_s[t + 1] - s_p[t + 1])
    contrib = []
    for t in range(1, y.shape[0]):
        du = np.linalg.lstsq(Q, s_s[t] - P @ s_s[t - 1], rcond=None)[0]
        contrib.append(H @ Q * du[None, :])
    contrib = np.array(contrib)
    dates = post.data.index[1:]
    out = []
    for j, shock in enumerate(nk.SHOCKS):
        for k, obs in enumerate(["output_gap", "inflation", "policy_rate"]):
            out.append(pd.DataFrame({"date": dates, "shock": shock, "observable": obs,
                                     "contribution": contrib[:, k, j]}))
    return pd.concat(out, ignore_index=True)


def run(country: str = "BRA", ndraws: int = 22000, burn: int = 6000) -> Posterior:
    post = estimate(country, ndraws=ndraws, burn=burn)
    tag = country.lower()
    post.draws.to_parquet(settings.PROCESSED / f"dsge_small_draws_{tag}.parquet")
    post.summary().to_csv(settings.PROCESSED / f"dsge_small_posterior_{tag}.csv", index=False)
    pd.DataFrame({"logpost": post.logpost}).to_csv(
        settings.PROCESSED / f"dsge_small_logpost_{tag}.csv", index=False)
    sv, sens = identification(post)
    sv.to_csv(settings.PROCESSED / f"dsge_small_identification_svd_{tag}.csv", index=False)
    sens.to_csv(settings.PROCESSED / f"dsge_small_identification_params_{tag}.csv", index=False)
    irfs(post).to_csv(settings.PROCESSED / f"dsge_small_irf_{tag}.csv", index=False)
    fevd(post).to_csv(settings.PROCESSED / f"dsge_small_fevd_{tag}.csv", index=False)
    dm = data_moments((post.data - post.means).values)
    mm = model_moments(post.full_params(), T=60000)
    pd.DataFrame([{"moment": k, "data": v, "model": mm.get(k)} for k, v in dm.items()]) \
        .to_csv(settings.PROCESSED / f"dsge_small_moments_{tag}.csv", index=False)
    smoothed_shocks(post).to_csv(settings.PROCESSED / f"dsge_small_histdecomp_{tag}.csv", index=False)
    meta = {"country": country, "n_obs": int(len(post.data)), "sample": [str(post.data.index.min()),
            str(post.data.index.max())], "acceptance": post.acceptance,
            "means": post.means.to_dict(), "params": post.draws.mean().to_dict(),
            "calibrated": CALIBRATED}
    with open(settings.PROCESSED / f"dsge_small_meta_{tag}.json", "w", encoding="utf-8") as fh:
        json.dump(meta, fh, ensure_ascii=False, indent=2, default=str)
    print(f"[dsge] {country}: n={len(post.data)} acc={post.acceptance:.2f}")
    print(post.summary().round(3).to_string(index=False))
    return post


if __name__ == "__main__":
    run("BRA")
