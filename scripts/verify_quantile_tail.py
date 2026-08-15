"""
Adversarial check on the upper-tail rural penalty.

The quantile sweep in run_median_inference.py reports a within-CDE rural
coefficient that is zero through the centre and turns sharply negative in
the upper tail. Before that becomes a claim in a paper it has to survive
the obvious objection, which is that it may be an artifact of the
estimator rather than a fact about the program.

The objection is specific and serious. Quantile regression with fixed
effects suffers an incidental-parameter bias of order 1/T, where T is the
number of observations per fixed effect. Here the median intermediary
originates roughly a dozen deals, T is small, and the bias is known to be
worse in the tails, where the effective local sample around the fitted
quantile is thinner still. A tail coefficient estimated off a dozen deals
per intermediary is exactly the configuration the literature warns about.

Three checks, in increasing order of how much they would hurt.

  T1  Re-run the sweep on intermediaries with many deals, where 1/T is
      small. If the tail pattern is incidental-parameter bias it should
      weaken substantially as T grows. If it is real it should survive.

  T2  Drop the regression entirely. For every intermediary with enough
      deals on both sides, take its rural quantile minus its urban
      quantile at the same tau, and test that paired collection against
      zero with a Wilcoxon signed-rank test. This carries no fixed
      effects, so it cannot have an incidental-parameter problem. It is
      a weaker design, since it does not adjust for year or project type,
      but it is a genuinely independent look.

  T3  Placebo. Randomly relabel rural within each intermediary, holding
      every book composition fixed, then rebuild the T2 statistic. The
      real tail difference must sit outside what relabeling produces, or
      T2 is measuring the shape of the distribution rather than a rural
      effect.

  T4  Residualize leverage on additive year and QALICB-type effects, then
      rebuild the within-intermediary paired gaps. This removes those two
      observed composition margins while preserving T2's per-CDE paired
      construction; the adjusted outcome changes the estimand.

Reads:  data/processed/nmtc_projects.csv
Writes: data/processed/regressions/quantile_tail_verification.json / .md

Run:    uv run --no-project --with pandas --with numpy --with statsmodels \
            --with scipy python scripts/verify_quantile_tail.py
"""
from __future__ import annotations

import json
import os
import sys
import warnings
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
from qreg_lp import fit_quantile          # noqa: E402

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
IN = ROOT / "data" / "processed"
OUT = IN / "regressions"

TAUS = (0.50, 0.75, 0.90)
BIG_CDE_MIN_DEALS = int(os.environ.get("NMTC_BIG_MIN", 30))
B_BOOT = int(os.environ.get("NMTC_TAIL_BOOT", 200))
B_PLACEBO = int(os.environ.get("NMTC_TAIL_PLACEBO", 500))
MIN_SIDE = int(os.environ.get("NMTC_MIN_SIDE", 5))
SEED = 20260814
N_WORKERS = max(1, min(4, int(os.environ.get("NMTC_WORKERS", 4))))
FORMULA = "leverage_win ~ rural + C(year) + C(qalicb_type) + C(cde_name)"


def load() -> pd.DataFrame:
    pr = pd.read_csv(IN / "nmtc_projects.csv")
    pr["rural"] = (pr["metro"] == "non_metro").astype(int)
    pr = pr.dropna(subset=["leverage_win", "rural", "year", "qalicb_type",
                           "cde_name"]).reset_index(drop=True)
    pr["year"] = pr["year"].astype(int)
    return pr


def big_sample(pr: pd.DataFrame) -> pd.DataFrame:
    n = pr.groupby("cde_name").size()
    keep = n[n >= BIG_CDE_MIN_DEALS].index
    sub = pr[pr.cde_name.isin(keep)].reset_index(drop=True)
    return sub


_PR: pd.DataFrame | None = None
_GROUPS: dict[str, np.ndarray] | None = None


def _init() -> None:
    global _PR, _GROUPS
    _PR = big_sample(load())
    _GROUPS = {n: g.index.to_numpy() for n, g in _PR.groupby("cde_name")}


def _boot(job: tuple[int, float]) -> float | None:
    seed, tau = job
    assert _PR is not None and _GROUPS is not None
    rng = np.random.default_rng(seed)
    names = np.array(list(_GROUPS.keys()))
    drawn = rng.choice(names, size=len(names), replace=True)
    frames = []
    for k, name in enumerate(drawn):
        s = _PR.loc[_GROUPS[name]].copy()
        s["cde_name"] = f"{name}#{k}"
        frames.append(s)
    rep = pd.concat(frames, ignore_index=True)
    if rep["rural"].nunique() < 2:
        return None
    try:
        return fit_quantile(rep, "leverage_win", tau)
    except Exception:                                           # noqa: BLE001
        return None


def paired_gaps(
    pr: pd.DataFrame, tau: float, outcome: str = "leverage_win"
) -> np.ndarray:
    """Per-intermediary rural-minus-urban gap at quantile tau."""
    g = pr.groupby(["cde_name", "rural"])[outcome]
    qq = g.quantile(tau).unstack()
    nn = g.size().unstack()
    ok = (nn[0] >= MIN_SIDE) & (nn[1] >= MIN_SIDE)
    ok = ok.fillna(False)
    d = (qq[1] - qq[0])[ok]
    return d.dropna().to_numpy(dtype=float)


def conditioned_paired_gaps(pr: pd.DataFrame, tau: float) -> np.ndarray:
    """Paired gaps after additive year/type conditional-mean adjustment."""
    adjusted = pr.copy()
    design = pd.get_dummies(
        adjusted[["year", "qalicb_type"]].astype(str),
        drop_first=True,
        dtype=float,
    )
    x = np.column_stack([np.ones(len(adjusted)), design.to_numpy(dtype=float)])
    y = adjusted["leverage_win"].to_numpy(dtype=float)
    coef, *_ = np.linalg.lstsq(x, y, rcond=None)
    adjusted["leverage_year_type_resid"] = y - x @ coef
    return paired_gaps(adjusted, tau, outcome="leverage_year_type_resid")


def main() -> None:
    pr = load()
    big = big_sample(pr)
    R: dict = {
        "taus": list(TAUS),
        "big_cde_min_deals": BIG_CDE_MIN_DEALS,
        "big_n_projects": int(len(big)),
        "big_n_cdes": int(big["cde_name"].nunique()),
        "full_n_projects": int(len(pr)),
        "full_n_cdes": int(pr["cde_name"].nunique()),
        "paired_min_per_side": MIN_SIDE,
    }
    print(f"T1 large-intermediary subsample: {len(big):,} projects across "
          f"{big['cde_name'].nunique()} CDEs with >= {BIG_CDE_MIN_DEALS} deals "
          f"(median deals per CDE in full sample: "
          f"{int(pr.groupby('cde_name').size().median())})")

    # ── T1 the sweep where 1/T is small ────────────────────────────────
    t1 = []
    for tau in TAUS:
        b = fit_quantile(big, "leverage_win", tau)
        jobs = [(SEED + int(tau * 100) * 7919 + i, tau) for i in range(B_BOOT)]
        vals = [v for v in POOL.map(_boot, jobs, chunksize=2) if v is not None]
        arr = np.array(vals, dtype=float)
        se = float(arr.std(ddof=1))
        row = {"tau": tau, "beta": round(b, 5),
               "se_cluster_bootstrap": round(se, 5), "reps": len(arr),
               "ci95": [round(float(np.percentile(arr, 2.5)), 4),
                        round(float(np.percentile(arr, 97.5)), 4)],
               "t": round(b / se, 2) if se > 0 else None}
        t1.append(row)
        print(f"   tau={tau:.2f}  beta {b:+.4f}  clustered SE {se:.4f}  "
              f"t {row['t']}  CI {row['ci95']}")
    R["T1_large_cdes"] = t1

    # ── T2 design-free paired gaps ─────────────────────────────────────
    t2 = []
    for tau in TAUS:
        d = paired_gaps(pr, tau)
        w_p = float(stats.wilcoxon(d, zero_method="wilcox").pvalue) if len(d) > 5 else None
        nz = d[d != 0]
        sp = float(stats.binomtest(int((nz > 0).sum()), len(nz), 0.5).pvalue) if len(nz) else None
        row = {"tau": tau, "n_pairs": int(len(d)),
               "median_gap": round(float(np.median(d)), 4),
               "mean_gap": round(float(d.mean()), 4),
               "share_negative": round(float((d < 0).mean()), 4),
               "wilcoxon_p": round(w_p, 4) if w_p is not None else None,
               "sign_p": round(sp, 4) if sp is not None else None}
        t2.append(row)
        print(f"T2 tau={tau:.2f}  {len(d)} paired intermediaries  "
              f"median gap {np.median(d):+.4f}  "
              f"{100*row['share_negative']:.0f}% negative  "
              f"Wilcoxon p {row['wilcoxon_p']}")
    R["T2_paired_design_free"] = t2

    # ── T3 placebo on the paired statistic ─────────────────────────────
    rng = np.random.default_rng(SEED + 77)
    groups = {n: g.index.to_numpy() for n, g in pr.groupby("cde_name")}
    t3 = []
    for tau in TAUS:
        observed = float(np.median(paired_gaps(pr, tau)))
        null = []
        for _ in range(B_PLACEBO):
            shuffled = pr.copy()
            rural = shuffled["rural"].to_numpy().copy()
            for idx in groups.values():
                if len(idx) > 1:
                    rural[idx] = rng.permutation(rural[idx])
            shuffled["rural"] = rural
            g = paired_gaps(shuffled, tau)
            if len(g):
                null.append(float(np.median(g)))
        null_arr = np.array(null)
        p = float((np.abs(null_arr) >= abs(observed)).sum() + 1) / (len(null_arr) + 1)
        row = {"tau": tau, "observed_median_gap": round(observed, 4),
               "placebo_draws": len(null_arr),
               "placebo_sd": round(float(null_arr.std(ddof=1)), 4),
               "placebo_ci95": [round(float(np.percentile(null_arr, 2.5)), 4),
                                round(float(np.percentile(null_arr, 97.5)), 4)],
               "p_two_sided": round(p, 4)}
        t3.append(row)
        print(f"T3 tau={tau:.2f}  observed {observed:+.4f} vs placebo "
              f"95% {row['placebo_ci95']}  p = {p:.3f}")
    R["T3_placebo"] = t3

    # ── T4 condition year and QALICB type ─────────────────────────────
    t4 = []
    for tau in TAUS:
        # Keep production T4 on the focused-test path; do not duplicate the
        # residualization here.
        d = conditioned_paired_gaps(pr, tau)
        nz = d[d != 0]
        w_p = float(stats.wilcoxon(d, zero_method="wilcox").pvalue) if len(nz) else None
        sign_p = (
            float(stats.binomtest(int((nz > 0).sum()), len(nz), 0.5).pvalue)
            if len(nz) else None
        )
        row = {"tau": tau, "n_pairs": int(len(d)),
               "median_gap": round(float(np.median(d)), 4),
               "mean_gap": round(float(d.mean()), 4),
               "share_negative": round(float((d < 0).mean()), 4),
               "wilcoxon_p": round(w_p, 4) if w_p is not None else None,
               "sign_p": round(sign_p, 4) if sign_p is not None else None,
               "estimand": "CDE paired quantile gaps after additive year/type mean adjustment"}
        t4.append(row)
        print(f"T4 tau={tau:.2f}  {len(d)} conditioned pairs  "
              f"median gap {np.median(d):+.4f}  Wilcoxon p {row['wilcoxon_p']}")

    R["T4_year_type_conditioned_paired"] = t4

    survives = all(r["ci95"][1] < 0 for r in t1 if r["tau"] >= 0.90)
    R["tail_survives_large_cde_restriction"] = bool(survives)

    (OUT / "quantile_tail_verification.json").write_text(json.dumps(R, indent=2))

    md = ["# Does the upper-tail rural penalty survive scrutiny?", "",
          "_Generated by `scripts/verify_quantile_tail.py`._", "",
          f"Quantile regression with fixed effects carries an incidental-parameter",
          f"bias of order 1/T. The median intermediary here originates",
          f"{int(pr.groupby('cde_name').size().median())} deals, so T is small and the",
          "bias is worst in the tails. These checks ask whether the tail result",
          "survives that objection.", "",
          f"## T1. Intermediaries with at least {BIG_CDE_MIN_DEALS} deals "
          f"({R['big_n_cdes']} CDEs, {R['big_n_projects']:,} projects)", "",
          "| tau | beta | clustered SE | t | 95% CI |", "|---:|---:|---:|---:|:--:|"]
    for r in t1:
        md.append(f"| {r['tau']:.2f} | {r['beta']:+.4f} | "
                  f"{r['se_cluster_bootstrap']:.4f} | {r['t']} | "
                  f"[{r['ci95'][0]:+.3f}, {r['ci95'][1]:+.3f}] |")
    md += ["", "## T2. No regression at all: paired within-intermediary gaps", "",
           "| tau | pairs | median gap | share negative | Wilcoxon p | sign p |",
           "|---:|---:|---:|---:|---:|---:|"]
    for r in t2:
        md.append(f"| {r['tau']:.2f} | {r['n_pairs']} | {r['median_gap']:+.4f} | "
                  f"{100*r['share_negative']:.0f}% | {r['wilcoxon_p']} | {r['sign_p']} |")
    md += ["", "## T3. Placebo: rural relabelled within each intermediary", "",
           "| tau | observed | placebo 95% | p |", "|---:|---:|:--:|---:|"]
    for r in t3:
        md.append(f"| {r['tau']:.2f} | {r['observed_median_gap']:+.4f} | "
                  f"[{r['placebo_ci95'][0]:+.3f}, {r['placebo_ci95'][1]:+.3f}] | "
                  f"{r['p_two_sided']:.3f} |")
    md += ["", "## T4. Paired gaps after additive year/type adjustment", "",
           "| tau | pairs | median gap | share negative | Wilcoxon p | sign p |",
           "|---:|---:|---:|---:|---:|---:|"]
    for r in t4:
        md.append(f"| {r['tau']:.2f} | {r['n_pairs']} | {r['median_gap']:+.4f} | "
                  f"{100*r['share_negative']:.0f}% | {r['wilcoxon_p']} | {r['sign_p']} |")
    md.append("")
    (OUT / "quantile_tail_verification.md").write_text("\n".join(md))
    print(f"\nWrote {OUT/'quantile_tail_verification.json'} and .md")


POOL: ThreadPoolExecutor | None = None

if __name__ == "__main__":
    POOL = ThreadPoolExecutor(max_workers=N_WORKERS, initializer=_init)
    try:
        main()
    finally:
        POOL.shutdown(wait=False, cancel_futures=True)
