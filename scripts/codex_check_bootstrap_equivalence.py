#!/usr/bin/env python3
"""Independent audit of the median QR cluster bootstrap and penalty bound.

This script deliberately does not read any committed regression JSON.  It
reconstructs the analysis sample from ``nmtc_projects.csv``, solves quantile
regression as a sparse linear program, and writes all audit results (including
the bootstrap draws) to a separate machine-readable JSON file.

Full audit defaults are intentionally recorded here:

* relabelled pairs reference bootstrap: 250 draws at seed 20260814;
* seed sensitivity: 100 draws at seeds 20260815, 20260816, and 20260817;
* matched pooled-label comparison: all 250 reference draws;
* exponential cluster multiplier bootstrap: 250 draws at seed 20261814;
* deliberately invalid iid-row bootstrap baseline: 100 draws at seed 20262814.

At most four worker processes are used.  Each long map emits a heartbeat.

Run from the repository root:

    UV_CACHE_DIR=/private/tmp/us-nmtc-codex-audit-20260814-cache UV_OFFLINE=1 \
      uv run --no-project --with pandas --with numpy --with scipy \
      --with statsmodels --with matplotlib python \
      scripts/codex_check_bootstrap_equivalence.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import scipy
import scipy.sparse as sp
import statsmodels
import statsmodels.formula.api as smf
from scipy import stats
from scipy.optimize import linprog


ROOT = Path(__file__).resolve().parent.parent
INPUT = ROOT / "data" / "processed" / "nmtc_projects.csv"
OUTPUT = (ROOT / "data" / "processed" / "regressions" /
          "codex_check_bootstrap_equivalence.json")
FORMULA = "leverage_win ~ rural + C(year) + C(qalicb_type) + C(cde_name)"
TAU = 0.5
SEEDS = {
    "pairs_main": 20260814,
    "pairs_sensitivity_1": 20260815,
    "pairs_sensitivity_2": 20260816,
    "pairs_sensitivity_3": 20260817,
    "multiplier": 20261814,
    "iid_broken_baseline": 20262814,
    "mc_uncertainty": 20263814,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int,
                        default=int(os.environ.get("CODEX_AUDIT_WORKERS", "4")))
    parser.add_argument("--pairs-main", type=int, default=250)
    parser.add_argument("--pairs-seed", type=int, default=100)
    parser.add_argument("--pooled", type=int, default=250)
    parser.add_argument("--multiplier", type=int, default=250)
    parser.add_argument("--iid-broken", type=int, default=100)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    if not 1 <= args.workers <= 4:
        parser.error("--workers must be between 1 and 4")
    for name in ("pairs_main", "pairs_seed", "pooled", "multiplier",
                 "iid_broken"):
        if getattr(args, name) < 2:
            parser.error(f"--{name.replace('_', '-')} must be at least 2")
    if args.pooled > args.pairs_main:
        parser.error("--pooled cannot exceed --pairs-main (matched draws)")
    return args


def load_data() -> pd.DataFrame:
    df = pd.read_csv(INPUT)
    df["rural"] = (df["metro"] == "non_metro").astype(int)
    needed = ["leverage_win", "rural", "year", "qalicb_type", "cde_name"]
    df = df.dropna(subset=needed).reset_index(drop=True)
    df["year"] = df["year"].astype(int)
    return df


def build_design(df: pd.DataFrame) -> sp.csc_matrix:
    """Intercept, rural, and drop-first year/type/CDE indicators."""
    n = len(df)
    blocks: list[sp.spmatrix] = [
        sp.csr_matrix(np.ones((n, 1))),
        sp.csr_matrix(df[["rural"]].to_numpy(dtype=float)),
    ]
    for col in ("year", "qalicb_type", "cde_name"):
        cat = pd.Categorical(df[col])
        width = len(cat.categories) - 1
        if width <= 0:
            continue
        keep = cat.codes > 0
        rows = np.flatnonzero(keep)
        blocks.append(sp.csr_matrix(
            (np.ones(len(rows)), (rows, cat.codes[keep] - 1)),
            shape=(n, width),
        ))
    return sp.hstack(blocks, format="csc")


def fit_weighted_qr(df: pd.DataFrame,
                    observation_weights: np.ndarray | None = None) -> float:
    """Solve weighted median regression exactly enough for the audit.

    Cluster multinomial counts and Exp(1) multiplier weights enter the
    check-loss objective.  Coefficients, including all FE, are free.
    """
    if df["rural"].nunique() < 2:
        raise RuntimeError("bootstrap sample has no rural variation")
    X = build_design(df)
    y = df["leverage_win"].to_numpy(dtype=float)
    n, k = X.shape
    if observation_weights is None:
        weights = np.ones(n)
    else:
        weights = np.asarray(observation_weights, dtype=float)
        if weights.shape != (n,) or np.any(weights <= 0):
            raise ValueError("weights must be positive and match the rows")
    A = sp.hstack([X, sp.identity(n, format="csc"),
                   -sp.identity(n, format="csc")], format="csc")
    c = np.concatenate([
        np.zeros(k), TAU * weights, (1.0 - TAU) * weights,
    ])
    bounds = [(None, None)] * k + [(0, None)] * (2 * n)
    result = linprog(c, A_eq=A, b_eq=y, bounds=bounds, method="highs")
    if not result.success or result.status != 0:
        raise RuntimeError(
            f"HiGHS failure status={result.status}: {result.message}")
    beta = float(result.x[1])
    if not np.isfinite(beta):
        raise RuntimeError("non-finite rural coefficient")
    return beta


_DF: pd.DataFrame | None = None
_NAMES: np.ndarray | None = None
_GROUP_ROWS: dict[str, np.ndarray] | None = None


def worker_init() -> None:
    global _DF, _NAMES, _GROUP_ROWS
    _DF = load_data()
    _GROUP_ROWS = {
        str(name): group.index.to_numpy()
        for name, group in _DF.groupby("cde_name", sort=True)
    }
    _NAMES = np.array(list(_GROUP_ROWS), dtype=object)


def cluster_draw(seed: int) -> np.ndarray:
    assert _NAMES is not None
    rng = np.random.default_rng(seed)
    return rng.choice(_NAMES, size=len(_NAMES), replace=True)


def pairs_relabelled(seed: int) -> float:
    """Literal cluster pairs bootstrap with a fresh FE label per draw."""
    assert _DF is not None and _GROUP_ROWS is not None
    frames = []
    for draw_number, name in enumerate(cluster_draw(seed)):
        copy = _DF.loc[_GROUP_ROWS[str(name)]].copy()
        copy["cde_name"] = f"draw_{draw_number}"
        frames.append(copy)
    return fit_weighted_qr(pd.concat(frames, ignore_index=True))


def pairs_pooled(seed: int) -> float:
    """Same multinomial draw, retaining original FE labels.

    Using the draw counts as check-loss weights is algebraically identical
    to physically pooling duplicate rows, but avoids needless row copies.
    """
    assert _DF is not None and _NAMES is not None and _GROUP_ROWS is not None
    drawn = cluster_draw(seed)
    names, counts = np.unique(drawn, return_counts=True)
    frames = []
    weights = []
    for name, count in zip(names, counts, strict=True):
        rows = _GROUP_ROWS[str(name)]
        frames.append(_DF.loc[rows])
        weights.append(np.full(len(rows), float(count)))
    return fit_weighted_qr(pd.concat(frames, ignore_index=True),
                           np.concatenate(weights))


def cluster_multiplier(seed: int) -> float:
    """Cluster-level Exp(1) exchangeably weighted/multiplier bootstrap."""
    assert _DF is not None and _NAMES is not None and _GROUP_ROWS is not None
    rng = np.random.default_rng(seed)
    cluster_weights = rng.exponential(scale=1.0, size=len(_NAMES))
    row_weights = np.empty(len(_DF), dtype=float)
    for name, weight in zip(_NAMES, cluster_weights, strict=True):
        row_weights[_GROUP_ROWS[str(name)]] = weight
    return fit_weighted_qr(_DF, row_weights)


def iid_row_broken(seed: int) -> float:
    """Deliberately invalid baseline: multinomially resample individual rows."""
    assert _DF is not None
    rng = np.random.default_rng(seed)
    counts = rng.multinomial(len(_DF), np.full(len(_DF), 1.0 / len(_DF)))
    keep = counts > 0
    return fit_weighted_qr(_DF.loc[keep].reset_index(drop=True),
                           counts[keep].astype(float))


def map_with_heartbeat(pool: ThreadPoolExecutor, fn, seeds: list[int],
                       label: str) -> list[float]:
    started = time.monotonic()
    values: list[float] = []
    for done, value in enumerate(pool.map(fn, seeds, chunksize=1), start=1):
        values.append(float(value))
        if done % 20 == 0 or done == len(seeds):
            elapsed = time.monotonic() - started
            print(f"HEARTBEAT {label}: {done}/{len(seeds)} "
                  f"({elapsed:.1f}s elapsed)", flush=True)
    return values


def mc_uncertainty_of_sd(values: list[float], seed_offset: int) -> dict:
    """Nonparametric MC uncertainty of an estimated bootstrap SD."""
    arr = np.asarray(values, dtype=float)
    rng = np.random.default_rng(SEEDS["mc_uncertainty"] + seed_offset)
    sd_replicates = np.empty(2000)
    for i in range(len(sd_replicates)):
        sd_replicates[i] = rng.choice(arr, size=len(arr), replace=True).std(ddof=1)
    return {
        "mcse_of_se_nonparametric": float(sd_replicates.std(ddof=1)),
        "mc_ci95_for_se_nonparametric": [
            float(np.quantile(sd_replicates, 0.025)),
            float(np.quantile(sd_replicates, 0.975)),
        ],
        "normal_reference_mcse_of_se": float(arr.std(ddof=1) /
                                                np.sqrt(2 * (len(arr) - 1))),
        "mc_resamples": int(len(sd_replicates)),
    }


def summarize(values: list[float], seed: int, seed_offset: int) -> dict:
    arr = np.asarray(values, dtype=float)
    result = {
        "seed": seed,
        "replications": int(len(arr)),
        "mean": float(arr.mean()),
        "se": float(arr.std(ddof=1)),
        "median": float(np.median(arr)),
        "q025": float(np.quantile(arr, 0.025)),
        "q975": float(np.quantile(arr, 0.975)),
        "draws": [float(x) for x in arr],
    }
    result.update(mc_uncertainty_of_sd(values, seed_offset))
    return result


def prefix_stability(values: list[float]) -> list[dict]:
    sizes = sorted({min(100, len(values)), min(250, len(values)), len(values)})
    return [
        {"replications": n,
         "se": float(np.std(values[:n], ddof=1)),
         "mean": float(np.mean(values[:n]))}
        for n in sizes if n >= 2
    ]


def penalty_bound_checks() -> dict:
    beta = -0.0467
    se = 0.1011
    z_convention = 1.645
    z_exact = float(stats.norm.ppf(0.95))
    delta = z_convention * se - beta
    # H0: beta <= -Delta; reject when (beta_hat + Delta)/se > z_.95.
    grid = [0.20, delta, 0.22]
    tests = []
    for margin in grid:
        statistic = (beta + margin) / se
        tests.append({
            "penalty_threshold": float(margin),
            "wald_statistic": float(statistic),
            "reject_with_strict_gt_1p645": bool(statistic > z_convention),
        })
    lower_margin = z_convention * se - beta
    upper_margin = z_convention * se + beta
    symmetric_equivalence_margin = max(lower_margin, upper_margin)
    assert abs(delta - 0.2130095) < 1e-12
    assert not tests[0]["reject_with_strict_gt_1p645"]
    assert not tests[1]["reject_with_strict_gt_1p645"]  # equality is boundary
    assert tests[2]["reject_with_strict_gt_1p645"]
    assert abs(symmetric_equivalence_margin - delta) < 1e-12
    return {
        "beta_hat": beta,
        "se": se,
        "z_convention": z_convention,
        "z_exact_norm_ppf_0p95": z_exact,
        "delta_star_convention": float(delta),
        "delta_star_exact_z": float(z_exact * se - beta),
        "null": "H0: beta <= -Delta",
        "alternative": "H1: beta > -Delta",
        "rejection_rule": "(beta_hat + Delta) / se > z_0.95",
        "solved_rule": "Delta > z_0.95 * se - beta_hat",
        "numerical_tests": tests,
        "tost_lower_boundary": float(lower_margin),
        "tost_upper_boundary": float(upper_margin),
        "minimum_symmetric_equivalence_margin": float(
            symmetric_equivalence_margin),
        "terminology": (
            "Correct as the one-sided noninferiority bound for ruling out a "
            "penalty. Full symmetric equivalence additionally requires the "
            "upper-side test; here beta_hat < 0, so the lower-side bound is "
            "the binding TOST condition and the numerical margin is the same."
        ),
    }


def main() -> None:
    args = parse_args()
    started = time.monotonic()
    df = load_data()
    print(f"DATA n={len(df)} CDEs={df['cde_name'].nunique()}", flush=True)

    # Independent M1 reconstruction from raw CSV.
    irls = smf.quantreg(FORMULA, df).fit(q=TAU, max_iter=5000)
    beta_irls = float(irls.params["rural"])
    se_asymptotic = float(irls.bse["rural"])
    beta_lp = fit_weighted_qr(df)
    print(f"POINT beta_lp={beta_lp:+.9f} beta_irls={beta_irls:+.9f} "
          f"asymptotic_se={se_asymptotic:.9f}", flush=True)

    main_seeds = [SEEDS["pairs_main"] + 1000 + i
                  for i in range(args.pairs_main)]
    seed1 = [SEEDS["pairs_sensitivity_1"] + 1000 + i
             for i in range(args.pairs_seed)]
    seed2 = [SEEDS["pairs_sensitivity_2"] + 1000 + i
             for i in range(args.pairs_seed)]
    seed3 = [SEEDS["pairs_sensitivity_3"] + 1000 + i
             for i in range(args.pairs_seed)]
    multiplier_seeds = [SEEDS["multiplier"] + 1000 + i
                        for i in range(args.multiplier)]
    iid_seeds = [SEEDS["iid_broken_baseline"] + 1000 + i
                 for i in range(args.iid_broken)]

    # Python 3.14's ProcessPoolExecutor calls sysconf(SC_SEM_NSEMS_MAX), which
    # is denied in the managed audit sandbox.  HiGHS releases the GIL, so a
    # bounded thread pool preserves parallel execution without semaphores.
    # Set the read-only worker globals once before starting the threads.
    worker_init()
    with ThreadPoolExecutor(max_workers=args.workers,
                            thread_name_prefix="codex-audit") as pool:
        main_draws = map_with_heartbeat(pool, pairs_relabelled, main_seeds,
                                        "pairs-relabelled-main")
        seed1_draws = map_with_heartbeat(pool, pairs_relabelled, seed1,
                                         "pairs-relabelled-seed-2")
        seed2_draws = map_with_heartbeat(pool, pairs_relabelled, seed2,
                                         "pairs-relabelled-seed-3")
        seed3_draws = map_with_heartbeat(pool, pairs_relabelled, seed3,
                                         "pairs-relabelled-seed-4")
        pooled_draws = map_with_heartbeat(pool, pairs_pooled,
                                          main_seeds[:args.pooled],
                                          "pairs-pooled-matched")
        multiplier_draws = map_with_heartbeat(pool, cluster_multiplier,
                                               multiplier_seeds,
                                               "cluster-multiplier")
        iid_draws = map_with_heartbeat(pool, iid_row_broken, iid_seeds,
                                       "iid-row-broken-baseline")

    pairs_main = summarize(main_draws, SEEDS["pairs_main"], 0)
    pairs_main["prefix_stability"] = prefix_stability(main_draws)
    pairs_seed1 = summarize(seed1_draws, SEEDS["pairs_sensitivity_1"], 1)
    pairs_seed2 = summarize(seed2_draws, SEEDS["pairs_sensitivity_2"], 2)
    pairs_seed3 = summarize(seed3_draws, SEEDS["pairs_sensitivity_3"], 3)
    pooled = summarize(pooled_draws, SEEDS["pairs_main"], 4)
    multiplier = summarize(multiplier_draws, SEEDS["multiplier"], 5)
    iid_broken = summarize(iid_draws, SEEDS["iid_broken_baseline"], 6)

    matched_relabelled = np.asarray(main_draws[:args.pooled])
    matched_pooled = np.asarray(pooled_draws)
    matched_diff = matched_relabelled - matched_pooled
    pooled_comparison = {
        "replications": args.pooled,
        "same_cluster_draws": True,
        "relabelled_se_on_matched_prefix": float(
            matched_relabelled.std(ddof=1)),
        "pooled_se": float(matched_pooled.std(ddof=1)),
        "se_difference": float(matched_pooled.std(ddof=1) -
                               matched_relabelled.std(ddof=1)),
        "max_abs_coefficient_difference": float(np.max(np.abs(matched_diff))),
        "median_abs_coefficient_difference": float(
            np.median(np.abs(matched_diff))),
        "share_abs_difference_gt_1e_7": float(
            np.mean(np.abs(matched_diff) > 1e-7)),
        "explanation": (
            "For multiplicity m_g, pooling gives m_g times cluster g's "
            "profiled check loss. Relabelling creates m_g identical FE "
            "subproblems whose minimized losses sum to the same value. Any "
            "coefficient difference is solver selection within a flat/nonunique "
            "optimum, not a different bootstrap estimand."
        ),
    }

    output = {
        "metadata": {
            "script": str(Path(__file__).relative_to(ROOT)),
            "input": str(INPUT.relative_to(ROOT)),
            "input_sha256": hashlib.sha256(INPUT.read_bytes()).hexdigest(),
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scipy": scipy.__version__,
            "statsmodels": statsmodels.__version__,
            "workers": args.workers,
            "worker_backend": "ThreadPoolExecutor (HiGHS releases GIL)",
            "fixed_seeds": SEEDS,
            "elapsed_seconds": float(time.monotonic() - started),
        },
        "sample": {
            "n_projects": int(len(df)),
            "n_cdes": int(df["cde_name"].nunique()),
            "mass_at_leverage_one": float(
                np.mean(df["leverage_win"].to_numpy() == 1.0)),
        },
        "point_estimate": {
            "lp": beta_lp,
            "statsmodels_irls": beta_irls,
            "asymptotic_se": se_asymptotic,
        },
        "pairs_relabelled": {
            "main": pairs_main,
            "seed_sensitivity": [pairs_seed1, pairs_seed2, pairs_seed3],
        },
        "pairs_pooled_matched": pooled,
        "pooled_vs_relabelled": pooled_comparison,
        "cluster_exponential_multiplier": multiplier,
        "iid_row_broken_baseline": iid_broken,
        "comparisons": {
            "pairs_se_over_asymptotic": float(pairs_main["se"] /
                                                 se_asymptotic),
            "multiplier_se_over_asymptotic": float(multiplier["se"] /
                                                      se_asymptotic),
            "iid_broken_se_over_pairs": float(iid_broken["se"] /
                                                  pairs_main["se"]),
        },
        "penalty_bound": penalty_bound_checks(),
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n")
    print("RESULT " + json.dumps({
        "beta_lp": beta_lp,
        "asymptotic_se": se_asymptotic,
        "pairs_se": pairs_main["se"],
        "pairs_inflation": output["comparisons"]["pairs_se_over_asymptotic"],
        "pooled_se_matched": pooled["se"],
        "max_matched_abs_diff": pooled_comparison[
            "max_abs_coefficient_difference"],
        "multiplier_se": multiplier["se"],
        "iid_broken_se": iid_broken["se"],
        "delta_star": output["penalty_bound"]["delta_star_convention"],
        "output": str(args.output),
    }, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
