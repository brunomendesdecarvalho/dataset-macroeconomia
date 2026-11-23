"""Modelo NK pequeno (3 equações) com hábitos, indexação e AR(1) nos choques.

Variáveis (desvios do estado estacionário, trimestral):
  x   hiato do produto (fração)
  pi  inflação trimestral (fração)
  i   taxa nominal trimestral (fração)
  ex, epi, ei  choques de demanda, markup e política monetária (AR(1))

Equações:
  x_t  = a x_{t-1} + (1-a) E_t x_{t+1} - sigma (i_t - E_t pi_{t+1}) + ex_t
  pi_t = b pi_{t-1} + (1-b) beta E_t pi_{t+1} + kappa x_t + epi_t
  i_t  = rho i_{t-1} + (1-rho)(phi_pi pi_t + phi_x x_t) + ei_t
  ex_t = rho_x ex_{t-1} + u_x,t ; epi_t = rho_pi epi_{t-1} + u_pi,t ;
  ei_t = rho_i ei_{t-1} + u_i,t
"""
from __future__ import annotations

import numpy as np
from scipy.linalg import solve_discrete_lyapunov

from .solver import Solution, solve

NAMES = ["x", "pi", "i", "ex", "epi", "ei"]
OBS = ["output_gap", "inflation", "policy_rate"]
SHOCKS = ["demanda", "markup", "monetario"]

BASE = dict(sigma=1.0, kappa=0.30, a=0.50, b=0.50, beta=0.9925, rho=0.75,
            phi_pi=1.50, phi_x=0.125, rho_x=0.50, rho_pi=0.40, rho_i=0.50,
            sd_x=0.005, sd_pi=0.003, sd_i=0.002, me_x=0.002)


def matrices(p: dict) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    n = len(NAMES)
    A0 = np.zeros((n, n))
    A1 = np.zeros((n, n))
    A2 = np.zeros((n, n))
    A3 = np.zeros((n, 3))
    # IS
    A0[0, 0] = 1.0
    A0[0, 2] = p["sigma"]
    A0[0, 3] = -1.0
    A1[0, 0] = -p["a"]
    A2[0, 0] = -(1 - p["a"])
    A2[0, 1] = -p["sigma"]
    # NKPC
    A0[1, 1] = 1.0
    A0[1, 0] = -p["kappa"]
    A0[1, 4] = -1.0
    A1[1, 1] = -p["b"]
    A2[1, 1] = -(1 - p["b"]) * p["beta"]
    # Taylor
    A0[2, 2] = 1.0
    A0[2, 1] = -(1 - p["rho"]) * p["phi_pi"]
    A0[2, 0] = -(1 - p["rho"]) * p["phi_x"]
    A0[2, 5] = -1.0
    A1[2, 2] = -p["rho"]
    # choques AR(1)
    A0[3, 3] = 1.0; A1[3, 3] = -p["rho_x"]; A3[3, 0] = -1.0
    A0[4, 4] = 1.0; A1[4, 4] = -p["rho_pi"]; A3[4, 1] = -1.0
    A0[5, 5] = 1.0; A1[5, 5] = -p["rho_i"]; A3[5, 2] = -1.0
    return A0, A1, A2, A3


def measure() -> tuple[np.ndarray, np.ndarray]:
    H = np.zeros((3, len(NAMES)))
    H[0, 0] = 100.0
    H[1, 1] = 400.0
    H[2, 2] = 400.0
    return H, np.zeros(3)


def solve_model(p: dict) -> tuple[Solution, np.ndarray]:
    A0, A1, A2, A3 = matrices(p)
    sol = solve(A0, A1, A2, A3)
    H, _ = measure()
    return sol, H


def simulate(p: dict, sol: Solution, T: int = 3000, seed: int = 42,
             burn: int = 500) -> np.ndarray:
    rng = np.random.default_rng(seed)
    sd = np.array([p["sd_x"], p["sd_pi"], p["sd_i"]])
    eps = rng.standard_normal((T + burn, 3)) * sd
    y = np.zeros((T + burn, len(NAMES)))
    for t in range(1, T + burn):
        y[t] = sol.P @ y[t - 1] + sol.Q @ eps[t]
    return y[burn:]


def irf(p: dict, sol: Solution, horizon: int = 16, shock: int = 0, size: float = 0.01) -> np.ndarray:
    y = np.zeros(len(NAMES))
    e = np.zeros(3); e[shock] = size
    y = sol.Q @ e
    out = [y.copy()]
    for _ in range(horizon - 1):
        y = sol.P @ y
        out.append(y.copy())
    return np.array(out)
