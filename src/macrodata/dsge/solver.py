"""Solução de modelos lineares de expectativas racionais via QZ (Klein/Sims).

Forma do modelo:
    A0 y_t + A1 y_{t-1} + A2 E_t y_{t+1} + A3 eps_t = 0
Solução:
    y_t = P y_{t-1} + Q eps_t
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.linalg import ordqz


class IndeterminacyError(RuntimeError):
    pass


@dataclass
class Solution:
    P: np.ndarray
    Q: np.ndarray
    eig: np.ndarray
    n_stable: int
    residual: float


def solve(A0: np.ndarray, A1: np.ndarray, A2: np.ndarray, A3: np.ndarray,
          tol: float = 1e-10) -> Solution:
    n = A0.shape[0]
    M = np.block([[np.zeros((n, n)), np.eye(n)], [-A1, -A0]])
    N = np.block([[np.eye(n), np.zeros((n, n))], [np.zeros((n, n)), A2]])
    AA, BB, alpha, beta, Qz, Z = ordqz(M, N, sort="iuc")
    stable = np.abs(alpha) < np.abs(beta)
    ns = int(stable.sum())
    if ns != n:
        raise IndeterminacyError(
            f"Blanchard-Kahn violado: {ns} raízes estáveis para {n} variáveis "
            f"(esperado {n}). Modelo indeterminado ou sem solução limitada."
        )
    V = Z[:, :n]
    V1, V2 = V[:n, :], V[n:, :]
    if np.linalg.matrix_rank(V1) < n:
        raise IndeterminacyError("Subespaço estável singular (V1 não invertível).")
    P = V2 @ np.linalg.inv(V1)
    Mq = A0 + A2 @ P
    try:
        Q = np.linalg.solve(Mq, -A3)
    except np.linalg.LinAlgError:
        Q = np.linalg.lstsq(Mq, -A3, rcond=None)[0]
    # resíduo da equação matricial A2 P^2 + A0 P + A1 = 0
    res = np.max(np.abs(A2 @ P @ P + A0 @ P + A1))
    if not np.isfinite(res) or res > 1e-6:
        raise IndeterminacyError(f"Resíduo da solução alto: {res:.3e}")
    eig = np.linalg.eigvals(P)
    if np.max(np.abs(eig)) > 1 + 1e-7:
        raise IndeterminacyError("Solução explosiva.")
    return Solution(P=P, Q=Q, eig=eig, n_stable=ns, residual=float(res))


def check(A0, A1, A2, A3, P, Q, tol=1e-8) -> float:
    n = A0.shape[0]
    # y_t = P y_{t-1} + Q e_t ; E_t y_{t+1} = P y_t
    lhs = A0 @ P + A1 + A2 @ P @ P
    rhs = -(A0 @ Q + A2 @ P @ Q + A3)
    return float(max(np.max(np.abs(lhs)), np.max(np.abs(rhs - 0))))


if __name__ == "__main__":
    # Teste 1: AR(1)
    rho = 0.8
    s = solve(np.array([[1.0]]), np.array([[-rho]]), np.array([[0.0]]), np.array([[-1.0]]))
    print("AR1 P,Q", s.P, s.Q, s.eig)
    # Teste 2: modelo forward simples x_t = E x_{t+1} + e_t
    s2 = solve(np.array([[1.0]]), np.array([[0.0]]), np.array([[-1.0]]), np.array([[-1.0]]))
    print("forward P,Q", s2.P, s2.Q, s2.eig)
