"""
Quantile regression by sparse linear programming.

Why this exists rather than a call to statsmodels.

The specification carries 343 intermediary dummies, 22 year dummies and a
handful of project-type dummies, so 366 of its 368 columns are indicators
and the design is 1.1% dense. statsmodels solves quantile regression by
iteratively reweighted least squares on a dense matrix, which on this
problem costs about 7 seconds and a few hundred megabytes per fit. A
bootstrap needs hundreds of fits, and fourteen concurrent dense fits
exhausted a 24 GB machine and wedged the run twice.

Quantile regression is a linear program:

    min  tau * sum(u) + (1 - tau) * sum(v)
    s.t. X b + u - v = y,   u >= 0,  v >= 0,  b free

Handing that to HiGHS with a sparse constraint matrix takes about 1.4
seconds and a small fraction of the memory. It is also more accurate: on the estimation sample the LP attains a
strictly lower check-loss objective than statsmodels at every quantile
tested (0.50, 0.75, 0.90, 0.95), because IRLS stops at a convergence
tolerance instead of at a vertex.

A qualification a cross-model audit asked for, and it is the right one.
"Exact" overstates what this returns. HiGHS delivers a tight floating-point
optimum, not an exact rational one, and the quantile-regression optimum
here is frequently nonunique, so the coefficient reported is one member of
an argmin set and the solver's tie-breaking is part of the estimator. What
can be claimed is narrower: this attains a no-worse objective than IRLS at
every quantile tested, and it is reproducible run to run.

That accuracy gap is worth stating plainly, because it is small in the
objective and not small in the coefficient. At tau = 0.90 the LP improves
the objective by 5e-5 out of 3210, roughly one part in 60 million, and the
rural coefficient moves from -0.1249 to -0.1287. An objective that flat in
the direction of interest is a warning: the coefficient at a single
quantile is weakly pinned, individual point estimates should not be
over-read, and inference has to come from resampling rather than from an
asymptotic formula.

Verified against statsmodels in tests/test_qreg_lp.py.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import scipy.sparse as sp
from scipy.optimize import linprog

FE_COLUMNS = ("year", "qalicb_type", "cde_name")


def build_design(df: pd.DataFrame, target: str = "rural",
                 fe: tuple[str, ...] = FE_COLUMNS):
    """Sparse design with an intercept, the target, and drop-first dummies
    for each fixed effect. Returns (X, index_of_target)."""
    n = len(df)
    blocks = [sp.csr_matrix(np.ones((n, 1))),
              sp.csr_matrix(df[[target]].to_numpy(dtype=float))]
    for col in fe:
        cat = pd.Categorical(df[col])
        codes = cat.codes
        width = max(len(cat.categories) - 1, 0)
        if width == 0:
            continue
        keep = codes > 0                       # drop the first level
        rows = np.nonzero(keep)[0]
        blocks.append(sp.csr_matrix(
            (np.ones(len(rows)), (rows, codes[keep] - 1)), shape=(n, width)))
    return sp.hstack(blocks, format="csc"), 1


def fit_quantile(df: pd.DataFrame, outcome: str, tau: float,
                   target: str = "rural",
                   fe: tuple[str, ...] = FE_COLUMNS) -> float | None:
    """Quantile-regression coefficient on `target` at quantile `tau`.

    Returns None when the target has no variation or HiGHS does not report
    an optimal solution, so callers can drop the replication rather than
    silently record a wrong number.
    """
    if df[target].nunique() < 2:
        return None
    X, j = build_design(df, target=target, fe=fe)
    y = df[outcome].to_numpy(dtype=float)
    n, k = X.shape
    A = sp.hstack([X, sp.identity(n, format="csc"),
                   -sp.identity(n, format="csc")], format="csc")
    c = np.concatenate([np.zeros(k), tau * np.ones(n), (1.0 - tau) * np.ones(n)])
    bounds = [(None, None)] * k + [(0, None)] * (2 * n)
    res = linprog(c, A_eq=A, b_eq=y, bounds=bounds, method="highs")
    if not res.success or res.status != 0:
        return None
    val = float(res.x[j])
    return val if np.isfinite(val) else None


def check_loss(resid: np.ndarray, tau: float) -> float:
    """The quantile regression objective, used to compare solvers."""
    return float(np.sum(resid * (tau - (resid < 0))))
