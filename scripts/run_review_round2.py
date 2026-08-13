"""
Round-two analysis, answering the cross-model review (Claude + Codex Sol).
Each item exists because a specific reviewer objection could not be answered
from the existing outputs. Assertions guard the arithmetic.

  G1  Genuinely nested workhorse: year + QALICB + state + CDE effects, so
      the movement from the state-effects column to the CDE column is an
      addition and not a swap. (The published M4 omitted state effects,
      which made the layered narrative inaccurate.)
  G2  Bunching in DOLLAR shares, matching how the mandate is described,
      with a CDE cluster bootstrap. The published test used deal counts.
  G3  Bunching restricted to origination years 2007+, because the
      non-metropolitan proportionality rule enters the code at
      IRC 45D(i)(6) via P.L. 109-432 (2006) and did not govern the early
      sample. Reported for count and dollar shares.
  G4  Fiscal denominators: the tax expenditure is 39% of QEI basis, so the
      paper must separate the project-cost multiple on subsidized
      investment from any per-federal-dollar statement.

Reads:  data/processed/nmtc_projects.csv, nmtc_transactions.csv
Writes: data/processed/regressions/review_round2.json

Run:    python3 scripts/run_review_round2.py
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
SEED = 20260813
BOOT = 999
CREDIT_RATE = 0.39

pr = pd.read_csv(IN / "nmtc_projects.csv")
pr["rural"] = (pr["metro"] == "non_metro").astype(int)
pr = pr.dropna(subset=["leverage_win", "rural", "year", "qalicb_type",
                       "state", "cde_name"]).reset_index(drop=True)
pr["year"] = pr["year"].astype(int)
R: dict = {}

# ── G1 nested workhorse ────────────────────────────────────────────────
print("G1: nested workhorse (year + type + state + CDE)")
fits = {}
for key, rhs in {
    "M3_state_only": "rural + C(year) + C(qalicb_type) + C(state)",
    "M4_cde_no_state": "rural + C(year) + C(qalicb_type) + C(cde_name)",
    "M4S_nested": "rural + C(year) + C(qalicb_type) + C(state) + C(cde_name)",
}.items():
    kw = ({"cov_type": "cluster", "cov_kwds": {"groups": pr["cde_name"]}}
          if "cde_name" in rhs else {"cov_type": "HC1"})
    f = smf.ols(f"leverage_win ~ {rhs}", data=pr).fit(**kw)
    fits[key] = {"beta": round(float(f.params["rural"]), 4),
                 "se": round(float(f.bse["rural"]), 4),
                 "p": round(float(f.pvalues["rural"]), 4),
                 "rsq": round(float(f.rsquared), 4),
                 "n": int(f.nobs)}
    print(f"  {key:18} beta={fits[key]['beta']:+.4f} se={fits[key]['se']:.4f} "
          f"p={fits[key]['p']:.3f}")
# the nested model must fit at least as well as either restricted model
assert fits["M4S_nested"]["rsq"] >= fits["M4_cde_no_state"]["rsq"] - 1e-9
assert fits["M4S_nested"]["rsq"] >= fits["M3_state_only"]["rsq"] - 1e-9
R["G1_specs"] = fits
R["G1_note"] = ("M4 as published omits state effects; M4S adds them to the "
                "CDE-effects model so the layered comparison is nested.")

# ── bunching machinery ─────────────────────────────────────────────────
BINS = np.linspace(0, 1, 41)
MID = 0.5 * (BINS[:-1] + BINS[1:])
WIN = (MID >= 0.175) & (MID <= 0.225)
FITM = (~WIN) & (MID <= 0.95)


def excess_mass(shares: np.ndarray) -> float:
    counts, _ = np.histogram(shares, bins=BINS)
    if counts.sum() == 0:
        return float("nan")
    dens = counts / (counts.sum() * (BINS[1] - BINS[0]))
    cfac = np.polyval(np.polyfit(MID[FITM], dens[FITM], 3), MID).clip(min=0)
    return float(np.trapezoid(dens[WIN], MID[WIN])
                 - np.trapezoid(cfac[WIN], MID[WIN]))


def boot_ci(shares: np.ndarray, reps: int = BOOT) -> list[float]:
    rng = np.random.default_rng(SEED)
    draws = [excess_mass(rng.choice(shares, size=len(shares), replace=True))
             for _ in range(reps)]
    draws = np.array([d for d in draws if np.isfinite(d)])
    return [round(float(np.percentile(draws, 2.5)), 5),
            round(float(np.percentile(draws, 97.5)), 5)]


tx = pd.read_csv(IN / "nmtc_transactions.csv")
tx["is_nm"] = (tx["metro"] == "non_metro").astype(float)


def cde_shares(frame: pd.DataFrame) -> pd.DataFrame:
    g = frame.groupby("cde_name").apply(lambda d: pd.Series({
        "n": len(d),
        "count_share": d["is_nm"].mean(),
        "dollar_share": (d["qlici_amount"] * d["is_nm"]).sum()
                        / max(d["qlici_amount"].sum(), 1e-9),
    }), include_groups=False)
    return g[g["n"] >= 5]


# ── G2 dollar shares, full period ──────────────────────────────────────
print("\nG2: dollar-share bunching, full period")
full = cde_shares(tx)
for lab, col in (("count", "count_share"), ("dollar", "dollar_share")):
    b = excess_mass(full[col].values)
    ci = boot_ci(full[col].values)
    R[f"G2_full_{lab}"] = {"n_cde": int(len(full)), "B": round(b, 5), "ci95": ci}
    print(f"  {lab:6} B={b:+.5f} CI95={ci}")
R["G2_corr_count_dollar"] = round(float(full["count_share"].corr(full["dollar_share"])), 3)

# ── G3 post-2007 subsample ─────────────────────────────────────────────
print("\nG3: bunching restricted to origination years 2007+")
if "year" in tx.columns:
    post = cde_shares(tx[tx["year"] >= 2007])
    for lab, col in (("count", "count_share"), ("dollar", "dollar_share")):
        b = excess_mass(post[col].values)
        ci = boot_ci(post[col].values)
        R[f"G3_post2007_{lab}"] = {"n_cde": int(len(post)), "B": round(b, 5), "ci95": ci}
        print(f"  {lab:6} n_cde={len(post)} B={b:+.5f} CI95={ci}")
else:
    R["G3_post2007_note"] = "transaction file carries no origination year"
    print("  transaction file has no year column; see note")

# ── G4 fiscal denominators ─────────────────────────────────────────────
print("\nG4: denominators")
qlici_total = float(tx["qlici_amount"].sum())
cost_total = float(pr["project_cost"].sum())
other_capital = cost_total - qlici_total
R["G4_denominators"] = {
    "qlici_total_musd": round(qlici_total / 1e6, 1),
    "project_cost_total_musd": round(cost_total / 1e6, 1),
    "other_capital_per_qlici_dollar": round(other_capital / qlici_total, 3),
    "credit_rate_on_qei_basis": CREDIT_RATE,
    "implied_tax_expenditure_musd": round(CREDIT_RATE * qlici_total / 1e6, 1),
    "other_capital_per_credit_dollar": round(
        other_capital / (CREDIT_RATE * qlici_total), 3),
    "note": ("QLICI principal is subsidized investment, not public outlay. "
             "The federal cost is the 39% credit on QEI basis claimed over "
             "seven years; QEI approximately equals QLICI under the "
             "substantially-all requirement. Both ratios are reported so "
             "the paper never labels QLICI principal a federal dollar."),
}
print(f"  other capital per QLICI dollar:  {R['G4_denominators']['other_capital_per_qlici_dollar']}")
print(f"  other capital per credit dollar: {R['G4_denominators']['other_capital_per_credit_dollar']}")

(OUT / "review_round2.json").write_text(json.dumps(R, indent=2))
print(f"\nWrote {OUT/'review_round2.json'}")
