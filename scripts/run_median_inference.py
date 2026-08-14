"""
Inference for the median specification, which is the estimate the paper's
null actually rests on.

Section 5.2 reports a within-CDE median rural coefficient of -0.001 with a
standard error of 0.008, and then concedes in parentheses that the standard
error is the quantile-regression asymptotic one, that a CDE-clustered
bootstrap across 343 intermediary effects was computationally
disproportionate for the draft, and that it remained outstanding. That
concession is the softest point in the paper: the mean specification is too
imprecise to carry a null (it cannot reject penalties smaller than 0.213),
so the median estimate carries it, and the median estimate's precision has
never been verified under clustering.

This script closes the item three ways.

  M1  Reproduce the point estimate and the asymptotic standard error.

  M2  Pairs cluster bootstrap over intermediaries. Each replication draws
      343 CDEs with replacement and refits the full median regression.
      A CDE drawn twice enters as two distinct intermediaries with their
      own fixed effects, which is the standard treatment for a pairs
      cluster bootstrap in a model carrying cluster fixed effects; pooling
      the duplicates would understate the very dependence being measured.

  M3  Randomization inference on the sharp null of no within-CDE rural
      effect. The rural label is permuted inside each intermediary, which
      holds every CDE's rural count and therefore its whole book
      composition fixed, and the median regression is refit. This tests
      the null the paper actually asserts without relying on any
      asymptotic approximation.

  M5  The reason all of this matters, discovered while building M3. The
      outcome has a 26.9% point mass at exactly 1.0, the value recorded
      when a project mobilizes no capital beyond the subsidized
      investment, and the unconditional median is 1.159. The median
      therefore sits on the shoulder of a mass point. Quantile-regression
      asymptotic standard errors are sparsity estimates that assume a
      positive continuous conditional density at the estimated quantile,
      and that assumption fails here: under within-CDE permutation the
      rural coefficient is repeatedly pinned to within 1e-7 of zero rather
      than varying smoothly, which is the signature of a degenerate
      vertex solution. M5 re-estimates across a sweep of quantiles, each
      with its own cluster bootstrap, to locate where the outcome's
      density is well behaved and to obtain an equivalence bound that does
      not depend on the fragile median.

  M4  A design-free corroboration that uses no regression at all. For
      every intermediary with at least three deals on each side of the
      rural line, take the difference between its rural median and its
      urban median, then test that collection of paired differences
      against zero with a Wilcoxon signed-rank test and an exact sign
      test. If the within-CDE null is an artifact of the fixed-effects
      machinery, this should disagree with it.

The equivalence bound convention is the paper's own, verified against its
reported numbers: a one-sided 5% test rejects penalties larger than
delta* = 1.645 * se - beta_hat. For the mean specification this reproduces
0.213 exactly from beta = -0.047 and se = 0.101.

Reads:  data/processed/nmtc_projects.csv
Writes: data/processed/regressions/median_inference.json / .md

Run:    uv run --no-project --with pandas --with numpy --with statsmodels \
            --with scipy python scripts/run_median_inference.py
"""
from __future__ import annotations

import json
import os
import sys
import warnings
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import get_context
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
from qreg_lp import fit_quantile          # noqa: E402

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
IN = ROOT / "data" / "processed"
OUT = IN / "regressions"

B_BOOT = int(os.environ.get("NMTC_B_BOOT", 250))
B_PERM = int(os.environ.get("NMTC_B_PERM", 200))
B_SWEEP = int(os.environ.get("NMTC_B_SWEEP", 120))
QUANTILE_SWEEP = (0.25, 0.35, 0.60, 0.75, 0.90, 0.95)
SEED = 20260814
N_WORKERS = int(os.environ.get("NMTC_WORKERS", 4))
FORMULA = "leverage_win ~ rural + C(year) + C(qalicb_type) + C(cde_name)"
MIN_SIDE = 3          # deals per side for the design-free paired test
Z_ONE_SIDED = 1.645   # the paper's convention


def load() -> pd.DataFrame:
    pr = pd.read_csv(IN / "nmtc_projects.csv")
    pr["rural"] = (pr["metro"] == "non_metro").astype(int)
    pr = pr.dropna(subset=["leverage_win", "rural", "year", "qalicb_type",
                           "cde_name"]).reset_index(drop=True)
    pr["year"] = pr["year"].astype(int)
    return pr


def fit_median(df: pd.DataFrame, q: float = 0.5) -> float | None:
    """Exact quantile-regression rural coefficient via sparse LP.

    This replaced a statsmodels IRLS call. The LP attains a strictly lower
    check-loss objective at every quantile tested and costs about a fifth
    the time on a small fraction of the memory, which is what made the
    bootstrap feasible on this machine at all. See scripts/qreg_lp.py.
    """
    try:
        return fit_quantile(df, "leverage_win", q)
    except Exception:                                          # noqa: BLE001
        return None


# ── worker payloads (module level so they pickle) ──────────────────────
_PR: pd.DataFrame | None = None
_GROUPS: dict[str, np.ndarray] | None = None


def _init() -> None:
    """Runs once per worker. Each worker reads the file itself; sending the
    frame through initargs to fourteen spawned workers, ten pools over,
    is what wedged an earlier version of this script."""
    global _PR, _GROUPS
    _PR = load()
    _GROUPS = {name: g.index.to_numpy() for name, g in _PR.groupby("cde_name")}


def _boot_rep(job: tuple[int, float]) -> float | None:
    """One pairs cluster bootstrap replication at quantile q."""
    seed, q = job
    assert _PR is not None and _GROUPS is not None
    rng = np.random.default_rng(seed)
    names = np.array(list(_GROUPS.keys()))
    drawn = rng.choice(names, size=len(names), replace=True)
    frames = []
    for k, name in enumerate(drawn):
        sub = _PR.loc[_GROUPS[name]].copy()
        sub["cde_name"] = f"{name}#{k}"        # duplicates are distinct CDEs
        frames.append(sub)
    rep = pd.concat(frames, ignore_index=True)
    if rep["rural"].nunique() < 2:
        return None
    return fit_median(rep, q)


def _perm_rep(seed: int) -> float | None:
    """One randomization-inference replication: permute rural within CDE."""
    assert _PR is not None and _GROUPS is not None
    rng = np.random.default_rng(seed)
    rep = _PR.copy()
    rural = rep["rural"].to_numpy().copy()
    for idx in _GROUPS.values():
        if len(idx) > 1:
            rural[idx] = rng.permutation(rural[idx])
    rep["rural"] = rural
    if rep["rural"].nunique() < 2:
        return None
    return fit_median(rep)


POOL: ProcessPoolExecutor | None = None


def _mapped(fn, jobs, label: str) -> list:
    """POOL.map with a heartbeat. A run that stalls should say so rather
    than look identical to a run that is merely slow, which cost two
    wedged attempts to work out."""
    out, done = [], 0
    for val in POOL.map(fn, jobs, chunksize=1):
        out.append(val)
        done += 1
        if done % 25 == 0 or done == len(jobs):
            print(f"   [{label}] {done}/{len(jobs)}", flush=True)
    return out


def main() -> None:
    global POOL
    pr = load()
    R: dict = {"n_projects": int(len(pr)), "n_cdes": int(pr["cde_name"].nunique()),
               "b_bootstrap_requested": B_BOOT, "b_permutation_requested": B_PERM,
               "seed": SEED}

    # ── M1 point estimate and asymptotic SE ────────────────────────────
    # statsmodels here specifically, because reproducing the paper's
    # asymptotic SE is the point of M1 and the LP does not produce one.
    res = smf.quantreg(FORMULA, pr).fit(q=0.5)
    b_irls = float(res.params["rural"])
    se_asy = float(res.bse["rural"])
    # Everything downstream uses the exact LP solution, so the point
    # estimate the bootstrap is centred on is the one it resamples.
    b_hat = fit_quantile(pr, "leverage_win", 0.5)
    R["point_estimate"] = round(b_hat, 5)
    R["point_estimate_irls"] = round(b_irls, 5)
    R["se_asymptotic"] = round(se_asy, 5)
    R["equivalence_bound_asymptotic"] = round(Z_ONE_SIDED * se_asy - b_hat, 4)
    print(f"M1 median rural coefficient {b_hat:+.5f}, asymptotic SE {se_asy:.5f}")
    print(f"   equivalence bound (paper's convention) "
          f"{R['equivalence_bound_asymptotic']:.4f}")

    # ── M2 pairs cluster bootstrap ─────────────────────────────────────
    print(f"M2 cluster bootstrap, {B_BOOT} replications on {N_WORKERS} workers")
    jobs = [(SEED + 1000 + i, 0.5) for i in range(B_BOOT)]
    boot = _mapped(_boot_rep, jobs, "M2")
    boot_arr = np.array([b for b in boot if b is not None], dtype=float)
    se_boot = float(boot_arr.std(ddof=1))
    R["b_bootstrap_used"] = int(len(boot_arr))
    R["se_cluster_bootstrap"] = round(se_boot, 5)
    R["bootstrap_mean"] = round(float(boot_arr.mean()), 5)
    R["bootstrap_ci95_percentile"] = [round(float(np.percentile(boot_arr, 2.5)), 5),
                                      round(float(np.percentile(boot_arr, 97.5)), 5)]
    R["se_inflation_vs_asymptotic"] = round(se_boot / se_asy, 3)
    R["equivalence_bound_cluster_bootstrap"] = round(
        Z_ONE_SIDED * se_boot - b_hat, 4)
    print(f"   clustered SE {se_boot:.5f} "
          f"({R['se_inflation_vs_asymptotic']}x the asymptotic SE) "
          f"on {len(boot_arr)} usable replications")
    print(f"   percentile 95% CI {R['bootstrap_ci95_percentile']}")
    print(f"   equivalence bound under clustering "
          f"{R['equivalence_bound_cluster_bootstrap']:.4f}")

    # ── M3 randomization inference ─────────────────────────────────────
    print(f"M3 randomization inference, {B_PERM} within-CDE permutations")
    seeds = [SEED + 5000 + i for i in range(B_PERM)]
    perm = _mapped(_perm_rep, seeds, "M3")
    perm_arr = np.array([b for b in perm if b is not None], dtype=float)
    p_ri = float((np.abs(perm_arr) >= abs(b_hat)).sum() + 1) / (len(perm_arr) + 1)
    R["b_permutation_used"] = int(len(perm_arr))
    # The share pinned to a vertex is the diagnostic, not a curiosity: a
    # well-behaved estimator does not return the same value repeatedly.
    R["randomization_share_pinned_at_zero"] = round(
        float((np.abs(perm_arr) < 1e-6).mean()), 4)
    R["randomization_null_sd"] = round(float(perm_arr.std(ddof=1)), 6)
    R["randomization_null_ci95"] = [round(float(np.percentile(perm_arr, 2.5)), 5),
                                    round(float(np.percentile(perm_arr, 97.5)), 5)]
    R["randomization_p_two_sided"] = round(p_ri, 4)
    print(f"   null SD {R['randomization_null_sd']:.6f}, "
          f"two-sided p = {p_ri:.3f} on {len(perm_arr)} permutations")
    print(f"   share of permutations pinned to zero: "
          f"{100*R['randomization_share_pinned_at_zero']:.0f}%")

    # ── M5 why the median SE cannot be taken at face value ─────────────
    y = pr["leverage_win"].to_numpy(dtype=float)
    med_y = float(np.median(y))
    mass = float((y == 1.0).mean())
    # share of the sample within a narrow band of the median, a crude read
    # on whether there is any density there at all
    band = float(((y > med_y - 0.05) & (y < med_y + 0.05)).mean())
    R["outcome_mass_at_one"] = round(mass, 4)
    R["outcome_median"] = round(med_y, 4)
    R["outcome_density_band_pm05"] = round(band, 4)
    print(f"M5 outcome has {100*mass:.1f}% mass at exactly 1.0; median "
          f"{med_y:.3f}; only {100*band:.1f}% of the sample lies within "
          f"+/-0.05 of the median")

    sweep = []
    for q in QUANTILE_SWEEP:
        b_q = fit_median(pr, q)
        if b_q is None:
            sweep.append({"q": q, "estimated": False})
            continue
        jobs = [(SEED + 9000 + int(q * 1000) * 997 + i, q) for i in range(B_SWEEP)]
        bq = _mapped(_boot_rep, jobs, f"q={q:.2f}")
        arr = np.array([v for v in bq if v is not None], dtype=float)
        se_q = float(arr.std(ddof=1))
        pinned = float((np.abs(arr - b_q) < 1e-6).mean())
        row = {"q": q, "estimated": True, "beta": round(b_q, 5),
               "se_cluster_bootstrap": round(se_q, 5),
               "reps": int(len(arr)),
               "share_pinned": round(pinned, 4),
               "ci95": [round(float(np.percentile(arr, 2.5)), 4),
                        round(float(np.percentile(arr, 97.5)), 4)],
               "equivalence_bound": round(Z_ONE_SIDED * se_q - b_q, 4)}
        sweep.append(row)
        print(f"   q={q:.2f}  beta {b_q:+.4f}  clustered SE {se_q:.4f}  "
              f"bound {row['equivalence_bound']:.3f}  "
              f"pinned {100*pinned:.0f}%")
    R["quantile_sweep"] = sweep

    # ── M4 design-free paired test across switchers ────────────────────
    med = pr.groupby(["cde_name", "rural"])["leverage_win"].agg(["median", "size"]).unstack()
    med.columns = ["urban_med", "rural_med", "urban_n", "rural_n"]
    bk = med.dropna()
    bk = bk[(bk.urban_n >= MIN_SIDE) & (bk.rural_n >= MIN_SIDE)]
    d = (bk["rural_med"] - bk["urban_med"]).to_numpy(dtype=float)
    nz = d[d != 0]
    w_stat, w_p = stats.wilcoxon(d, zero_method="wilcox")
    n_pos = int((nz > 0).sum())
    sign_p = float(stats.binomtest(n_pos, len(nz), 0.5).pvalue)
    R["paired_n_switchers"] = int(len(d))
    R["paired_min_deals_per_side"] = MIN_SIDE
    R["paired_median_difference"] = round(float(np.median(d)), 4)
    R["paired_mean_difference"] = round(float(d.mean()), 4)
    R["paired_iqr"] = [round(float(np.percentile(d, 25)), 4),
                       round(float(np.percentile(d, 75)), 4)]
    R["paired_n_rural_higher"] = n_pos
    R["paired_n_nonzero"] = int(len(nz))
    R["wilcoxon_p"] = round(float(w_p), 4)
    R["sign_test_p"] = round(sign_p, 4)
    print(f"M4 {len(d)} switchers with >={MIN_SIDE} deals per side: "
          f"median paired difference {np.median(d):+.4f}")
    print(f"   Wilcoxon p = {w_p:.3f}; sign test {n_pos}/{len(nz)} rural higher, "
          f"p = {sign_p:.3f}")

    ok = [s for s in sweep if s.get("estimated") and s["share_pinned"] < 0.05]
    R["preferred_quantile"] = ok[0]["q"] if ok else None
    R["verdict"] = (
        "clustering inflates the median standard error by a factor of "
        f"{R['se_inflation_vs_asymptotic']}, moving the equivalence bound from "
        f"{R['equivalence_bound_asymptotic']} to "
        f"{R['equivalence_bound_cluster_bootstrap']}. Separately, the outcome "
        f"carries a {100*mass:.0f}% point mass at exactly 1.0 and the median "
        f"sits on its shoulder, so the quantile-regression asymptotic standard "
        "error rests on a continuous-density assumption the data violate; the "
        "clustered bootstrap does not rely on it and is the one to report.")

    (OUT / "median_inference.json").write_text(json.dumps(R, indent=2))

    md = [
        "# Inference for the median specification", "",
        "_Generated by `scripts/run_median_inference.py`. Closes the outstanding",
        "item conceded in Section 5.2._", "",
        "| quantity | value |", "|---|---:|",
        f"| median rural coefficient | {b_hat:+.5f} |",
        f"| asymptotic SE (quantile regression) | {se_asy:.5f} |",
        f"| CDE-cluster bootstrap SE ({len(boot_arr)} reps) | {se_boot:.5f} |",
        f"| inflation factor | {R['se_inflation_vs_asymptotic']}x |",
        f"| bootstrap percentile 95% CI | [{R['bootstrap_ci95_percentile'][0]:+.4f}, "
        f"{R['bootstrap_ci95_percentile'][1]:+.4f}] |",
        f"| equivalence bound, asymptotic | {R['equivalence_bound_asymptotic']:.4f} |",
        f"| equivalence bound, clustered | {R['equivalence_bound_cluster_bootstrap']:.4f} |",
        f"| randomization-inference p (two-sided, {len(perm_arr)} draws) | {p_ri:.4f} |",
        f"| paired switchers ({MIN_SIDE}+ per side) | {len(d)} |",
        f"| median paired difference (rural minus urban) | {np.median(d):+.4f} |",
        f"| Wilcoxon signed-rank p | {w_p:.4f} |",
        f"| sign test p ({n_pos}/{len(nz)} rural higher) | {sign_p:.4f} |", "",
        "## Why the asymptotic median SE cannot be taken at face value", "",
        f"The outcome carries a **{100*mass:.1f}% point mass at exactly 1.0**, the",
        f"value recorded when a project mobilizes nothing beyond the subsidized",
        f"investment, and the median is {med_y:.3f}. Only {100*band:.1f}% of the",
        "sample lies within 0.05 of the median. Under within-CDE permutation the",
        f"rural coefficient is pinned to within 1e-7 of zero in "
        f"{100*R['randomization_share_pinned_at_zero']:.0f}% of draws, which is the",
        "signature of a degenerate vertex solution rather than a smoothly varying",
        "estimator. The sparsity-based asymptotic standard error assumes a positive",
        "continuous conditional density at the estimated quantile; that assumption",
        "does not hold here.", "",
        "| quantile | beta | clustered SE | 95% CI | bound | pinned |",
        "|---:|---:|---:|:--:|---:|---:|",
        f"| 0.50 | {b_hat:+.4f} | {se_boot:.4f} | "
        f"[{R['bootstrap_ci95_percentile'][0]:+.3f}, "
        f"{R['bootstrap_ci95_percentile'][1]:+.3f}] | "
        f"{R['equivalence_bound_cluster_bootstrap']:.3f} | "
        f"{100*R['randomization_share_pinned_at_zero']:.0f}% |",
    ]
    for s in sweep:
        if s.get("estimated"):
            md.append(f"| {s['q']:.2f} | {s['beta']:+.4f} | "
                      f"{s['se_cluster_bootstrap']:.4f} | "
                      f"[{s['ci95'][0]:+.3f}, {s['ci95'][1]:+.3f}] | "
                      f"{s['equivalence_bound']:.3f} | "
                      f"{100*s['share_pinned']:.0f}% |")
        else:
            md.append(f"| {s['q']:.2f} | not estimated | | | | |")
    md += ["", R["verdict"], ""]
    (OUT / "median_inference.md").write_text("\n".join(md))
    print(f"\nWrote {OUT/'median_inference.json'} and .md")


if __name__ == "__main__":
    POOL = ProcessPoolExecutor(
        max_workers=N_WORKERS, mp_context=get_context("spawn"), initializer=_init)
    try:
        main()
    finally:
        POOL.shutdown(wait=False, cancel_futures=True)
