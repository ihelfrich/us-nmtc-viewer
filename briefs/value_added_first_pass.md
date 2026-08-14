# Intermediary value-added: first pass

## Bottom line

The year- and QALICB-adjusted fixed effects are widely dispersed across
343 CDEs. Their raw standard deviation is 1.037
leverage points (IQR 0.777; p10 -0.874, p90
+0.990). Removing the mean pooled-OLS sampling variance leaves an estimated
signal standard deviation of 0.265, only
6.6% of the raw effect variance; mean posterior
reliability is 0.193. The shrunk p10-p90 range is -0.126 to
+0.208. The signal-variance estimate is
strictly positive.

The central portability test uses the 104 CDEs with at least
3 urban and
3 rural projects. Urban- and rural-book
VA correlate at **+0.348**. The classical
reliability correction is **+6.527**
(urban variance reliability 0.086; rural
0.033). This corrected value is **inadmissible as a correlation**: the estimated book reliabilities are so low that classical disattenuation is unstable. It is reported because it is the requested calculation, not as an estimate of a latent correlation. The urban-rural correlation is positive but moderate. Portability has some support, but geography-specific noise or performance remains substantial.

The main surprise is that the geographic portability test is much weaker than the between-CDE dispersion alone would suggest. The repeated split-half exercise is a useful check on whether any CDE
ranking is stable at all: the median half-sample correlation is
+0.446, with a 95% range across 499
random splits of [+0.332, +0.529]. The corresponding Spearman-Brown
full-sample reliability is 0.617.
This exercise includes every CDE with at least two projects, so the thinnest books
contribute one project to each half. That range reflects split assignment, not a
confidence interval.

## Counterfactual accounting

Below-median-VA CDEs hold $6.43 billion,
or 49.3%, of observed non-metro QLICI. Moving
all of those dollars to above-median CDEs in proportion to the recipients' existing
non-metro books raises the dollar-weighted VA component by
+0.128 leverage points. Relative to the observed
project-weighted raw rural gap of -0.262, that is
48.9% of the gap; the normal-normal EB posterior
interval is [29.4%, 67.6%].

This is an accounting exercise, not a causal estimate. It assumes that CDE VA is
causal and portable to rural projects; year and QALICB composition stays fixed;
all below-median deployment can move; above-median CDEs can absorb it without
diminishing returns; the recipient mix follows existing above-median rural dollar
shares; reallocating intermediaries does not change project selection, prices,
entry, or equilibrium; and a leverage-point VA change can be compared with the
project-weighted -0.262 raw gap even though the reallocation itself is dollar
weighted. The interval propagates EB estimation uncertainty conditional on these
assumptions and the estimated signal variance. It does not cover model uncertainty
or causal uncertainty. The reported interval holds the plug-in donor and recipient
sets fixed, as an implementable ranking would. Re-ranking intermediaries inside each
posterior draw gives the separately recorded sensitivity interval
[63.7%,
109.6%], which is
optimistic because every draw selects on its own latent effects.

## What the numbers support

- They support persistent cross-CDE heterogeneity only to the extent that the EB
  signal variance is positive and split-half rankings are stable.
- They support portable intermediary performance only to the extent shown by the
  urban-rural correlation. The disattenuated coefficient can exceed one in finite
  samples; when it does, it signals an imprecise correction rather than a literal
  correlation above one.
- They do not establish that changing the intermediary changes leverage, that
  leverage is social value, or that redirecting allocations would reproduce the
  accounting gain.

## Design weaknesses a referee will attack

1. **Assignment is endogenous.** CDE effects combine intermediary practice with
   persistent borrower, sponsor, local-market, and project selection not absorbed
   by year and four QALICB categories. They are not random-assignment effects.
2. **The outcome is narrow.** `leverage_win` is a winsorized financing multiple on
   subsidized investment, not welfare, additionality, tax expenditure efficiency,
   project survival, or community benefit.
3. **Small and selected books.** The portability sample excludes one-sided and
   thin-book CDEs. Rural-book sampling error is substantial, and the three-deal
   threshold is inherited from the paper's switcher exhibit rather than identified
   by a power calculation.
4. **EB structure is strong.** The normal-normal calculation treats the pooled-OLS
   coefficient variance as known and uses a common signal variance. The pooling is
   what gives thin CDEs a meaningful variance instead of HC1's singleton
   degeneracy, but it imposes homoskedastic project noise. Heavy tails,
   heterogeneous signal variance, correlated coefficient error, and uncertainty in
   the estimated prior variance are only partly represented by the posterior draws.
5. **Portability is correlational.** A positive book correlation could come from
   common deal pipelines, national partners, or persistent sorting; a low one could
   reflect noisier rural books rather than geography-specific technology. The two
   book samples are disjoint, but their nuisance specification is common.
6. **Split-half risk adjustment is shared.** Holding full-sample year/type
   coefficients fixed prevents nuisance re-estimation from dominating the split,
   but their estimation error is shared across halves and can mildly raise the
   correlation. CDEs with only two projects contribute one observation per half,
   which makes the reported reliability deliberately demanding.
7. **The counterfactual has no capacity or equilibrium discipline.** It moves every
   below-median rural dollar, preserves the existing above-median recipient shares,
   and assumes constant VA at expanded scale. It also compares a dollar-weighted
   accounting change with a project-weighted raw gap.
8. **External validity is bounded by the release.** The estimates describe observed
   completed projects and named CDEs in this file, not applicants, rejected projects,
   the full certified-CDE population, or future allocation rounds.

---

## Independent verification and a ninth weakness (2026-08-14)

`scripts/verify_value_added.py` recomputes the load-bearing quantities from
the raw file without reading anything from `value_added.json` except for
comparison.

| quantity | this pass | independent recomputation |
|---|---:|---:|
| raw rural gap | −0.26226 | −0.26226 (exact) |
| CDE effect SD | 1.037 | 1.037 |
| EB signal SD | 0.265 | 0.272 |
| portability *r* | +0.348 on 104 CDEs | +0.363 on 104 CDEs |

The small differences in the last two rows come from the sampling-variance
convention and from residualizing before averaging books; neither changes a
conclusion. The 104 intermediaries in the portability sample are the same
104 the manuscript's switchboard exhibit uses, which is a useful cross-check
between two independently written scripts.

**The ninth weakness, not in the list above.** The counterfactual ranks
intermediaries by estimated value-added and then values the reallocation
using those same estimates. Ranking and evaluating on one draw of the same
noise is the classic way a value-added policy exercise flatters itself, and
it is why this literature uses leave-out estimates. Splitting each
intermediary's deals at random, ranking on one half and valuing the move on
the other, over 200 splits:

- in-sample gain: +0.290, which is 110% of the raw gap
- out-of-sample median: +0.163, which is 62% of the raw gap
- the in-sample figure overstates by about 44%

Two things follow. The reallocation result survives in direction and rough
magnitude, which is the important part. But any number quoted from this
exercise should be the out-of-sample one, and the in-sample version should
never appear in a paper without the split-sample figure beside it. Note
also that the in-sample gain exceeds the entire raw gap, which is a signal
in itself: an accounting exercise that closes more than 100% of the thing
it is decomposing is reporting fitted noise as if it were policy headroom.
