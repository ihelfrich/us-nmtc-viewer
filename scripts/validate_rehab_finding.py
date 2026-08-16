"""
Independent validation of the commercial real-estate rehabilitation result.

This does not re-run `verify_rehab_cell.py`. It rebuilds the quantities from
the raw CDFI workbook with a separate code path, so that a bug in the
processed-CSV pipeline or in the purpose construction would show up as a
disagreement instead of being reproduced faithfully.

The finding under test: within intermediary, rural commercial real-estate
rehabilitation projects carry a rural coefficient near -0.44 with a
CDE-clustered standard error near 0.10, the only cell of twenty in the
residual scan to survive a Benjamini-Hochberg correction.

  W1  Rebuild from `data/raw/*.xlsx`. Reconstruct leverage, rural status,
      and the project-level purpose directly from the two workbook sheets,
      then re-estimate the cell. Compares against the processed pipeline.

  W2  The purpose definition is a choice, so vary it. The pipeline assigns
      each project the purpose holding the largest share of its QLICI
      dollars. Alternatives: the modal purpose by transaction count, and
      restricting to projects whose transactions all share one purpose,
      which removes the assignment rule entirely.

  W3  Multi-CDE attribution. One fifth of projects involve more than one
      intermediary, and the project sheet records a single CDE name for
      each. Re-estimate on single-CDE projects only, where attribution is
      unambiguous.

  W4  Check the Benjamini-Hochberg implementation in
      `run_residual_analysis.py` against statsmodels' `multipletests`,
      which is independently maintained.

  W6  Where inside the cell the effect lives. A mean coefficient can be
      carried by a thin upper tail, which matters for interpretation even
      when the estimate is precise. This reports quantile regressions
      inside the cell and re-estimates the mean after trimming the outer
      decile of the leverage distribution.

  W5  Check the wild cluster bootstrap in `verify_rehab_cell.py`. A wild
      cluster bootstrap-t is easy to get subtly wrong: the null must be
      imposed when generating the pseudo-outcome, weights must be drawn at
      the cluster level, and the statistic compared must be the
      studentized one. This re-implements it independently and also
      reports the rejection rate of the same machinery on a placebo
      outcome, which should be near the nominal level.

Writes: data/processed/regressions/rehab_validation.json / .md

Run:    uv run --no-project --with pandas --with numpy --with statsmodels \
            --with openpyxl python scripts/validate_rehab_finding.py
"""
from __future__ import annotations

import json
import os
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "NMTC_Public_Data_Release_FY2003-FY2022.xlsx"
IN = ROOT / "data" / "processed"
OUT = IN / "regressions"

TX_SHEET = "Financial Notes 1 - Data Set PU"
PR_SHEET = "Projects 2 - Data Set PUBLISH.P"
RHS = "rural + C(year) + C(qalicb_type) + C(cde_name)"
B_WILD = int(os.environ.get("NMTC_W_WILD", 2000))
B_PLACEBO_RUNS = int(os.environ.get("NMTC_W_PLACEBO", 200))
SEED = 20260816

REHAB = "Real Estate–Rehabilitation–Commercial"


def raw_frames() -> tuple[pd.DataFrame, pd.DataFrame]:
    tx = pd.read_excel(RAW, sheet_name=TX_SHEET)
    tx.columns = ["project_id", "transaction_id", "tract", "metro_flag", "year",
                  "cde_name", "qlici", "city", "state", "zip", "purpose",
                  "qalicb_type"]
    pr = pd.read_excel(RAW, sheet_name=PR_SHEET)
    pr.columns = ["project_id", "tract", "metro_flag", "year", "cde_name",
                  "project_qlici", "project_cost", "city", "state", "zip",
                  "qalicb_type", "multi_cde", "multi_tract"]
    return tx, pr


def build(pr: pd.DataFrame, tx: pd.DataFrame, rule: str) -> pd.DataFrame:
    """Project-level analysis frame built from the workbook only."""
    d = pr.copy()
    # rural from the raw string, tolerating its three spellings
    flag = d["metro_flag"].astype(str).str.strip().str.lower()
    assert set(flag.unique()) <= {"metro", "non-metro"}, sorted(flag.unique())
    d["rural"] = (flag == "non-metro").astype(int)
    d["leverage"] = d["project_cost"] / d["project_qlici"]
    d["leverage_win"] = d["leverage"].clip(lower=1.0, upper=20.0)

    t = tx.dropna(subset=["purpose", "project_id"]).copy()
    if rule == "dollar":
        g = t.groupby(["project_id", "purpose"])["qlici"].sum().reset_index()
        dom = g.sort_values(["project_id", "qlici"]).groupby("project_id").tail(1)
        d["purpose"] = d["project_id"].map(dom.set_index("project_id")["purpose"])
    elif rule == "modal":
        g = t.groupby(["project_id", "purpose"]).size().rename("n").reset_index()
        dom = g.sort_values(["project_id", "n"]).groupby("project_id").tail(1)
        d["purpose"] = d["project_id"].map(dom.set_index("project_id")["purpose"])
    elif rule == "pure":
        n_kinds = t.groupby("project_id")["purpose"].nunique()
        pure = n_kinds[n_kinds == 1].index
        only = t[t["project_id"].isin(pure)].groupby("project_id")["purpose"].first()
        d["purpose"] = d["project_id"].map(only)
    else:
        raise ValueError(rule)

    d = d.dropna(subset=["leverage_win", "rural", "year", "qalicb_type",
                         "cde_name", "purpose"]).reset_index(drop=True)
    d["year"] = d["year"].astype(int)
    return d


def fit_cell(df: pd.DataFrame, outcome: str = "leverage_win"):
    return smf.ols(f"{outcome} ~ {RHS}", df).fit(
        cov_type="cluster", cov_kwds={"groups": df["cde_name"]})


def summarize(df: pd.DataFrame, label: str) -> dict:
    cell = df[df["purpose"] == REHAB]
    sw = cell.groupby("cde_name")["rural"].agg(["mean", "size"])
    n_sw = int(((sw["mean"] > 0) & (sw["mean"] < 1)).sum())
    if len(cell) < 100 or cell["rural"].sum() < 20 or n_sw < 5:
        return {"label": label, "estimated": False, "n": int(len(cell))}
    r = fit_cell(cell)
    b, se = float(r.params["rural"]), float(r.bse["rural"])
    out = {"label": label, "estimated": True, "n": int(len(cell)),
           "n_rural": int(cell["rural"].sum()), "n_cde": int(cell["cde_name"].nunique()),
           "n_switcher_cde": n_sw, "beta": round(b, 4), "se": round(se, 4),
           "t": round(b / se, 2), "p": float(f"{float(r.pvalues['rural']):.3e}")}
    print(f"   {label:38s} beta {b:+.4f} (SE {se:.4f}) t {b/se:+.2f} "
          f"n={len(cell):,} rural={int(cell['rural'].sum())}")
    return out


def main() -> None:
    R: dict = {"seed": SEED}
    tx, pr_raw = raw_frames()

    # ── W1 rebuild from the workbook ───────────────────────────────────
    print("W1 rebuilt from the raw workbook")
    d_dollar = build(pr_raw, tx, "dollar")
    R["W1_raw_rebuild"] = summarize(d_dollar, "raw rebuild, dollar-dominant")
    R["W1_n_projects_rebuilt"] = int(len(d_dollar))

    # the pipeline's own numbers, for comparison only
    pub = json.loads((OUT / "rehab_cell_verification.json").read_text())
    R["pipeline_beta"] = pub["R1"]["beta"]
    R["pipeline_se"] = pub["R1"]["se_cde_cluster"]
    w1 = R["W1_raw_rebuild"]
    R["W1_matches_pipeline"] = bool(
        w1.get("estimated")
        and abs(w1["beta"] - pub["R1"]["beta"]) < 5e-3
        and abs(w1["se"] - pub["R1"]["se_cde_cluster"]) < 5e-3)
    print(f"   pipeline reports beta {pub['R1']['beta']:+.4f} "
          f"(SE {pub['R1']['se_cde_cluster']:.4f}); "
          f"match={R['W1_matches_pipeline']}")

    # ── W2 alternative purpose definitions ─────────────────────────────
    print("W2 alternative purpose assignment rules")
    R["W2_modal"] = summarize(build(pr_raw, tx, "modal"), "modal by transaction count")
    R["W2_pure"] = summarize(build(pr_raw, tx, "pure"), "single-purpose projects only")

    # ── W3 multi-CDE attribution ───────────────────────────────────────
    print("W3 multi-CDE attribution")
    single = d_dollar[d_dollar["multi_cde"].astype(str).str.upper() == "NO"]
    R["W3_single_cde"] = summarize(single, "single-CDE projects only")

    # ── W4 Benjamini-Hochberg against statsmodels ──────────────────────
    from statsmodels.stats.multitest import multipletests
    scan = json.loads((OUT / "residual_analysis.json").read_text())
    est = [c for c in scan["cells"] if c.get("estimated")]
    pvals = [c["p_exact"] for c in est]
    rej, _, _, _ = multipletests(pvals, alpha=0.05, method="fdr_bh")
    ours = [c["bh_reject_at_05"] for c in est]
    R["W4_bh"] = {
        "n_tests": len(pvals),
        "statsmodels_n_reject": int(rej.sum()),
        "pipeline_n_reject": int(sum(ours)),
        "agree": bool(list(rej) == list(ours)),
        "rejected_cells": [c["cell"] for c, k in zip(est, rej) if k]}
    print(f"W4 Benjamini-Hochberg: statsmodels rejects "
          f"{int(rej.sum())} of {len(pvals)}, pipeline rejects {int(sum(ours))}, "
          f"agree={R['W4_bh']['agree']} -> {R['W4_bh']['rejected_cells']}")

    # ── W5 wild cluster bootstrap, re-implemented ──────────────────────
    print(f"W5 wild cluster bootstrap-t re-implemented, {B_WILD} draws")
    cell = d_dollar[d_dollar["purpose"] == REHAB].reset_index(drop=True)
    full = fit_cell(cell)
    t_obs = float(full.params["rural"] / full.bse["rural"])
    restricted = smf.ols(f"leverage_win ~ {RHS.replace('rural + ', '')}", cell).fit()
    u = restricted.resid.to_numpy()
    fitted = restricted.fittedvalues.to_numpy()
    codes = pd.Categorical(cell["cde_name"]).codes
    n_cl = codes.max() + 1
    rng = np.random.default_rng(SEED)

    def wild_p(y_base: np.ndarray, resid: np.ndarray, t_ref: float, n: int) -> float:
        ts = []
        for _ in range(n):
            w = rng.choice([-1.0, 1.0], size=n_cl)[codes]
            rep = cell.assign(ystar=y_base + resid * w)
            rr = smf.ols(f"ystar ~ {RHS}", rep).fit(
                cov_type="cluster", cov_kwds={"groups": rep["cde_name"]})
            ts.append(float(rr.params["rural"] / rr.bse["rural"]))
        ts = np.array(ts)
        return float((np.abs(ts) >= abs(t_ref)).sum() + 1) / (len(ts) + 1)

    p_wild = wild_p(fitted, u, t_obs, B_WILD)
    R["W5_wild"] = {"t_observed": round(t_obs, 3), "draws": B_WILD,
                    "p_two_sided": round(p_wild, 5),
                    "pipeline_p": pub["R5_wild_cluster"]["p_two_sided"],
                    "null_imposed": True, "weights": "Rademacher at CDE level"}
    print(f"   observed t {t_obs:+.2f}, p = {p_wild:.4f} "
          f"(pipeline reported {pub['R5_wild_cluster']['p_two_sided']})")

    # placebo calibration: the same machinery on a synthetic null outcome
    print(f"   placebo calibration over {B_PLACEBO_RUNS} synthetic nulls")
    rejects = 0
    for k in range(B_PLACEBO_RUNS):
        g = np.random.default_rng(SEED + 7000 + k)
        y0 = fitted + u * g.choice([-1.0, 1.0], size=n_cl)[codes]
        rep = cell.assign(y0=y0)
        rr = smf.ols(f"y0 ~ {RHS}", rep).fit(
            cov_type="cluster", cov_kwds={"groups": rep["cde_name"]})
        if abs(float(rr.params["rural"] / rr.bse["rural"])) > 1.96:
            rejects += 1
    R["W5_placebo_rejection_rate"] = round(rejects / B_PLACEBO_RUNS, 4)
    print(f"   naive 5% rejection rate on synthetic nulls: "
          f"{100*R['W5_placebo_rejection_rate']:.1f}% "
          f"(nominal 5%; a much higher rate would indicate the CRVE "
          f"t-statistic over-rejects here)")

    # ── W6 where inside the cell the effect lives ──────────────────────
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).resolve().parent))
    from qreg_lp import fit_quantile
    print("W6 location of the effect inside the cell")
    qs = {}
    for tau in (0.25, 0.50, 0.75, 0.90):
        b_q = fit_quantile(cell, "leverage_win", tau)
        qs[f"{tau:.2f}"] = round(float(b_q), 4)
        print(f"   tau={tau:.2f}  beta {b_q:+.4f}")
    lo, hi = cell["leverage_win"].quantile([0.05, 0.95])
    tr = cell[(cell["leverage_win"] >= lo) & (cell["leverage_win"] <= hi)]
    rt = fit_cell(tr)
    R["W6_quantiles_in_cell"] = qs
    R["W6_trimmed"] = {
        "n": int(len(tr)),
        "beta": round(float(rt.params["rural"]), 4),
        "se": round(float(rt.bse["rural"]), 4),
        "p": round(float(rt.pvalues["rural"]), 5)}
    R["W6_share_of_effect_from_outer_decile"] = round(
        1 - R["W6_trimmed"]["beta"] / R["W1_raw_rebuild"]["beta"], 3)
    print(f"   trimmed to the central 90%: beta "
          f"{R['W6_trimmed']['beta']:+.4f} (SE {R['W6_trimmed']['se']:.4f}, "
          f"p {R['W6_trimmed']['p']:.4f}); the outer decile carries "
          f"{100*R['W6_share_of_effect_from_outer_decile']:.0f}% of the estimate")

    scan_ps = sorted(c["p_exact"] for c in est)
    R["W6_p_separation_ratio"] = round(scan_ps[1] / scan_ps[0], 1)
    print(f"   second-smallest p in the scan is "
          f"{scan_ps[1]/scan_ps[0]:.0f}x the smallest")

    checks = {
        "raw rebuild matches pipeline": R["W1_matches_pipeline"],
        "survives trimming the outer decile": bool(
            R["W6_trimmed"]["beta"] < 0 and R["W6_trimmed"]["p"] < 0.01),
        "modal purpose rule negative and significant": bool(
            R["W2_modal"].get("estimated") and R["W2_modal"]["beta"] < 0
            and R["W2_modal"]["p"] < 0.01),
        "single-purpose projects negative and significant": bool(
            R["W2_pure"].get("estimated") and R["W2_pure"]["beta"] < 0
            and R["W2_pure"]["p"] < 0.01),
        "single-CDE projects negative": bool(
            R["W3_single_cde"].get("estimated") and R["W3_single_cde"]["beta"] < 0),
        "BH agrees with statsmodels": R["W4_bh"]["agree"],
        "wild bootstrap reproduces": bool(abs(p_wild - pub["R5_wild_cluster"]["p_two_sided"]) < 0.01),
    }
    R["checks"] = checks
    R["all_pass"] = bool(all(checks.values()))
    print("\nvalidation summary")
    for k, v in checks.items():
        print(f"   {'PASS' if v else 'FAIL'}  {k}")
    print(f"   overall: {'PASS' if R['all_pass'] else 'FAIL'}")

    (OUT / "rehab_validation.json").write_text(json.dumps(R, indent=2))
    md = ["# Independent validation of the rehabilitation finding", "",
          "_Generated by `scripts/validate_rehab_finding.py`, which rebuilds from",
          "the raw workbook rather than re-running the verification script._", "",
          "| check | estimate | result |", "|---|---|:--:|"]
    for key in ("W1_raw_rebuild", "W2_modal", "W2_pure", "W3_single_cde"):
        v = R[key]
        if v.get("estimated"):
            md.append(f"| {v['label']} | ${v['beta']:+.4f}$ (SE {v['se']:.4f}), "
                      f"n={v['n']:,} | |")
        else:
            md.append(f"| {v['label']} | not estimated | |")
    md += [f"| Benjamini-Hochberg vs statsmodels | "
           f"{R['W4_bh']['statsmodels_n_reject']} rejected | "
           f"{'agree' if R['W4_bh']['agree'] else 'DISAGREE'} |",
           f"| wild cluster bootstrap re-implemented | p = {p_wild:.4f} | |",
           f"| placebo rejection rate at nominal 5% | "
           f"{100*R['W5_placebo_rejection_rate']:.1f}% | |", "",
           f"**Overall: {'PASS' if R['all_pass'] else 'FAIL'}.**", ""]
    (OUT / "rehab_validation.md").write_text("\n".join(md))
    print(f"\nWrote {OUT/'rehab_validation.json'} and .md")


if __name__ == "__main__":
    main()
