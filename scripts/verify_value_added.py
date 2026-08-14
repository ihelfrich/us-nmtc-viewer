"""
Independent check of scripts/run_value_added.py, plus the one weakness its
own memo does not list.

V1  Recompute the raw gap, the CDE effect dispersion, and the empirical
    Bayes decomposition from scratch and compare against the published
    JSON. Nothing is taken from that file except for comparison.

V2  Recompute the urban/rural portability correlation independently.

V3  The missing critique: the counterfactual ranks intermediaries by
    estimated value-added and then evaluates the gain using those same
    estimates. Ranking and evaluating on one draw of noise mechanically
    overstates what reallocation would achieve, which is why the
    value-added literature uses leave-out estimates. This computes an
    out-of-sample version: split every intermediary's deals in half, rank
    on one half, evaluate on the other, and repeat. The gap between the
    in-sample and out-of-sample figures is the size of the problem.

Writes: data/processed/regressions/value_added_verification.json
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
SEED = 20260814
REPS = 200

pub = json.load(open(OUT / "value_added.json"))

pr = pd.read_csv(IN / "nmtc_projects.csv")
pr["rural"] = (pr["metro"] == "non_metro").astype(int)
pr = pr.dropna(subset=["leverage_win", "rural", "year", "qalicb_type",
                       "cde_name", "project_qlici"]).reset_index(drop=True)
pr["year"] = pr["year"].astype(int)

V: dict = {}

# ── V1 raw gap and CDE effects ─────────────────────────────────────────
gap = pr.loc[pr.rural == 1, "leverage_win"].mean() - pr.loc[pr.rural == 0, "leverage_win"].mean()
V["raw_gap_recomputed"] = round(float(gap), 6)
V["raw_gap_published"] = round(pub["raw_rural_gap"]["gap"], 6)
V["raw_gap_matches"] = bool(abs(gap - pub["raw_rural_gap"]["gap"]) < 1e-9)

fit = smf.ols("leverage_win ~ C(cde_name) + C(year) + C(qalicb_type)", data=pr).fit()
eff = {}
base = pr["cde_name"].iloc[0]
for name in pr["cde_name"].unique():
    key = f"C(cde_name)[T.{name}]"
    eff[name] = float(fit.params.get(key, 0.0))
e = pd.Series(eff)
e = e - e.mean()                                   # same normalization
V["cde_effect_sd_recomputed"] = round(float(e.std(ddof=1)), 4)
V["cde_effect_sd_published"] = round(pub["raw_value_added"]["distribution"]["sd"], 4)
V["cde_effect_sd_close"] = bool(abs(e.std(ddof=1) - pub["raw_value_added"]["distribution"]["sd"]) < 0.02)

sigma2 = float(fit.mse_resid)
n_c = pr.groupby("cde_name").size()
samp = (sigma2 / n_c).reindex(e.index)
tot = float(e.var(ddof=1))
sig = tot - float(samp.mean())
V["eb_total_variance_recomputed"] = round(tot, 4)
V["eb_mean_sampling_variance_recomputed"] = round(float(samp.mean()), 4)
V["eb_signal_variance_recomputed"] = round(sig, 4)
V["eb_signal_sd_recomputed"] = round(float(np.sqrt(max(sig, 0))), 4)
V["eb_signal_sd_published"] = round(pub["empirical_bayes"]["signal_sd"], 4)
V["eb_signal_sd_close"] = bool(abs(np.sqrt(max(sig, 0)) - pub["empirical_bayes"]["signal_sd"]) < 0.05)
print(f"V1 raw gap {gap:+.5f} (published {pub['raw_rural_gap']['gap']:+.5f}) "
      f"match={V['raw_gap_matches']}")
print(f"   CDE effect SD {e.std(ddof=1):.3f} vs published "
      f"{pub['raw_value_added']['distribution']['sd']:.3f}")
print(f"   signal SD {np.sqrt(max(sig,0)):.3f} vs published "
      f"{pub['empirical_bayes']['signal_sd']:.3f}")

# ── V2 portability ─────────────────────────────────────────────────────
resid = pr.assign(r=fit.resid + pr["cde_name"].map(e).fillna(0.0))
books = resid.groupby(["cde_name", "rural"])["r"].agg(["mean", "size"]).unstack()
books.columns = ["urban_mean", "rural_mean", "urban_n", "rural_n"]
bk = books.dropna()
bk = bk[(bk.urban_n >= 3) & (bk.rural_n >= 3)]
r_raw = float(np.corrcoef(bk.urban_mean, bk.rural_mean)[0, 1])
V["portability_n_cdes_recomputed"] = int(len(bk))
V["portability_r_recomputed"] = round(r_raw, 4)
V["portability_r_published"] = round(pub["portability"]["raw_correlation"], 4)
V["portability_n_matches"] = bool(int(len(bk)) == pub["portability"]["n_cdes"])
print(f"V2 portability r={r_raw:+.3f} on {len(bk)} CDEs "
      f"(published {pub['portability']['raw_correlation']:+.3f} on "
      f"{pub['portability']['n_cdes']})")

# ── V3 the missing critique: rank out of sample ────────────────────────
# In-sample: rank on all deals, evaluate with the same estimates.
# Out-of-sample: rank on half the deals, evaluate on the held-out half.
rng = np.random.default_rng(SEED)
rural = pr[pr.rural == 1]
dollars_by_cde = rural.groupby("cde_name")["project_qlici"].sum()

def gain_from(rank_series: pd.Series, eval_series: pd.Series) -> float:
    """Move every rural dollar held by below-median-ranked CDEs to the
    above-median group, weighting recipients by their existing rural
    dollars, then value the move with eval_series."""
    common = rank_series.index.intersection(eval_series.index).intersection(dollars_by_cde.index)
    if len(common) < 20:
        return np.nan
    rk, ev = rank_series[common], eval_series[common]
    d = dollars_by_cde[common]
    med = rk.median()
    lo, hi = rk <= med, rk > med
    if d[hi].sum() <= 0 or d.sum() <= 0:
        return np.nan
    moved = d[lo].sum()
    w_obs = float((d * ev).sum() / d.sum())
    d_new = d.copy()
    d_new[lo] = 0.0
    d_new[hi] = d[hi] + moved * (d[hi] / d[hi].sum())
    w_new = float((d_new * ev).sum() / d_new.sum())
    return w_new - w_obs

in_sample = gain_from(e, e)
oos = []
for _ in range(REPS):
    halves = {}
    for name, g in pr.groupby("cde_name"):
        idx = rng.permutation(g.index.to_numpy())
        halves[name] = (idx[: len(idx) // 2], idx[len(idx) // 2:])
    a_idx = np.concatenate([h[0] for h in halves.values() if len(h[0])])
    b_idx = np.concatenate([h[1] for h in halves.values() if len(h[1])])
    ea, eb = {}, {}
    for label, idx, store in (("a", a_idx, ea), ("b", b_idx, eb)):
        sub = pr.loc[idx]
        keep = sub.groupby("cde_name").size()
        keep = keep[keep >= 2].index
        sub = sub[sub.cde_name.isin(keep)]
        if sub["cde_name"].nunique() < 25:
            continue
        m = sub.groupby("cde_name")["leverage_win"].mean()
        store.update((m - m.mean()).to_dict())
    if not ea or not eb:
        continue
    g_oos = gain_from(pd.Series(ea), pd.Series(eb))
    if np.isfinite(g_oos):
        oos.append(g_oos)

oos = np.array(oos)
V["counterfactual_in_sample_gain"] = round(float(in_sample), 4)
V["counterfactual_in_sample_share_of_gap"] = round(float(in_sample / abs(gap)), 4)
V["counterfactual_out_of_sample_gain_median"] = round(float(np.median(oos)), 4)
V["counterfactual_out_of_sample_share_of_gap_median"] = round(float(np.median(oos) / abs(gap)), 4)
V["counterfactual_out_of_sample_interval"] = [
    round(float(np.percentile(oos, 2.5) / abs(gap)), 4),
    round(float(np.percentile(oos, 97.5) / abs(gap)), 4)]
V["counterfactual_reps_used"] = int(len(oos))
V["counterfactual_shrinkage_from_out_of_sample"] = round(
    1 - float(np.median(oos)) / float(in_sample), 4) if in_sample else None
V["counterfactual_note"] = (
    "In-sample ranks and values intermediaries with the same estimates, so "
    "part of the apparent gain is estimation error that would not persist. "
    "The out-of-sample figure ranks on one random half of each "
    "intermediary's deals and values the move on the other half.")
print(f"V3 counterfactual, in sample {in_sample:+.4f} "
      f"({100*in_sample/abs(gap):.1f}% of the gap)")
print(f"   out of sample median {np.median(oos):+.4f} "
      f"({100*np.median(oos)/abs(gap):.1f}% of the gap) over {len(oos)} splits")
print(f"   overstatement from ranking in sample: "
      f"{100*(1-np.median(oos)/in_sample):.0f}%")

(OUT / "value_added_verification.json").write_text(json.dumps(V, indent=2))
print(f"\nWrote {OUT/'value_added_verification.json'}")
