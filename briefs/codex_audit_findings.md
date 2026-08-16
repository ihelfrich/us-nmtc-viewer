# Adversarial audit findings: median inference and the quantile process

Audit snapshot: current working tree on `71f5527`, including user-owned commits
and a concurrent C6 prose/result update made while the audit was running. The
audit did not edit `paper/sections/*.tex` or `paper/DECISIONS.md` and created no
commit.

## Severity ranking

| Rank | Severity | Claim | Finding |
|---:|:--|:--|:--|
| 1 | **High** | C6 | The reported within-CDE randomization p-value is not design-valid without an unsupported within-CDE exchangeability assumption. Preserving year and project type changes the Monte Carlo p-value from 0.090 to 0.248. |
| 2 | **High** | C1 | Relabelled cluster pairs is defensible, but its stated rationale against pooled multiplicity weights is false. A cluster multiplier sensitivity gives SE 0.00755 rather than 0.00951, exposing genuine nonregularity/method sensitivity. |
| 3 | **Moderate–high** | C8 | Declining to use unconditioned T2/T3 as corroboration is correct, but one conditioned statistic is inconvenient: the additive-OLS-residualized median-gap randomization at τ=.90 is stable near p=.001–.002 under expanded draws. Other conditioned estimands and Wilcoxon/sign tests do not corroborate it. |
| 4 | **Moderate** | C4 | The practical nonregularity diagnosis survives, but the unconditional 26.9% atom alone is not proof. Conditional fitted-value, residual, cell, jitter, and continuous-null diagnostics are needed. |
| 5 | **Moderate** | C5 | The LP formulation and loss comparison are correct; calling the returned coefficient “exact” is not. HiGHS gives a tight floating-point numerical optimum, and QR optima can be nonunique. |
| 6 | **Moderate** | C9 | The numerical audit was materially incomplete: 124 load-bearing anchors were absent from the 66-claim manifest. Coverage is now 196/196, including six anchors for concurrent C6 prose added after the original inventory. This was a guard-coverage failure, not a detected wrong number. |
| 7 | **Low** | C7 | Withdrawal of the tested upper-tail results is warranted. Fresh SEs are 0.118 and 0.205, and all reported interval constructions include zero. |
| 8 | **Low** | C2 | The asserted median coefficient and approximate 0.0093 pairs-bootstrap SE are reproducible, with visible Monte Carlo sensitivity in the third decimal. |
| 9 | **Low** | C3 | The 0.213 calculation is correct for a one-sided noninferiority/penalty bound. “Equivalence” requires the usual two-sided qualification. |

## C1 — pairs cluster bootstrap implementation

**Verdict: REFUTED as stated.** Drawing 343 CDEs with replacement and assigning
separate fixed-effect labels to repeated draws is a valid literal pairs-cluster
bootstrap. It is not, however, required to avoid understating dependence.

If CDE `g` is drawn `m_g` times, profiling the copy-specific fixed effects in
the relabelled problem gives `m_g q_g(beta)`. Pooling the identical copies under
the original label and applying multiplicity weight `m_g` gives the same
profiled criterion and rural-coefficient argmin set. In this nonunique QR
problem the solver can select different members of that common set unless a
common tie rule is imposed, so coefficient-by-coefficient identity is not
guaranteed.

On 250 matched draws:

- relabelled pairs SE: **0.009505953**;
- pooled multiplicity-weight SE: **0.009476696**;
- difference: **−0.000029257 (−0.31%)**.

An exchangeably weighted `Exp(1)` cluster multiplier diagnostic gives SE
**0.007548368** (MC 95% interval **[0.006574, 0.008447]**), materially below the
pairs result and close to the asymptotic SE. An intentionally broken iid-row
bootstrap gives **0.005933149**. The pairs/multiplier disagreement is evidence
of mass-point/nonunique-objective sensitivity, not proof that the literal pairs
implementation is wrong. A proper wild-gradient QR bootstrap would require
the cluster-score construction and its regularity conditions; a residual
sign-flip is not a substitute.

Recommended prose: retain relabelling as the literal pairs representation, but
do not say pooling understates dependence. Describe pooled multiplicity weights
as criterion-equivalent, disclose the multiplier sensitivity, and avoid
presenting any one bootstrap as a smooth-asymptotic theorem in this mass-point
setting. The current user-owned manuscript snapshot already incorporates the
main correction.

Reproduction:

```sh
UV_CACHE_DIR=/private/tmp/us-nmtc-codex-audit-20260814-cache \
UV_OFFLINE=1 CODEX_AUDIT_WORKERS=4 timeout 900 \
uv run --no-project --with pandas --with numpy --with scipy \
  --with statsmodels --with matplotlib \
  python scripts/codex_check_bootstrap_equivalence.py
```

Machine-readable evidence:
`data/processed/regressions/codex_check_bootstrap_equivalence.json`.

## C2 — 0.0093 bootstrap SE versus 0.0076 asymptotic SE

**Verdict: CONFIRMED.** Independent reconstruction from the processed project
CSV gives:

- LP median coefficient: **−0.0006522815**;
- statsmodels IRLS coefficient: **−0.0006540860**;
- asymptotic SE: **0.0076277913**;
- 250-draw reference pairs SE: **0.009505953** (**1.246×** asymptotic);
- 550 draws pooled across four disjoint streams: **0.009229562** (**1.210×**).

The paper's rounded **0.0093** and **1.23×** are therefore reproduced. They
should be treated as approximate. Across separate 100-draw streams, SEs range
from **0.008590** to **0.009361**; the 550-draw nonparametric MCSE of the SE is
**0.000412**. Relabelling versus pooled multiplicity weights is immaterial for
the SE, but seed and replication count matter at the third decimal.

Recommended prose: “roughly 20–25% larger” is better supported than treating
1.23 as a stable exact ratio.

Reproduction: use the C1 command; the script prints both SEs, inflation ratios,
and seed/replication summaries, and stores every draw in the same JSON.

## C3 — the 0.213 penalty/equivalence bound

**Verdict: CONFIRMED with a terminology qualification.** For the one-sided
null `H0: beta <= -Delta`, rejection requires
`(beta_hat + Delta)/se > z_.95`, hence the boundary is

```text
Delta* = 1.645(0.1011) - (-0.0467) = 0.2130095.
```

This is the smallest penalty magnitude that can be ruled out at the one-sided
5% level, equivalently the upper one-sided 95% confidence bound on `-beta`.
Calling it the largest rejectable penalty reverses the monotonicity.

A symmetric TOST equivalence claim additionally requires rejecting
`beta >= Delta`. Here the two margin thresholds are 0.2130095 and 0.1196095;
the penalty side binds, so 0.2130095 is also the minimum symmetric equivalence
margin in this particular application. The one formula is not a general
two-sided equivalence test.

Reproduction:

```sh
UV_CACHE_DIR=/private/tmp/us-nmtc-codex-audit-20260814-cache UV_OFFLINE=1 \
uv run --no-project python - <<'PY'
b, se, z = -0.0467, 0.1011, 1.645
print(z * se - b)
print({d: (b + d) / se for d in (0.20, z * se - b, 0.22)})
PY
```

## C4 — mass point, sparsity SE, and coefficient pinning

**Verdict: CONFIRMED with a necessary qualification.** An unconditional atom
does not by itself falsify the conditional-density condition at the fitted
quantile. Here the direct conditional diagnostics do support practical
nonregularity:

- **2,156/8,024 = 26.87%** of outcomes equal 1.0;
- **526** fitted conditional medians equal 1.0 within `1e-7`;
- **788** residuals equal zero within `1e-7`, of which **471 (59.8%)** come
  from `Y=1`;
- among full `(CDE, year, type, rural)` cells with at least five observations,
  **85/284** have 1.0 in their empirical median set, covering **37.0%** of
  observations in eligible cells.

The proposed generic-LP-vertex explanation is falsified computationally. In
200 real-outcome within-CDE permutations, **90.0%** of rural coefficients are
within `1e-7` of zero. After continuously jittering all observed outcomes,
pinning falls to **0/64** at `1e-7` and **1/64** at `1e-6`. Under a continuous
FE-plus-noise null it is **0/64** at both thresholds, even though an ordinary
LP vertex still interpolates 368 residuals. Exact outcome ties/discreteness,
prominently the 1.0 atom, drive the observed coefficient pinning; generic
vertex geometry does not.

This is sample evidence, not proof of a population asymptotic law or selective
identification of the 1.0 atom alone. Recommended prose should make that
distinction and avoid saying the unconditional percentage alone invalidates
the SE.

Reproduction:

```sh
UV_CACHE_DIR=/private/tmp/us-nmtc-codex-audit-20260814-cache \
UV_OFFLINE=1 CODEX_AUDIT_WORKERS=4 timeout 900 \
uv run --no-project --with pandas --with numpy --with scipy \
  --with statsmodels --with matplotlib \
  python scripts/codex_check_lp_randomization.py
```

Machine-readable evidence:
`data/processed/regressions/codex_check_lp_randomization.json`.

## C5 — “the LP is exact and IRLS is not”

**Verdict: REFUTED as worded; numerical formulation confirmed.** All 368
regression coefficients are explicitly free; only the positive/negative
residual variables are nonnegative. HiGHS dual simplex and interior point with
crossover both report optimal status and agree on the rural coefficient and
check loss to displayed precision. Maximum equality residual is
`3.55e-15`; stationarity and complementarity diagnostics are similarly tight.

The LP check loss is **3300.422130053762** versus IRLS
**3300.422177269314**, an improvement of **4.7216e-05**. A known negative-line
case returns `[-3, -2]` with free coefficient bounds and zero loss; SciPy's
default nonnegative bounds incorrectly return `[0, 0]` with loss 8.5. A
two-observation median example has the full optimum set `[0, 2]`, while the
solver returns one endpoint. Thus the LP is an exact *representation* solved
to tight floating-point tolerances, not symbolic exact arithmetic and not a
unique coefficient certificate.

Recommended prose: “LP solution to the exact check-loss formulation” or
“numerically optimal LP solution,” with nonuniqueness acknowledged.

Reproduction: use the C4 command; C5 diagnostics and synthetic controls are
stored under `C5` in the same JSON.

## C6 — within-CDE randomization inference

**Verdict: REFUTED.** The production permutation keeps each CDE's rural count
fixed but does not preserve year or QALICB-type composition. The observed
rural associations with year, type, and their interaction lie beyond the
within-CDE permutation reference ranges. Adding year/type fixed effects to the
coefficient statistic does not make the raw labels exchangeable.

The inferential result is sensitive to the assignment restriction:

- within CDE: 17/200 extreme draws, plus-one Monte Carlo p
  **18/201 = 0.089552**;
- within exact `CDE × year × type`: 29/120 extreme draws, plus-one Monte Carlo
  p **30/121 = 0.247934**.

Only **460/3,255** exact strata are mixed, containing 2,688 observations, so
the conditioned exercise is also limited. Neither value is automatically a
design-based causal p-value in this observational setting. The first requires
exchangeability conditional only on CDE; the second requires exchangeability
inside the exact measured strata. Both additionally require the relevant
sharp-null/no-interference setup.

Recommended prose: do not call 0.09 design-valid without defending the
assignment mechanism. Present it, if retained, as a sensitivity result under
an explicit within-CDE exchangeability assumption and disclose the 0.248
year/type-conditioned result.

A concurrent, independently seeded 400-draw implementation now in the working
tree gives **0.0998** within CDE and **0.1696** within exact
`CDE × year × type` strata. Its larger grid is more precise than the bounded
120-draw audit comparison; both establish the same conclusion that conditioning
materially weakens the nominal evidence. The concurrent manuscript update now
states the exchangeability limitation and reports 0.170; that edit was not made
by this audit.

Reproduction: use the C4 command; both permutation grids and every coefficient
are stored under `C6` in the same JSON.

## C7 — withdrawal of the upper-tail result

**Verdict: CONFIRMED.** Four disjoint streams of 80 literal pairs-cluster
draws—320 per quantile, all successful—give:

| τ | β | bootstrap SE | MCSE(SE) | percentile 95% | basic 95% | normal 95% |
|---:|---:|---:|---:|:--:|:--:|:--:|
| .90 | −0.12867 | **0.11801** | 0.00467 | [−0.39125, 0.04536] | [−0.30270, 0.13391] | [−0.35998, 0.10264] |
| .95 | −0.19972 | **0.20452** | 0.00810 | [−0.63496, 0.12905] | [−0.52848, 0.23553] | [−0.60057, 0.20114] |

These independently reproduce the reported **0.125** and **0.215** within
roughly 1.5 MCSEs. Per-stream ranges are [0.11539, 0.12305] and
[0.19630, 0.21386]. At τ=.90 the pooled SE rises from 0.1035 at 80 draws to
0.1180 at 320; at τ=.95 it is stable around 0.205. No interval excludes zero.

A valid bootstrap-t interval was not fabricated because the LP estimator has
no replication-level analytic SE; it would require a nested cluster bootstrap.
The percentile, basic, and unstudentized normal intervals agree on the
decision. A deliberately shifted rural outcome moves each fitted coefficient
by exactly 0.50, showing that the audit could detect a contrary result.

Recommended prose: say the **tested τ=.90 and τ=.95 quantiles** are not
distinguishable from zero, not that no conceivable upper-tail quantile is.

Reproduction:

```sh
UV_CACHE_DIR=/private/tmp/us-nmtc-codex-audit-20260814-cache \
UV_OFFLINE=1 OMP_NUM_THREADS=1 CODEX_MAX_WORKERS=4 timeout 1200 \
uv run --no-project --with pandas --with numpy --with scipy \
  --with statsmodels --with matplotlib \
  python scripts/codex_check_tail_conditioning.py
```

Machine-readable evidence:
`data/processed/regressions/codex_check_tail_conditioning.json`.

## C8 — year/type-conditioned paired gaps

**Verdict: CONFIRMED, with a material test-sensitive finding.** The paper is
right not to treat unadjusted T2/T3 as corroboration. Conditioning makes the
answer depend strongly on the estimand and statistic.

For 69 paired CDEs, additive OLS year/type residualization gives:

| τ | median gap | Wilcoxon p | sign p | conditioned randomization p |
|---:|---:|---:|---:|---:|
| .50 | −0.04629 | .3467 | .2750 | .015 |
| .75 | −0.12521 | .0226 | .1480 | .030 |
| .90 | −0.39805 | .2400 | .1480 | **.005** |
| .95 | −0.54363 | .2192 | .1480 | .030 |

Across 12 conditioned method×quantile comparisons, Holm-adjusted OLS
randomization p-values are .165, .300, **.060**, and .300. Quantile-specific
residualization produces no Wilcoxon p below .073 and no sign p below .091.
Exact `CDE × year × type` gaps use only 41 cells across 19 CDEs; every
Wilcoxon p is at least .623 and every conditional randomization p is at least
.54.

The inconvenient exception is the additive-OLS median statistic at τ=.90.
Four explicitly post-hoc 499-draw streams yield extreme counts 0, 1, 0, 0.
Pooled only as a Monte Carlo precision check, that is 1/1,996 with plus-one
absolute-statistic p **0.0010**. It is therefore not a seed accident. It is
nevertheless not broad
corroboration: Wilcoxon/sign tests disagree, the quantile-specific and exact
cell estimands disagree, the expanded search is post hoc, and conditional
label exchangeability is not a known assignment mechanism.

The multiplicity conclusion depends on the defensible family definition. The
declared conservative family includes all 12 conditioned methods and quantiles
and gives .060 at τ=.90. Treating the requested OLS-residualized diagnostic as
the primary four-quantile family gives Holm p **.020**. That sensitivity is
another reason to report the result rather than reduce it to a binary claim.

The concrete improvement is implemented as deterministic production check
`T4_year_type_conditioned_paired` in `scripts/verify_quantile_tail.py`; the
full conditional randomization remains in the dedicated audit script. The
production executor is capped at four workers.

Recommended prose: retain the decision not to use T2/T3 as corroboration, but
disclose that one conditioned median-randomization statistic at τ=.90 remains
large and stable. Characterize it as estimand/test-sensitive observational
sensitivity evidence, not a causal randomization result.

Reproduction: use the C7 command. The production T4 can be regenerated with:

```sh
UV_CACHE_DIR=/private/tmp/us-nmtc-codex-audit-20260814-cache \
UV_OFFLINE=1 OMP_NUM_THREADS=1 MPLCONFIGDIR=/private/tmp/us-nmtc-mpl-cache \
timeout 1200 uv run --no-project --with pandas --with numpy --with scipy \
  --with statsmodels --with matplotlib python scripts/verify_quantile_tail.py
```

## C9 — manuscript-number audit coverage

**Verdict: CONFIRMED; fixed.** On the final current manuscript snapshot, the
pre-C9 manifest contained only **66** claims: 8 in the abstract, 57 in results,
1 in the conclusion, and none in the introduction, background, data, or
strategy sections. The audit could pass while many load-bearing numbers were
unguarded.

The audit added **124** anchors for claims already present, expanding the
manifest from 66 to **190**. A concurrent C6 implementation then added six new
manuscript claims and their source mappings, so the final current manifest has
**196** pipeline-tied claims. Coverage includes repeated headline results,
sample and CDE counts, aggregate dollars,
uncertainty bounds, identifying-sample and switcher diagnostics, robustness
and subgroup results, multiple-testing family counts written as number words,
bunching estimates, confidence intervals, and the 47% positive-bootstrap
share. The loader now supports existing processed CSV, top-level JSON, and
figure-sidecar sources; CDE concentration statistics are recomputed
deterministically from the transaction output.

This is a material audit-coverage correction, not evidence that a printed
number was wrong. The manifest remains human-curated and does not pretend that
a numeral regex can infer scientific importance.

Reproduction:

```sh
timeout 30 python3 scripts/audit_paper_numbers.py

UV_CACHE_DIR=/private/tmp/us-nmtc-codex-audit-20260814-cache \
UV_OFFLINE=1 timeout 30 uv run --no-project --with pytest \
  python -m pytest tests/test_audit_paper_numbers.py -q
```

Expected outputs: `196/196 claims tied to a pipeline output`, followed by
`every audited claim matches its source`, and `9 passed` for the focused test.

## Files produced or changed

- `scripts/codex_check_bootstrap_equivalence.py`
- `scripts/codex_check_lp_randomization.py`
- `scripts/codex_check_tail_conditioning.py`
- `scripts/verify_quantile_tail.py`
- `scripts/audit_paper_numbers.py`
- `tests/test_codex_check_lp_randomization.py`
- `tests/test_verify_quantile_tail.py`
- `tests/test_audit_paper_numbers.py`
- `data/processed/regressions/codex_check_bootstrap_equivalence.json`
- `data/processed/regressions/codex_check_lp_randomization.json`
- `data/processed/regressions/codex_check_tail_conditioning.json`
- regenerated `data/processed/regressions/quantile_tail_verification.json`
  and `.md`

No manuscript section or decisions-log edit was made by this audit.
