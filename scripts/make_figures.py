"""
Generate PNG figures from the processed NMTC data for Katia's brief.

Reads:
  data/processed/nmtc_projects.csv      (project-level, with leverage)
  data/processed/nmtc_transactions.csv  (QLICI-level)

Writes to figures/:
  1_allocation_timeseries.png       annual NMTC $ deployed, metro vs non-metro
  2_non_metro_share_timeseries.png  non-metro share of $ per year vs. 20% target
  3_leverage_distribution.png       project-level leverage ratio distribution, metro-split
  4_qalicb_type_by_metro.png        QALICB-type composition, metro vs non-metro
  5_leverage_by_qalicb_metro.png    leverage ratio by QALICB type × metro

Run:  python3 scripts/make_figures.py
"""
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

plt.rcParams.update({
    "figure.dpi": 130,
    "savefig.dpi": 160,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "font.family": "DejaVu Sans",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "grid.linestyle": "--",
})

METRO_C = "#1f77b4"        # steel blue
NONMETRO_C = "#d62728"     # red
TARGET_C = "#888888"

ROOT = Path(__file__).resolve().parent.parent
IN = ROOT / "data" / "processed"
OUT = ROOT / "figures"
OUT.mkdir(exist_ok=True)

pr = pd.read_csv(IN / "nmtc_projects.csv")
tx = pd.read_csv(IN / "nmtc_transactions.csv")

# ---------------------------------------------------------------------------
# Fig 1: annual allocation, metro vs non-metro, stacked bar
# ---------------------------------------------------------------------------
by_year = (
    tx.groupby(["year", "metro"])["qlici_amount"].sum().div(1e6).unstack(fill_value=0)
      .sort_index()
)
by_year = by_year[["non_metro", "metro"]] if "non_metro" in by_year.columns else by_year

fig, ax = plt.subplots(figsize=(9, 4.2))
ax.bar(by_year.index, by_year["non_metro"], color=NONMETRO_C, label="Non-metro")
ax.bar(by_year.index, by_year["metro"], bottom=by_year["non_metro"],
       color=METRO_C, label="Metro")
ax.set_ylabel("QLICI deployed ($M, nominal)")
ax.set_xlabel("Origination year")
ax.set_title("NMTC QLICI deployment by year (FY2001–FY2022)",
             fontsize=12, loc="left")
ax.legend(loc="upper left", frameon=False)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v/1000:.1f}B"))
fig.tight_layout()
fig.savefig(OUT / "1_allocation_timeseries.png")
plt.close(fig)

# ---------------------------------------------------------------------------
# Fig 2: non-metro dollar share, vs. 20% statutory target
# ---------------------------------------------------------------------------
total = by_year.sum(axis=1)
nm_share = (by_year["non_metro"] / total * 100).rename("non_metro_share_pct")

fig, ax = plt.subplots(figsize=(9, 4.2))
ax.plot(nm_share.index, nm_share.values, color=NONMETRO_C, lw=2, marker="o",
        markersize=4, label="Non-metro dollar share")
ax.axhline(20, color=TARGET_C, lw=1.5, ls="--",
           label="Statutory 20% mandate")
ax.set_ylabel("Non-metro share of QLICI $ (%)")
ax.set_xlabel("Origination year")
ax.set_title("Non-metro share pins against the 20% statutory target — most years",
             fontsize=12, loc="left")
ax.legend(loc="upper right", frameon=False)
ax.set_ylim(0, max(40, nm_share.max() + 5))
fig.tight_layout()
fig.savefig(OUT / "2_non_metro_share_timeseries.png")
plt.close(fig)

# ---------------------------------------------------------------------------
# Fig 3: leverage ratio distribution, metro-split (histograms + medians)
# ---------------------------------------------------------------------------
# Winsorized (1×–20×) to keep the tails visible
x_metro = pr.loc[pr.metro == "metro", "leverage_win"].dropna()
x_nonm  = pr.loc[pr.metro == "non_metro", "leverage_win"].dropna()
bins = np.linspace(1, 10, 46)

fig, ax = plt.subplots(figsize=(9, 4.6))
ax.hist(x_metro, bins=bins, density=True, color=METRO_C, alpha=0.55,
        label=f"Metro  (n={len(x_metro):,}, median {x_metro.median():.2f}×)")
ax.hist(x_nonm, bins=bins, density=True, color=NONMETRO_C, alpha=0.55,
        label=f"Non-metro  (n={len(x_nonm):,}, median {x_nonm.median():.2f}×)")
ax.axvline(x_metro.median(), color=METRO_C, lw=1.5, ls=":")
ax.axvline(x_nonm.median(), color=NONMETRO_C, lw=1.5, ls=":")
ax.set_xlabel("Leverage ratio  (total project cost / QLICI)")
ax.set_ylabel("Density")
ax.set_title("Non-metro deals mobilize less private capital per public dollar",
             fontsize=12, loc="left")
ax.legend(loc="upper right", frameon=False)
fig.tight_layout()
fig.savefig(OUT / "3_leverage_distribution.png")
plt.close(fig)

# ---------------------------------------------------------------------------
# Fig 4: QALICB-type composition, metro vs non-metro
# ---------------------------------------------------------------------------
ct = (pr.groupby(["metro", "qalicb_type"])["project_id"].count()
        .unstack(fill_value=0))
ct_pct = ct.div(ct.sum(axis=1), axis=0).mul(100)
type_order = ["RE", "NRE", "SPE", "CDE"]
ct_pct = ct_pct[type_order]

labels = {
    "RE": "Real Estate",
    "NRE": "Non-Real-Estate (operating business)",
    "SPE": "Special-Purpose Entity",
    "CDE": "Loan to another CDE",
}
colors = ["#4c72b0", "#55a868", "#c44e52", "#8172b2"]
fig, ax = plt.subplots(figsize=(9, 3.6))
bottom = np.zeros(len(ct_pct))
for t, c in zip(type_order, colors):
    ax.barh(ct_pct.index, ct_pct[t], left=bottom, color=c, label=labels[t])
    bottom += ct_pct[t].values
ax.set_xlabel("Share of projects (%)")
ax.set_title("QALICB-type mix differs rural-vs-urban",
             fontsize=12, loc="left")
ax.legend(loc="lower right", frameon=False, fontsize=9)
ax.set_xlim(0, 100)
fig.tight_layout()
fig.savefig(OUT / "4_qalicb_type_by_metro.png")
plt.close(fig)

# ---------------------------------------------------------------------------
# Fig 5: median leverage by QALICB type × metro
# ---------------------------------------------------------------------------
med = (pr.groupby(["qalicb_type", "metro"])["leverage_win"].median()
         .unstack(fill_value=np.nan).reindex(type_order))

fig, ax = plt.subplots(figsize=(9, 4.2))
x = np.arange(len(type_order))
w = 0.38
ax.bar(x - w/2, med.get("metro", np.zeros(len(type_order))), width=w,
       color=METRO_C, label="Metro")
ax.bar(x + w/2, med.get("non_metro", np.zeros(len(type_order))), width=w,
       color=NONMETRO_C, label="Non-metro")
ax.set_xticks(x)
ax.set_xticklabels([labels[t] for t in type_order], rotation=0, fontsize=9)
ax.set_ylabel("Median leverage (winsorized 1–20)")
ax.set_title("Leverage gap persists within every QALICB type",
             fontsize=12, loc="left")
ax.legend(frameon=False)
# value labels
for i, t in enumerate(type_order):
    for offset, metro_key in [(-w/2, "metro"), (w/2, "non_metro")]:
        v = med.get(metro_key, pd.Series(dtype=float)).get(t, np.nan)
        if pd.notna(v):
            ax.text(i + offset, v + 0.03, f"{v:.2f}×",
                    ha="center", va="bottom", fontsize=8)
fig.tight_layout()
fig.savefig(OUT / "5_leverage_by_qalicb_metro.png")
plt.close(fig)

print(f"Wrote 5 figures → {OUT}")
for p in sorted(OUT.glob("*.png")):
    print(f"  {p.name:40s}  {p.stat().st_size/1024:6.1f} KB")
