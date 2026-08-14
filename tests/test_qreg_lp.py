"""
The sparse LP quantile solver must be at least as good as the estimator it
replaces, and that has to be demonstrated rather than asserted.

Run: uv run --no-project --with pytest --with pandas --with numpy \
         --with scipy --with statsmodels python -m pytest tests/ -q
"""
from __future__ import annotations

import importlib.util
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("qreg_lp", ROOT / "scripts" / "qreg_lp.py")
qreg = importlib.util.module_from_spec(spec)
sys.modules["qreg_lp"] = qreg
spec.loader.exec_module(qreg)

FORMULA = "leverage_win ~ rural + C(year) + C(qalicb_type) + C(cde_name)"


@pytest.fixture(scope="module")
def pr() -> pd.DataFrame:
    df = pd.read_csv(ROOT / "data" / "processed" / "nmtc_projects.csv")
    df["rural"] = (df["metro"] == "non_metro").astype(int)
    df = df.dropna(subset=["leverage_win", "rural", "year", "qalicb_type",
                           "cde_name"]).reset_index(drop=True)
    df["year"] = df["year"].astype(int)
    return df


def test_design_is_sparse_and_correctly_shaped(pr):
    X, j = qreg.build_design(pr)
    assert j == 1
    n_levels = sum(pr[c].nunique() - 1 for c in qreg.FE_COLUMNS)
    assert X.shape == (len(pr), 2 + n_levels)
    assert X.nnz / (X.shape[0] * X.shape[1]) < 0.05      # genuinely sparse
    # the target column is reproduced exactly
    assert np.array_equal(np.asarray(X[:, 1].todense()).ravel(),
                          pr["rural"].to_numpy(dtype=float))


@pytest.mark.parametrize("tau", [0.5, 0.75, 0.9])
def test_lp_attains_no_worse_objective_than_statsmodels(pr, tau):
    """The claim justifying the swap: the LP is exact, IRLS stops early."""
    patsy = pytest.importorskip("patsy")
    smf = pytest.importorskip("statsmodels.formula.api")

    _, Xdm = patsy.dmatrices(FORMULA, pr, return_type="dataframe")
    Xd = Xdm.to_numpy(dtype=float)
    y = pr["leverage_win"].to_numpy(dtype=float)

    b_sm = smf.quantreg(FORMULA, pr).fit(q=tau).params.to_numpy()
    obj_sm = qreg.check_loss(y - Xd @ b_sm, tau)

    # solve with the LP on the identical design so objectives are comparable
    import scipy.sparse as sp
    from scipy.optimize import linprog
    n, k = Xd.shape
    A = sp.hstack([sp.csc_matrix(Xd), sp.identity(n, format="csc"),
                   -sp.identity(n, format="csc")], format="csc")
    c = np.concatenate([np.zeros(k), tau * np.ones(n), (1 - tau) * np.ones(n)])
    res = linprog(c, A_eq=A, b_eq=y,
                  bounds=[(None, None)] * k + [(0, None)] * (2 * n),
                  method="highs")
    obj_lp = qreg.check_loss(y - Xd @ res.x[:k], tau)

    assert obj_lp <= obj_sm + 1e-9, (
        f"LP objective {obj_lp} worse than statsmodels {obj_sm} at tau={tau}")


def test_median_coefficient_matches_statsmodels_closely(pr):
    """At the median the two agree; the divergence is a tail phenomenon."""
    smf = pytest.importorskip("statsmodels.formula.api")
    b_lp = qreg.fit_quantile(pr, "leverage_win", 0.5)
    b_sm = float(smf.quantreg(FORMULA, pr).fit(q=0.5).params["rural"])
    assert b_lp == pytest.approx(b_sm, abs=1e-4)


def test_returns_none_without_target_variation(pr):
    urban_only = pr[pr["rural"] == 0]
    assert qreg.fit_quantile(urban_only, "leverage_win", 0.5) is None


def test_solver_is_deterministic(pr):
    a = qreg.fit_quantile(pr, "leverage_win", 0.9)
    b = qreg.fit_quantile(pr, "leverage_win", 0.9)
    assert a == b
