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

# Drawn at the printed width (the 4.9in text block) so no scaling shrinks
# the labels; the figure prints at width=\textwidth.
fig, (ax, axg) = plt.subplots(
    1, 2, figsize=(4.9, 3.35), width_ratios=[5.0, 1.15], sharey=False,
    gridspec_kw={"wspace": 0.06})

# ── main panel: the spines ──────────────────────────────────────────────
x = np.arange(n)
for i, r in sw.iterrows():
    lo, hi = sorted([r["urban_mean"], r["rural_mean"]])
    ax.plot([i, i], [lo, hi], color=PENCIL, lw=0.6, alpha=0.75, zorder=1)
ax.scatter(x, sw["urban_mean"], s=7, color=INK, zorder=3, label="urban book mean")
ax.scatter(x, sw["rural_mean"], s=7, facecolors="white", edgecolors=PENBLUE,
           linewidths=1.1, zorder=3, label="rural book mean")

ax.set_xlim(-2, n + 1)
ax.set_ylim(0.85, 6.4)
ax.set_xlabel("intermediaries, ordered by pooled mean leverage", fontsize=8)
ax.set_ylabel("mean leverage of the book", fontsize=8)
ax.tick_params(labelsize=7)
leg = ax.legend(loc="upper left", frameon=False, fontsize=7.2, handletextpad=0.4)

ax.annotate(
    "levels differ widely\nacross intermediaries",
    xy=(n * 0.90, sw["pooled"].iloc[int(n * 0.95)]),
    xytext=(n * 0.52, 5.55), fontsize=6.8, style="italic", color=INK,
    arrowprops=dict(arrowstyle="-|>", color=PENCIL, lw=0.7,
                    connectionstyle="arc3,rad=-0.28"))
ax.annotate(
    "within one intermediary the two\nbooks track each other",
    xy=(n * 0.28, sw["pooled"].iloc[int(n * 0.28)] + 0.5),
    xytext=(n * 0.03, 4.6), fontsize=6.8, style="italic", color=INK,
    arrowprops=dict(arrowstyle="-|>", color=PENCIL, lw=0.7,
                    connectionstyle="arc3,rad=0.24"))

# ── marginal panel: within-CDE gaps against zero ────────────────────────
axg.axhspan(iqr_gap[0], iqr_gap[1], color=WASH, zorder=0)
axg.hist(sw["gap"], bins=25, orientation="horizontal", color=PENBLUE,
         alpha=0.85, edgecolor="white", linewidth=0.4)
axg.axhline(0, color=INK, lw=1.0)
axg.axhline(med_gap, color=PENBLUE, lw=1.0, ls=(0, (3, 2)))
axg.set_ylim(-2.6, 2.6)
axg.set_xlabel("within-CDE gap\n(rural $-$ urban)", fontsize=7.2)
axg.tick_params(labelsize=6.5)
axg.spines["left"].set_visible(True)
axg.text(0.96, 0.985, f"median {med_gap:+.2f}", transform=axg.transAxes,
         ha="right", va="top", fontsize=7, color=PENBLUE, style="italic")

# No figure title: the LaTeX caption names the exhibit, and repeating it
# inside the image wastes the scarce vertical room at this printed width.
fig.tight_layout(pad=0.4)
fig.subplots_adjust(bottom=0.17, top=0.97)
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


# ══════════════════════════════════════════════════════════════════════════
# The ladder: the paper's central argument as one exhibit.
#
# Reading a seven-column table to watch a coefficient collapse asks the
# reader to hold seven numbers in mind. Drawn as intervals against zero,
# the collapse is a single glance: precise and far from zero on the left,
# straddling zero the moment intermediary identity enters. The marginal
# panel decomposes the movement (Gelbach) so the reader sees where the gap
# went, not merely that it went.
#
# Every value is read from the pipeline outputs; nothing is typed in.
# ══════════════════════════════════════════════════════════════════════════
import json as _json

_MAIN = pd.read_csv(ROOT / "data" / "processed" / "regressions" / "main_table.csv").set_index("spec")
_R2 = _json.load(open(ROOT / "data" / "processed" / "regressions" / "review_round2.json"))
_RF = _json.load(open(ROOT / "data" / "processed" / "regressions" / "referee_fixes.json"))

_specs = [
    ("raw difference", "M0"),
    ("+ origination year", "M1"),
    ("+ project type", "M2"),
    ("+ state", "M3"),
    ("+ intermediary", "M4"),
]
_rows = [(lab, float(_MAIN.loc[k, "rural_beta"]), float(_MAIN.loc[k, "rural_se"])) for lab, k in _specs]
_nested = _R2["G1_specs"]["M4S_nested"]
_rows.append(("all four, nested", _nested["beta"], _nested["se"]))

fig, (axL, axR) = plt.subplots(
    1, 2, figsize=(4.9, 2.7), width_ratios=[3.0, 1.35],
    gridspec_kw={"wspace": 0.62})

ys = np.arange(len(_rows))[::-1]
for y, (lab, b, se) in zip(ys, _rows):
    live = "intermediary" in lab or "nested" in lab
    c = PENBLUE if live else INK
    axL.plot([b - 1.96 * se, b + 1.96 * se], [y, y], color=c, lw=1.1,
             solid_capstyle="butt", zorder=2)
    axL.plot([b], [y], "o", ms=4.2, color=c, zorder=3)
axL.axvline(0, color=INK, lw=0.9, zorder=1)
axL.set_yticks(ys)
axL.set_yticklabels([r[0] for r in _rows], fontsize=7)
axL.set_xlabel("non-metro coefficient, with 95% interval", fontsize=7.5)
axL.tick_params(axis="x", labelsize=7)
axL.set_xlim(-0.42, 0.26)
axL.text(0.012, ys[0] + 0.42, "no gap", fontsize=6.6, color=PENCIL, style="italic")

# Gelbach: where the movement went
_g = _RF["F1_gelbach"]
_parts = [("intermediary", _g["contrib_cde"]), ("project type", _g["contrib_qalicb"]),
          ("origination year", _g["contrib_year"])]
yy = np.arange(len(_parts))[::-1]
for y, (lab, v) in zip(yy, _parts):
    axR.barh(y, v, height=0.5, color=PENBLUE if "intermediary" in lab else INK,
             alpha=0.9 if "intermediary" in lab else 0.55)
axR.axvline(0, color=INK, lw=0.9)
axR.set_yticks(yy); axR.set_yticklabels([p[0] for p in _parts], fontsize=7)
axR.set_xlabel("share of the closed gap", fontsize=7.5)
axR.tick_params(axis="x", labelsize=7)
_denom = _g["beta_M0"] - _g["beta_full"]
for y, (lab, v) in zip(yy, _parts):
    axR.text(0.014, y, f"{100*v/_denom:.0f}%", va="center", ha="left",
             fontsize=6.8, color=PENCIL)
axR.set_xlim(-0.215, 0.105)

for ax in (axL, axR):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.grid(axis="x", color=PENCIL, alpha=0.12, lw=0.5)
    ax.set_axisbelow(True)

fig.tight_layout(pad=0.35)
fig.subplots_adjust(left=0.235, bottom=0.20, right=0.985, top=0.90)
fig.savefig(FIG / "8_ladder.pdf")
fig.savefig(FIG / "8_ladder.png")
print(f"ladder: M0 {_rows[0][1]:+.3f} -> M4 {_rows[4][1]:+.3f}; "
      f"nested {_nested['beta']:+.3f}; CDE share "
      f"{100*_g['contrib_cde']/(_g['beta_M0']-_g['beta_full']):.1f}%")


# ══════════════════════════════════════════════════════════════════════════
# The mandate panels. The manuscript reports the excess-mass test three
# ways: deal counts over the full period, QLICI dollars, and dollars from
# 2007 onward, once the proportionality instruction was in the code. A
# single-panel figure showing only the first left the other two asserted
# but not shown. Each panel carries its own estimate and interval, read
# from review_round2.json rather than recomputed here.
# ══════════════════════════════════════════════════════════════════════════
_R2B = _json.load(open(ROOT / "data" / "processed" / "regressions" / "review_round2.json"))
_tx = pd.read_csv(ROOT / "data" / "processed" / "nmtc_transactions.csv")
_tx["is_nm"] = (_tx["metro"] == "non_metro").astype(float)

_BINS = np.linspace(0, 1, 41)
_MID = 0.5 * (_BINS[:-1] + _BINS[1:])
_WIN = (_MID >= 0.175) & (_MID <= 0.225)
_FIT = (~_WIN) & (_MID <= 0.95)


def _cde_shares(frame):
    g = frame.groupby("cde_name").apply(lambda d: pd.Series({
        "n": len(d),
        "count_share": d["is_nm"].mean(),
        "dollar_share": (d["qlici_amount"] * d["is_nm"]).sum()
                        / max(d["qlici_amount"].sum(), 1e-9),
    }), include_groups=False)
    return g[g["n"] >= 5]


def _density_and_cf(shares):
    counts, _ = np.histogram(shares, bins=_BINS)
    dens = counts / (counts.sum() * (_BINS[1] - _BINS[0]))
    cf = np.polyval(np.polyfit(_MID[_FIT], dens[_FIT], 3), _MID).clip(min=0)
    return dens, cf


_full = _cde_shares(_tx)
_post = _cde_shares(_tx[_tx["year"] >= 2007])
_panels = [
    ("deal counts, 2001–2022", _full["count_share"].to_numpy(), _R2B["G2_full_count"]),
    ("QLICI dollars, 2007–2022", _post["dollar_share"].to_numpy(), _R2B["G3_post2007_dollar"]),
]

fig, axes = plt.subplots(1, 2, figsize=(4.9, 2.15), sharey=True,
                         gridspec_kw={"wspace": 0.12})
for ax, (lab, sh, stat) in zip(axes, _panels):
    dens, cf = _density_and_cf(sh)
    ax.axvspan(0.175, 0.225, color=WASH, zorder=0)
    ax.bar(_MID, dens, width=(_BINS[1] - _BINS[0]) * 0.92, color=INK, alpha=0.55,
           edgecolor="white", linewidth=0.3, zorder=2)
    ax.plot(_MID, cf, color=INK, lw=1.0, ls=(0, (4, 2)), zorder=3)
    ax.axvline(0.20, color=PENBLUE, lw=1.0, zorder=4)
    ax.set_title(lab, fontsize=7.2, color=INK, pad=4, loc="left")
    ax.text(0.97, 0.93,
            f"$\\hat B$ = {stat['B']:+.4f}\n[{stat['ci95'][0]:+.3f}, {stat['ci95'][1]:+.3f}]",
            transform=ax.transAxes, ha="right", va="top", fontsize=6.4, color=PENCIL)
    ax.set_xlim(0, 1)
    ax.set_xticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_xticklabels(["0", "20%", "40%", "60%", "80%", "100%"], fontsize=6.6)
    ax.tick_params(axis="y", labelsize=6.6)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.set_axisbelow(True)
axes[0].set_ylabel("density", fontsize=7.2)
fig.supxlabel("CDE cumulative non-metro share", fontsize=7.2, y=0.02)
fig.tight_layout(pad=0.3)
fig.subplots_adjust(bottom=0.24)
fig.savefig(FIG / "9_mandate_panels.pdf")
fig.savefig(FIG / "9_mandate_panels.png")
print(f"mandate panels: counts B={_panels[0][2]['B']:+.5f}, "
      f"dollars 2007+ B={_panels[1][2]['B']:+.5f} "
      f"({len(_full)} and {len(_post)} CDEs)")
