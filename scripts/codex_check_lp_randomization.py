#!/usr/bin/env python3
"""Independent adversarial audit of claims C4--C6.

The script deliberately does not import the production qreg_lp module.  It
rebuilds the sparse quantile-regression LP, exercises two HiGHS algorithms,
and runs fixed-seed permutation controls with no more than four processes.

Run with the exact environment recorded in ``task-2-report.md``.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
import platform
import time
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

# A four-process pool must not silently become 4 x N BLAS threads.
for _thread_var in (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
):
    os.environ[_thread_var] = "1"

import numpy as np
import pandas as pd
import scipy
import scipy.sparse as sp
import statsmodels
import statsmodels.formula.api as smf
from scipy.optimize import linprog

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
INPUT = ROOT / "data" / "processed" / "nmtc_projects.csv"
OUTPUT = ROOT / "data" / "processed" / "regressions" / "codex_check_lp_randomization.json"

FORMULA = "leverage_win ~ rural + C(year) + C(qalicb_type) + C(cde_name)"
FE_COLUMNS = ("year", "qalicb_type", "cde_name")
TAU = 0.5
THRESHOLDS = (1e-7, 1e-6)
MAX_WORKERS = min(4, max(1, int(os.environ.get("CODEX_AUDIT_WORKERS", "4"))))

# Experimental design, fixed before the simulation runs.
SEEDS = {
    "production_replication_base": 20260814 + 5000,
    "jitter_outcome": 2026081402,
    "jitter_permutation_base": 2026082400,
    "continuous_outcome": 2026081403,
    "continuous_permutation_base": 2026083400,
    "conditioned_permutation_base": 2026084400,
}
REPLICATIONS = {
    "real_within_cde": 200,
    "jitter_within_cde": 64,
    "continuous_within_cde": 64,
    "real_within_cde_year_type": 120,
}
JITTER_SCALE = 1e-4


def run_provenance() -> dict[str, Any]:
    """Identify the exact input, script, interpreter, and numerical stack."""
    script_path = Path(__file__).resolve()
    return {
        "input_sha256": hashlib.sha256(INPUT.read_bytes()).hexdigest(),
        "script_sha256": hashlib.sha256(script_path.read_bytes()).hexdigest(),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "dependencies": {
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scipy": scipy.__version__,
            "statsmodels": statsmodels.__version__,
        },
    }


def load_sample() -> pd.DataFrame:
    """Rebuild the paper's estimation sample from the project file."""
    frame = pd.read_csv(INPUT)
    frame["rural"] = (frame["metro"] == "non_metro").astype(int)
    frame = frame.dropna(
        subset=["leverage_win", "rural", "year", "qalicb_type", "cde_name"]
    ).reset_index(drop=True)
    frame["year"] = frame["year"].astype(int)
    return frame


def independent_design(frame: pd.DataFrame) -> tuple[sp.csc_matrix, int, list[str]]:
    """Construct intercept, rural, and drop-first FE dummies independently."""
    n = len(frame)
    blocks: list[sp.spmatrix] = [
        sp.csr_matrix(np.ones((n, 1))),
        sp.csr_matrix(frame[["rural"]].to_numpy(float)),
    ]
    names = ["Intercept", "rural"]
    for col in FE_COLUMNS:
        cat = pd.Categorical(frame[col])
        levels = list(cat.categories)
        codes = cat.codes
        width = max(len(levels) - 1, 0)
        if width == 0:
            continue
        keep = codes > 0
        rows = np.flatnonzero(keep)
        blocks.append(
            sp.csr_matrix(
                (np.ones(len(rows)), (rows, codes[keep] - 1)),
                shape=(n, width),
            )
        )
        names.extend([f"{col}[{level}]" for level in levels[1:]])
    return sp.hstack(blocks, format="csc"), 1, names


def check_loss(residual: np.ndarray, tau: float = TAU) -> float:
    return float(np.sum(residual * (tau - (residual < 0))))


def solve_lp(
    frame: pd.DataFrame,
    outcome: np.ndarray,
    method: str = "highs",
) -> tuple[Any, sp.csc_matrix, np.ndarray, int, list[str], np.ndarray]:
    """Solve min check loss with every regression coefficient explicitly free."""
    X, target_index, names = independent_design(frame)
    y = np.asarray(outcome, dtype=float)
    n, k = X.shape
    A = sp.hstack(
        [X, sp.identity(n, format="csc"), -sp.identity(n, format="csc")],
        format="csc",
    )
    c = np.concatenate(
        [np.zeros(k), TAU * np.ones(n), (1.0 - TAU) * np.ones(n)]
    )
    bounds = [(None, None)] * k + [(0, None)] * (2 * n)
    result = linprog(c, A_eq=A, b_eq=y, bounds=bounds, method=method)
    return result, X, c, target_index, names, A


def solver_diagnostics(
    result: Any,
    X: sp.csc_matrix,
    A: sp.csc_matrix,
    c: np.ndarray,
    y: np.ndarray,
    target_index: int,
) -> dict[str, Any]:
    n, k = X.shape
    beta = result.x[:k]
    residual = y - X @ beta
    equality_error = A @ result.x - y
    dual = np.asarray(result.eqlin.marginals)
    reduced_cost = c - np.asarray(A.T @ dual).ravel()
    return {
        "success": bool(result.success),
        "status": int(result.status),
        "message": str(result.message),
        "iterations": int(result.nit),
        "crossover_iterations": int(getattr(result, "crossover_nit", 0)),
        "objective_reported": float(result.fun),
        "objective_check_loss": check_loss(np.asarray(residual)),
        "objective_absolute_difference": abs(float(result.fun) - check_loss(np.asarray(residual))),
        "rural_coefficient": float(beta[target_index]),
        "max_primal_equality_error": float(np.max(np.abs(equality_error))),
        "minimum_u_or_v": float(np.min(result.x[k:])),
        "max_free_variable_stationarity_error": float(np.max(np.abs(reduced_cost[:k]))),
        "minimum_nonnegative_variable_reduced_cost": float(np.min(reduced_cost[k:])),
        "max_complementarity_error": float(
            np.max(np.abs(result.x[k:] * reduced_cost[k:]))
        ),
        "negative_free_coefficients": int(np.sum(beta < -1e-10)),
        "n_free_coefficients": int(k),
    }


def solve_generic(
    X: np.ndarray,
    y: np.ndarray,
    method: str,
    free_coefficients: bool = True,
) -> dict[str, Any]:
    """Small dense known-answer LP, including a deliberately broken bound case."""
    Xs = sp.csc_matrix(np.asarray(X, float))
    y = np.asarray(y, float)
    n, k = Xs.shape
    A = sp.hstack(
        [Xs, sp.identity(n, format="csc"), -sp.identity(n, format="csc")],
        format="csc",
    )
    c = np.concatenate([np.zeros(k), 0.5 * np.ones(2 * n)])
    if free_coefficients:
        bounds = [(None, None)] * k + [(0, None)] * (2 * n)
    else:
        # SciPy's default nonnegative bounds are the deliberately broken baseline.
        bounds = None
    res = linprog(c, A_eq=A, b_eq=y, bounds=bounds, method=method)
    beta = res.x[:k]
    residual = y - Xs @ beta
    return {
        "method": method,
        "free_coefficients": free_coefficients,
        "success": bool(res.success),
        "status": int(res.status),
        "message": str(res.message),
        "beta": [float(v) for v in beta],
        "objective": float(res.fun),
        "check_loss": check_loss(np.asarray(residual)),
        "max_primal_error": float(np.max(np.abs(A @ res.x - y))),
    }


def threshold_shares(values: np.ndarray) -> dict[str, float]:
    values = np.asarray(values, float)
    return {
        f"abs_lt_{threshold:.0e}": float(np.mean(np.abs(values) < threshold))
        for threshold in THRESHOLDS
    }


def conditional_cell_summary(frame: pd.DataFrame) -> dict[str, Any]:
    """Describe outcome atoms in observed FE-defined conditional cells."""
    output: dict[str, Any] = {}
    for label, columns in {
        "cde": ["cde_name"],
        "year_type": ["year", "qalicb_type"],
        "cde_year_type": ["cde_name", "year", "qalicb_type"],
    }.items():
        grouped = frame.groupby(columns, observed=True)["leverage_win"]
        cells = grouped.agg(["size", "median"])
        cells["mass_one"] = grouped.apply(lambda s: float(np.mean(s.to_numpy() == 1.0)))
        eligible = cells[cells["size"] >= 5]
        at_one = eligible["median"] == 1.0
        output[label] = {
            "minimum_cell_size": 5,
            "eligible_cells": int(len(eligible)),
            "eligible_observations": int(eligible["size"].sum()),
            "cells_with_median_exactly_one": int(at_one.sum()),
            "share_eligible_cells_median_one": float(at_one.mean()) if len(eligible) else math.nan,
            "share_eligible_observations_in_median_one_cells": float(
                eligible.loc[at_one, "size"].sum() / eligible["size"].sum()
            ) if len(eligible) else math.nan,
            "weighted_mean_mass_at_one": float(
                np.average(eligible["mass_one"], weights=eligible["size"])
            ) if len(eligible) else math.nan,
        }
    return output


def full_covariate_cell_summary(frame: pd.DataFrame) -> dict[str, Any]:
    """Diagnose whether 1.0 lies in empirical median sets at repeated full X."""
    columns = ["cde_name", "year", "qalicb_type", "rural"]
    grouped = frame.groupby(columns, observed=True)["leverage_win"]
    cells = grouped.agg(
        size="size",
        below_one=lambda values: int(np.sum(values.to_numpy() < 1.0)),
        at_or_below_one=lambda values: int(np.sum(values.to_numpy() <= 1.0)),
    )
    eligible = cells[cells["size"] >= 5].copy()
    one_in_median_set = (
        (eligible["below_one"] < 0.5 * eligible["size"])
        & (eligible["at_or_below_one"] >= 0.5 * eligible["size"])
    )
    observations_in_median_cells = int(
        eligible.loc[one_in_median_set, "size"].sum()
    )
    return {
        "minimum_cell_size": 5,
        "total_cells": int(len(cells)),
        "eligible_cells": int(len(eligible)),
        "eligible_observations": int(eligible["size"].sum()),
        "cells_with_one_in_empirical_median_set": int(one_in_median_set.sum()),
        "observations_in_one_median_cells": observations_in_median_cells,
        "share_eligible_cells_one_in_median_set": float(one_in_median_set.mean()),
        "share_eligible_observations_in_one_median_cells": float(
            observations_in_median_cells / eligible["size"].sum()
        ),
        "share_full_sample_observations_in_one_median_cells": float(
            observations_in_median_cells / len(frame)
        ),
    }


def _cramers_v(rural: np.ndarray, codes: np.ndarray, n_levels: int) -> float:
    table = np.zeros((2, n_levels), dtype=float)
    np.add.at(table, (rural.astype(int), codes), 1.0)
    expected = table.sum(axis=1, keepdims=True) @ table.sum(axis=0, keepdims=True) / table.sum()
    valid = expected > 0
    chi2 = float(np.sum(((table - expected) ** 2)[valid] / expected[valid]))
    return math.sqrt(chi2 / table.sum())


def _group_shares(rural: np.ndarray, codes: np.ndarray, n_levels: int) -> np.ndarray:
    count = np.bincount(codes, minlength=n_levels)
    total = np.bincount(codes, weights=rural, minlength=n_levels)
    return np.divide(total, count, out=np.zeros(n_levels), where=count > 0)


def balance_metrics(frame: pd.DataFrame, rural: np.ndarray) -> dict[str, Any]:
    """Association of rural with year/type, both raw and after CDE demeaning."""
    rural = np.asarray(rural, float)
    cde_codes, cde_levels = pd.factorize(frame["cde_name"], sort=True)
    year_codes, year_levels = pd.factorize(frame["year"], sort=True)
    type_codes, type_levels = pd.factorize(frame["qalicb_type"], sort=True)
    joint_codes, joint_levels = pd.factorize(
        frame["year"].astype(str) + "|" + frame["qalicb_type"].astype(str), sort=True
    )
    cde_mean = _group_shares(rural, cde_codes, len(cde_levels))
    demeaned = rural - cde_mean[cde_codes]

    def weighted_rms(codes: np.ndarray, levels: int) -> float:
        counts = np.bincount(codes, minlength=levels)
        sums = np.bincount(codes, weights=demeaned, minlength=levels)
        means = np.divide(sums, counts, out=np.zeros(levels), where=counts > 0)
        return float(math.sqrt(np.sum(counts * means**2) / np.sum(counts)))

    return {
        "cramers_v_rural_year": _cramers_v(rural, year_codes, len(year_levels)),
        "cramers_v_rural_type": _cramers_v(rural, type_codes, len(type_levels)),
        "cramers_v_rural_year_type": _cramers_v(rural, joint_codes, len(joint_levels)),
        "within_cde_year_rms": weighted_rms(year_codes, len(year_levels)),
        "within_cde_type_rms": weighted_rms(type_codes, len(type_levels)),
        "within_cde_year_type_rms": weighted_rms(joint_codes, len(joint_levels)),
        "rural_share_by_year": _group_shares(rural, year_codes, len(year_levels)).tolist(),
        "rural_share_by_type": _group_shares(rural, type_codes, len(type_levels)).tolist(),
    }


_WORKER_FRAME: pd.DataFrame | None = None
_WORKER_OUTCOMES: dict[str, np.ndarray] | None = None
_WORKER_GROUPS: dict[str, list[np.ndarray]] | None = None
_OBS_YEAR_SHARES: np.ndarray | None = None
_OBS_TYPE_SHARES: np.ndarray | None = None


def init_worker() -> None:
    global _WORKER_FRAME, _WORKER_OUTCOMES, _WORKER_GROUPS
    global _OBS_YEAR_SHARES, _OBS_TYPE_SHARES
    frame = load_sample()
    real = frame["leverage_win"].to_numpy(float)
    jitter_rng = np.random.default_rng(SEEDS["jitter_outcome"])
    jitter = real + jitter_rng.uniform(-JITTER_SCALE, JITTER_SCALE, len(frame))
    continuous_rng = np.random.default_rng(SEEDS["continuous_outcome"])
    cde_codes, cde_levels = pd.factorize(frame["cde_name"], sort=True)
    type_codes, type_levels = pd.factorize(frame["qalicb_type"], sort=True)
    cde_effect = continuous_rng.normal(0.0, 0.08, len(cde_levels))
    type_effect = continuous_rng.normal(0.0, 0.04, len(type_levels))
    continuous = (
        1.25
        + 0.006 * (frame["year"].to_numpy(float) - frame["year"].mean())
        + cde_effect[cde_codes]
        + type_effect[type_codes]
        + continuous_rng.normal(0.0, 0.16, len(frame))
    )
    cde_groups = [g.index.to_numpy() for _, g in frame.groupby("cde_name", sort=False)]
    conditioned_groups = [
        g.index.to_numpy()
        for _, g in frame.groupby(["cde_name", "year", "qalicb_type"], sort=False, observed=True)
    ]
    observed_balance = balance_metrics(frame, frame["rural"].to_numpy(int))
    _WORKER_FRAME = frame
    _WORKER_OUTCOMES = {"real": real, "jitter": jitter, "continuous": continuous}
    _WORKER_GROUPS = {"cde": cde_groups, "conditioned": conditioned_groups}
    _OBS_YEAR_SHARES = np.asarray(observed_balance["rural_share_by_year"])
    _OBS_TYPE_SHARES = np.asarray(observed_balance["rural_share_by_type"])


def permutation_rep(job: tuple[str, str, int]) -> dict[str, Any]:
    outcome_name, group_name, seed = job
    assert _WORKER_FRAME is not None
    assert _WORKER_OUTCOMES is not None
    assert _WORKER_GROUPS is not None
    assert _OBS_YEAR_SHARES is not None and _OBS_TYPE_SHARES is not None
    rng = np.random.default_rng(seed)
    original = _WORKER_FRAME["rural"].to_numpy(int)
    rural = original.copy()
    for indices in _WORKER_GROUPS[group_name]:
        if len(indices) > 1:
            rural[indices] = rng.permutation(rural[indices])
    frame = _WORKER_FRAME.copy()
    frame["rural"] = rural
    outcome = _WORKER_OUTCOMES[outcome_name]
    result, X, _, target_index, _, _ = solve_lp(frame, outcome, method="highs-ds")
    if not result.success:
        return {"seed": seed, "success": False, "status": int(result.status)}
    beta = result.x[: X.shape[1]]
    residual = outcome - X @ beta
    balance = balance_metrics(frame, rural)
    return {
        "seed": seed,
        "success": True,
        "coefficient": float(beta[target_index]),
        "coefficient_thresholds": threshold_shares(np.array([beta[target_index]])),
        "residual_zero_thresholds": threshold_shares(np.asarray(residual)),
        "relabelled_share": float(np.mean(rural != original)),
        "max_abs_year_share_change": float(
            np.max(np.abs(np.asarray(balance["rural_share_by_year"]) - _OBS_YEAR_SHARES))
        ),
        "max_abs_type_share_change": float(
            np.max(np.abs(np.asarray(balance["rural_share_by_type"]) - _OBS_TYPE_SHARES))
        ),
        **{k: float(v) for k, v in balance.items() if not isinstance(v, list)},
    }


def run_jobs(label: str, jobs: list[tuple[str, str, int]]) -> list[dict[str, Any]]:
    print(f"HEARTBEAT start {label}: {len(jobs)} fits on {MAX_WORKERS} workers", flush=True)
    start = time.monotonic()
    output: list[dict[str, Any]] = []
    # ThreadPool avoids the managed macOS sandbox's forbidden SC_SEM_NSEMS_MAX
    # probe. HiGHS releases the GIL, and all numerical-library thread counts are
    # pinned to one above, so total solver parallelism remains at most four.
    if _WORKER_FRAME is None:
        init_worker()
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(permutation_rep, job) for job in jobs]
        for completed, future in enumerate(as_completed(futures), 1):
            output.append(future.result())
            if completed % 10 == 0 or completed == len(jobs):
                print(
                    f"HEARTBEAT {label}: {completed}/{len(jobs)} "
                    f"elapsed={time.monotonic() - start:.1f}s",
                    flush=True,
                )
    return sorted(output, key=lambda row: row["seed"])


def summarize_repetitions(records: list[dict[str, Any]], observed: float | None) -> dict[str, Any]:
    usable = [row for row in records if row.get("success")]
    coef = np.asarray([row["coefficient"] for row in usable])
    summary: dict[str, Any] = {
        "requested": len(records),
        "usable": len(usable),
        "coefficient_mean": float(np.mean(coef)),
        "coefficient_sd": float(np.std(coef, ddof=1)),
        "coefficient_quantiles_025_50_975": [float(v) for v in np.quantile(coef, [0.025, 0.5, 0.975])],
        "coefficient_pinning": {},
        "residual_zero_share_mean": {},
        "relabelled_share_mean": float(np.mean([r["relabelled_share"] for r in usable])),
        "max_abs_year_share_change_mean": float(np.mean([r["max_abs_year_share_change"] for r in usable])),
        "max_abs_type_share_change_mean": float(np.mean([r["max_abs_type_share_change"] for r in usable])),
    }
    for threshold in THRESHOLDS:
        key = f"abs_lt_{threshold:.0e}"
        indicators = np.abs(coef) < threshold
        share = float(np.mean(indicators))
        summary["coefficient_pinning"][key] = {
            "share": share,
            "mc_standard_error": float(math.sqrt(share * (1.0 - share) / len(coef))),
            "first_half_share": float(np.mean(indicators[: len(indicators) // 2])),
            "second_half_share": float(np.mean(indicators[len(indicators) // 2 :])),
        }
        summary["residual_zero_share_mean"][key] = float(
            np.mean([r["residual_zero_thresholds"][key] for r in usable])
        )
    balance_keys = [
        "cramers_v_rural_year",
        "cramers_v_rural_type",
        "cramers_v_rural_year_type",
        "within_cde_year_rms",
        "within_cde_type_rms",
        "within_cde_year_type_rms",
    ]
    summary["balance_distribution"] = {
        key: {
            "mean": float(np.mean([r[key] for r in usable])),
            "q025": float(np.quantile([r[key] for r in usable], 0.025)),
            "q975": float(np.quantile([r[key] for r in usable], 0.975)),
        }
        for key in balance_keys
    }
    if observed is not None:
        exceed = int(np.sum(np.abs(coef) >= abs(observed)))
        p_value = (exceed + 1.0) / (len(coef) + 1.0)
        summary["two_sided_permutation_p"] = float(p_value)
        summary["p_mc_standard_error_approx"] = float(
            math.sqrt(p_value * (1.0 - p_value) / (len(coef) + 1.0))
        )
        summary["exceedances"] = exceed
    summary["records"] = usable
    return summary


def checkpoint(results: dict[str, Any]) -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    temp = OUTPUT.with_suffix(".json.tmp")
    temp.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")
    temp.replace(OUTPUT)


def refresh_completed_results(
    stored: dict[str, Any], frame: pd.DataFrame
) -> dict[str, Any]:
    """Refresh deterministic evidence and summaries without fitting any model."""
    if stored.get("status") != "complete":
        raise ValueError("refusing to refresh an incomplete audit artifact")
    results = copy.deepcopy(stored)
    observed_beta = float(
        results["C5"]["highs_algorithms"]["highs-ds"]["rural_coefficient"]
    )
    permutation_results = {
        label: summarize_repetitions(
            block["records"],
            observed_beta
            if label in {"real_within_cde", "real_within_cde_year_type"}
            else None,
        )
        for label, block in results["permutations"].items()
    }
    results["permutations"] = permutation_results

    cell_atoms = conditional_cell_summary(frame)
    cell_atoms["cde_year_type_rural"] = full_covariate_cell_summary(frame)
    results["C4"]["observed_fe_cell_atoms"] = cell_atoms
    results["C4"]["permutation_vertex_controls"] = {
        "real": permutation_results["real_within_cde"],
        "continuous_jitter_broken_atom": permutation_results[
            "jitter_within_cde"
        ],
        "continuous_outcome_null": permutation_results["continuous_within_cde"],
    }

    observed_rural = frame["rural"].to_numpy(int)
    strata = frame.groupby(
        ["cde_name", "year", "qalicb_type"], sort=False, observed=True
    )["rural"].agg(["size", "sum"])
    mixed = (strata["sum"] > 0) & (strata["sum"] < strata["size"])
    results["C6"] = {
        "observed_balance": balance_metrics(frame, observed_rural),
        "conditioning_support": {
            "cde_year_type_strata": int(len(strata)),
            "mixed_strata": int(mixed.sum()),
            "observations_in_mixed_strata": int(strata.loc[mixed, "size"].sum()),
            "share_observations_in_mixed_strata": float(
                strata.loc[mixed, "size"].sum() / len(frame)
            ),
        },
        "within_cde_permutation": permutation_results["real_within_cde"],
        "within_cde_year_type_permutation": permutation_results[
            "real_within_cde_year_type"
        ],
    }
    results["provenance"] = run_provenance()
    return results


def main() -> None:
    started = time.monotonic()
    frame = load_sample()
    y = frame["leverage_win"].to_numpy(float)
    results: dict[str, Any] = {
        "status": "in_progress",
        "script": str(Path(__file__).relative_to(ROOT)),
        "input": str(INPUT.relative_to(ROOT)),
        "n_projects": int(len(frame)),
        "n_cdes": int(frame["cde_name"].nunique()),
        "tau": TAU,
        "thresholds": list(THRESHOLDS),
        "max_workers": MAX_WORKERS,
        "seeds": SEEDS,
        "replications": REPLICATIONS,
        "jitter_scale": JITTER_SCALE,
        "provenance": run_provenance(),
    }
    checkpoint(results)

    print("HEARTBEAT C5 real-sample solver comparison", flush=True)
    algorithm_results: dict[str, Any] = {}
    saved: dict[str, Any] = {}
    for method in ("highs-ds", "highs-ipm"):
        res, X, c, target_index, names, A = solve_lp(frame, y, method=method)
        if not res.success:
            algorithm_results[method] = {
                "success": False,
                "status": int(res.status),
                "message": str(res.message),
            }
            continue
        algorithm_results[method] = solver_diagnostics(
            res, X, A, c, y, target_index
        )
        saved[method] = (res, X, target_index, names)
    if "highs-ds" not in saved:
        raise RuntimeError("HiGHS dual simplex did not solve the real-sample LP")
    ds, X, target_index, names = saved["highs-ds"]
    beta = ds.x[: X.shape[1]]
    fitted = np.asarray(X @ beta)
    residual = y - fitted

    print("HEARTBEAT C5 statsmodels IRLS comparison", flush=True)
    irls = smf.quantreg(FORMULA, frame).fit(q=TAU)
    irls_residual = y - np.asarray(irls.model.exog @ irls.params.to_numpy())
    results["C5"] = {
        "lp_formulation": {
            "n_rows": int(X.shape[0]),
            "n_coefficients_all_explicitly_free": int(X.shape[1]),
            "n_nonnegative_positive_residuals": int(len(frame)),
            "n_nonnegative_negative_residuals": int(len(frame)),
            "target_column_index": int(target_index),
            "intercept_column_index": 0,
        },
        "highs_algorithms": algorithm_results,
        "statsmodels_irls": {
            "rural_coefficient": float(irls.params["rural"]),
            "asymptotic_se": float(irls.bse["rural"]),
            "objective_check_loss": check_loss(irls_residual),
            "iterations": int(getattr(irls, "iterations", -1)),
            "sparsity": float(irls.sparsity),
            "bandwidth": float(irls.bandwidth),
        },
        "known_answer_cases": {
            "unique_negative_line": {
                "expected_beta": [-3.0, -2.0],
                "expected_objective": 0.0,
                "free_highs_ds": solve_generic(
                    np.column_stack([np.ones(5), np.arange(-2, 3)]),
                    -3.0 - 2.0 * np.arange(-2, 3),
                    "highs-ds",
                    True,
                ),
                "free_highs_ipm": solve_generic(
                    np.column_stack([np.ones(5), np.arange(-2, 3)]),
                    -3.0 - 2.0 * np.arange(-2, 3),
                    "highs-ipm",
                    True,
                ),
                "broken_default_nonnegative_bounds": solve_generic(
                    np.column_stack([np.ones(5), np.arange(-2, 3)]),
                    -3.0 - 2.0 * np.arange(-2, 3),
                    "highs-ds",
                    False,
                ),
            },
            "nonunique_even_sample_median": {
                "symbolic_optimum_set": "intercept in [0, 2]",
                "symbolic_objective": 1.0,
                "highs_ds": solve_generic(np.ones((2, 1)), np.array([0.0, 2.0]), "highs-ds"),
                "highs_ipm": solve_generic(np.ones((2, 1)), np.array([0.0, 2.0]), "highs-ipm"),
            },
        },
    }
    checkpoint(results)

    base_zero = threshold_shares(residual)
    fitted_one = threshold_shares(fitted - 1.0)
    y_one = y == 1.0
    observed_cell_atoms = conditional_cell_summary(frame)
    observed_cell_atoms["cde_year_type_rural"] = full_covariate_cell_summary(
        frame
    )
    results["C4"] = {
        "unconditional": {
            "mass_at_exactly_one": float(np.mean(y_one)),
            "outcome_median": float(np.median(y)),
        },
        "conditional_lp_fit": {
            "fitted_quantile_min": float(np.min(fitted)),
            "fitted_quantile_median": float(np.median(fitted)),
            "fitted_quantile_max": float(np.max(fitted)),
            "unique_fitted_rounded_12dp": int(len(np.unique(np.round(fitted, 12)))),
            "fitted_quantiles_at_one": fitted_one,
            "zero_residual_share": base_zero,
            "negative_residual_share": float(np.mean(residual < -1e-7)),
            "positive_residual_share": float(np.mean(residual > 1e-7)),
            "zero_residual_count_from_y_equal_one": {
                f"abs_lt_{threshold:.0e}": int(np.sum((np.abs(residual) < threshold) & y_one))
                for threshold in THRESHOLDS
            },
            "share_zero_residuals_from_y_equal_one": {
                f"abs_lt_{threshold:.0e}": float(
                    np.sum((np.abs(residual) < threshold) & y_one)
                    / max(1, np.sum(np.abs(residual) < threshold))
                )
                for threshold in THRESHOLDS
            },
            "statsmodels_sparsity": float(irls.sparsity),
            "statsmodels_bandwidth": float(irls.bandwidth),
            "share_abs_residual_below_statsmodels_bandwidth": float(
                np.mean(np.abs(residual) <= irls.bandwidth)
            ),
        },
        "observed_fe_cell_atoms": observed_cell_atoms,
    }
    checkpoint(results)

    observed_beta = float(beta[target_index])
    scenarios = [
        (
            "real_within_cde",
            "real",
            "cde",
            SEEDS["production_replication_base"],
            REPLICATIONS["real_within_cde"],
            observed_beta,
        ),
        (
            "jitter_within_cde",
            "jitter",
            "cde",
            SEEDS["jitter_permutation_base"],
            REPLICATIONS["jitter_within_cde"],
            None,
        ),
        (
            "continuous_within_cde",
            "continuous",
            "cde",
            SEEDS["continuous_permutation_base"],
            REPLICATIONS["continuous_within_cde"],
            None,
        ),
        (
            "real_within_cde_year_type",
            "real",
            "conditioned",
            SEEDS["conditioned_permutation_base"],
            REPLICATIONS["real_within_cde_year_type"],
            observed_beta,
        ),
    ]
    permutation_results: dict[str, Any] = {}
    for label, outcome_name, group_name, seed_base, count, observed in scenarios:
        jobs = [(outcome_name, group_name, seed_base + i) for i in range(count)]
        records = run_jobs(label, jobs)
        permutation_results[label] = summarize_repetitions(records, observed)
        results["permutations"] = permutation_results
        checkpoint(results)

    observed_rural = frame["rural"].to_numpy(int)
    observed_balance = balance_metrics(frame, observed_rural)
    strata = frame.groupby(
        ["cde_name", "year", "qalicb_type"], sort=False, observed=True
    )["rural"].agg(["size", "sum"])
    mixed = (strata["sum"] > 0) & (strata["sum"] < strata["size"])
    results["C6"] = {
        "observed_balance": observed_balance,
        "conditioning_support": {
            "cde_year_type_strata": int(len(strata)),
            "mixed_strata": int(mixed.sum()),
            "observations_in_mixed_strata": int(strata.loc[mixed, "size"].sum()),
            "share_observations_in_mixed_strata": float(
                strata.loc[mixed, "size"].sum() / len(frame)
            ),
        },
        "within_cde_permutation": permutation_results["real_within_cde"],
        "within_cde_year_type_permutation": permutation_results[
            "real_within_cde_year_type"
        ],
    }
    results["C4"]["permutation_vertex_controls"] = {
        "real": permutation_results["real_within_cde"],
        "continuous_jitter_broken_atom": permutation_results["jitter_within_cde"],
        "continuous_outcome_null": permutation_results["continuous_within_cde"],
    }
    results["status"] = "complete"
    results["elapsed_seconds"] = float(time.monotonic() - started)
    checkpoint(results)
    print(f"HEARTBEAT complete elapsed={results['elapsed_seconds']:.1f}s output={OUTPUT}", flush=True)


def cli() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--refresh-completed-json",
        action="store_true",
        help=(
            "recompute deterministic diagnostics and summaries from the "
            "completed artifact's stored records without refitting"
        ),
    )
    args = parser.parse_args()
    if args.refresh_completed_json:
        stored = json.loads(OUTPUT.read_text())
        refreshed = refresh_completed_results(stored, load_sample())
        checkpoint(refreshed)
        print(
            "HEARTBEAT refreshed completed JSON from stored records; "
            "no model fits executed",
            flush=True,
        )
        return
    main()


if __name__ == "__main__":
    cli()
