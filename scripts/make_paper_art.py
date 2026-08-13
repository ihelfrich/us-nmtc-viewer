"""
The switchboard figure: every intermediary that deploys on both sides of
the rural line, drawn as a vertical spine from its urban book's mean
leverage to its rural book's mean leverage, ordered by the CDE's pooled
mean. The paper's claim becomes visible before it is read: the spines
climb across an enormous between-CDE range while the within-spine gaps
stay short and centered on zero. A marginal panel shows the distribution
of within-CDE gaps against zero.

Sample rule (documented as D10): switcher CDEs with at least three urban
and three rural projects, so both book means are estimated from more than
anecdote. The figure writes a JSON sidecar recording every number it
displays, and asserts the arithmetic identities it relies on.

Reads:  data/processed/nmtc_projects.csv
Writes: figures/7_switcher_spines.pdf / .png
        figures/7_switcher_spines.json

Run:    python3 scripts/make_paper_art.py
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "figures"

INK = "#16161D"
PENBLUE = "#2852E8"
PENCIL = "#6B6B70"
WASH = "#EEF2FA"
MIN_PER_SIDE = 3

plt.rcParams.update({
    "figure.dpi": 130, "savefig.dpi": 300,
    "font.family": "serif", "font.serif": ["Palatino", "TeX Gyre Pagella", "DejaVu Serif"],
    "axes.facecolor": "white", "figure.facecolor": "white",
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.edgecolor": PENCIL, "axes.linewidth": 0.6,
    "xtick.color": PENCIL, "ytick.color": PENCIL,
    "text.color": INK, "axes.labelcolor": INK,
})

pr = pd.read_csv(ROOT / "data" / "processed" / "nmtc_projects.csv")
pr["rural"] = (pr["metro"] == "non_metro").astype(int)
pr = pr.dropna(subset=["leverage_win", "rural", "cde_name"])

g = pr.groupby(["cde_name", "rural"])["leverage_win"].agg(["mean", "count"]).unstack()
g.columns = ["urban_mean", "rural_mean", "urban_n", "rural_n"]
sw = g.dropna()
sw = sw[(sw["urban_n"] >= MIN_PER_SIDE) & (sw["rural_n"] >= MIN_PER_SIDE)].copy()
sw["pooled"] = (sw["urban_mean"] * sw["urban_n"] + sw["rural_mean"] * sw["rural_n"]) \
    / (sw["urban_n"] + sw["rural_n"])
sw["gap"] = sw["rural_mean"] - sw["urban_mean"]
sw = sw.sort_values("pooled").reset_index()

n = len(sw)
med_gap = float(sw["gap"].median())
iqr_gap = [float(sw["gap"].quantile(q)) for q in (0.25, 0.75)]
lvl_range = [float(sw["pooled"].min()), float(sw["pooled"].max())]
share_small = float((sw["gap"].abs() < 0.25).mean())
# identity check: pooled mean must sit between the two book means
assert ((sw["pooled"] >= sw[["urban_mean", "rural_mean"]].min(axis=1) - 1e-9) &
        (sw["pooled"] <= sw[["urban_mean", "rural_mean"]].max(axis=1) + 1e-9)).all()
print(f"{n} switcher CDEs with >= {MIN_PER_SIDE} projects per side; "
      f"median within gap {med_gap:+.3f}; IQR [{iqr_gap[0]:+.3f}, {iqr_gap[1]:+.3f}]; "
      f"pooled levels {lvl_range[0]:.2f} to {lvl_range[1]:.2f}")

fig, (ax, axg) = plt.subplots(
    1, 2, figsize=(10.6, 5.4), width_ratios=[5.0, 1.15], sharey=False,
    gridspec_kw={"wspace": 0.06})

# ── main panel: the spines ──────────────────────────────────────────────
x = np.arange(n)
for i, r in sw.iterrows():
    lo, hi = sorted([r["urban_mean"], r["rural_mean"]])
    ax.plot([i, i], [lo, hi], color=PENCIL, lw=0.85, alpha=0.75, zorder=1)
ax.scatter(x, sw["urban_mean"], s=13, color=INK, zorder=3, label="urban book mean")
ax.scatter(x, sw["rural_mean"], s=13, facecolors="white", edgecolors=PENBLUE,
           linewidths=1.1, zorder=3, label="rural book mean")

ax.set_xlim(-2, n + 1)
ax.set_ylim(0.85, 6.4)
ax.set_xlabel("intermediaries, ordered by pooled mean leverage", fontsize=10)
ax.set_ylabel("mean leverage of the book", fontsize=10)
ax.tick_params(labelsize=9)
leg = ax.legend(loc="upper left", frameon=False, fontsize=9, handletextpad=0.4)

ax.annotate(
    "levels differ enormously\nacross intermediaries …",
    xy=(n * 0.86, sw["pooled"].iloc[int(n * 0.93)]),
    xytext=(n * 0.44, 5.45), fontsize=10, style="italic", color=INK,
    arrowprops=dict(arrowstyle="-|>", color=PENCIL, lw=0.9,
                    connectionstyle="arc3,rad=-0.25"))
ax.annotate(
    "… while within an intermediary the two\nbooks track each other: gaps center on zero",
    xy=(n * 0.35, sw["pooled"].iloc[int(n * 0.35)]),
    xytext=(n * 0.06, 4.35), fontsize=10, style="italic", color=INK,
    arrowprops=dict(arrowstyle="-|>", color=PENCIL, lw=0.9,
                    connectionstyle="arc3,rad=0.22"))

# ── marginal panel: within-CDE gaps against zero ────────────────────────
axg.axhspan(iqr_gap[0], iqr_gap[1], color=WASH, zorder=0)
axg.hist(sw["gap"], bins=25, orientation="horizontal", color=PENBLUE,
         alpha=0.85, edgecolor="white", linewidth=0.4)
axg.axhline(0, color=INK, lw=1.0)
axg.axhline(med_gap, color=PENBLUE, lw=1.0, ls=(0, (3, 2)))
axg.set_ylim(-2.6, 2.6)
axg.set_xlabel("within-CDE gap\n(rural $-$ urban)", fontsize=9)
axg.tick_params(labelsize=8)
axg.spines["left"].set_visible(True)
axg.text(0.96, 0.985, f"median {med_gap:+.2f}", transform=axg.transAxes,
         ha="right", va="top", fontsize=8.5, color=PENBLUE, style="italic")

fig.suptitle(
    "The switchboard: every dual-market intermediary's urban and rural books",
    fontsize=12, x=0.085, ha="left", color=INK)
fig.text(0.085, 0.925,
         f"{n} CDEs with at least {MIN_PER_SIDE} projects on each side of the rural line",
         fontsize=9.5, color=PENCIL, style="italic")
fig.tight_layout(rect=[0, 0, 1, 0.93])
fig.savefig(FIG / "7_switcher_spines.pdf")
fig.savefig(FIG / "7_switcher_spines.png")

(FIG / "7_switcher_spines.json").write_text(json.dumps({
    "min_projects_per_side": MIN_PER_SIDE,
    "n_switchers_shown": n,
    "median_within_gap": round(med_gap, 4),
    "iqr_within_gap": [round(v, 4) for v in iqr_gap],
    "pooled_level_range": [round(v, 4) for v in lvl_range],
    "share_abs_gap_below_0p25": round(share_small, 4),
}, indent=2))
print("Wrote figures/7_switcher_spines.{pdf,png,json}")
