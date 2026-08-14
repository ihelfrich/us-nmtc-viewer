"""
The quantile process of the within-CDE rural coefficient.

The paper's central claim is a within-intermediary null, and it establishes
that at the mean and the median. Both describe the centre of the
conditional distribution and neither says anything about its shape.
Estimating the same specification across the quantile process shows the
coefficient sitting at zero through the lower half and drifting negative
above the median, reaching -0.20 at the 0.95 quantile.

An early reading of that gradient, taken off a bootstrap with too few
replications, treated it as a rural penalty concentrated among the deals
that mobilize the most capital. The full bootstrap does not support that
reading. The interval widens at least as fast as the point estimate falls,
and no quantile in the upper tail is distinguishable from zero. The figure
is drawn so that this is the first thing a reader sees, which is why the
band is plotted rather than the point estimates alone.

Two further features carry information and are drawn deliberately.

The shaded region marks where the estimator is degenerate. The outcome has
a 26.9% point mass at exactly 1.0, so quantiles inside that mass are pinned
to a vertex and their standard errors are not interpretable; the run
records the pinned share at each quantile and this figure reads it rather
than assuming where the boundary falls. The median itself is inside that
region, which is the single most consequential thing this figure shows.

The interval band is the CDE-cluster bootstrap, not the asymptotic
quantile-regression band, because the asymptotic sparsity estimator assumes
a positive continuous density at the estimated quantile and the mass point
violates that assumption exactly where the paper leans hardest.

Reads:  data/processed/regressions/median_inference.json
Writes: figures/10_quantile_process.{pdf,png} and a .json sidecar

Run:    uv run --no-project --with pandas --with numpy --with matplotlib \
            python scripts/make_quantile_figure.py
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "figures"
REG = ROOT / "data" / "processed" / "regressions"

INK = "#16161D"
PENBLUE = "#2852E8"
PENCIL = "#6B6B70"
WASH = "#EEF2FA"
PINNED_WASH = "#F2EFE9"
PINNED_THRESHOLD = 0.05      # share of bootstrap draws stuck at the point estimate

plt.rcParams.update({
    "figure.dpi": 130, "savefig.dpi": 300,
    "font.family": "serif",
    "font.serif": ["Palatino", "TeX Gyre Pagella", "DejaVu Serif"],
    "axes.edgecolor": PENCIL, "axes.linewidth": 0.6,
    "xtick.color": PENCIL, "ytick.color": PENCIL,
    "text.color": INK, "axes.labelcolor": INK,
    "axes.spines.top": False, "axes.spines.right": False,
})

R = json.loads((REG / "median_inference.json").read_text())

# Assemble the process: the median from M1/M2, the sweep from M5.
rows = [{"q": 0.50,
         "beta": R["point_estimate"],
         "se": R["se_cluster_bootstrap"],
         "lo": R["bootstrap_ci95_percentile"][0],
         "hi": R["bootstrap_ci95_percentile"][1],
         "pinned": R["randomization_share_pinned_at_zero"]}]
for s in R["quantile_sweep"]:
    if not s.get("estimated"):
        continue
    rows.append({"q": s["q"], "beta": s["beta"], "se": s["se_cluster_bootstrap"],
                 "lo": s["ci95"][0], "hi": s["ci95"][1],
                 "pinned": s["share_pinned"]})
rows.sort(key=lambda r: r["q"])

q = np.array([r["q"] for r in rows])
b = np.array([r["beta"] for r in rows])
lo = np.array([r["lo"] for r in rows])
hi = np.array([r["hi"] for r in rows])
pinned = np.array([r["pinned"] for r in rows])

degenerate = pinned >= PINNED_THRESHOLD
if degenerate.any():
    # the boundary is read from the data, not assumed
    q_edge = float(q[degenerate].max())
    edge = (q_edge + float(q[~degenerate].min())) / 2 if (~degenerate).any() else q_edge
else:
    edge = None

fig, ax = plt.subplots(figsize=(4.9, 3.1))

if edge is not None:
    ax.axvspan(q.min() - 0.02, edge, color=PINNED_WASH, zorder=0)
    ax.text(q.min() + 0.005, ax.get_ylim()[0], "", fontsize=6)

ax.axhline(0, color=INK, lw=0.9, zorder=2)
ax.fill_between(q, lo, hi, color=WASH, zorder=1)
ax.plot(q, b, color=PENBLUE, lw=1.6, zorder=3)
ax.scatter(q[~degenerate], b[~degenerate], s=13, color=PENBLUE, zorder=4)
ax.scatter(q[degenerate], b[degenerate], s=13, facecolors="white",
           edgecolors=PENBLUE, linewidths=0.9, zorder=4)

ax.set_xlabel("quantile of the project leverage distribution", fontsize=8)
ax.set_ylabel("within-CDE rural coefficient", fontsize=8)
ax.tick_params(labelsize=7.5)
ax.set_xlim(q.min() - 0.02, q.max() + 0.03)
ax.set_ylim(min(lo.min() * 1.05, -0.35), max(0.10, hi.max() * 1.2))

# Direct labels on the two ends that carry the argument, not on every point.
i_med = int(np.argmin(np.abs(q - 0.50)))
ax.annotate(f"median  {b[i_med]:+.3f}",
            xy=(q[i_med], b[i_med]), xytext=(q[i_med] + 0.02, b[i_med] + 0.075),
            fontsize=6.8, style="italic", color=INK,
            arrowprops=dict(arrowstyle="-|>", color=PENCIL, lw=0.7,
                            shrinkA=0, shrinkB=2))
i_top = int(np.argmax(q))
ax.annotate(f"{q[i_top]:.2f} quantile  {b[i_top]:+.3f}",
            xy=(q[i_top], b[i_top]), xytext=(q[i_top] - 0.30, b[i_top] - 0.02),
            fontsize=6.8, style="italic", color=PENBLUE,
            arrowprops=dict(arrowstyle="-|>", color=PENBLUE, lw=0.7,
                            shrinkA=0, shrinkB=3))

if edge is not None:
    ax.text((q.min() + edge) / 2, ax.get_ylim()[1] * 0.62,
            "estimator pinned inside\nthe 26.9% mass at 1.0",
            ha="center", va="top", fontsize=6.4, style="italic", color=PENCIL)

i_wide = int(np.argmax(hi - lo))
ax.annotate("CDE-cluster bootstrap\n95% interval",
            xy=(q[i_wide], lo[i_wide] * 0.72),
            xytext=(q[i_wide] - 0.16, lo[i_wide] * 0.80),
            ha="right", va="center", fontsize=6.4, style="italic", color=PENCIL,
            arrowprops=dict(arrowstyle="-", color=PENCIL, lw=0.6))

fig.tight_layout()
FIG.mkdir(exist_ok=True)
fig.savefig(FIG / "10_quantile_process.pdf")
fig.savefig(FIG / "10_quantile_process.png")

sidecar = {
    "figure": "10_quantile_process",
    "source": "data/processed/regressions/median_inference.json",
    "interval": "CDE-cluster pairs bootstrap, percentile method",
    "pinned_threshold": PINNED_THRESHOLD,
    "degenerate_quantiles": [float(x) for x in q[degenerate]],
    "points": rows,
}
(FIG / "10_quantile_process.json").write_text(json.dumps(sidecar, indent=2))
print(f"wrote {FIG/'10_quantile_process.pdf'} over {len(rows)} quantiles; "
      f"{int(degenerate.sum())} flagged degenerate")
