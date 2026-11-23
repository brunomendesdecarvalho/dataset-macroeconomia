import numpy as np
from macrodata.dsge.solver import solve
from macrodata.dsge import small_nk as nk


def test_ar1():
    s = solve(np.array([[1.0]]), np.array([[-0.8]]), np.array([[0.0]]), np.array([[-1.0]]))
    assert abs(s.P[0, 0] - 0.8) < 1e-9
    assert abs(s.Q[0, 0] - 1.0) < 1e-9


def test_forward():
    s = solve(np.array([[1.0]]), np.array([[0.0]]), np.array([[-1.0]]), np.array([[-1.0]]))
    assert abs(s.P[0, 0]) < 1e-10


def test_nk_determinacy():
    sol, H = nk.solve_model(nk.BASE)
    assert sol.residual < 1e-8
    assert np.max(np.abs(sol.eig)) < 1.0
    assert H.shape == (3, len(nk.NAMES))
