"""
============================================================================
 NMTC walkthrough — a learning script, for Katia
============================================================================

Read this file top-to-bottom as a tutorial.  Every block is narrated so
you can see *what* we're computing and *why*.  Nothing here is novel —
everything has already been computed and saved in `data/processed/`
by `scripts/describe_nmtc.py`.  The point of this file is to show you
how to reproduce the headline numbers yourself, step by step, so you
understand the dataset before you use it.

Run it:
    python3 scripts/explore_nmtc_walkthrough.py

It will print a series of numbered sections to your terminal, each one
showing a small pandas operation and the result.  You can also just
read it — it's designed to make sense without running.

Prerequisite: `scripts/describe_nmtc.py` has already been run, so
`data/processed/*.csv` exists.  (If not, run that first.)

----------------------------------------------------------------------------
 Vocabulary you need before you start
----------------------------------------------------------------------------

 - NMTC:   New Markets Tax Credit.  A US federal program that gives
           investors a 39%-over-7-years tax credit in exchange for putting
           equity into a Community Development Entity (CDE).
 - CDE:    Community Development Entity.  A certified intermediary —
           usually a bank subsidiary or a nonprofit CDFI — that takes
           investor equity (the QEI) and lends/invests it into eligible
           low-income-community businesses (QALICBs).
 - QEI:    Qualified Equity Investment.  Investor → CDE.  Not in our data.
 - QLICI:  Qualified Low-Income Community Investment.  CDE → QALICB.
           *This is what our transactions file records.*
 - QALICB: Qualified Active Low-Income Community Business.  The ultimate
           recipient / project.  Four types: RE, NRE, SPE, CDE.
 - Project: The economic object (a building, a factory, an operating
            business).  One project can receive multiple QLICIs from
            multiple CDEs.
 - Leverage ratio:   total project cost / QLICI.  If a project cost $5M
                     and the QLICI was $1M, leverage is 5×.
 - Mobilization:     (total project cost − QLICI) / QLICI = leverage − 1.
                     This is "private dollars mobilized per public dollar".
                     0.82× means every $1 of federal credit pulled in
                     $0.82 of non-federal capital.

----------------------------------------------------------------------------
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

# Point at the processed-data folder regardless of where you run this from.
ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "data" / "processed"


def section(n, title):
    """Just a pretty-printer for console sections."""
    print(f"\n{'=' * 72}\n  Section {n}.  {title}\n{'=' * 72}")


# ---------------------------------------------------------------------------
section(1, "Load the two cleaned tables")
# ---------------------------------------------------------------------------
# `nmtc_transactions.csv`  = 19,907 rows, one per QLICI (a single deal
# between a CDE and a QALICB).  Good for $-totals and time series.
#
# `nmtc_projects.csv`      =  8,024 rows, one per project.  Includes the
# `leverage_ratio` and `leverage_win` columns we computed.  Use THIS
# when you talk about leverage, because leverage is a project-level
# concept (total project cost / total QLICI to the project).

tx = pd.read_csv(PROCESSED / "nmtc_transactions.csv")
pr = pd.read_csv(PROCESSED / "nmtc_projects.csv")

print(f"transactions shape:  {tx.shape}   (rows, cols)")
print(f"projects shape:      {pr.shape}")
print(f"\ntransactions columns (first 10): {list(tx.columns[:10])}")
print(f"projects columns (first 10):     {list(pr.columns[:10])}")

# ---------------------------------------------------------------------------
section(2, "The program in one sentence: $66.6B of QLICI over 2001–2022")
# ---------------------------------------------------------------------------
# The total federal-credit capital ever deployed in this program.  We get
# it by summing `qlici_amount` over every transaction.

total_qlici = tx["qlici_amount"].sum()
print(f"Total QLICI deployed:     ${total_qlici:,.0f}")
print(f"  = ${total_qlici / 1e9:.2f} B")
print(f"Across {tx['year'].min()}–{tx['year'].max()}  ({tx['year'].nunique()} years)")
print(f"From {len(tx):,} transactions into {pr['project_id'].nunique():,} unique projects.")

# ---------------------------------------------------------------------------
section(3, "Mobilization: $0.82 of private per $1 of public")
# ---------------------------------------------------------------------------
# THIS is the headline blended-finance number.  Aggregate over the whole
# program:
#     private $  =  total project cost  −  total QLICI
#     mobilization  =  private $ / QLICI
#
# Note we pull total project cost from the PROJECT table (not transactions)
# because project cost is reported at the project level — each transaction
# doesn't get its own cost.

total_cost = pr["project_cost"].sum()
mobilization = (total_cost - total_qlici) / total_qlici
print(f"Total project cost:       ${total_cost / 1e9:.2f} B")
print(f"Total QLICI:              ${total_qlici / 1e9:.2f} B")
print(f"Implied private capital:  ${(total_cost - total_qlici) / 1e9:.2f} B")
print(f"Mobilization ratio:        {mobilization:.2f}× "
      "  (private $ per $1 of federal credit)")

# ---------------------------------------------------------------------------
section(4, "Metro vs. non-metro — the 20% statutory target")
# ---------------------------------------------------------------------------
# The NMTC statute requires CDEs to direct *at least 20%* of their QLICIs
# to non-metropolitan census tracts.  Did they?  Let's check both ways:
# by transaction count AND by dollar share.

by_metro_n = tx["metro"].value_counts()
by_metro_d = tx.groupby("metro")["qlici_amount"].sum()

print("By number of transactions:")
for m, n in by_metro_n.items():
    print(f"  {m:<12s}  {n:>7,}   ({100 * n / len(tx):.2f}%)")

print("\nBy dollars:")
total_d = by_metro_d.sum()
for m in ["non_metro", "metro", "unknown"]:
    if m in by_metro_d.index:
        d = by_metro_d[m]
        print(f"  {m:<12s}  ${d / 1e9:6.2f} B   ({100 * d / total_d:.2f}%)")

# Interpretation: ~19.6% of DOLLARS in non-metro.  That's at (not above)
# the 20% statutory target.  CDEs are bunching against the mandate — a
# classic sign that the constraint binds.

# ---------------------------------------------------------------------------
section(5, "Leverage — the core object we care about")
# ---------------------------------------------------------------------------
# Leverage = project_cost / project_qlici.  This was computed once, in
# describe_nmtc.py, and stored in the project table.

print("First 5 rows of the leverage columns:")
print(pr[["project_id", "metro", "project_qlici", "project_cost",
          "leverage_ratio", "leverage_win"]].head().to_string(index=False))

# Why two leverage columns?
#   leverage_ratio = raw
#   leverage_win   = clipped to [1.0, 20.0]
# A few projects report total cost < QLICI (leverage < 1, which is
# implausible — project cost should *include* the QLICI).  And a small
# number report absurd leverage (50×, 100× — small-ticket QLICI into
# a very large RE stack).  We winsorize to [1, 20] to keep summary
# statistics from being dominated by these.

print("\nDistribution of raw leverage_ratio (unwinsorized):")
print(pr["leverage_ratio"].describe().round(2).to_string())

# ---------------------------------------------------------------------------
section(6, "The leverage gap: metro vs. non-metro")
# ---------------------------------------------------------------------------
# THIS is our empirical headline.  Compute mean AND median leverage
# separately for metro and non-metro projects, using the winsorized
# version.  The median is the number we quote in the brief because it
# isn't affected by the handful of very-high-leverage outliers.

lev_by_metro = (
    pr.groupby("metro")["leverage_win"]
      .agg(["count", "mean", "median", "std"])
      .round(3)
)
print(lev_by_metro.to_string())

m_med = lev_by_metro.loc["metro", "median"]
nm_med = lev_by_metro.loc["non_metro", "median"]
print(f"\nMedian-leverage gap  (metro − non_metro):  "
      f"{m_med:.2f} − {nm_med:.2f} = +{m_med - nm_med:.2f}×")

# Interpretation: the median metro project mobilizes ~0.12× more private
# capital per federal dollar than the median non-metro project.  That is
# the *within-program* rural-urban gap, and it's what we want to explain.

# ---------------------------------------------------------------------------
section(7, "Does the gap survive controlling for WHAT the money funds?")
# ---------------------------------------------------------------------------
# Maybe metro projects just look more leveraged because metro projects
# are disproportionately Real Estate (which stacks more layers of private
# debt) and non-metro projects are operating businesses (fewer layers).
# Check: is the gap still there WITHIN each QALICB type?

by_type = (
    pr.groupby(["qalicb_type", "metro"])["leverage_win"]
      .median()
      .unstack("metro")
      .round(3)
)
print("Median leverage, QALICB type × metro:")
print(by_type.to_string())

# If "metro" column > "non_metro" column in every row, the gap is NOT
# just a composition artefact — it persists within every project type.
# That is in fact what we find (see figure 5).

# ---------------------------------------------------------------------------
section(8, "CDE-level heterogeneity — the mechanism candidate")
# ---------------------------------------------------------------------------
# The top 20 CDEs do >50% of all $.  Their non-metro shares vary
# enormously — from <5% (urban-focused bank subsidiaries) to >70%
# (rural-focused specialized CDEs).  THIS is where we think the paper
# really lives:  rural under-leverage might be about WHICH institutions
# deploy the credit, not the credit itself.

top = pd.read_csv(PROCESSED / "top_cdes.csv")
print("Top 20 CDEs by total QLICI $, sorted by non-metro share:")
print(top[["cde_name", "total_qlici_m", "non_metro_share"]]
        .sort_values("non_metro_share", ascending=False)
        .round(2)
        .to_string(index=False))

# Look at the contrast between, e.g., Rural Development Partners LLC
# (80%+ non-metro) and some of the big-bank CDEs (<5%).  Same program,
# same tax credit, same 39% subsidy — totally different deployment
# pattern.  That is the variation we want to exploit.

# ---------------------------------------------------------------------------
section(9, "Sanity check: our computed numbers match headline.json")
# ---------------------------------------------------------------------------
# headline.json was written by describe_nmtc.py.  Every number in the
# brief comes from there.  Let's confirm we get the same values.

with open(PROCESSED / "headline.json") as f:
    headline = json.load(f)

print("From headline.json:")
for k, v in headline.items():
    print(f"  {k:<45s}  {v}")

# Quick assertion that the three headline numbers we computed above match:
assert abs(round(total_qlici / 1e9, 2) -
           headline["total_qlici_billion_usd"]) < 0.01
assert abs(round(total_cost / 1e9, 1) -
           headline["total_project_cost_billion_usd"]) < 0.01
assert abs(round(m_med - nm_med, 2) -
           headline["leverage_gap_metro_minus_nonmetro"]) < 0.01
print("\nAll three headline numbers reproduce ✓")

# ---------------------------------------------------------------------------
section(10, "Where to go from here")
# ---------------------------------------------------------------------------
# Exercises to build your intuition:
#
#   1. Compute the same metro/non-metro leverage gap using the MEAN
#      (not median).  Why is the mean gap bigger?  (Hint: long right tail.)
#
#   2. Repeat Section 6 splitting by `year` — does the gap shrink or
#      grow over time?  (Merge `summary_by_year.csv` with a groupby.)
#
#   3. Compute mobilization ratio by QALICB type.  Which type mobilizes
#      the most private capital per public dollar — and does the ranking
#      flip between metro and non-metro?
#
#   4. Top-CDE exercise: pick the CDE with the highest non-metro share
#      AND the CDE with the lowest.  What's their median leverage?
#      Same question: same credit, different deployment — why?
#
#   5. Look at `summary_by_year.csv` and plot the non-metro dollar share
#      over time (Fig 2).  Does the 20% mandate seem to "bind"?
#
# Everything you need is in `data/processed/`.  Happy exploring.
print("End of walkthrough.")
