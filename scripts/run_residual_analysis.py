"""
Section 5.5 of the paper outline, never built until now: where the
within-CDE residual lives.

The paper reports a within-CDE rural coefficient that is null on average.
A referee's natural next question is whether it is null everywhere, or
whether the average conceals a subpopulation in which rural deployment
genuinely does mobilize less. This script conditions on the workhorse
specification and asks, cell by cell, whether any subgroup shows a
within-CDE rural penalty distinguishable from zero.

  S1  by CDE size (deal-count quartiles among switchers)
  S2  by era (five-year origination bands)
  S3  by census region
  S4  by QALICB type
  S5  by the CDE's own rural orientation (its non-metro share)
  S6  multiple-comparison discipline: Benjamini-Hochberg across every cell
      tested above, since scanning twenty cells at the 5% level is expected
      to produce one rejection by chance alone

Every cell is estimated with the same fixed effects as the workhorse
specification, year and QALICB type and CDE, and CDE-clustered standard
errors. Cells too small to identify the coefficient are reported as such
rather than dropped silently.

Reads:  data/processed/nmtc_projects.csv
Writes: data/processed/regressions/residual_analysis.json / .md

Run:    uv run --no-project --with pandas --with numpy --with statsmodels \
            python scripts/run_residual_analysis.py
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
MIN_CELL_PROJECTS = 150
MIN_CELL_RURAL = 25
MIN_CELL_CDES = 10

# The state column carries full names, not postal abbreviations, which an
# earlier version of this map assumed; every region cell came back empty.
CENSUS_REGION = {
    "Northeast": {"Connecticut", "Maine", "Massachusetts", "New Hampshire",
                  "Rhode Island", "Vermont", "New Jersey", "New York",
                  "Pennsylvania"},
    "Midwest": {"Illinois", "Indiana", "Michigan", "Ohio", "Wisconsin", "Iowa",
                "Kansas", "Minnesota", "Missouri", "Nebraska", "North Dakota",
                "South Dakota"},
    "South": {"Delaware", "District of Columbia", "Florida", "Georgia",
              "Maryland", "North Carolina", "South Carolina", "Virginia",
              "West Virginia", "Alabama", "Kentucky", "Mississippi",
              "Tennessee", "Arkansas", "Louisiana", "Oklahoma", "Texas"},
    "West": {"Arizona", "Colorado", "Idaho", "Montana", "Nevada", "New Mexico",
             "Utah", "Wyoming", "Alaska", "California", "Hawaii", "Oregon",
             "Washington"},
}

def region_of(state: str) -> str:
    for name, members in CENSUS_REGION.items():
        if state in members:
            return name
    return "Other"


pr = pd.read_csv(IN / "nmtc_projects.csv")
pr["rural"] = (pr["metro"] == "non_metro").astype(int)
pr = pr.dropna(subset=["leverage_win", "rural", "year", "qalicb_type",
                       "state", "cde_name"]).reset_index(drop=True)
pr["year"] = pr["year"].astype(int)
pr["region"] = pr["state"].map(region_of)
_unmapped = pr.loc[pr["region"] == "Other", "state"].value_counts()
if len(_unmapped):
    print(f"note: {int(_unmapped.sum())} projects in {len(_unmapped)} unmapped "
          f"jurisdictions (territories and similar): {list(_unmapped.index)[:6]}")
assert (pr["region"] != "Other").mean() > 0.95, \
    "region mapping failed for more than 5% of projects; check the state column"

# a CDE's own characteristics, used to slice the sample
by_cde = pr.groupby("cde_name").agg(
    n_deals=("rural", "size"), rural_share=("rural", "mean")).reset_index()
pr = pr.merge(by_cde, on="cde_name", how="left")

RHS = "rural + C(year) + C(qalicb_type) + C(cde_name)"


def fit_cell(df: pd.DataFrame, label: str) -> dict:
    """Estimate the workhorse specification inside one cell."""
    n, n_rural = len(df), int(df["rural"].sum())
    n_cde = df["cde_name"].nunique()
    switchers = df.groupby("cde_name")["rural"].agg(["mean", "size"])
    n_switch = int(((switchers["mean"] > 0) & (switchers["mean"] < 1)).sum())
    base = {"cell": label, "n": n, "n_rural": n_rural, "n_cde": n_cde,
            "n_switcher_cde": n_switch}
    if n < MIN_CELL_PROJECTS or n_rural < MIN_CELL_RURAL or n_switch < MIN_CELL_CDES:
        return {**base, "estimated": False,
                "reason": "cell too small to identify a within-CDE comparison"}
    try:
        res = smf.ols(f"leverage_win ~ {RHS}", data=df).fit(
            cov_type="cluster", cov_kwds={"groups": df["cde_name"]})
    except Exception as exc:                                   # noqa: BLE001
        return {**base, "estimated": False, "reason": f"fit failed: {exc}"}
    if "rural" not in res.params:
        return {**base, "estimated": False, "reason": "rural absorbed by fixed effects"}
    b, se = float(res.params["rural"]), float(res.bse["rural"])
    return {**base, "estimated": True, "beta": round(b, 4), "se": round(se, 4),
            "p": round(float(res.pvalues["rural"]), 4),
            "ci95": [round(b - 1.96 * se, 4), round(b + 1.96 * se, 4)]}


results: dict = {"min_cell_rules": {
    "min_projects": MIN_CELL_PROJECTS, "min_rural_projects": MIN_CELL_RURAL,
    "min_switcher_cdes": MIN_CELL_CDES}}
cells: list[dict] = []

print("S1: by CDE size (deal-count quartiles)")
q = by_cde["n_deals"].quantile([0.25, 0.5, 0.75]).to_list()
edges = [(0, q[0]), (q[0], q[1]), (q[1], q[2]), (q[2], np.inf)]
for i, (lo, hi) in enumerate(edges, 1):
    sub = pr[(pr["n_deals"] > lo) & (pr["n_deals"] <= hi)]
    r = fit_cell(sub, f"CDE size quartile {i} ({lo:.0f}<n<={hi:.0f})")
    cells.append(r); print("  ", r["cell"], r.get("beta", r.get("reason")))

print("S2: by era")
for lo, hi in [(2001, 2009), (2010, 2015), (2016, 2022)]:
    r = fit_cell(pr[pr["year"].between(lo, hi)], f"origination {lo}-{hi}")
    cells.append(r); print("  ", r["cell"], r.get("beta", r.get("reason")))

print("S3: by census region")
for reg in ["Northeast", "Midwest", "South", "West"]:
    r = fit_cell(pr[pr["region"] == reg], f"region {reg}")
    cells.append(r); print("  ", r["cell"], r.get("beta", r.get("reason")))

print("S4: by QALICB type")
for qt in sorted(pr["qalicb_type"].dropna().unique()):
    r = fit_cell(pr[pr["qalicb_type"] == qt], f"QALICB type {qt}")
    cells.append(r); print("  ", r["cell"], r.get("beta", r.get("reason")))

print("S5: by the CDE's own rural orientation")
for lo, hi, lab in [(0.0, 0.2, "rural share <=20%"),
                    (0.2, 0.5, "rural share 20-50%"),
                    (0.5, 1.01, "rural share >50%")]:
    sub = pr[(pr["rural_share"] > lo) & (pr["rural_share"] <= hi)]
    r = fit_cell(sub, f"CDE {lab}")
    cells.append(r); print("  ", r["cell"], r.get("beta", r.get("reason")))

# ── S6 multiple comparisons ────────────────────────────────────────────
est = [c for c in cells if c["estimated"]]
pvals = np.array([c["p"] for c in est])
order = np.argsort(pvals)
m = len(pvals)
bh_reject = np.zeros(m, dtype=bool)
if m:
    crit = (np.arange(1, m + 1) / m) * 0.05
    passed = pvals[order] <= crit
    if passed.any():
        kmax = np.max(np.where(passed)[0])
        bh_reject[order[: kmax + 1]] = True
for c, rej in zip([est[i] for i in range(m)], bh_reject):
    c["bh_reject_at_05"] = bool(rej)

results["cells"] = cells
results["n_cells_estimated"] = m
results["n_cells_skipped"] = len(cells) - m
results["n_significant_uncorrected"] = int((pvals < 0.05).sum()) if m else 0
results["n_significant_after_bh"] = int(bh_reject.sum())
results["min_p"] = float(pvals.min()) if m else None
results["expected_false_positives_at_05"] = round(0.05 * m, 2) if m else 0

print(f"\nS6: {m} cells estimated, {results['n_cells_skipped']} too small.")
print(f"  uncorrected p<0.05: {results['n_significant_uncorrected']} "
      f"(chance alone would give about {results['expected_false_positives_at_05']})")
print(f"  surviving Benjamini-Hochberg at 5%: {results['n_significant_after_bh']}")
print(f"  smallest p across all cells: {results['min_p']}")

(OUT / "residual_analysis.json").write_text(json.dumps(results, indent=2))

md = ["# Where the within-CDE residual lives", "",
      "_Generated by `scripts/run_residual_analysis.py`. Each cell repeats the",
      "workhorse specification (year, QALICB-type and CDE fixed effects, CDE-clustered",
      "standard errors) inside a subgroup. Cells too small to identify a within-CDE",
      "comparison are reported rather than dropped._", "",
      "| cell | beta | (SE) | p | N | rural | switcher CDEs | BH 5% |",
      "|---|---:|---:|---:|---:|---:|---:|:--:|"]
for c in cells:
    if c["estimated"]:
        md.append(f"| {c['cell']} | {c['beta']:+.3f} | ({c['se']:.3f}) | {c['p']:.3f} | "
                  f"{c['n']:,} | {c['n_rural']:,} | {c['n_switcher_cde']} | "
                  f"{'yes' if c['bh_reject_at_05'] else 'no'} |")
    else:
        md.append(f"| {c['cell']} | not estimated | | | {c['n']:,} | {c['n_rural']:,} | "
                  f"{c['n_switcher_cde']} | |")
md += ["",
       f"{m} cells estimated. {results['n_significant_uncorrected']} reach p < 0.05 "
       f"uncorrected, against roughly {results['expected_false_positives_at_05']} "
       f"expected by chance at that threshold across this many tests. "
       f"{results['n_significant_after_bh']} survive a Benjamini-Hochberg correction "
       f"at the 5% level.", ""]
(OUT / "residual_analysis.md").write_text("\n".join(md))
print(f"\nWrote {OUT/'residual_analysis.json'} and .md")
