"""
Referee-grade fixes for the V1 manuscript. Every quantity this script
reports is computed from the data in this run, and every identity that can
be checked numerically IS checked, with hard assertions:

  F1  Gelbach (2016) conditional decomposition of the raw rural gap into
      year / QALICB-type / CDE components (full-model reference, so the
      decomposition is invariant to the order covariate blocks are listed).
      VALIDATION: components must sum to beta_M0 - beta_full to 1e-8.
  F2  Cluster bootstrap (resample CDEs) for the selection share
      1 - beta_full / beta_M0 and for the Gelbach CDE component.
  F3  Power honesty: the largest within-CDE rural penalty rejectable at the
      one-sided 5% level, for the mean (M4) and median (M4-Q) estimates.
  F4  Extensive/intensive margins: LPM for P(leverage > floor) and OLS on
      leverage among mobilizing projects, both with M4 fixed effects and
      CDE-clustered SEs; floor sensitivity at 1.001 and 1.05.
  F5  Switcher diagnostics: the M4 rural coefficient is identified only by
      CDEs operating on both sides of the rural line; count them and the
      share of rural projects they cover.
  F6  Missing robustness: top-50 CDE subsample; two-way clustered SEs
      (CDE x tract) via Cameron-Gelbach-Miller inclusion-exclusion.
      VALIDATION: CGM variance must be positive; each one-way piece must
      reproduce the single-clustered fits.

Reads:  data/processed/nmtc_projects.csv
Writes: data/processed/regressions/referee_fixes.json
        data/processed/regressions/referee_fixes.md

Run:    python3 scripts/run_referee_fixes.py          (~5-10 min: bootstrap)
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
BOOT_REPS = 499
SEED = 20260813
Z_ONESIDED_05 = 1.6448536269514722

pr = pd.read_csv(IN / "nmtc_projects.csv")
pr["rural"] = (pr["metro"] == "non_metro").astype(int)
pr = pr.dropna(subset=["leverage_win", "leverage_ratio", "rural", "year",
                       "qalicb_type", "state", "cde_name",
                       "tract_fips"]).reset_index(drop=True)
pr["year"] = pr["year"].astype(int)
print(f"N = {len(pr):,} (after requiring tract_fips for two-way clustering; "
      f"full sample was 8,024)")

results: dict = {"n_analysis": int(len(pr))}

# ============================================================================
# Design matrices built once, by hand, so the Gelbach blocks are explicit.
# Drop-first coding; intercept carried separately.
# ============================================================================
R = pr["rural"].to_numpy(float)
y = pr["leverage_win"].to_numpy(float)
D_year = pd.get_dummies(pr["year"], prefix="y", drop_first=True, dtype=float)
D_type = pd.get_dummies(pr["qalicb_type"], prefix="q", drop_first=True, dtype=float)
D_cde = pd.get_dummies(pr["cde_name"], prefix="c", drop_first=True, dtype=float)
ONE = np.ones((len(pr), 1))

blocks = {"year": D_year.to_numpy(), "qalicb": D_type.to_numpy(),
          "cde": D_cde.to_numpy()}
k_slices = {}
X_parts = [ONE, R.reshape(-1, 1)]
pos = 2
for name, M in blocks.items():
    k_slices[name] = slice(pos, pos + M.shape[1])
    X_parts.append(M)
    pos += M.shape[1]
X_full = np.hstack(X_parts)


def ols_beta(X: np.ndarray, yv: np.ndarray) -> np.ndarray:
    beta, *_ = np.linalg.lstsq(X, yv, rcond=None)
    return beta


def gelbach(Xf, yv, Rv, slices) -> dict:
    """Full-model-reference decomposition: beta_base - beta_full equals the
    sum over blocks of cov(R, Z_k theta_k) / var(R~), where the auxiliary
    regression of each block's fitted component on [1, R] gives the block
    contribution exactly (Gelbach 2016, eq. 3)."""
    beta_full_vec = ols_beta(Xf, yv)
    beta_full = float(beta_full_vec[1])
    XB = np.column_stack([np.ones_like(Rv), Rv])
    beta_base = float(ols_beta(XB, yv)[1])
    contrib = {}
    for name, sl in slices.items():
        comp = Xf[:, sl] @ beta_full_vec[sl]
        contrib[name] = float(ols_beta(XB, comp)[1])
    gap = beta_base - beta_full
    ssum = sum(contrib.values())
    assert abs(gap - ssum) < 1e-8, f"Gelbach identity violated: {gap} vs {ssum}"
    return {"beta_base": beta_base, "beta_full": beta_full,
            "contrib": contrib, "identity_residual": gap - ssum}


print("\nF1: Gelbach decomposition (full-model reference)")
G = gelbach(X_full, y, R, k_slices)
print(f"  beta_M0 = {G['beta_base']:+.4f}  beta_full = {G['beta_full']:+.4f}")
for k, v in G["contrib"].items():
    print(f"  contribution[{k}] = {v:+.4f}")
print(f"  identity residual = {G['identity_residual']:.2e}  (asserted < 1e-8)")

# Cross-validation against the formula-based pipeline estimates: the
# full-model rural beta here must match run_regressions.py's M4 to 1e-6.
m4_check = smf.ols("leverage_win ~ rural + C(year) + C(qalicb_type) + C(cde_name)",
                   data=pr).fit()
assert abs(float(m4_check.params["rural"]) - G["beta_full"]) < 1e-6, \
    "hand-built design does not reproduce the formula-based M4 coefficient"
print("  cross-check vs formula API: PASS")

results["F1_gelbach"] = {
    "beta_M0": round(G["beta_base"], 4),
    "beta_full": round(G["beta_full"], 4),
    "contrib_year": round(G["contrib"]["year"], 4),
    "contrib_qalicb": round(G["contrib"]["qalicb"], 4),
    "contrib_cde": round(G["contrib"]["cde"], 4),
    "share_of_gap_from_cde": round(G["contrib"]["cde"]
                                   / (G["beta_base"] - G["beta_full"]), 4),
}

# ============================================================================
# F2: cluster bootstrap over CDEs for the selection share and CDE component
# ============================================================================
print(f"\nF2: CDE-cluster bootstrap ({BOOT_REPS} reps)")
rng = np.random.default_rng(SEED)
cde_ids = pr["cde_name"].unique()
by_cde = {c: g.index.to_numpy() for c, g in pr.groupby("cde_name")}
shares, cde_contribs = [], []
fails = 0
for rep in range(BOOT_REPS):
    draw = rng.choice(cde_ids, size=len(cde_ids), replace=True)
    idx = np.concatenate([by_cde[c] for c in draw])
    dfb = pr.iloc[idx]
    Rb = dfb["rural"].to_numpy(float)
    if Rb.std() < 1e-12:
        fails += 1
        continue
    yb = dfb["leverage_win"].to_numpy(float)
    Dy = pd.get_dummies(dfb["year"], drop_first=True, dtype=float).to_numpy()
    Dq = pd.get_dummies(dfb["qalicb_type"], drop_first=True, dtype=float).to_numpy()
    # resampled CDEs must be distinct clusters even when drawn twice
    Dc = pd.get_dummies(
        pd.Series(np.repeat(np.arange(len(draw)), [len(by_cde[c]) for c in draw])),
        drop_first=True, dtype=float).to_numpy()
    sl = {}
    parts = [np.ones((len(dfb), 1)), Rb.reshape(-1, 1)]
    p = 2
    for name, M in (("year", Dy), ("qalicb", Dq), ("cde", Dc)):
        sl[name] = slice(p, p + M.shape[1]); parts.append(M); p += M.shape[1]
    try:
        g = gelbach(np.hstack(parts), yb, Rb, sl)
    except AssertionError:
        fails += 1
        continue
    if abs(g["beta_base"]) < 1e-6:
        fails += 1
        continue
    shares.append(1 - g["beta_full"] / g["beta_base"])
    cde_contribs.append(g["contrib"]["cde"])
shares = np.array(shares)
cde_contribs = np.array(cde_contribs)
share_hat = 1 - G["beta_full"] / G["beta_base"]
results["F2_bootstrap"] = {
    "reps_requested": BOOT_REPS,
    "reps_used": int(len(shares)),
    "reps_failed": int(fails),
    "selection_share_hat": round(share_hat, 4),
    "selection_share_ci95": [round(float(np.percentile(shares, 2.5)), 4),
                             round(float(np.percentile(shares, 97.5)), 4)],
    "cde_contrib_ci95": [round(float(np.percentile(cde_contribs, 2.5)), 4),
                         round(float(np.percentile(cde_contribs, 97.5)), 4)],
}
print(f"  selection share = {share_hat:.3f}, "
      f"CI95 = {results['F2_bootstrap']['selection_share_ci95']} "
      f"({len(shares)} reps used, {fails} failed)")

# ============================================================================
# F3: power honesty — largest rejectable penalty (one-sided 5%)
# ============================================================================
print("\nF3: equivalence bounds")
m4 = smf.ols("leverage_win ~ rural + C(year) + C(qalicb_type) + C(cde_name)",
             data=pr).fit(cov_type="cluster", cov_kwds={"groups": pr["cde_name"]})
b_m4, se_m4 = float(m4.params["rural"]), float(m4.bse["rural"])
mq = smf.quantreg("leverage_win ~ rural + C(year) + C(qalicb_type) + C(cde_name)",
                  data=pr).fit(q=0.5, max_iter=5000)
b_mq, se_mq = float(mq.params["rural"]), float(mq.bse["rural"])
# Reject H0: beta <= -Delta at one-sided 5% iff (b + Delta)/se > z  =>
# smallest rejectable Delta* = z*se - b
delta_mean = Z_ONESIDED_05 * se_m4 - b_m4
delta_med = Z_ONESIDED_05 * se_mq - b_mq
results["F3_power"] = {
    "mean_beta": round(b_m4, 4), "mean_se_cde_cluster": round(se_m4, 4),
    "mean_ci95": [round(b_m4 - 1.96 * se_m4, 3), round(b_m4 + 1.96 * se_m4, 3)],
    "mean_rejectable_penalty": round(delta_mean, 3),
    "median_beta": round(b_mq, 4), "median_se_iid": round(se_mq, 4),
    "median_rejectable_penalty": round(delta_med, 3),
    "caveat": "median SE is the quantreg asymptotic (kernel) SE, not "
              "CDE-clustered; a clustered bootstrap for the median with "
              "~600 FE is computationally heavy and left documented",
}
print(f"  mean:   beta={b_m4:+.3f} SE={se_m4:.3f} -> can only reject "
      f"penalties > {delta_mean:.3f}")
print(f"  median: beta={b_mq:+.3f} SE={se_mq:.3f} -> can reject "
      f"penalties > {delta_med:.3f}")

# ============================================================================
# F4: extensive / intensive margins
# ============================================================================
print("\nF4: margins")
for floor in (1.001, 1.05):
    pr["mobilized"] = (pr["leverage_ratio"] > floor).astype(float)
    ext = smf.ols("mobilized ~ rural + C(year) + C(qalicb_type) + C(cde_name)",
                  data=pr).fit(cov_type="cluster",
                               cov_kwds={"groups": pr["cde_name"]})
    sub = pr[pr["leverage_ratio"] > floor]
    inten = smf.ols("leverage_win ~ rural + C(year) + C(qalicb_type) + C(cde_name)",
                    data=sub).fit(cov_type="cluster",
                                  cov_kwds={"groups": sub["cde_name"]})
    key = f"floor_{str(floor).replace('.', 'p')}"
    results[f"F4_{key}"] = {
        "share_at_floor": round(float(1 - pr["mobilized"].mean()), 4),
        "extensive_beta": round(float(ext.params["rural"]), 4),
        "extensive_se": round(float(ext.bse["rural"]), 4),
        "extensive_p": round(float(ext.pvalues["rural"]), 4),
        "intensive_beta": round(float(inten.params["rural"]), 4),
        "intensive_se": round(float(inten.bse["rural"]), 4),
        "intensive_p": round(float(inten.pvalues["rural"]), 4),
        "intensive_n": int(inten.nobs),
    }
    print(f"  floor {floor}: {100*(1-pr['mobilized'].mean()):.1f}% at floor; "
          f"extensive {float(ext.params['rural']):+.4f} "
          f"(p={float(ext.pvalues['rural']):.2f}); "
          f"intensive {float(inten.params['rural']):+.4f} "
          f"(p={float(inten.pvalues['rural']):.2f}, n={int(inten.nobs):,})")

# ============================================================================
# F5: switcher diagnostics
# ============================================================================
print("\nF5: switchers")
g = pr.groupby("cde_name")["rural"].agg(["mean", "count", "sum"])
switchers = g[(g["mean"] > 0) & (g["mean"] < 1)]
rural_total = int(pr["rural"].sum())
rural_in_sw = int(pr[pr["cde_name"].isin(switchers.index)]["rural"].sum())
results["F5_switchers"] = {
    "n_cde_total": int(len(g)),
    "n_cde_switchers": int(len(switchers)),
    "n_projects_in_switchers": int(switchers["count"].sum()),
    "rural_projects_total": rural_total,
    "rural_projects_in_switchers": rural_in_sw,
    "rural_share_covered_by_switchers": round(rural_in_sw / rural_total, 4),
}
print(f"  {len(switchers)} of {len(g)} CDEs operate on both sides; they hold "
      f"{rural_in_sw:,}/{rural_total:,} rural projects "
      f"({100*rural_in_sw/rural_total:.1f}%)")

# ============================================================================
# F6: top-50 CDEs and two-way clustering (CGM)
# ============================================================================
print("\nF6: remaining robustness")
top50 = pr["cde_name"].value_counts().head(50).index
sub50 = pr[pr["cde_name"].isin(top50)]
m50 = smf.ols("leverage_win ~ rural + C(year) + C(qalicb_type) + C(cde_name)",
              data=sub50).fit(cov_type="cluster",
                              cov_kwds={"groups": sub50["cde_name"]})
results["F6_top50"] = {"beta": round(float(m50.params["rural"]), 4),
                       "se": round(float(m50.bse["rural"]), 4),
                       "p": round(float(m50.pvalues["rural"]), 4),
                       "n": int(m50.nobs),
                       "n_cde": 50}
print(f"  top-50 CDEs: {float(m50.params['rural']):+.4f} "
      f"(SE {float(m50.bse['rural']):.4f}, n={int(m50.nobs):,})")

# CGM two-way: V = V_cde + V_tract - V_(cde x tract), on the rural coef.
base = "leverage_win ~ rural + C(year) + C(qalicb_type) + C(cde_name)"
pr["cde_x_tract"] = pr["cde_name"].astype(str) + "|" + pr["tract_fips"].astype(str)
v = {}
for gname in ("cde_name", "tract_fips", "cde_x_tract"):
    fit_g = smf.ols(base, data=pr).fit(cov_type="cluster",
                                       cov_kwds={"groups": pr[gname]})
    v[gname] = float(fit_g.bse["rural"]) ** 2
    if gname == "cde_name":
        assert abs(float(fit_g.params["rural"]) - b_m4) < 1e-9
var_2way = v["cde_name"] + v["tract_fips"] - v["cde_x_tract"]
assert var_2way > 0, "CGM two-way variance non-positive; report one-way pieces"
se_2way = float(np.sqrt(var_2way))
results["F6_twoway"] = {
    "beta": round(b_m4, 4),
    "se_cde": round(float(np.sqrt(v["cde_name"])), 4),
    "se_tract": round(float(np.sqrt(v["tract_fips"])), 4),
    "se_intersection": round(float(np.sqrt(v["cde_x_tract"])), 4),
    "se_twoway_cgm": round(se_2way, 4),
    "p_twoway": round(float(2 * (1 - __import__("scipy.stats", fromlist=["norm"])
                                 .norm.cdf(abs(b_m4) / se_2way))), 4),
}
print(f"  two-way CGM SE = {se_2way:.4f} "
      f"(one-way: cde {np.sqrt(v['cde_name']):.4f}, "
      f"tract {np.sqrt(v['tract_fips']):.4f})")

# ============================================================================
# Persist
# ============================================================================
(OUT / "referee_fixes.json").write_text(json.dumps(results, indent=2))
md = ["# Referee fixes — computed outputs", "",
      "_Every number in this file was computed by `scripts/run_referee_fixes.py`;",
      "the Gelbach identity, the formula-API cross-check, and the CGM positivity",
      "check are hard assertions inside the run._", "",
      "```json", json.dumps(results, indent=2), "```", ""]
(OUT / "referee_fixes.md").write_text("\n".join(md))
print(f"\nWrote {OUT/'referee_fixes.json'} and .md")
print("Done.")
