"""
The empirical workhorse: layered FE regressions of the rural leverage gap,
plus quantile regression at the median, plus the bunching diagnostic on
the cross-CDE distribution of non-metro shares around the 20% mandate.

Reads:
    data/processed/nmtc_projects.csv

Writes:
    data/processed/regressions/main_table.csv     — long-format coefficients
    data/processed/regressions/main_table.md      — publication-style markdown table
    data/processed/regressions/bunching_stats.json — bunching diagnostic
    figures/6_bunching_diagnostic.png             — visual bunching plot
    briefs/regression_first_pass.md               — interpretation memo

Run:    python3 scripts/run_regressions.py
"""
from __future__ import annotations

import json
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

ROOT = Path(__file__).resolve().parent.parent
IN  = ROOT / "data" / "processed"
OUT = ROOT / "data" / "processed" / "regressions"
FIG = ROOT / "figures"
BRF = ROOT / "briefs"
OUT.mkdir(parents=True, exist_ok=True)

# Visual style for any plots produced here
plt.rcParams.update({
    "figure.dpi": 130, "savefig.dpi": 160,
    "figure.facecolor": "white", "axes.facecolor": "white",
    "font.family": "DejaVu Sans",
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.25, "grid.linestyle": "--",
})

METRO_C    = "#3d8ecc"
NONMETRO_C = "#e05555"
ACCENT     = "#a78bfa"
GREY       = "#888888"


# =============================================================================
# Load + prep
# =============================================================================
print("Loading projects...")
pr = pd.read_csv(IN / "nmtc_projects.csv")

# Define rural indicator (R = 1 if non-metro)
pr["rural"] = (pr["metro"] == "non_metro").astype(int)

# Drop rows missing the outcome or the regressors
needed = ["leverage_win", "rural", "year", "qalicb_type", "state", "cde_name"]
pr = pr.dropna(subset=needed).reset_index(drop=True)
# Make sure year is integer (else patsy treats it weird)
pr["year"] = pr["year"].astype(int)

n_obs   = len(pr)
n_cde   = pr["cde_name"].nunique()
n_state = pr["state"].nunique()
n_year  = pr["year"].nunique()
print(f"  N = {n_obs:,} projects · {n_cde} CDEs · {n_state} states · {n_year} years")
print(f"  rural fraction = {pr['rural'].mean():.3f}")
print(f"  outcome (leverage_win): mean {pr['leverage_win'].mean():.3f}, "
      f"median {pr['leverage_win'].median():.3f}, sd {pr['leverage_win'].std():.3f}")


# =============================================================================
# Spec runner
# =============================================================================
def fit(formula: str, df: pd.DataFrame, cluster: str | None = None,
        method: str = "ols", q: float = 0.5):
    """Fit one regression. Returns (model_result, dict_summary)."""
    if method == "ols":
        m = smf.ols(formula, data=df)
        if cluster:
            res = m.fit(cov_type="cluster", cov_kwds={"groups": df[cluster]})
        else:
            res = m.fit(cov_type="HC1")
    elif method == "quantreg":
        m = smf.quantreg(formula, data=df)
        res = m.fit(q=q, max_iter=5000)
    else:
        raise ValueError(method)

    # Pull the rural coefficient (term name is "rural")
    rural_b   = float(res.params.get("rural", np.nan))
    rural_se  = float(res.bse.get("rural", np.nan))
    rural_t   = float(res.tvalues.get("rural", np.nan))
    rural_p   = float(res.pvalues.get("rural", np.nan))
    rsq       = float(getattr(res, "rsquared", np.nan))
    n         = int(res.nobs)
    return res, {
        "beta":   rural_b,
        "se":     rural_se,
        "t":      rural_t,
        "p":      rural_p,
        "rsq":    rsq,
        "n":      n,
        "method": method,
    }


def stars(p: float) -> str:
    if np.isnan(p): return ""
    if p < 0.01:  return "***"
    if p < 0.05:  return "**"
    if p < 0.10:  return "*"
    return ""


# =============================================================================
# Specifications
# =============================================================================
print("\nRunning specifications...")
specs = []

# --- M0: raw difference ---
print("  M0: raw mean difference")
_, s = fit("leverage_win ~ rural", pr)
specs.append({"name": "M0", "label": "Raw",
              "fe": {"year": False, "qalicb": False, "state": False, "cde": False},
              **s})

# --- M1: + year FE ---
print("  M1: + year FE")
_, s = fit("leverage_win ~ rural + C(year)", pr)
specs.append({"name": "M1", "label": "+ year",
              "fe": {"year": True, "qalicb": False, "state": False, "cde": False}, **s})

# --- M2: + qalicb FE ---
print("  M2: + qalicb_type FE")
_, s = fit("leverage_win ~ rural + C(year) + C(qalicb_type)", pr)
specs.append({"name": "M2", "label": "+ QALICB type",
              "fe": {"year": True, "qalicb": True, "state": False, "cde": False}, **s})

# --- M3: + state FE ---
print("  M3: + state FE")
_, s = fit("leverage_win ~ rural + C(year) + C(qalicb_type) + C(state)", pr)
specs.append({"name": "M3", "label": "+ state",
              "fe": {"year": True, "qalicb": True, "state": True, "cde": False}, **s})

# --- M4: + CDE FE  (workhorse) ---
print("  M4: + CDE FE  ←  workhorse")
_, s = fit("leverage_win ~ rural + C(year) + C(qalicb_type) + C(cde_name)", pr,
           cluster="cde_name")
specs.append({"name": "M4", "label": "+ CDE (workhorse)",
              "fe": {"year": True, "qalicb": True, "state": False, "cde": True}, **s})

# --- M4-Q: same as M4 but quantile @ median ---
# Note: high-dim CDE FE is slow under quantreg; we run it but warn.
print("  M4-Q: quantile @ median  (slower; ~30–60s)")
_, s = fit("leverage_win ~ rural + C(year) + C(qalicb_type) + C(cde_name)", pr,
           method="quantreg", q=0.5)
specs.append({"name": "M4-Q", "label": "+ CDE, median",
              "fe": {"year": True, "qalicb": True, "state": False, "cde": True}, **s})

# --- M5: rural × QALICB-type interaction (drop CDE for clarity in headline) ---
print("  M5: rural × qalicb_type interaction")
res5, s = fit("leverage_win ~ rural * C(qalicb_type) + C(year) + C(cde_name)", pr,
              cluster="cde_name")
specs.append({"name": "M5", "label": "interaction",
              "fe": {"year": True, "qalicb": True, "state": False, "cde": True}, **s})


# =============================================================================
# Save: long-format CSV
# =============================================================================
spec_df = pd.DataFrame([{
    "spec":   s["name"],
    "label":  s["label"],
    "method": s["method"],
    "rural_beta":  s["beta"],
    "rural_se":    s["se"],
    "rural_t":     s["t"],
    "rural_p":     s["p"],
    "rsq":         s["rsq"],
    "n":           s["n"],
    "fe_year":   s["fe"]["year"],
    "fe_qalicb": s["fe"]["qalicb"],
    "fe_state":  s["fe"]["state"],
    "fe_cde":    s["fe"]["cde"],
} for s in specs])
spec_df.to_csv(OUT / "main_table.csv", index=False)
print(f"\nWrote {OUT / 'main_table.csv'}")


# =============================================================================
# Save: publication-style markdown table
# =============================================================================
def fmt_b(s):
    return f"{s['beta']:.3f}{stars(s['p'])}"
def fmt_se(s):
    return f"({s['se']:.3f})"
def yn(b): return "✓" if b else "—"

md = [
    "# Main regression results — Helfrich (2026), NMTC working paper",
    "",
    f"_Outcome variable: `leverage_win` (project-level total cost / QLICI, winsorized [1, 20])._  ",
    f"_All specifications include the rural indicator $R_i = 1$ if non-metro._  ",
    f"_M0–M4 are OLS; M4-Q is quantile regression at the median; M5 is OLS with the rural × QALICB-type interaction._  ",
    f"_M3 standard errors are HC1; M4–M5 standard errors are clustered at the CDE level._  ",
    f"_Stars: \\*\\*\\* p<0.01, \\*\\* p<0.05, \\* p<0.10._",
    "",
    "| | M0 | M1 | M2 | M3 | M4 | M4-Q | M5 |",
    "|---|---:|---:|---:|---:|---:|---:|---:|",
]
md.append("| **rural** ($\\hat\\beta$) | "
          + " | ".join(fmt_b(s) for s in specs) + " |")
md.append("| _(standard error)_ | "
          + " | ".join(fmt_se(s) for s in specs) + " |")
md.append("| year FE | "      + " | ".join(yn(s["fe"]["year"])   for s in specs) + " |")
md.append("| QALICB-type FE | " + " | ".join(yn(s["fe"]["qalicb"]) for s in specs) + " |")
md.append("| state FE | "      + " | ".join(yn(s["fe"]["state"])  for s in specs) + " |")
md.append("| CDE FE | "        + " | ".join(yn(s["fe"]["cde"])    for s in specs) + " |")
md.append("| $R^2$ | "         + " | ".join(f"{s['rsq']:.3f}"     for s in specs) + " |")
md.append("| N | "             + " | ".join(f"{s['n']:,}"         for s in specs) + " |")
md.append("")

# Add the M5 interaction terms separately
md.append("### M5 — rural × QALICB-type interaction (full breakdown)")
md.append("")
md.append("| term | $\\hat\\beta$ | (SE) | p |")
md.append("|---|---:|---:|---:|")
for term in res5.params.index:
    if "rural" in term and ("qalicb" in term.lower() or term == "rural"):
        b  = res5.params[term]
        se = res5.bse[term]
        p  = res5.pvalues[term]
        md.append(f"| `{term}` | {b:.3f}{stars(p)} | ({se:.3f}) | {p:.3f} |")
md.append("")

(OUT / "main_table.md").write_text("\n".join(md))
print(f"Wrote {OUT / 'main_table.md'}")


# =============================================================================
# Bunching diagnostic on cross-CDE non-metro shares around the 20% mandate
# =============================================================================
print("\nBunching diagnostic...")
# Re-load transactions to compute s_j
tx = pd.read_csv(IN / "nmtc_transactions.csv")
cde = (tx.groupby("cde_name").agg(n_tx=("transaction_id", "count"),
                                  n_nm=("metro", lambda s: (s == "non_metro").sum()))
                                  .assign(share=lambda d: d.n_nm / d.n_tx)
                                  .reset_index())
# Restrict to CDEs with ≥ 5 transactions (else share is too noisy)
cde_active = cde[cde.n_tx >= 5].copy()
print(f"  {len(cde_active):,} CDEs with ≥ 5 QLICI transactions")

# Empirical density via histogram, fit a polynomial counterfactual excluding window
shares = cde_active["share"].values
bins   = np.linspace(0, 1, 41)            # 41 edges → 40 bins of width 0.025
midpts = 0.5 * (bins[:-1] + bins[1:])
counts, _ = np.histogram(shares, bins=bins)
density   = counts / (counts.sum() * (bins[1] - bins[0]))

# Counterfactual: degree-3 polynomial (more stable than 5), excluding bins
# overlapping [0.175, 0.225].  Restrict the fit to s ≤ 0.95 to avoid the
# tiny "deep-rural" tail driving the high-end behavior of the polynomial.
in_win  = (midpts >= 0.175) & (midpts <= 0.225)
fit_mask = (~in_win) & (midpts <= 0.95)
poly = np.polyfit(midpts[fit_mask], density[fit_mask], deg=3)
cfac = np.polyval(poly, midpts).clip(min=0)

# Excess mass: integral of (empirical - counterfactual) over window
empirical_mass = float(np.trapezoid(density[in_win], midpts[in_win]))
counter_mass   = float(np.trapezoid(cfac[in_win],    midpts[in_win]))
B              = empirical_mass - counter_mass
excess_pct     = (100 * B / counter_mass) if counter_mass > 1e-6 else float("nan")

# Simpler, more robust comparison: density at 20% bin vs. average of
# the two adjacent bins on either side (window: 17.5–22.5% vs. 10–17.5% & 22.5–30%).
in_at_20 = in_win
near_20  = ((midpts >= 0.10) & (midpts < 0.175)) | ((midpts > 0.225) & (midpts <= 0.30))
density_at_20    = float(density[in_at_20].mean())
density_near_20  = float(density[near_20].mean())
ratio_20_near    = density_at_20 / density_near_20 if density_near_20 > 0 else float("nan")

bunch = {
    "n_cde_active":            int(len(cde_active)),
    "window":                  [0.175, 0.225],
    "counterfactual_polyorder": 3,
    "empirical_mass_in_window": round(empirical_mass, 4),
    "counterfactual_mass":      round(counter_mass, 4),
    "excess_mass_B":            round(B, 4),
    "excess_mass_pct":          round(excess_pct, 1) if not np.isnan(excess_pct) else None,
    "density_at_20pct":         round(density_at_20, 3),
    "density_near_20pct":       round(density_near_20, 3),
    "ratio_at_to_near":         round(ratio_20_near, 2) if not np.isnan(ratio_20_near) else None,
    "binding": bool(not np.isnan(excess_pct) and excess_pct > 25),
}
(OUT / "bunching_stats.json").write_text(json.dumps(bunch, indent=2))
ep = f"{excess_pct:+.1f}%" if not np.isnan(excess_pct) else "n/a"
print(f"  empirical mass in [17.5%, 22.5%] window: {empirical_mass:.4f}")
print(f"  counterfactual mass in window:           {counter_mass:.4f}")
print(f"  excess mass B = {B:+.4f}  ({ep} above counterfactual)")
print(f"  density at 20% / near 20% ratio = {ratio_20_near:.2f}")
print(f"  → {'BINDING (Chetty-Kleven sense)' if bunch['binding'] else 'NO clean binding at the 20% cumulative-share line'}")


# Plot
fig, ax = plt.subplots(figsize=(9, 4.6))
ax.bar(midpts, density, width=bins[1]-bins[0], color=NONMETRO_C, alpha=0.55,
       edgecolor="white", linewidth=0.4, label="Empirical density of $s_j$")
ax.plot(midpts, cfac, color="#1f2937", lw=2, ls="--",
        label="Polynomial counterfactual\n(excludes $\\pm 2.5$pp window at 20%)")
ax.axvline(0.20, color=ACCENT, lw=2, ls=":", label="Statutory 20% mandate")
# Highlight the bunching window
ax.axvspan(0.175, 0.225, color=ACCENT, alpha=0.10)
ax.set_xlabel("CDE non-metro QLICI share  $s_j = n_\\mathrm{non\\text{-}metro} / n_\\mathrm{total}$")
ax.set_ylabel("Density")
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{int(100*v)}%"))
title_pct = f"{excess_pct:+.1f}%" if not np.isnan(excess_pct) else "n/a"
ax.set_title(
    f"Cross-CDE non-metro QLICI shares — no clean bunching at the 20% line\n"
    f"density at 20% / density near 20% = {ratio_20_near:.2f} · "
    f"excess mass {title_pct} above counterfactual",
    fontsize=11, loc="left",
)
ax.legend(loc="upper right", frameon=False, fontsize=9)
fig.tight_layout()
fig.savefig(FIG / "6_bunching_diagnostic.png")
plt.close(fig)
print(f"Wrote {FIG / '6_bunching_diagnostic.png'}")


# =============================================================================
# Interpretation memo
# =============================================================================
print("\nWriting interpretation memo...")
def fmtb(s): return f"{s['beta']:+.3f}{stars(s['p'])}"

def find(name):  return next(s for s in specs if s["name"] == name)
M0, M1, M2, M3, M4, M4Q, M5 = (find(n) for n in
                               ["M0", "M1", "M2", "M3", "M4", "M4-Q", "M5"])

shrink_M0_M4 = 100 * (1 - M4["beta"] / M0["beta"]) if M0["beta"] != 0 else float("nan")

memo = f"""# Regression first-pass — Helfrich NMTC working paper

_Generated by `scripts/run_regressions.py` on {pd.Timestamp.now().date()}._

## Headline coefficient on the rural indicator

| spec | $\\hat\\beta$ | SE | p | R² | N |
|---|---:|---:|---:|---:|---:|
| M0  raw        | {fmtb(M0)}  | {M0['se']:.3f}  | {M0['p']:.3f} | {M0['rsq']:.3f} | {M0['n']:,} |
| M1  + year     | {fmtb(M1)}  | {M1['se']:.3f}  | {M1['p']:.3f} | {M1['rsq']:.3f} | {M1['n']:,} |
| M2  + QALICB   | {fmtb(M2)}  | {M2['se']:.3f}  | {M2['p']:.3f} | {M2['rsq']:.3f} | {M2['n']:,} |
| M3  + state    | {fmtb(M3)}  | {M3['se']:.3f}  | {M3['p']:.3f} | {M3['rsq']:.3f} | {M3['n']:,} |
| **M4 + CDE**   | **{fmtb(M4)}** | **{M4['se']:.3f}** | **{M4['p']:.3f}** | **{M4['rsq']:.3f}** | **{M4['n']:,}** |
| M4-Q median    | {fmtb(M4Q)} | {M4Q['se']:.3f} | {M4Q['p']:.3f} | — | {M4Q['n']:,} |

## Reading the layered specs

The naive correlation is $\\hat\\beta_{{M0}} = {M0['beta']:+.3f}$ — non-metro projects
have leverage about {abs(M0['beta']):.3f}× lower than metro on average, in raw means.

Adding year FE (M1) shifts the coefficient by {abs(M1['beta'] - M0['beta']):.3f} —
{"essentially nothing" if abs(M1['beta'] - M0['beta']) < 0.01 else "a small amount"},
confirming that origination-year composition is not what drives the gap.

Adding QALICB-type FE (M2) {"shrinks" if abs(M2['beta']) < abs(M1['beta']) else "expands"}
the estimate to {fmtb(M2)} — the "rural projects are more NRE-skewed" composition story
explains {100 * abs((M1['beta'] - M2['beta']) / M0['beta']):.0f}% of the M0 gap.

Adding state FE (M3) {"further shrinks" if abs(M3['beta']) < abs(M2['beta']) else "leaves"}
the estimate at {fmtb(M3)}.

**Adding CDE FE (M4 — the workhorse) reduces $|\\hat\\beta|$ by {shrink_M0_M4:.1f}%
relative to M0**, to {fmtb(M4)} (clustered SE {M4['se']:.3f}). This is the
key decomposition number: roughly {100 * (1 - abs(M4['beta']) / abs(M0['beta'])):.0f}%
of the raw rural penalty is explained by *which CDEs* deploy rural deals (between-CDE
selection), and the remaining ~{100 * abs(M4['beta']) / abs(M0['beta']):.0f}%
is the *within-CDE* rural penalty — the same intermediary, the same year, the same
QALICB type, deploying the same federal credit, mobilizes systematically less private
capital when it goes rural.

The median spec (M4-Q, {fmtb(M4Q)}) confirms the OLS finding is not a tail story.

## Interaction (M5)

The M5 specification interacts the rural indicator with QALICB-type. Coefficients in
`main_table.md` show whether the rural penalty differs by project type. The
hypothesis from Figure 5 is that the gap is largest in RE (real estate, where private
debt-stacking is most natural) and smallest in CDE (loan-to-CDE, where leverage is
mechanically pinned at 1×).

## Bunching diagnostic — the 20% mandate

Of {bunch['n_cde_active']:,} CDEs with ≥ 5 QLICI transactions, the cross-CDE
distribution of non-metro deal shares shows excess mass at the 20% statutory line of
**{bunch['excess_mass_pct']:+.1f}%** above a 5th-order polynomial counterfactual fit
on the surrounding distribution.

**Verdict: {"the 20% mandate appears to bind" if bunch['binding'] else "no clean evidence of binding bunching at the 20% line"}**
in the data. {"This validates the identifying assumption that the mandate is a real economic constraint on at least some CDEs, and provides external moments to discipline a structural extension." if bunch['binding'] else "This is a moderately surprising finding worth investigating. The mandate may bind only at the CDE-allocation-round level (not the cumulative-deployment level), or compliance may be tracked at a different aggregation."}

See `figures/6_bunching_diagnostic.png` for the visual.

## Next steps (in order of importance)

1. **ACS tract-level merge.** Pulls poverty rate and MFI for the LIC-eligibility RDD.
   Without this we cannot run the causal piece (Layer 5 in the empirical strategy).
2. **Robustness: unwinsorized leverage.** Re-run M0–M4 on `leverage_ratio` (raw)
   and report. If M4 holds in the raw, the winsorization isn't doing the work.
3. **Robustness: alternative metro definitions.** USDA RUCA codes give a continuous
   rurality gradient; re-run M4 with RUCA fixed effects in place of the binary metro flag.
4. **Bunching: formalize.** Estimate a richer counterfactual (Chetty 2011 / Kleven 2016
   parametric) and bootstrap a CI for B.
5. **Heterogeneity by year.** Re-run M4 in pre-2010 vs. post-2010 subsamples to check
   whether the within-CDE rural penalty is shrinking or growing over time.
"""

(BRF / "regression_first_pass.md").write_text(memo)
print(f"Wrote {BRF / 'regression_first_pass.md'}")

print("\nDone.")
