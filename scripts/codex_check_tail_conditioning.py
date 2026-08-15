#!/usr/bin/env python3
"""Independent adversarial checks for audit claims C7--C8.

C7 independently resamples CDE clusters for the 0.90 and 0.95 fixed-effect
quantile-regression coefficients.  C8 compares three ways to hold year and
QALICB type fixed before forming rural-minus-urban paired gaps.

Reads:  data/processed/nmtc_projects.csv
Writes: data/processed/regressions/codex_check_tail_conditioning.json

Run with the repository's pinned audit environment; see task-3-report.md.
"""

from __future__ import annotations

import json
import hashlib
import os
import platform
import sys
import time
import warnings
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import scipy
import statsmodels
import statsmodels.formula.api as smf
import matplotlib
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
from qreg_lp import fit_quantile  # noqa: E402

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
INPUT_PATH = ROOT / "data" / "processed" / "nmtc_projects.csv"
OUTPUT_PATH = ROOT / "data" / "processed" / "regressions" / "codex_check_tail_conditioning.json"

# Initial fixed-seed full-run grid, specified before that full run.
C7_TAUS = (0.90, 0.95)
C8_TAUS = (0.50, 0.75, 0.90, 0.95)
C7_SEED_BASES = (2026081501, 2026181501, 2026281501, 2026381501)
C8_SEED_BASE = 2026481501
C8_FOLLOWUP_SEEDS = (2026581501, 2026681501, 2026781501, 2026881501)
C7_REPS_PER_SEED = int(os.environ.get("CODEX_C7_REPS_PER_SEED", 80))
C8_PLACEBO_REPS = int(os.environ.get("CODEX_C8_PLACEBO_REPS", 199))
C8_FOLLOWUP_REPS = int(os.environ.get("CODEX_C8_FOLLOWUP_REPS", 499))
MAX_WORKERS = min(4, max(1, int(os.environ.get("CODEX_MAX_WORKERS", 4))))
HEARTBEAT_EVERY = 20
MIN_SIDE = 5
EXACT_MIN_SIDE = 3
SHIFT_BASELINE = 0.50


def heartbeat(message: str) -> None:
    """Emit a timestamped progress marker."""
    print(f"[{time.strftime('%Y-%m-%dT%H:%M:%S')}] {message}", flush=True)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_data() -> pd.DataFrame:
    pr = pd.read_csv(INPUT_PATH)
    pr["rural"] = (pr["metro"] == "non_metro").astype(int)
    pr = pr.dropna(
        subset=["leverage_win", "rural", "year", "qalicb_type", "cde_name"]
    ).reset_index(drop=True)
    pr["year"] = pr["year"].astype(int)
    return pr


# C7 worker state. Each spawned worker loads the public processed input itself.
_C7_PR: pd.DataFrame | None = None
_C7_GROUPS: dict[str, np.ndarray] | None = None


def _init_c7_state(pr: pd.DataFrame) -> None:
    global _C7_PR, _C7_GROUPS
    _C7_PR = pr
    _C7_GROUPS = {
        str(name): group.index.to_numpy()
        for name, group in _C7_PR.groupby("cde_name", sort=True)
    }


def _c7_bootstrap_rep(job: tuple[int, float]) -> dict[str, Any]:
    seed, tau = job
    assert _C7_PR is not None and _C7_GROUPS is not None
    rng = np.random.default_rng(seed)
    names = np.array(list(_C7_GROUPS))
    drawn = rng.choice(names, size=len(names), replace=True)
    pieces: list[pd.DataFrame] = []
    for copy_number, name in enumerate(drawn):
        piece = _C7_PR.loc[_C7_GROUPS[str(name)]].copy()
        # Resampled copies are distinct fixed-effect clusters.
        piece["cde_name"] = f"{name}#{copy_number}"
        pieces.append(piece)
    sample = pd.concat(pieces, ignore_index=True)
    try:
        estimate = fit_quantile(sample, "leverage_win", tau)
    except Exception as exc:  # noqa: BLE001
        return {"seed": seed, "tau": tau, "estimate": None, "error": type(exc).__name__}
    return {"seed": seed, "tau": tau, "estimate": estimate, "error": None}


def _interval_summary(draws: np.ndarray, beta: float) -> dict[str, Any]:
    se = float(draws.std(ddof=1))
    pct = np.percentile(draws, [2.5, 97.5])
    return {
        "reps": int(len(draws)),
        "mean": float(draws.mean()),
        "se": se,
        "mcse_of_se_normal_approx": float(se / np.sqrt(2.0 * (len(draws) - 1))),
        "percentile_ci95": [float(pct[0]), float(pct[1])],
        "basic_ci95": [float(2.0 * beta - pct[1]), float(2.0 * beta - pct[0])],
        "normal_ci95": [float(beta - 1.96 * se), float(beta + 1.96 * se)],
        "share_nonnegative": float((draws >= 0).mean()),
    }


def run_c7(pr: pd.DataFrame) -> dict[str, Any]:
    heartbeat(
        f"C7 starting: {len(C7_SEED_BASES)} disjoint streams x "
        f"{C7_REPS_PER_SEED} reps x {len(C7_TAUS)} taus on {MAX_WORKERS} workers"
    )
    point: dict[float, float] = {}
    shifted: dict[float, float] = {}
    shifted_pr = pr.copy()
    shifted_pr["leverage_shifted"] = (
        shifted_pr["leverage_win"] + SHIFT_BASELINE * shifted_pr["rural"]
    )
    for tau in C7_TAUS:
        point[tau] = float(fit_quantile(pr, "leverage_win", tau))
        shifted[tau] = float(fit_quantile(shifted_pr, "leverage_shifted", tau))

    jobs: list[tuple[int, float]] = []
    job_meta: list[tuple[int, float, int]] = []
    for tau in C7_TAUS:
        for stream, base in enumerate(C7_SEED_BASES):
            for offset in range(C7_REPS_PER_SEED):
                jobs.append((base + int(tau * 100) * 10_000 + offset, tau))
                job_meta.append((stream, tau, offset))

    records: list[tuple[int, float, int, dict[str, Any]]] = []
    # Python 3.14's ProcessPoolExecutor probes SC_SEM_NSEMS_MAX, which the
    # audit sandbox denies. HiGHS releases the GIL, so a bounded thread pool
    # preserves parallelism without OS semaphores or copied mutable state.
    _init_c7_state(pr)
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        for done, (meta, result) in enumerate(
            zip(job_meta, pool.map(_c7_bootstrap_rep, jobs, chunksize=1)), start=1
        ):
            records.append((*meta, result))
            if done % HEARTBEAT_EVERY == 0 or done == len(jobs):
                heartbeat(f"C7 bootstrap heartbeat {done}/{len(jobs)}")

    by_tau: list[dict[str, Any]] = []
    prefix_sizes = sorted(
        {
            min(C7_REPS_PER_SEED, max(1, C7_REPS_PER_SEED // 4)),
            min(C7_REPS_PER_SEED, max(1, C7_REPS_PER_SEED // 2)),
            C7_REPS_PER_SEED,
        }
    )
    for tau in C7_TAUS:
        stream_arrays: list[np.ndarray] = []
        failures = 0
        stream_rows: list[dict[str, Any]] = []
        for stream, base in enumerate(C7_SEED_BASES):
            vals = [
                rec[3]["estimate"]
                for rec in records
                if rec[0] == stream and rec[1] == tau and rec[3]["estimate"] is not None
            ]
            failures += C7_REPS_PER_SEED - len(vals)
            arr = np.asarray(vals, dtype=float)
            stream_arrays.append(arr)
            stream_rows.append({"seed_base": base, **_interval_summary(arr, point[tau])})
        pooled = np.concatenate(stream_arrays)
        replication_sensitivity = []
        for prefix in prefix_sizes:
            prefix_draws = np.concatenate([arr[:prefix] for arr in stream_arrays])
            replication_sensitivity.append(
                {"reps_per_seed": prefix, **_interval_summary(prefix_draws, point[tau])}
            )
        pooled_summary = _interval_summary(pooled, point[tau])
        seed_ses = np.asarray([row["se"] for row in stream_rows], dtype=float)
        by_tau.append(
            {
                "tau": tau,
                "point_estimate": point[tau],
                "failed_reps": failures,
                "pooled": pooled_summary,
                "by_seed_stream": stream_rows,
                "replication_count_sensitivity": replication_sensitivity,
                "seed_se_range": [float(seed_ses.min()), float(seed_ses.max())],
                "seed_se_sd": float(seed_ses.std(ddof=1)),
                "percentile_excludes_zero": bool(
                    pooled_summary["percentile_ci95"][1] < 0
                    or pooled_summary["percentile_ci95"][0] > 0
                ),
                "normal_excludes_zero": bool(
                    pooled_summary["normal_ci95"][1] < 0
                    or pooled_summary["normal_ci95"][0] > 0
                ),
            }
        )
    return {
        "prediction": (
            "If the reported upper-tail inference is stable, independent CDE-cluster "
            "bootstrap SEs at tau 0.90 and 0.95 should remain near 0.125 and 0.215 "
            "across seed streams and neither 95% interval should exclude zero."
        ),
        "n_projects": int(len(pr)),
        "n_cdes": int(pr["cde_name"].nunique()),
        "workers": MAX_WORKERS,
        "reps_per_seed": C7_REPS_PER_SEED,
        "seed_bases": list(C7_SEED_BASES),
        "tail_results": by_tau,
        "broken_baseline": {
            "construction": f"add {SHIFT_BASELINE} to every rural outcome",
            "expected_coefficient_shift": SHIFT_BASELINE,
            "results": [
                {
                    "tau": tau,
                    "original_beta": point[tau],
                    "shifted_beta": shifted[tau],
                    "observed_shift": shifted[tau] - point[tau],
                }
                for tau in C7_TAUS
            ],
        },
        "studentized_interval": {
            "available": False,
            "reason": (
                "The exact LP estimator has no replication-level analytic SE. A valid "
                "bootstrap-t interval would require a nested cluster bootstrap inside "
                "each outer draw; it was not substituted with a non-equivalent quantity."
            ),
        },
    }


def additive_ols_residuals(pr: pd.DataFrame) -> np.ndarray:
    """Remove common additive year and QALICB-type conditional means."""
    design = pd.get_dummies(
        pr[["year", "qalicb_type"]].astype(str), drop_first=True, dtype=float
    )
    x = np.column_stack([np.ones(len(pr)), design.to_numpy(dtype=float)])
    y = pr["leverage_win"].to_numpy(dtype=float)
    coef, *_ = np.linalg.lstsq(x, y, rcond=None)
    return y - x @ coef


def quantile_residuals(pr: pd.DataFrame, tau: float) -> np.ndarray:
    """Remove additive year/type effects estimated at the requested quantile."""
    fit = smf.quantreg("leverage_win ~ C(year) + C(qalicb_type)", pr).fit(
        q=tau, max_iter=10_000, p_tol=1e-8
    )
    return pr["leverage_win"].to_numpy(dtype=float) - fit.predict(pr).to_numpy(dtype=float)


def paired_gaps(
    pr: pd.DataFrame, outcome: str, tau: float, min_side: int = MIN_SIDE
) -> np.ndarray:
    grouped = pr.groupby(["cde_name", "rural"])[outcome]
    quantiles = grouped.quantile(tau).unstack()
    counts = grouped.size().unstack()
    if 0 not in quantiles or 1 not in quantiles or 0 not in counts or 1 not in counts:
        return np.array([], dtype=float)
    eligible = ((counts[0] >= min_side) & (counts[1] >= min_side)).fillna(False)
    return (quantiles.loc[eligible, 1] - quantiles.loc[eligible, 0]).dropna().to_numpy(dtype=float)


def exact_cell_cde_gaps(
    pr: pd.DataFrame, tau: float, min_side: int = EXACT_MIN_SIDE
) -> tuple[np.ndarray, int]:
    """Aggregate supported exact-cell quantile gaps to one weighted gap per CDE.

    Each CDE×year×type cell must contain ``min_side`` observations on both sides.
    Cell gaps receive weight min(n_rural, n_urban), then inference is across CDEs.
    """
    keys = ["cde_name", "year", "qalicb_type", "rural"]
    grouped = pr.groupby(keys)["leverage_win"]
    quantiles = grouped.quantile(tau).unstack()
    counts = grouped.size().unstack()
    if 0 not in quantiles or 1 not in quantiles or 0 not in counts or 1 not in counts:
        return np.array([], dtype=float), 0
    eligible = ((counts[0] >= min_side) & (counts[1] >= min_side)).fillna(False)
    cells = pd.DataFrame(
        {
            "gap": quantiles.loc[eligible, 1] - quantiles.loc[eligible, 0],
            "weight": np.minimum(counts.loc[eligible, 0], counts.loc[eligible, 1]),
        }
    ).dropna()
    if cells.empty:
        return np.array([], dtype=float), 0
    cells = cells.reset_index()
    cde_gaps = cells.groupby("cde_name").apply(
        lambda frame: np.average(frame["gap"], weights=frame["weight"]),
        include_groups=False,
    )
    return cde_gaps.to_numpy(dtype=float), int(len(cells))


def paired_test_summary(gaps: np.ndarray) -> dict[str, Any]:
    if not len(gaps):
        return {"n_pairs": 0, "estimable": False}
    nonzero = gaps[gaps != 0]
    wilcoxon_p = None
    if len(nonzero):
        wilcoxon_p = float(stats.wilcoxon(gaps, zero_method="wilcox").pvalue)
    sign_p = None
    if len(nonzero):
        sign_p = float(stats.binomtest(int((nonzero > 0).sum()), len(nonzero), 0.5).pvalue)
    return {
        "n_pairs": int(len(gaps)),
        "n_nonzero": int(len(nonzero)),
        "median_gap": float(np.median(gaps)),
        "mean_gap": float(gaps.mean()),
        "iqr": [float(np.percentile(gaps, 25)), float(np.percentile(gaps, 75))],
        "share_negative": float((gaps < 0).mean()),
        "wilcoxon_p": wilcoxon_p,
        "sign_p": sign_p,
        "estimable": True,
    }


def permute_labels(
    pr: pd.DataFrame, rng: np.random.Generator, strata: list[str]
) -> pd.DataFrame:
    shuffled = pr.copy()
    rural = shuffled["rural"].to_numpy().copy()
    for indices in shuffled.groupby(strata, sort=False).indices.values():
        idx = np.asarray(indices, dtype=int)
        if len(idx) > 1:
            rural[idx] = rng.permutation(rural[idx])
    shuffled["rural"] = rural
    return shuffled


def randomization_summary(
    pr: pd.DataFrame,
    outcome: str,
    tau: float,
    observed: float,
    seed: int,
    exact_cells: bool = False,
    conditional: bool = True,
    draws: int = C8_PLACEBO_REPS,
) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    strata = ["cde_name", "year", "qalicb_type"] if conditional else ["cde_name"]
    null: list[float] = []
    for rep in range(draws):
        shuffled = permute_labels(pr, rng, strata)
        if exact_cells:
            gaps, _ = exact_cell_cde_gaps(shuffled, tau)
        else:
            gaps = paired_gaps(shuffled, outcome, tau)
        if len(gaps):
            null.append(float(np.median(gaps)))
        if (rep + 1) % 100 == 0 or rep + 1 == draws:
            heartbeat(
                f"C8 placebo tau={tau:.2f} outcome={outcome} "
                f"conditional={conditional} {rep + 1}/{draws}"
            )
    arr = np.asarray(null, dtype=float)
    extreme_count = int((np.abs(arr) >= abs(observed)).sum())
    return {
        "draws": int(len(arr)),
        "seed": seed,
        "strata": strata,
        "null_median_mean": float(arr.mean()),
        "null_sd": float(arr.std(ddof=1)),
        "null_ci95": [float(np.percentile(arr, 2.5)), float(np.percentile(arr, 97.5))],
        "extreme_count": extreme_count,
        "p_two_sided": float((extreme_count + 1) / (len(arr) + 1)),
    }


def holm_adjust(pvalues: list[float | None]) -> list[float | None]:
    adjusted: list[float | None] = [None] * len(pvalues)
    present = [(i, p) for i, p in enumerate(pvalues) if p is not None]
    ordered = sorted(present, key=lambda item: item[1])
    running = 0.0
    m = len(ordered)
    for rank, (index, pvalue) in enumerate(ordered):
        running = max(running, (m - rank) * pvalue)
        adjusted[index] = min(1.0, running)
    return adjusted


def run_c8(pr: pd.DataFrame) -> dict[str, Any]:
    heartbeat(f"C8 starting with {C8_PLACEBO_REPS} placebo draws per method/tau")
    work = pr.copy()
    work["resid_ols"] = additive_ols_residuals(work)
    method_estimands = {
        "unadjusted": (
            "Median CDE-level difference between rural and urban marginal outcome "
            "quantiles; year/type composition may differ."
        ),
        "ols_year_type_residual": (
            "Median CDE-level rural-minus-urban quantile gap after subtracting common "
            "additive year/type conditional-mean effects."
        ),
        "quantile_year_type_residual": (
            "Median CDE-level rural-minus-urban residual quantile gap after subtracting "
            "common additive year/type effects estimated at the same quantile."
        ),
        "exact_cde_year_type": (
            "Median across CDEs of overlap-weighted rural-minus-urban quantile gaps "
            "computed inside supported CDE×year×type cells."
        ),
    }
    results: list[dict[str, Any]] = []
    for tau_index, tau in enumerate(C8_TAUS):
        heartbeat(f"C8 tau={tau:.2f}: estimating residualizations and paired gaps")
        work["resid_quantile"] = quantile_residuals(work, tau)
        methods: list[tuple[str, str, bool, bool]] = [
            ("unadjusted", "leverage_win", False, False),
            ("ols_year_type_residual", "resid_ols", False, True),
            ("quantile_year_type_residual", "resid_quantile", False, True),
            ("exact_cde_year_type", "leverage_win", True, True),
        ]
        for method_index, (method, outcome, exact_cells, conditional) in enumerate(methods):
            if exact_cells:
                gaps, n_cells = exact_cell_cde_gaps(work, tau)
            else:
                gaps = paired_gaps(work, outcome, tau)
                n_cells = None
            summary = paired_test_summary(gaps)
            if not summary["estimable"]:
                results.append(
                    {"tau": tau, "method": method, "estimand": method_estimands[method], **summary}
                )
                continue
            placebo_seed = C8_SEED_BASE + tau_index * 100_000 + method_index * 10_000
            placebo = randomization_summary(
                work,
                outcome,
                tau,
                summary["median_gap"],
                placebo_seed,
                exact_cells=exact_cells,
                conditional=conditional,
            )
            results.append(
                {
                    "tau": tau,
                    "method": method,
                    "estimand": method_estimands[method],
                    "min_side": EXACT_MIN_SIDE if exact_cells else MIN_SIDE,
                    "n_exact_cells": n_cells,
                    **summary,
                    "randomization": placebo,
                }
            )

    inferential = [row for row in results if row.get("method") != "unadjusted"]
    for field in ("wilcoxon_p", "sign_p"):
        adjusted = holm_adjust([row.get(field) for row in inferential])
        for row, value in zip(inferential, adjusted):
            row[f"{field}_holm_across_conditioned_methods_and_taus"] = value
    placebo_adjusted = holm_adjust(
        [row.get("randomization", {}).get("p_two_sided") for row in inferential]
    )
    for row, value in zip(inferential, placebo_adjusted):
        row["randomization_p_holm_across_conditioned_methods_and_taus"] = value

    ols_rows = [row for row in results if row.get("method") == "ols_year_type_residual"]
    ols_placebo_adjusted = holm_adjust(
        [row.get("randomization", {}).get("p_two_sided") for row in ols_rows]
    )
    for row, value in zip(ols_rows, ols_placebo_adjusted):
        row["randomization_p_holm_across_ols_taus"] = value

    # This was selected only after the initial fixed-seed full-run grid exposed
    # a raw p=.005
    # at tau=.90. Keep it separate and label it post hoc rather than folding it
    # into the original family as if it had been specified in advance.
    followup_frame = work.copy()
    followup_gaps = paired_gaps(followup_frame, "resid_ols", 0.90)
    followup_observed = float(np.median(followup_gaps))
    followup_streams = [
        randomization_summary(
            followup_frame,
            "resid_ols",
            0.90,
            followup_observed,
            seed,
            conditional=True,
            draws=C8_FOLLOWUP_REPS,
        )
        for seed in C8_FOLLOWUP_SEEDS
    ]
    followup_extreme = sum(row["extreme_count"] for row in followup_streams)
    followup_draws = sum(row["draws"] for row in followup_streams)

    sensitivity = []
    for min_side in (3, 5):
        for tau in C8_TAUS:
            gaps = paired_gaps(work, "resid_ols", tau, min_side=min_side)
            sensitivity.append(
                {"method": "ols_year_type_residual", "min_side": min_side, "tau": tau, **paired_test_summary(gaps)}
            )
    return {
        "prediction": (
            "If the unadjusted T2/T3 pattern is compositional, holding year and "
            "QALICB type fixed should materially attenuate its paired gaps and tests."
        ),
        "n_projects": int(len(pr)),
        "n_cdes": int(pr["cde_name"].nunique()),
        "taus": list(C8_TAUS),
        "paired_min_side": MIN_SIDE,
        "exact_cell_min_side": EXACT_MIN_SIDE,
        "placebo_reps": C8_PLACEBO_REPS,
        "placebo_seed_base": C8_SEED_BASE,
        "results": results,
        "post_hoc_tau_090_ols_randomization_seed_sensitivity": {
            "selection_note": (
                "Post hoc follow-up selected because the initial fixed-seed "
                "full-run grid's 199-draw conditional randomization p-value was 0.005."
            ),
            "observed_median_gap": followup_observed,
            "draws_per_seed": C8_FOLLOWUP_REPS,
            "seed_streams": followup_streams,
            "combined_extreme_count": followup_extreme,
            "combined_draws": followup_draws,
            "combined_p_two_sided": float((followup_extreme + 1) / (followup_draws + 1)),
        },
        "min_side_sensitivity": sensitivity,
        "multiplicity": (
            "The conservative Holm family jointly covers 12 conditioned "
            "method×tau tests, separately for Wilcoxon, sign, and randomization "
            "p-values. Randomization p-values also report a four-test Holm "
            "sensitivity for the requested primary OLS residualization alone."
        ),
    }


def main() -> None:
    started = time.time()
    pr = load_data()
    heartbeat(f"loaded {len(pr)} projects across {pr['cde_name'].nunique()} CDEs")
    result = {
        "script": str(Path(__file__).relative_to(ROOT)),
        "input": str(INPUT_PATH.relative_to(ROOT)),
        "generated_at_local": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "provenance": {
            "script_sha256": sha256_file(Path(__file__)),
            "input_sha256": sha256_file(INPUT_PATH),
            "platform": platform.platform(),
            "python": sys.version,
            "dependencies": {
                "numpy": np.__version__,
                "pandas": pd.__version__,
                "scipy": scipy.__version__,
                "statsmodels": statsmodels.__version__,
                "matplotlib": matplotlib.__version__,
            },
        },
        "experimental_design": {
            "design_timing": (
                "initial fixed-seed full-run grid, specified before that full run"
            ),
            "max_workers": MAX_WORKERS,
            "c7_taus": list(C7_TAUS),
            "c7_seed_bases": list(C7_SEED_BASES),
            "c7_reps_per_seed": C7_REPS_PER_SEED,
            "c8_taus": list(C8_TAUS),
            "c8_placebo_seed_base": C8_SEED_BASE,
            "c8_placebo_reps": C8_PLACEBO_REPS,
            "c8_followup_seed_bases": list(C8_FOLLOWUP_SEEDS),
            "c8_followup_reps_per_seed": C8_FOLLOWUP_REPS,
            "diagnostics": [
                "bootstrap mean/SE/MCSE",
                "percentile/basic/normal intervals",
                "seed and replication-count sensitivity",
                "median/mean/IQR/share-negative paired gaps",
                "Wilcoxon/sign/randomization tests with Holm sensitivity",
            ],
        },
        "C7": run_c7(pr),
        "C8": run_c8(pr),
    }
    result["elapsed_seconds"] = time.time() - started
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    heartbeat(f"wrote {OUTPUT_PATH.relative_to(ROOT)} in {result['elapsed_seconds']:.1f}s")


if __name__ == "__main__":
    main()
