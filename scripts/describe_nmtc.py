"""
First-look descriptives on the CDFI Fund NMTC Public Data Release
(FY2003–FY2022, released June 2024).

Produces, in data/processed/:
  - nmtc_transactions.csv        cleaned QLICI-level rows
  - nmtc_projects.csv             cleaned project-level rows (with leverage)
  - summary_by_metro.csv          rural vs non-metro vs metro rollup
  - summary_by_qalicb_type.csv    RE vs operating business × metro
  - summary_by_year.csv           annual transaction counts + $ volume
  - top_cdes.csv                  top-20 CDEs by deployed $ and by rural share
  - leverage_distribution.csv     project-level leverage deciles, overall + metro cut

And prints a plain-language summary block that we can drop into the brief.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "NMTC_Public_Data_Release_FY2003-FY2022.xlsx"
OUT = ROOT / "data" / "processed"
OUT.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------
print(f"Reading {RAW.name}...")
tx = pd.read_excel(RAW, sheet_name="Financial Notes 1 - Data Set PU")
pr = pd.read_excel(RAW, sheet_name="Projects 2 - Data Set PUBLISH.P")

# Normalize column names
tx.columns = [c.strip() for c in tx.columns]
pr.columns = [c.strip() for c in pr.columns]

# Rename for convenience
tx = tx.rename(columns={
    "Project ID": "project_id",
    "Transaction ID": "transaction_id",
    "2020 Census Tract": "tract_fips",
    "Metro/Non-Metro, 2020 Census": "metro_flag",
    "Origination Year": "year",
    "Community Development Entity (CDE) Name": "cde_name",
    "QLICI Amount": "qlici_amount",
    "City": "city",
    "State": "state",
    "Zip Code": "zip",
    "Purpose of Investment": "purpose",
    "QALICB Type": "qalicb_type",
})

pr = pr.rename(columns={
    "Project ID": "project_id",
    "2020 Census Tract": "tract_fips",
    "Metro/Non-Metro, 2020 Census": "metro_flag",
    "Origination Year": "year",
    "Community Development Entity (CDE) Name": "cde_name",
    "Project QLICI Amount": "project_qlici",
    "Estimated Total Project Cost": "project_cost",
    "City": "city",
    "State": "state",
    "Zip Code": "zip",
    "QALICB Type": "qalicb_type",
    "Multi-CDE": "multi_cde",
    "Multi-Tract Project": "multi_tract",
})

print(f"  transactions (QLICI): {len(tx):,} rows, years {int(tx.year.min())}–{int(tx.year.max())}")
print(f"  projects:             {len(pr):,} rows")

# ---------------------------------------------------------------------------
# Clean
# ---------------------------------------------------------------------------
# metro_flag values in CDFI data: "Metropolitan" vs "Non-Metropolitan" typically;
# preserve as-is but build a short tag.
def metro_short(v):
    if pd.isna(v):
        return "unknown"
    s = str(v).strip().lower()
    if s.startswith("non"):
        return "non_metro"
    if s.startswith("metro"):
        return "metro"
    return s
tx["metro"] = tx["metro_flag"].apply(metro_short)
pr["metro"] = pr["metro_flag"].apply(metro_short)

# Ensure numeric
tx["qlici_amount"] = pd.to_numeric(tx["qlici_amount"], errors="coerce")
pr["project_qlici"] = pd.to_numeric(pr["project_qlici"], errors="coerce")
pr["project_cost"] = pd.to_numeric(pr["project_cost"], errors="coerce")

# Leverage ratio at project level (total project cost / public-credit QLICI)
pr["leverage_ratio"] = pr["project_cost"] / pr["project_qlici"]
# Cap for sanity (some messy rows); keep but also compute winsorized stats.
pr["leverage_win"] = pr["leverage_ratio"].clip(lower=1.0, upper=20.0)

# Write cleaned files
tx.to_csv(OUT / "nmtc_transactions.csv", index=False)
pr.to_csv(OUT / "nmtc_projects.csv", index=False)

# ---------------------------------------------------------------------------
# Descriptives
# ---------------------------------------------------------------------------
def pct(a, b):
    return 100 * a / b if b else float("nan")

print("\n" + "=" * 72)
print(" NMTC Public Data Release — FY2003–FY2022")
print("=" * 72)

# Overall
n_tx = len(tx)
n_pr = len(pr)
total_qlici = tx["qlici_amount"].sum() / 1e9
total_cost  = pr["project_cost"].sum() / 1e9
print(f"\nOverall:")
print(f"  {n_tx:,} QLICI transactions across {n_pr:,} unique projects")
print(f"  ${total_qlici:.1f}B total QLICI deployed")
print(f"  ${total_cost:.1f}B total project cost (public + private combined)")
print(f"  Implied mobilization (all private / total QLICI): "
      f"{(total_cost - total_qlici) / total_qlici:.2f}× of private per $ of NMTC QLICI")

# Metro vs non-metro summary (transactions)
by_metro_tx = (
    tx.groupby("metro").agg(
        n_transactions=("transaction_id", "count"),
        qlici_total_m=("qlici_amount", lambda s: s.sum() / 1e6),
        qlici_mean_m=("qlici_amount", lambda s: s.mean() / 1e6),
        qlici_median_m=("qlici_amount", lambda s: s.median() / 1e6),
    ).round(2).reset_index()
)
by_metro_tx.to_csv(OUT / "summary_by_metro_tx.csv", index=False)
print("\nTransactions × metro flag:")
print(by_metro_tx.to_string(index=False))

# Metro vs non-metro at project level (with leverage)
by_metro_pr = (
    pr.groupby("metro").agg(
        n_projects=("project_id", "count"),
        qlici_total_m=("project_qlici", lambda s: s.sum() / 1e6),
        project_cost_total_m=("project_cost", lambda s: s.sum() / 1e6),
        leverage_mean=("leverage_win", "mean"),
        leverage_median=("leverage_win", "median"),
    ).round(2).reset_index()
)
by_metro_pr["mobilization_ratio"] = (
    (by_metro_pr["project_cost_total_m"] - by_metro_pr["qlici_total_m"])
    / by_metro_pr["qlici_total_m"]
).round(3)
by_metro_pr.to_csv(OUT / "summary_by_metro.csv", index=False)
print("\nProjects × metro flag (leverage and mobilization ratio):")
print(by_metro_pr.to_string(index=False))

# QALICB type (real estate vs operating business) × metro
by_qalicb = (
    pr.groupby(["qalicb_type", "metro"]).agg(
        n=("project_id", "count"),
        qlici_total_m=("project_qlici", lambda s: s.sum() / 1e6),
        leverage_mean=("leverage_win", "mean"),
    ).round(2).reset_index()
)
by_qalicb.to_csv(OUT / "summary_by_qalicb_type.csv", index=False)
print("\nQALICB type × metro (projects):")
print(by_qalicb.to_string(index=False))

# Annual
by_year = (
    tx.groupby(["year", "metro"]).agg(
        n=("transaction_id", "count"),
        qlici_m=("qlici_amount", lambda s: s.sum() / 1e6),
    ).round(1).reset_index()
)
by_year.to_csv(OUT / "summary_by_year.csv", index=False)

# Top CDEs
top_cdes = (
    tx.groupby("cde_name").agg(
        n_tx=("transaction_id", "count"),
        total_qlici_m=("qlici_amount", lambda s: s.sum() / 1e6),
        n_non_metro=("metro", lambda s: (s == "non_metro").sum()),
    ).sort_values("total_qlici_m", ascending=False).head(20)
)
top_cdes["non_metro_share"] = (top_cdes["n_non_metro"] / top_cdes["n_tx"]).round(3)
top_cdes = top_cdes.round(1).reset_index()
top_cdes.to_csv(OUT / "top_cdes.csv", index=False)

# Leverage distribution
lev_q = pr["leverage_ratio"].quantile([.1, .25, .5, .75, .9, .95, .99]).round(2)
print("\nLeverage-ratio quantiles (project cost / QLICI):")
print(lev_q.to_string())

lev_by_metro = pr.groupby("metro")["leverage_win"].describe().round(2)
lev_by_metro.to_csv(OUT / "leverage_distribution.csv")
print("\nLeverage-ratio distribution × metro (winsorized 1×–20×):")
print(lev_by_metro.to_string())

# Multi-CDE (deal complexity proxy) × metro
if "multi_cde" in pr.columns:
    mc = pd.crosstab(pr["metro"], pr["multi_cde"], normalize="index").round(3)
    mc.to_csv(OUT / "multi_cde_by_metro.csv")
    print("\nShare of projects using multiple CDEs × metro:")
    print(mc.to_string())

# ---------------------------------------------------------------------------
# Headline numbers for the brief
# ---------------------------------------------------------------------------
def share(df, cond):
    return pct(int(cond.sum()), len(df))

non_metro_share_tx = share(tx, tx["metro"] == "non_metro")
non_metro_share_pr = share(pr, pr["metro"] == "non_metro")
non_metro_share_qlici = pct(
    tx.loc[tx["metro"] == "non_metro", "qlici_amount"].sum(),
    tx["qlici_amount"].sum(),
)

lev_metro = pr.loc[pr.metro == "metro",     "leverage_win"].median()
lev_nonm  = pr.loc[pr.metro == "non_metro", "leverage_win"].median()

headline = {
    "program_years": [int(tx.year.min()), int(tx.year.max())],
    "n_transactions_total": int(n_tx),
    "n_projects_total": int(n_pr),
    "total_qlici_billion_usd": round(total_qlici, 2),
    "total_project_cost_billion_usd": round(total_cost, 2),
    "non_metro_transaction_share_pct": round(non_metro_share_tx, 2),
    "non_metro_project_share_pct": round(non_metro_share_pr, 2),
    "non_metro_qlici_dollar_share_pct": round(non_metro_share_qlici, 2),
    "statutory_non_metro_target_pct": 20.0,
    "median_leverage_metro": round(float(lev_metro), 2),
    "median_leverage_non_metro": round(float(lev_nonm), 2),
    "leverage_gap_metro_minus_nonmetro": round(float(lev_metro - lev_nonm), 2),
}
(OUT / "headline.json").write_text(json.dumps(headline, indent=2))
print("\nHeadline numbers for brief:")
print(json.dumps(headline, indent=2))
print(f"\nAll outputs → {OUT}")
