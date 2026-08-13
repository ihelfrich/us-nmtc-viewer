# Decision log — NMTC working paper, referee-fix round (2026-08-13)

Standard for this document: every analytical choice made in this round is
recorded with its rationale; nothing in the manuscript asserts a quantity
that was not computed in this repository; validation checks that could be
automated are hard assertions inside the scripts and the run fails if they
fail. No observation in the data was added, dropped, or edited in this
round; every change below is a change of analysis or of claim, not of data.

## D1. Gelbach decomposition replaces the sequential story as primary

**Decision.** Report the Gelbach (2016) full-model-reference decomposition
of the raw rural gap alongside the layered table, and treat it as the
primary decomposition when attributing the gap to covariate blocks.

**Rationale.** Sequential FE addition is path-dependent: the "QALICB type
explains about a quarter" reading from M1 to M2 depends on the order the
blocks enter. The Gelbach decomposition is invariant to listing order.
Computed result: of the raw-to-full movement of -0.216, the CDE block
contributes -0.185 (85.6%), QALICB type -0.041 (19.2%), year +0.010
(-4.8%). The V1 text's "roughly a quarter from type" was an artifact of
sequencing and is corrected in the revision.

**Validation.** The identity (beta_M0 - beta_full = sum of block
contributions) is a hard assertion at 1e-8; observed residual 4.8e-15.
The hand-built design matrix reproduces the formula-API M4 coefficient to
1e-6 (asserted).

## D2. The headline ratio is demoted; the level component is promoted

**Decision.** Stop headlining "82.2% of the gap is selection" as a
precisely-known quantity. Report instead: the CDE component of the raw gap
is -0.185, CDE-cluster bootstrap 95% CI [-0.347, -0.023]; the selection
share point estimate is 82% with bootstrap CI [25%, 255%], reported with
that interval.

**Rationale.** The share is a ratio of two estimated coefficients whose
denominator resamples; its bootstrap distribution is wide and crosses 100%.
Honest inference lives at the level of the component (which excludes zero),
not the ratio. Claims sized to what the data can bear.

## D3. The mean null is reported as underpowered; the median carries the null

**Decision.** State explicitly that the mean specification's cluster-robust
CI is [-0.245, +0.151] and that a one-sided 5% test can only reject
within-CDE penalties larger than 0.213 - nearly the raw gap - so the mean
regression alone is weak evidence of a zero. The median regression
(beta = -0.001, SE 0.008, rejectable bound 0.013) carries the precision.

**Rationale.** "Statistically insignificant" was previously allowed to
imply "zero." Equivalence logic is the honest frame: report the smallest
penalty the design can reject, for both estimators.

**Caveat recorded.** The median SE is the quantreg asymptotic (kernel) SE,
not CDE-clustered; a clustered bootstrap of the median with ~600 fixed
effects was judged computationally disproportionate for V1 and is listed as
an outstanding item. The mean-vs-median SE gap (0.101 vs 0.008) also
reflects the outcome's long right tail, which inflates mean-regression
variance; this is stated in the text.

## D4. Extensive/intensive margins added

**Decision.** Add an LPM for P(leverage > floor) and an OLS on leverage
among mobilizing projects, both with the M4 fixed effects and CDE
clustering; floors 1.001 (the data's exact-floor mass) and 1.05
(sensitivity).

**Rationale.** 27.4% of projects sit at the leverage floor (zero private
mobilization); a mean effect could hide offsetting margins. Computed: both
margins are null within CDE (extensive -0.018, p=0.34; intensive -0.039,
p=0.77; stable at the 1.05 floor). The floor values are analysis choices,
not data edits; both are reported.

## D5. Switcher diagnostics reported

**Decision.** Report that 163 of 343 CDEs operate on both sides of the
rural line and hold 93.9% of rural projects.

**Rationale.** With CDE fixed effects, the rural coefficient is identified
only by such switchers; a referee should be shown that the identifying set
is broad, not a sliver. (The 343 differs from the bunching test's 310
because the bunching sample conditions on >= 5 transactions; both bases are
stated where used.)

## D6. Remaining robustness rows filled

**Decision.** Add the top-50-CDE subsample (beta -0.100, SE 0.148, n=4,229)
and two-way clustered SEs by CDE and tract via Cameron-Gelbach-Miller
inclusion-exclusion (SE 0.105 vs one-way 0.101).

**Rationale.** These were the two unrun rows from the paper outline's own
robustness plan (5.3.5, 5.3.6). CGM positivity is asserted in code; the
one-way CDE piece is asserted to reproduce the headline M4 fit exactly.

## D7. The interpretation caveat is moved into the paper's front matter

**Decision.** State in the empirical-strategy and discussion sections that
the between-CDE component is a composition fact, and that its "selection"
reading is an interpretation: rural market conditions could in principle
*cause* the specialization of low-leverage intermediaries into rural
deployment, in which case part of the between-CDE component is market
structure operating through intermediary business models. The within-CDE
null (precise at the median, both margins) is the paper's secure claim.

**Rationale.** This is the strongest referee objection to the paper's
framing and it is better raised by the paper than by a referee.

## D8. Sample notes

The analysis sample for the referee-fix round is the same 8,024 projects as
the main pipeline (requiring tract_fips removed zero rows). No winsorization
or trimming choices changed in this round. The bunching analysis is
unchanged. Bootstrap: 499 CDE-cluster resamples, seed 20260813, zero failed
replications; resampled duplicate CDEs are treated as distinct clusters
(standard cluster-bootstrap practice).
