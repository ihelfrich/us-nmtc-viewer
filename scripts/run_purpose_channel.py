"""
A variable the paper never used: Purpose of Investment.

The public release carries `Purpose of Investment` on the transaction sheet.
The project-level analysis file was built from the project sheet, which does
not have it, so the field has never entered any specification in this paper.
It should have, because it is exactly the sort of composition channel the
decomposition is designed to separate from intermediary identity.

The raw association is strong in the direction that matters. Non-metro
transactions are 56% Business Financing against 26% for metro, and metro
transactions are far more concentrated in commercial real estate. Business
Financing carries a project-level median leverage of 1.04; commercial real
estate rehabilitation carries 1.27. Rural deployment is therefore weighted
toward the purpose category that mobilizes least, which could account for
part of the raw gap the paper attributes elsewhere.

The obvious objection is that QALICB type already absorbs this, since a real
estate QALICB largely does real estate. That objection is testable and this
script tests it. Purpose separates construction from rehabilitation within
real estate, a distinction QALICB type cannot make and one whose metro
shares differ substantially, so the two are related without being redundant.

  P1  Build a project-level purpose from the transaction sheet, taking the
      purpose accounting for the largest share of a project's QLICI
      dollars. Report coverage and how often a project is mixed.

  P2  How much of the rural gap does purpose explain on its own, and how
      much survives QALICB type? If purpose is redundant with type its
      marginal contribution will be near zero.

  P3  Re-run the ladder with purpose inserted, and re-run the Gelbach
      order-invariant decomposition with purpose as a fourth block. The
      question the paper's headline depends on: does the CDE contribution
      shrink when purpose is allowed to compete for it?

  P4  Re-run the workhorse within-CDE specification adding purpose fixed
      effects. The within-CDE null should be unaffected if it is real.

Reads:  data/raw/NMTC_Public_Data_Release_FY2003-FY2022.xlsx
        data/processed/nmtc_projects.csv
Writes: data/processed/nmtc_project_purpose.csv
        data/processed/regressions/purpose_channel.json / .md

Run:    uv run --no-project --with pandas --with numpy --with statsmodels \
            --with openpyxl python scripts/run_purpose_channel.py
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
RAW = ROOT / "data" / "raw" / "NMTC_Public_Data_Release_FY2003-FY2022.xlsx"
IN = ROOT / "data" / "processed"
OUT = IN / "regressions"
TX_SHEET = "Financial Notes 1 - Data Set PU"

TX_COLS = ["project_id", "transaction_id", "tract", "metro_flag", "year",
           "cde_name", "qlici", "city", "state", "zip", "purpose",
           "qalicb_type"]

# Short labels. The release's own strings carry en dashes and inconsistent
# spacing, which make both regression output and LaTeX unpleasant.
SHORT = {
    "Business Financing": "business",
    "Real Estate – Construction/Permanent/Acquisition w/o Rehab – Commercial": "re_construction",
    "Real Estate–Rehabilitation–Commercial": "re_rehab",
    "Real Estate – Construction–Housing-Single Family": "housing_sf_new",
    "Real Estate – Rehabilitation – Housing -Single Family": "housing_sf_rehab",
    "Real Estate – Construction–Housing-Multi Family": "housing_mf_new",
    "Real Estate – Rehabilitation–Housing - Multi Family": "housing_mf_rehab",
    "Other Financing Purpose": "other",
    "Microenterprise": "microenterprise",
}
# Categories with too few projects to carry their own fixed effect get
# folded, and the fold is recorded rather than done silently.
RARE_MIN = 60
RARE_LABEL = "other_small"


def build_purpose() -> tuple[pd.DataFrame, dict]:
    tx = pd.read_excel(RAW, sheet_name=TX_SHEET)
    tx.columns = TX_COLS
    tx = tx.dropna(subset=["purpose", "project_id"])
    unmapped = sorted(set(tx["purpose"]) - set(SHORT))
    assert not unmapped, f"unmapped purpose strings: {unmapped}"
    tx["purpose"] = tx["purpose"].map(SHORT)

    # dominant purpose by dollars within a project
    g = tx.groupby(["project_id", "purpose"])["qlici"].sum().reset_index()
    total = g.groupby("project_id")["qlici"].transform("sum")
    g["share"] = np.where(total > 0, g["qlici"] / total, np.nan)
    dom = (g.sort_values(["project_id", "qlici"])
             .groupby("project_id").tail(1)
             .set_index("project_id"))
    n_purposes = g.groupby("project_id")["purpose"].nunique()
    meta = {
        "tx_rows": int(len(tx)),
        "projects_with_purpose": int(dom.shape[0]),
        "share_projects_mixed_purpose": round(float((n_purposes > 1).mean()), 4),
        "median_dominant_share": round(float(dom["share"].median()), 4),
        "label_map": SHORT,
    }
    return dom, meta


def main() -> None:
    dom, meta = build_purpose()
    pr = pd.read_csv(IN / "nmtc_projects.csv")
    pr["rural"] = (pr["metro"] == "non_metro").astype(int)
    pr["purpose"] = pr["project_id"].map(dom["purpose"])
    pr["purpose_share"] = pr["project_id"].map(dom["share"])

    R: dict = {"purpose_construction": meta}
    R["coverage"] = round(float(pr["purpose"].notna().mean()), 4)
    print(f"P1 purpose assigned to {100*R['coverage']:.1f}% of projects; "
          f"{100*meta['share_projects_mixed_purpose']:.1f}% of projects mix "
          f"purposes, median dominant share "
          f"{100*meta['median_dominant_share']:.0f}%")

    pr = pr.dropna(subset=["leverage_win", "rural", "year", "qalicb_type",
                           "cde_name", "purpose"]).reset_index(drop=True)
    pr["year"] = pr["year"].astype(int)

    counts = pr["purpose"].value_counts()
    rare = counts[counts < RARE_MIN].index.tolist()
    pr["purpose_grp"] = pr["purpose"].where(~pr["purpose"].isin(rare), RARE_LABEL)
    R["rare_categories_folded"] = rare
    R["rare_min_projects"] = RARE_MIN
    R["n_purpose_groups"] = int(pr["purpose_grp"].nunique())
    print(f"   {R['n_purpose_groups']} purpose groups after folding "
          f"{len(rare)} rare categories ({', '.join(rare) or 'none'})")

    # save the derived variable so other scripts can use it
    pr[["project_id", "purpose", "purpose_grp", "purpose_share"]].to_csv(
        IN / "nmtc_project_purpose.csv", index=False)

    # descriptive: purpose composition by metro status
    comp = (pd.crosstab(pr["purpose_grp"], pr["rural"], normalize="columns") * 100)
    R["composition_by_rural_pct"] = {
        k: {"metro": round(float(v[0]), 2), "rural": round(float(v[1]), 2)}
        for k, v in comp.iterrows()}
    lev = pr.groupby("purpose_grp")["leverage_win"].agg(["size", "median", "mean"])
    R["leverage_by_purpose"] = {
        k: {"n": int(v["size"]), "median": round(float(v["median"]), 4),
            "mean": round(float(v["mean"]), 4)} for k, v in lev.iterrows()}

    # ── P2/P3 the ladder, with purpose inserted ────────────────────────
    def fit(rhs: str, cluster: bool) -> dict:
        f = f"leverage_win ~ rural{rhs}"
        if cluster:
            res = smf.ols(f, pr).fit(cov_type="cluster",
                                     cov_kwds={"groups": pr["cde_name"]})
        else:
            res = smf.ols(f, pr).fit(cov_type="HC1")
        return {"beta": round(float(res.params["rural"]), 4),
                "se": round(float(res.bse["rural"]), 4),
                "p": round(float(res.pvalues["rural"]), 4)}

    ladder = {
        "M0_raw": fit("", False),
        "M1_year": fit(" + C(year)", False),
        "M2_year_type": fit(" + C(year) + C(qalicb_type)", False),
        "M2b_year_purpose": fit(" + C(year) + C(purpose_grp)", False),
        "M3_year_type_purpose": fit(" + C(year) + C(qalicb_type) + C(purpose_grp)", False),
        "M4_year_type_purpose_state": fit(
            " + C(year) + C(qalicb_type) + C(purpose_grp) + C(state)", False),
        "M5_within_cde_no_purpose": fit(
            " + C(year) + C(qalicb_type) + C(cde_name)", True),
        "M6_within_cde_with_purpose": fit(
            " + C(year) + C(qalicb_type) + C(purpose_grp) + C(cde_name)", True),
    }
    R["ladder"] = ladder
    for k, v in ladder.items():
        print(f"   {k:32s} {v['beta']:+.4f} (SE {v['se']:.4f}, p {v['p']:.3f})")

    # ── P3 Gelbach decomposition with purpose as a fourth block ────────
    # Full model reference, so contributions are order invariant.
    full_rhs = " + C(year) + C(qalicb_type) + C(purpose_grp) + C(cde_name)"
    base = smf.ols(f"leverage_win ~ rural{full_rhs}", pr).fit()
    beta_full = float(base.params["rural"])
    beta_m0 = float(smf.ols("leverage_win ~ rural", pr).fit().params["rural"])

    # Gelbach: contribution of block b is gamma_b' * delta_b, obtained by
    # regressing each covariate in b on rural and weighting by its full-model
    # coefficient. Equivalent and simpler: fitted contribution via the
    # auxiliary projection of the block's fitted values on rural.
    contribs = {}
    X = pd.get_dummies(pr[["year", "qalicb_type", "purpose_grp", "cde_name"]]
                       .astype(str), drop_first=True).astype(float)
    blocks = {"year": [c for c in X.columns if c.startswith("year_")],
              "qalicb": [c for c in X.columns if c.startswith("qalicb_type_")],
              "purpose": [c for c in X.columns if c.startswith("purpose_grp_")],
              "cde": [c for c in X.columns if c.startswith("cde_name_")]}
    design = pd.concat([pr[["rural"]].astype(float), X], axis=1)
    design = pd.concat([design, pr[["leverage_win"]]], axis=1)
    import statsmodels.api as sm
    Xf = sm.add_constant(design.drop(columns=["leverage_win"]))
    full = sm.OLS(design["leverage_win"], Xf).fit()
    r = pr["rural"].to_numpy(dtype=float)
    r_dm = r - r.mean()
    denom = float((r_dm ** 2).sum())
    for name, cols in blocks.items():
        if not cols:
            contribs[name] = 0.0
            continue
        gamma = full.params[cols].to_numpy(dtype=float)
        Z = X[cols].to_numpy(dtype=float)
        delta = (Z - Z.mean(axis=0)).T @ r_dm / denom     # aux regs on rural
        contribs[name] = float(delta @ gamma)
    total_expl = beta_m0 - beta_full
    R["gelbach_with_purpose"] = {
        "beta_M0": round(beta_m0, 4), "beta_full": round(beta_full, 4),
        "total_explained": round(total_expl, 4),
        "contrib_year": round(contribs["year"], 4),
        "contrib_qalicb": round(contribs["qalicb"], 4),
        "contrib_purpose": round(contribs["purpose"], 4),
        "contrib_cde": round(contribs["cde"], 4),
        "sum_check": round(sum(contribs.values()), 4),
        "identity_residual": round(total_expl - sum(contribs.values()), 8),
        "share_from_cde": round(contribs["cde"] / total_expl, 4) if total_expl else None,
        "share_from_purpose": round(contribs["purpose"] / total_expl, 4) if total_expl else None,
    }
    G = R["gelbach_with_purpose"]
    print(f"P3 Gelbach with purpose: total {G['total_explained']:+.4f} = "
          f"year {G['contrib_year']:+.4f} + type {G['contrib_qalicb']:+.4f} + "
          f"purpose {G['contrib_purpose']:+.4f} + CDE {G['contrib_cde']:+.4f}")
    print(f"   identity residual {G['identity_residual']:.2e}; "
          f"CDE share {100*G['share_from_cde']:.1f}%, "
          f"purpose share {100*G['share_from_purpose']:.1f}%")

    verdict = (
        f"Adding purpose moves the within-CDE coefficient from "
        f"{ladder['M5_within_cde_no_purpose']['beta']:+.4f} to "
        f"{ladder['M6_within_cde_with_purpose']['beta']:+.4f}. The CDE share of "
        f"the explained movement is {100*G['share_from_cde']:.1f}% with purpose "
        f"competing for it.")
    R["verdict"] = verdict

    (OUT / "purpose_channel.json").write_text(json.dumps(R, indent=2))

    md = ["# Purpose of Investment, a channel the paper never used", "",
          "_Generated by `scripts/run_purpose_channel.py`._", "",
          f"Purpose is assigned to {100*R['coverage']:.1f}% of analysis projects by",
          f"taking the purpose with the largest share of a project's QLICI dollars.",
          f"{100*meta['share_projects_mixed_purpose']:.1f}% of projects mix purposes;",
          f"the median dominant share is {100*meta['median_dominant_share']:.0f}%.", "",
          "## Composition and leverage by purpose", "",
          "| purpose | projects | median leverage | % of metro | % of rural |",
          "|---|---:|---:|---:|---:|"]
    for k, v in sorted(R["leverage_by_purpose"].items(),
                       key=lambda kv: -kv[1]["n"]):
        c = R["composition_by_rural_pct"].get(k, {"metro": 0, "rural": 0})
        md.append(f"| {k} | {v['n']:,} | {v['median']:.3f} | "
                  f"{c['metro']:.1f}% | {c['rural']:.1f}% |")
    md += ["", "## The ladder with purpose inserted", "",
           "| specification | beta | (SE) | p |", "|---|---:|---:|---:|"]
    for k, v in ladder.items():
        md.append(f"| {k} | {v['beta']:+.4f} | ({v['se']:.4f}) | {v['p']:.3f} |")
    md += ["", "## Gelbach decomposition with purpose as a fourth block", "",
           "| block | contribution | share of explained |", "|---|---:|---:|",
           f"| origination year | {G['contrib_year']:+.4f} | "
           f"{100*G['contrib_year']/G['total_explained']:.1f}% |",
           f"| QALICB type | {G['contrib_qalicb']:+.4f} | "
           f"{100*G['contrib_qalicb']/G['total_explained']:.1f}% |",
           f"| purpose of investment | {G['contrib_purpose']:+.4f} | "
           f"{100*G['share_from_purpose']:.1f}% |",
           f"| CDE identity | {G['contrib_cde']:+.4f} | "
           f"{100*G['share_from_cde']:.1f}% |",
           f"| **total** | **{G['total_explained']:+.4f}** | |", "",
           f"Identity residual {G['identity_residual']:.2e}.", "",
           verdict, ""]
    (OUT / "purpose_channel.md").write_text("\n".join(md))
    print(f"\nWrote {OUT/'purpose_channel.json'} and .md")


if __name__ == "__main__":
    main()
