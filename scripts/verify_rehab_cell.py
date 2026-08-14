"""
Verify, or break, the commercial real-estate rehabilitation cell.

Adding purpose-of-investment cells to the residual scan produced the first
subgroup in this paper to survive a multiple-comparison correction: within
intermediary, rural commercial real-estate rehabilitation deals show a
rural coefficient of -0.44 with a CDE-clustered standard error of 0.10.
The mechanism is the one Section 5.5 already nominated as most plausible,
since rehabilitation is where private debt-stacking is most natural, which
makes the result attractive and therefore dangerous.

The honest problem with it, stated before any test: the purpose cells were
added to the scan *after* the QALICB real-estate cell had been flagged as
the one worth a sharper look. The Benjamini-Hochberg correction covers the
twenty cells in the scan, and it does not cover the decision to add the
purpose dimension at all. No amount of within-scan correction repairs that.
The result is therefore reported as exploratory unless it survives
everything below, and the provenance is stated in the paper either way.

  R1  The exact p-value and t statistic, since the scan rounds to zero.

  R2  Does it depend on winsorization? Re-estimate on the unwinsorized
      outcome, on logs, and at tighter and looser caps. A result that
      exists only at one cap is a result about the cap.

  R3  Influence. Drop each intermediary in turn and each state in turn,
      and report the largest movement. A finding carried by one CDE or one
      state is not a finding about rural rehabilitation.

  R4  Randomization inference inside the cell. Permute rural within each
      intermediary, holding every book composition fixed, and rebuild the
      coefficient. This makes no distributional assumption and is the
      cleanest available test of the sharp null here.

  R5  Wild cluster bootstrap-t, the standard remedy when cluster count is
      moderate. Eighty switcher CDEs is not few, but the outcome is heavily
      skewed and the CRVE t-statistic can still over-reject.

  R6  Placebo purposes. Run the identical pipeline on the other purpose
      groups. If the machinery manufactures significance, it will do so
      elsewhere too.

Reads:  data/processed/nmtc_projects.csv, nmtc_project_purpose.csv
Writes: data/processed/regressions/rehab_cell_verification.json / .md

Run:    uv run --no-project --with pandas --with numpy --with statsmodels \
            python scripts/verify_rehab_cell.py
"""
from __future__ import annotations

import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
IN = ROOT / "data" / "processed"
OUT = IN / "regressions"

CELL = "re_rehab"
RHS = "rural + C(year) + C(qalicb_type) + C(cde_name)"
B_PERM = 2000
B_WILD = 2000
SEED = 20260814


def load() -> pd.DataFrame:
    pr = pd.read_csv(IN / "nmtc_projects.csv")
    pp = pd.read_csv(IN / "nmtc_project_purpose.csv").set_index("project_id")
    pr["purpose_grp"] = pr["project_id"].map(pp["purpose_grp"])
    pr["rural"] = (pr["metro"] == "non_metro").astype(int)
    pr = pr.dropna(subset=["leverage_ratio", "rural", "year", "qalicb_type",
                           "cde_name", "purpose_grp"]).reset_index(drop=True)
    pr["year"] = pr["year"].astype(int)
    return pr


def fit(df: pd.DataFrame, outcome: str = "leverage_win"):
    return smf.ols(f"{outcome} ~ {RHS}", df).fit(
        cov_type="cluster", cov_kwds={"groups": df["cde_name"]})


def main() -> None:
    pr = load()
    cell = pr[pr["purpose_grp"] == CELL].reset_index(drop=True)
    R: dict = {"cell": CELL, "n": int(len(cell)),
               "n_rural": int(cell["rural"].sum()),
               "n_cde": int(cell["cde_name"].nunique())}

    # ── R1 exact statistics ────────────────────────────────────────────
    res = fit(cell)
    b = float(res.params["rural"]); se = float(res.bse["rural"])
    p = float(res.pvalues["rural"])
    R["R1"] = {"beta": round(b, 5), "se_cde_cluster": round(se, 5),
               "t": round(b / se, 3), "p_exact": float(f"{p:.3e}"),
               "ci95": [round(b - 1.96 * se, 4), round(b + 1.96 * se, 4)]}
    print(f"R1 beta {b:+.4f}, clustered SE {se:.4f}, t {b/se:+.2f}, p {p:.3e}")

    # ── R2 outcome transformations ─────────────────────────────────────
    r2 = {}
    variants = {
        "winsor_1_20 (baseline)": ("leverage_win", cell),
        "unwinsorized": ("leverage_ratio", cell),
        # log of the winsorized outcome, matching the paper's robustness
        # table. Ten projects in the release have a leverage ratio of
        # exactly zero, so logging the raw ratio is undefined.
        "log": ("log_lev", cell.assign(log_lev=np.log(cell["leverage_win"]))),
        "winsor_1_10": ("lev10", cell.assign(
            lev10=cell["leverage_ratio"].clip(1, 10))),
        "winsor_1_50": ("lev50", cell.assign(
            lev50=cell["leverage_ratio"].clip(1, 50))),
    }
    for name, (out, df) in variants.items():
        rr = fit(df, out)
        r2[name] = {"beta": round(float(rr.params["rural"]), 4),
                    "se": round(float(rr.bse["rural"]), 4),
                    "p": round(float(rr.pvalues["rural"]), 5)}
        print(f"R2 {name:24s} {r2[name]['beta']:+.4f} "
              f"(SE {r2[name]['se']:.4f}, p {r2[name]['p']:.4f})")
    R["R2_outcome_variants"] = r2

    # ── R3 influence ───────────────────────────────────────────────────
    drops = {}
    for name, g in cell.groupby("cde_name"):
        sub = cell[cell["cde_name"] != name]
        if sub["rural"].nunique() < 2 or sub["cde_name"].nunique() < 5:
            continue
        drops[name] = float(fit(sub).params["rural"])
    dser = pd.Series(drops)
    worst_cde = dser.idxmax()
    st_drops = {}
    for name, g in cell.groupby("state"):
        sub = cell[cell["state"] != name]
        if sub["rural"].nunique() < 2:
            continue
        st_drops[name] = float(fit(sub).params["rural"])
    sser = pd.Series(st_drops)
    R["R3_influence"] = {
        "leave_one_cde_min": round(float(dser.min()), 4),
        "leave_one_cde_max": round(float(dser.max()), 4),
        "most_influential_cde_moves_beta_to": round(float(dser.max()), 4),
        "n_cde_dropped_tested": int(len(dser)),
        "leave_one_state_min": round(float(sser.min()), 4),
        "leave_one_state_max": round(float(sser.max()), 4),
        "most_influential_state": str(sser.idxmax()),
        "sign_stable_across_all_drops": bool((dser < 0).all() and (sser < 0).all()),
    }
    print(f"R3 leave-one-CDE beta range [{dser.min():+.4f}, {dser.max():+.4f}] "
          f"over {len(dser)} drops; leave-one-state "
          f"[{sser.min():+.4f}, {sser.max():+.4f}] "
          f"(most influential state {sser.idxmax()})")

    # ── R4 randomization inference inside the cell ─────────────────────
    rng = np.random.default_rng(SEED)
    groups = {n: g.index.to_numpy() for n, g in cell.groupby("cde_name")}
    null = []
    y = cell["leverage_win"]
    for _ in range(B_PERM):
        rep = cell.copy()
        rr = rep["rural"].to_numpy().copy()
        for idx in groups.values():
            if len(idx) > 1:
                rr[idx] = rng.permutation(rr[idx])
        rep["rural"] = rr
        if rep["rural"].nunique() < 2:
            continue
        try:
            null.append(float(smf.ols(f"leverage_win ~ {RHS}", rep).fit().params["rural"]))
        except Exception:                                       # noqa: BLE001
            continue
    null = np.array(null)
    p_ri = float((np.abs(null) >= abs(b)).sum() + 1) / (len(null) + 1)
    R["R4_randomization"] = {
        "draws": int(len(null)), "null_sd": round(float(null.std(ddof=1)), 4),
        "null_ci95": [round(float(np.percentile(null, 2.5)), 4),
                      round(float(np.percentile(null, 97.5)), 4)],
        "p_two_sided": round(p_ri, 5)}
    print(f"R4 randomization p = {p_ri:.4f} over {len(null)} within-CDE "
          f"permutations; null 95% "
          f"[{np.percentile(null,2.5):+.3f}, {np.percentile(null,97.5):+.3f}]")

    # ── R5 wild cluster bootstrap-t (Rademacher, null imposed) ─────────
    restricted = smf.ols(f"leverage_win ~ {RHS.replace('rural + ', '')}", cell).fit()
    u = restricted.resid.to_numpy()
    fitted = restricted.fittedvalues.to_numpy()
    codes = pd.Categorical(cell["cde_name"]).codes
    t_obs = b / se
    tstats = []
    for _ in range(B_WILD):
        w = rng.choice([-1.0, 1.0], size=codes.max() + 1)[codes]
        rep = cell.assign(y_star=fitted + u * w)
        rr = smf.ols(f"y_star ~ {RHS}", rep).fit(
            cov_type="cluster", cov_kwds={"groups": rep["cde_name"]})
        tstats.append(float(rr.params["rural"] / rr.bse["rural"]))
    tstats = np.array(tstats)
    p_wild = float((np.abs(tstats) >= abs(t_obs)).sum() + 1) / (len(tstats) + 1)
    R["R5_wild_cluster"] = {
        "draws": int(len(tstats)), "t_observed": round(t_obs, 3),
        "p_two_sided": round(p_wild, 5),
        "null_t_ci95": [round(float(np.percentile(tstats, 2.5)), 3),
                        round(float(np.percentile(tstats, 97.5)), 3)]}
    print(f"R5 wild cluster bootstrap-t p = {p_wild:.4f} "
          f"(observed t {t_obs:+.2f}, null 95% "
          f"[{np.percentile(tstats,2.5):+.2f}, {np.percentile(tstats,97.5):+.2f}])")

    # ── R6 the same pipeline on other purposes ─────────────────────────
    placebo = {}
    for pu in sorted(pr["purpose_grp"].dropna().unique()):
        if pu == CELL:
            continue
        sub = pr[pr["purpose_grp"] == pu]
        sw = sub.groupby("cde_name")["rural"].agg(["mean", "size"])
        n_sw = int(((sw["mean"] > 0) & (sw["mean"] < 1)).sum())
        if len(sub) < 150 or sub["rural"].sum() < 25 or n_sw < 10:
            placebo[pu] = {"estimated": False, "n": int(len(sub))}
            continue
        rr = fit(sub)
        placebo[pu] = {"estimated": True,
                       "beta": round(float(rr.params["rural"]), 4),
                       "se": round(float(rr.bse["rural"]), 4),
                       "p": round(float(rr.pvalues["rural"]), 4),
                       "n": int(len(sub))}
        print(f"R6 placebo {pu:18s} {placebo[pu]['beta']:+.4f} "
              f"(p {placebo[pu]['p']:.3f})")
    R["R6_other_purposes"] = placebo

    survives = (
        R["R1"]["p_exact"] < 0.01
        and all(v["beta"] < 0 for v in r2.values())
        and R["R3_influence"]["sign_stable_across_all_drops"]
        and R["R4_randomization"]["p_two_sided"] < 0.05
        and R["R5_wild_cluster"]["p_two_sided"] < 0.05)
    R["survives_all_checks"] = bool(survives)
    R["provenance_caveat"] = (
        "The purpose cells were added to the residual scan after the QALICB "
        "real-estate cell had been flagged. Benjamini-Hochberg covers the "
        "twenty cells in the scan and does not cover the choice to add the "
        "purpose dimension. This result is exploratory and is reported as "
        "such regardless of how many checks it survives.")
    print(f"\nsurvives every check: {survives}")

    (OUT / "rehab_cell_verification.json").write_text(json.dumps(R, indent=2))

    md = ["# The commercial real-estate rehabilitation cell", "",
          "_Generated by `scripts/verify_rehab_cell.py`._", "",
          f"Cell: {R['n']:,} projects, {R['n_rural']} of them rural, "
          f"{R['n_cde']} intermediaries.", "",
          "| check | result |", "|---|---|",
          f"| R1 point estimate | ${R['R1']['beta']:+.4f}$ (clustered SE "
          f"{R['R1']['se_cde_cluster']:.4f}, $t={R['R1']['t']:+.2f}$, "
          f"$p={R['R1']['p_exact']:.2e}$) |",
          f"| R2 outcome variants | all {len(r2)} negative; "
          f"range {min(v['beta'] for v in r2.values()):+.3f} to "
          f"{max(v['beta'] for v in r2.values()):+.3f} |",
          f"| R3 leave-one-CDE | $[{R['R3_influence']['leave_one_cde_min']:+.3f}, "
          f"{R['R3_influence']['leave_one_cde_max']:+.3f}]$ |",
          f"| R3 leave-one-state | $[{R['R3_influence']['leave_one_state_min']:+.3f}, "
          f"{R['R3_influence']['leave_one_state_max']:+.3f}]$ |",
          f"| R4 randomization inference | $p={R['R4_randomization']['p_two_sided']:.4f}$ "
          f"({R['R4_randomization']['draws']} draws) |",
          f"| R5 wild cluster bootstrap-$t$ | $p={R['R5_wild_cluster']['p_two_sided']:.4f}$ "
          f"({R['R5_wild_cluster']['draws']} draws) |",
          f"| R6 other purposes | "
          f"{', '.join(f'{k} {v[chr(98)+chr(101)+chr(116)+chr(97)]:+.3f}' if v.get('estimated') else f'{k} n/a' for k, v in placebo.items())} |",
          "", f"**Survives every check: {survives}.**", "",
          R["provenance_caveat"], ""]
    (OUT / "rehab_cell_verification.md").write_text("\n".join(md))
    print(f"Wrote {OUT/'rehab_cell_verification.json'} and .md")


if __name__ == "__main__":
    main()
