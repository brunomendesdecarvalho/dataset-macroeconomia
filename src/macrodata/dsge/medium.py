"""DSGE médio (SW-lite) calibrado para o Brasil.

Blocos: famílias (consumo residual com hábitos via persistência do produto),
firmas (Calvo na inflação e no salário), capital/investimento, política
monetária (Taylor), política fiscal (gasto AR), setor externo (demanda e
prêmio de risco) e tecnologia. Modelo linear, calibrado e simulado — NÃO
estimado, conforme decisão metodológica registrada no relatório.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
from scipy.linalg import solve_discrete_lyapunov
from scipy.optimize import least_squares

from .. import settings
from .solver import IndeterminacyError, solve

NAMES = ["x", "pi", "w", "n", "k", "inv", "c", "i", "g", "ystar", "rp", "a"]
SHOCKS = ["demanda", "markup", "salario", "monetario", "fiscal", "externo", "risco", "tecnologia", "investimento"]
OBS = ["x", "pi", "i", "c", "inv", "g"]

CALIB = dict(
    beta=0.9925, sigma=1.5, a_x=0.50, theta_g=0.20, theta_y=0.10,
    bp=0.50, kappa=0.10, bw=0.50, kappa_w=0.10, sigma_c=1.5, phi=1.0,
    alpha=0.33, delta=0.025, kappa_x=0.30, kappa_r=0.10,
    rho=0.80, phi_pi=1.50, phi_x=0.125,
    c_y=0.60, i_y=0.20, g_y=0.20,
    rho_g=0.50, rho_y=0.50, rho_r=0.50, rho_a=0.50,
    sd_ed=0.006, sd_epi=0.003, sd_ew=0.003, sd_ei=0.002, sd_eg=0.004,
    sd_ey=0.006, sd_er=0.003, sd_ea=0.004, sd_einv=0.006,
)


def matrices(p: dict) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    n = len(NAMES)
    A0 = np.zeros((n, n)); A1 = np.zeros((n, n)); A2 = np.zeros((n, n))
    A3 = np.zeros((n, len(SHOCKS)))
    # 1 IS
    A0[0, 0] = 1.0; A0[0, 7] = p["sigma"]; A0[0, 10] = -p["sigma"]
    A0[0, 8] = -p["theta_g"]; A0[0, 9] = -p["theta_y"]
    A1[0, 0] = -p["a_x"]; A2[0, 0] = -(1 - p["a_x"]); A2[0, 1] = -p["sigma"]
    A3[0, 0] = -1.0
    # 2 NKPC
    A0[1, 1] = 1.0; A0[1, 2] = -p["kappa"]; A0[1, 11] = p["kappa"]
    A1[1, 1] = -p["bp"]; A2[1, 1] = -(1 - p["bp"]) * p["beta"]
    A3[1, 1] = -1.0
    # 3 Wage PC
    A0[2, 2] = 1.0 + (1 - p["bw"]) * p["kappa_w"]
    A0[2, 0] = -(1 - p["bw"]) * p["kappa_w"] * p["sigma_c"]
    A0[2, 3] = -(1 - p["bw"]) * p["kappa_w"] * p["phi"]
    A1[2, 2] = -p["bw"]; A2[2, 2] = -(1 - p["bw"])
    A3[2, 2] = -1.0
    # 4 Produção
    A0[3, 0] = 1.0; A0[3, 3] = -(1 - p["alpha"]); A0[3, 11] = -1.0
    A1[3, 4] = -p["alpha"]
    # 5 Capital
    A0[4, 4] = 1.0; A0[4, 5] = -p["delta"]; A1[4, 4] = -(1 - p["delta"])
    # 6 Investimento
    # Demanda de investimento reduzida (sem Tobin's Q): evita raiz explosiva
    A0[5, 5] = 1.0; A0[5, 0] = -p["kappa_x"]; A0[5, 7] = p["kappa_r"]
    A3[5, 8] = -1.0
    # 7 Recurso
    A0[6, 6] = p["c_y"]; A0[6, 5] = p["i_y"]; A0[6, 8] = p["g_y"]; A0[6, 0] = -1.0
    # 8 Taylor
    A0[7, 7] = 1.0; A0[7, 1] = -(1 - p["rho"]) * p["phi_pi"]; A0[7, 0] = -(1 - p["rho"]) * p["phi_x"]
    A1[7, 7] = -p["rho"]; A3[7, 3] = -1.0
    # 9-12 AR(1)
    A0[8, 8] = 1.0; A1[8, 8] = -p["rho_g"]; A3[8, 4] = -1.0
    A0[9, 9] = 1.0; A1[9, 9] = -p["rho_y"]; A3[9, 5] = -1.0
    A0[10, 10] = 1.0; A1[10, 10] = -p["rho_r"]; A3[10, 6] = -1.0
    A0[11, 11] = 1.0; A1[11, 11] = -p["rho_a"]; A3[11, 7] = -1.0
    return A0, A1, A2, A3


def solve_model(p: dict | None = None):
    p = {**CALIB, **(p or {})}
    A0, A1, A2, A3 = matrices(p)
    sol = solve(A0, A1, A2, A3)
    return sol, p


def simulate(p: dict, sol, T: int = 30000, seed: int = 21) -> np.ndarray:
    rng = np.random.default_rng(seed)
    sds = np.array([p[f"sd_{s}"] for s in ["ed", "epi", "ew", "ei", "eg", "ey", "er", "ea", "einv"]])
    eps = rng.standard_normal((T + 500, len(SHOCKS))) * sds
    y = np.zeros((T + 500, len(NAMES)))
    for t in range(1, T + 500):
        y[t] = sol.P @ y[t - 1] + sol.Q @ eps[t]
    return y[500:]


def observed(y: np.ndarray) -> np.ndarray:
    """Converte estados para unidades observáveis: x,c,inv,g em %; pi,i anualizados."""
    out = np.column_stack([100 * y[:, 0], 400 * y[:, 1], 400 * y[:, 7],
                           100 * y[:, 6], 100 * y[:, 5], 100 * y[:, 8]])
    return out


def moments(y: np.ndarray) -> dict:
    obs = observed(y)
    out = {}
    for j, nm in enumerate(OBS):
        out[f"sd_{nm}"] = float(np.std(obs[:, j], ddof=1))
        out[f"ac1_{nm}"] = float(np.corrcoef(obs[:-1, j], obs[1:, j])[0, 1])
    out["corr_x_pi"] = float(np.corrcoef(obs[:, 0], obs[:, 1])[0, 1])
    out["corr_x_i"] = float(np.corrcoef(obs[:, 0], obs[:, 2])[0, 1])
    out["corr_pi_i"] = float(np.corrcoef(obs[:, 1], obs[:, 2])[0, 1])
    return out


def brazil_data() -> pd.DataFrame:
    from .estimate import _brazil_data
    base = _brazil_data()[["gap", "pi", "i"]].rename(columns={"gap": "x"})
    q = pd.read_parquet(settings.PROCESSED / "macro_quarterly_long.parquet")
    out = base.copy()
    for var, nm in (("consumption_real", "c"), ("investment_real", "inv"), ("gov_exp_real", "g")):
        s = q[(q.iso3 == "BRA") & (q.variable == var)].set_index("date")["value"].dropna()
        s = np.log(s)
        cyc, tr = __import__("statsmodels.tsa.filters.hp_filter", fromlist=["hpfilter"]).hpfilter(s, lamb=1600)
        out[nm] = 100 * cyc
    return out.dropna()


def calibrate_shocks(data_mom: dict, T: int = 20000) -> dict:
    def resid(theta):
        p = {**CALIB, "sd_ed": np.exp(theta[0]), "sd_epi": np.exp(theta[1]), "sd_ei": np.exp(theta[2])}
        sol, p = solve_model(p)
        m = moments(simulate(p, sol, T=T, seed=5))
        return [(m["sd_x"] - data_mom["sd_x"]) / data_mom["sd_x"],
                (m["sd_pi"] - data_mom["sd_pi"]) / data_mom["sd_pi"],
                (m["sd_i"] - data_mom["sd_i"]) / data_mom["sd_i"]]
    x0 = np.log([CALIB["sd_ed"], CALIB["sd_epi"], CALIB["sd_ei"]])
    res = least_squares(resid, x0, bounds=(-12, 0), max_nfev=60)
    return {"sd_ed": float(np.exp(res.x[0])), "sd_epi": float(np.exp(res.x[1])),
            "sd_ei": float(np.exp(res.x[2])), "cost": float(np.sqrt(np.mean(res.fun ** 2)))}


def irf(p: dict, sol, horizon: int = 16, shock: int = 3, size: float | None = None) -> pd.DataFrame:
    sd_name = ["sd_ed", "sd_epi", "sd_ew", "sd_ei", "sd_eg", "sd_ey", "sd_er", "sd_ea", "sd_einv"][shock]
    size = p[sd_name] if size is None else size
    y = sol.Q[:, shock] * size
    rows = []
    for h in range(horizon):
        obs = observed(y[None, :])[0]
        for k, nm in enumerate(OBS):
            rows.append({"shock": SHOCKS[shock], "horizon": h, "observable": nm, "response": obs[k]})
        y = sol.P @ y
    return pd.DataFrame(rows)


def fevd(p: dict, sol, T: int = 30000, seed: int = 9) -> pd.DataFrame:
    full = moments(simulate(p, sol, T=T, seed=seed))
    rows = []
    base = {k: v for k, v in p.items() if not k.startswith("sd_")}
    for j, s in enumerate(SHOCKS):
        pj = {**base, **{f"sd_{x}": 0.0 for x in ["ed", "epi", "ew", "ei", "eg", "ey", "er", "ea", "einv"]}}
        sd_name = ["sd_ed", "sd_epi", "sd_ew", "sd_ei", "sd_eg", "sd_ey", "sd_er", "sd_ea", "sd_einv"][j]
        pj[sd_name] = p[sd_name]
        solj, pj = solve_model(pj)
        y = observed(simulate(pj, solj, T=T, seed=seed))
        rows.append({"shock": s, "var_x": float(np.var(y[:, 0]) / np.var(observed(simulate(p, sol, T=T, seed=seed))[:, 0]))})
    return pd.DataFrame(rows)


def run() -> dict:
    data = brazil_data()
    dm = {}
    for nm in OBS:
        dm[f"sd_{nm}"] = float(data[nm].std(ddof=1))
        dm[f"ac1_{nm}"] = float(np.corrcoef(data[nm][:-1], data[nm][1:])[0, 1])
    dm["corr_x_pi"] = float(data["x"].corr(data["pi"]))
    dm["corr_x_i"] = float(data["x"].corr(data["i"]))
    dm["corr_pi_i"] = float(data["pi"].corr(data["i"]))

    cal = calibrate_shocks(dm)
    p = {**CALIB, **{k: cal[k] for k in ("sd_ed", "sd_epi", "sd_ei")}}
    sol, p = solve_model(p)
    y = simulate(p, sol, T=40000, seed=17)
    mm = moments(y)

    calib = pd.DataFrame([{"parameter": k, "value": v, "status": "calibrado"}
                          for k, v in p.items()])
    calib.loc[calib.parameter.isin(["sd_ed", "sd_epi", "sd_ei"]), "status"] = "calibrado para casar volatilidades"
    calib.to_csv(settings.PROCESSED / "dsge_medium_calibration.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame([{"moment": k, "data": dm.get(k), "model": mm.get(k)} for k in dm]) \
        .to_csv(settings.PROCESSED / "dsge_medium_moments.csv", index=False, encoding="utf-8-sig")

    irfs = pd.concat([irf(p, sol, shock=j) for j in range(len(SHOCKS))], ignore_index=True)
    irfs.to_csv(settings.PROCESSED / "dsge_medium_irf.csv", index=False, encoding="utf-8-sig")
    fevd(p, sol).to_csv(settings.PROCESSED / "dsge_medium_fevd.csv", index=False, encoding="utf-8-sig")

    # Sensibilidade: +/-20% em parâmetros estruturais
    sens = []
    for name in ("sigma", "kappa", "bp", "bw", "phi_pi", "rho", "a_x"):
        for shock, label in ((0.8, "-20%"), (1.2, "+20%")):
            q = {**p, name: p[name] * shock}
            try:
                s2, q2 = solve_model(q)
                m2 = moments(simulate(q2, s2, T=20000, seed=17))
                sens.append({"parameter": name, "variation": label,
                             "sd_x": m2["sd_x"], "sd_pi": m2["sd_pi"], "sd_i": m2["sd_i"],
                             "corr_x_pi": m2["corr_x_pi"], "corr_x_i": m2["corr_x_i"]})
            except IndeterminacyError:
                sens.append({"parameter": name, "variation": label, "sd_x": np.nan,
                             "sd_pi": np.nan, "sd_i": np.nan, "corr_x_pi": np.nan, "corr_x_i": np.nan})
    pd.DataFrame(sens).to_csv(settings.PROCESSED / "dsge_medium_sensitivity.csv", index=False, encoding="utf-8-sig")

    meta = {"n_sim": int(len(y)), "solution_eig_max": float(np.abs(sol.eig).max()),
            "shock_calibration": cal, "n_data": int(len(data)),
            "sample": [str(data.index.min()), str(data.index.max())]}
    with open(settings.PROCESSED / "dsge_medium_meta.json", "w", encoding="utf-8") as fh:
        json.dump(meta, fh, ensure_ascii=False, indent=2)
    print("medium:", len(y), "eig", round(np.abs(sol.eig).max(), 3), "cal", {k: round(v, 5) for k, v in cal.items()})
    print(pd.DataFrame([{"moment": k, "data": dm.get(k), "model": mm.get(k)} for k in dm]).round(3).to_string(index=False))
    return {"meta": meta, "moments": mm, "data": dm}


if __name__ == "__main__":
    run()
