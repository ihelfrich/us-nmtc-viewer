# Working paper outline — Helfrich (2026)

**Working title:** *The Rural Mobilization Gap in U.S. Place-Based Tax Credit:
Intermediary Selection vs. Market Structure in the New Markets Tax Credit*

**Author:** Dr. Ian Helfrich (sole-authored)
**Status:** First-pass empirics complete · drafting toward SSRN preprint
**Target journals (in preference order):** AEJ:Applied · J. Public Economics · J. Urban Economics · Regional Science & Urban Economics

---

## Abstract draft (≈ 250 words)

The U.S. New Markets Tax Credit (NMTC), enacted in 2000, subsidizes private
investors with a 39% federal tax credit conditional on routing capital
through certified Community Development Entities (CDEs) into projects in
low-income census tracts. Over FY2001–FY2022 the program deployed
\$66.6 billion of public credit into 8,024 projects worth \$120.9 billion
in total project cost, implying an aggregate private-mobilization ratio of
\$0.82 per federal dollar. Non-metropolitan tracts received 19.6% of dollars
— effectively the 20% statutory minimum — but project-level leverage in
non-metro tracts is systematically lower (median 1.07× versus 1.19× metro).
This paper decomposes the rural mobilization penalty using project-level
fixed-effects regressions on the CDFI Fund's public release. The naive
estimate is a precise −0.26× rural penalty in mean leverage. Year, project-type,
and state fixed effects shrink it to −0.17×. **Adding CDE fixed effects
reduces the rural coefficient by approximately 80% to a statistically
insignificant −0.05×, with a quantile-regression analog at the median of
essentially zero.** The aggregate rural leverage gap is, therefore, almost
entirely explained by *which* intermediary CDEs deploy in rural tracts, not
by within-CDE heterogeneity in deployment. A cross-CDE bunching test on the
20% non-metropolitan statutory share finds no excess mass at the cumulative-
share level, consistent with the mandate binding at the allocation-award
level rather than the deployment level. The findings reframe the rural
mobilization debate: policy levers should target intermediary selection and
capacity, not market-structure interventions.

**JEL codes:** H25 (Business Taxes and Subsidies), H81 (Govt Lending),
R51 (Finance in Urban and Rural Economies), G28 (Govt Policy and Regulation)

**Keywords:** New Markets Tax Credit · place-based policy · blended finance ·
mobilization ratio · Community Development Entities · rural finance ·
fixed-effects decomposition

---

## 1 — Introduction (target: 4 pages)

### Motivation

The blended-finance literature has long debated which structures most
effectively mobilize private capital alongside public concessional finance
(Convergence 2024; Attridge & Engen 2019; Lankes 2021). A persistent
empirical limitation: the "mobilization ratio" — private dollars per public
dollar — is rarely directly observed at the project level. Most work
relies on either survey-reported figures or coarse program-level estimates.

The U.S. New Markets Tax Credit is a setting where this central blended-
finance quantity is *directly observed*: the CDFI Fund publishes, for every
project, the federal-credit-subsidized investment (the QLICI) and the total
project cost. Their ratio is exactly the leverage that the literature
otherwise infers indirectly. This makes NMTC an unusually clean within-
country laboratory for measurement-driven blended-finance research.

### Question

Does the NMTC mobilize private capital differently in rural vs. urban
markets — and if so, is the gap a *market-structure* phenomenon (rural
markets fundamentally less leverageable) or an *intermediary-selection*
phenomenon (the CDEs allocated to rural deals are systematically less
effective at mobilization)? The distinction has direct policy implications
for whether to redesign the program (market-structure story) or reallocate
intermediaries (selection story).

### Contribution (three sentences)

This paper makes three contributions to a literature that has examined
NMTC outcomes (Freedman 2012; Harger & Ross 2016; Theodos et al. 2022)
extensively but mobilization sparingly. **First**, it is — to our
knowledge — the first econometric paper to model project-level leverage
as the central NMTC outcome variable, importing the blended-finance
mobilization framework into a literature that has otherwise focused on
neighborhood employment, demographic change, and price effects. **Second**,
it implements a layered fixed-effects decomposition with CDE fixed effects,
isolating the within-CDE rural penalty from the between-CDE selection
component — a decomposition that descriptive work by Theodos et al. (2021)
has motivated but not estimated. **Third**, it applies a Chetty–Kleven-style
bunching diagnostic to the cross-CDE distribution of non-metro deployment
shares around the 20% statutory minimum — a test that, despite the
mandate's prominence in NMTC policy discussions, has not previously been
run.

### Headline result

Once CDE fixed effects are included, the rural leverage penalty is
statistically and economically zero. Approximately 80% of the raw rural
gap is between-CDE selection. **The rural mobilization debate is
mis-framed when posed in market-structure terms.**

---

## 2 — Institutional background (target: 2.5 pages)

### NMTC mechanics

- The 39% credit, claimed over 7 years
- Investor → CDE → QALICB cash flow
- The QEI / QLICI distinction
- The four QALICB types (RE, NRE, SPE, CDE)
- The 7-year compliance period

### Eligibility

- Low-income community (LIC) tract definition: poverty ≥ 20% **OR** MFI ≤ 80% area
- Targeted populations override
- The 20% non-metro statutory minimum (PL 106-554 §121)
- The CDE certification process

### CDE heterogeneity

- ~600 active CDEs over 2001–2022
- Top 20 do >50% of dollars
- Cross-CDE non-metro share variation: 0% to 80%+
- Bank subsidiaries vs. nonprofit CDFIs vs. for-profit specialized vs. government
  *(currently as-named in the data; institutional-form classification is a
  next-step extension)*

### Why this is the right testbed for the question

- Single instrument, single country, 22 years
- Direct observation of leverage
- Two embedded discontinuities: LIC eligibility cutoff + 20% mandate
- 8,000 projects → power to estimate CDE fixed effects with reasonable precision

---

## 3 — Data (target: 2 pages)

- CDFI Fund Public Data Release FY2003–FY2022 (released June 2024)
- 19,907 QLICI transactions across 8,024 projects, 2001–2022 origination years
- Two sheets: transactions (QLICI-level) and projects (deal-level)
- Cleaning steps in `scripts/describe_nmtc.py`; SHA-256 hashes in `PROVENANCE.md`
- Geocoding via U.S. Census 2020 tract gazetteer; 99.94% match rate
- Outcome variable: $\text{Leverage}_i = \text{ProjectCost}_i / \text{QLICI}_i$
  - Winsorized to [1, 20] (rationale in §3.3)
- Reproducibility: full pipeline + raw data published at the GitHub repo

### Tables / figures from data
- Table 1: descriptive statistics by metro/non-metro
- Table 2: by QALICB type × metro
- Figure 1: annual deployment time series (already produced)
- Figure 2: non-metro dollar share over time vs. 20% mandate (already produced)

---

## 4 — Empirical strategy (target: 3.5 pages)

### 4.1 — The mobilization framework

Define $\text{Leverage}_i$ and $\text{Mobilization}_i = \text{Leverage}_i - 1$.
Note that $\text{Leverage}_i \geq 1$ by construction; the mass at 1 has the
substantive interpretation of zero private mobilization.

### 4.2 — Layered fixed-effects decomposition

Sequentially estimate:

$$L_i = \alpha + \beta R_i + \delta_{t(i)} + \eta_{q(i)} + \mu_{s(i)} + \gamma_{c(i)} + \varepsilon_i$$

with each FE added in turn. The decomposition is informative about which
sources of variation account for the raw rural gap. The CDE FE step is
the workhorse: $\hat\beta$ post-CDE FE is the *within-CDE* rural penalty,
which is the "market structure" component; the shrinkage from M3 to M4
is the *between-CDE selection* component.

### 4.3 — Identification assumptions and limitations

- Selection on observables within CDE × year × type cells
- Within-CDE rural-vs-urban deal allocation is *not* random; we are not
  claiming a causal interpretation of $\hat\beta_{M4}$ in the LATE sense.
  The decomposition is descriptive but framed economically.
- Causal piece (LIC-eligibility RDD) deferred to §6.

### 4.4 — Quantile / median specification

Re-estimate at the median to address the long right tail of leverage and
to confirm the result is not driven by the mean.

### 4.5 — Heterogeneity by QALICB type

Interact rural with QALICB-type dummies. Hypothesis from Figure 5: the
within-CDE rural penalty is largest in real-estate deals (where private
debt-stacking is most natural) and smallest in CDE-to-CDE deals (where
leverage is mechanically pinned at 1).

### 4.6 — The 20% mandate as a Kleven-Waseem notch

For each CDE $j$, compute $s_j = n_{j,\text{non-metro}} / n_{j,\text{total}}$.
Apply Chetty (2011) / Kleven & Waseem (2013) excess-mass estimator to test
whether the cross-CDE distribution shows bunching at $s_j = 0.20$.

---

## 5 — Results (target: 4 pages)

### 5.1 — Headline FE decomposition

(Insert main_table.md from `data/processed/regressions/main_table.md`.)

Reading: M0 → M4 sees the rural coefficient shrink from −0.262*** to
−0.047 (insignificant). The decomposition: ~80% between-CDE selection,
~20% within-CDE within-type within-year residual. M4-Q at the median:
≈ 0. **The rural penalty is not a within-CDE phenomenon.**

### 5.2 — QALICB-type heterogeneity

(M5 results.) Brief discussion.

### 5.3 — Robustness

- 5.3.1 — Unwinsorized leverage
- 5.3.2 — Restricted to projects with leverage ≤ 5×
- 5.3.3 — RUCA-based continuous rurality (post-merge)
- 5.3.4 — Sub-period split (pre-2010 vs. post-2010)
- 5.3.5 — Restricted to top-50 CDEs (where FE is most precisely estimated)
- 5.3.6 — Two-way clustering (CDE × tract)

### 5.4 — Bunching at the 20% mandate

The cross-CDE distribution of cumulative non-metro shares does **not**
exhibit bunching at the 20% line. We discuss two interpretations:
(i) the mandate may bind at the allocation-award level rather than at the
realized-deployment level (CDFI does not disclose award-level commitments
in the public release); (ii) CDEs sort bimodally into rural-specialist and
urban-specialist groups, leaving the 20% point in a low-density valley
between modes.

### 5.5 — Where the within-CDE residual lives

Residual analysis: condition on M4, plot the residual rural penalty by
CDE size (top-20 vs. tail), by state, by year. Is there *any* sub-cell
where the within-CDE rural penalty is statistically distinguishable from zero?

---

## 6 — The causal extension: LIC-eligibility RDD (target: 2.5 pages, §6 or "future work")

If included as §6 (preferred), this requires the ACS tract-level merge
(poverty rate + MFI + AreaMFI) for the running variable.

- Fuzzy first stage: probability of NMTC investment as function of poverty
- Reduced form: tract-level mean leverage as function of poverty
- Wald estimator → LATE
- **Critical**: run separately for metro and non-metro samples
- The rural × treatment interaction is the new finding for the literature

If running this is out of scope for the V1 paper, frame it as the
follow-up paper and submit V1 to a more applied venue.

---

## 7 — Discussion / contribution (target: 1.5 pages)

### 7.1 — What this paper does and does not say

- **Does say:** the within-CDE rural penalty is approximately zero
- **Does say:** the aggregate rural penalty is real but is a between-CDE
  selection phenomenon
- **Does not say:** rural markets are not different (they may be — the
  question is whether the *NMTC* program detects that difference)
- **Does not say:** any individual CDE could not deploy more leverage in
  rural tracts. The result is an average across the CDE fixed-effects
  distribution.

### 7.2 — Policy implications

- The marginal rural deal is not constrained by market structure under
  the existing program design
- The aggregate rural penalty is amenable to *intermediary-allocation*
  policy levers
- Specifically: shifting allocation toward CDEs with demonstrated
  high-leverage capacity (regardless of their current rural orientation)
  could close the aggregate gap without redesigning the credit
- The 20% mandate, as currently enforced, may bind on the wrong margin
  (allocation share) relative to the policy goal (deployment leverage)

### 7.3 — Connection to the broader spatial public-finance research agenda

This paper is Phase 0 of a sequence: NMTC alone (this paper) → multi-
program U.S. comparison (NMTC + LIHTC + Opportunity Zones) → international
extension (MDB project finance + private capital response). See the
strategic memo (`briefs/spatial_finance_atlas_vision.md`).

---

## 8 — Conclusion (target: 0.5–1 page)

Brief restatement; flag the LIC RDD extension; situate in the larger
research program.

---

## References (organized; 25–35 cited)

### Primary NMTC empirical literature

- Abravanel, M.D., Pindus, N., Theodos, B., Bertumen, K., Brash, R., & McDade, Z.
  (2013). *NMTC Program Evaluation Final Report.* Urban Institute / CDFI Fund.
- Corinth, K., Coyne, D., Feldman, N., & Johnson, C.E. (2024/2025).
  *The Targeting of Place-Based Policies: NMTC vs. Opportunity Zones.* NBER
  chapter c15066 / SSRN 5122131.
- Freedman, M. (2012). Teaching new markets old tricks: Effects of
  subsidized investment on low-income neighborhoods. *J. Public Economics*
  96(11–12), 1000–1014.
- Freedman, M., & Kuhns, A. (2018). Supply-side subsidies to improve food
  access: Evidence from NMTC. *Urban Studies* 55(14), 3234–3252.
- Gurley-Calvez, T., Gilbert, T.J., Harper, K., Marples, D.J., & Daly, K.
  (2009). Do tax incentives affect investment? An analysis of the NMTC.
  *Public Finance Review* 37(4), 371–398.
- Harger, K., & Ross, A. (2016). Do capital tax incentives attract new
  businesses? Evidence across industries from the NMTC. *J. Regional
  Science* 56(5), 733–753.
- Theodos, B., Hariharan, A., González-Hermoso, J., & Edelman, S. (2020).
  *Where Do New Markets Tax Credit Projects Go?* Urban Institute.
- Theodos, B., Stacy, C.P., Teles, D., Davis, C., Rajasekaran, P., &
  Hariharan, A. (2021). *Which Community Development Entities Receive
  NMTC Funding?* Urban Institute.
- Theodos, B., Stacy, C., Teles, D., Davis, C., & Hariharan, A. (2022).
  Place-based investment and neighborhood change: NMTC impacts on jobs,
  poverty, and demographic composition. *J. Regional Science* 62(4),
  1092–1121.

### Place-based policy / public finance

- Diamond, R., & McQuade, T. (2019). Who wants affordable housing in their
  backyard? Equilibrium effects of LIHTC. *J. Political Economy* 127(3),
  1063–1117.
- Glaeser, E.L., & Gottlieb, J.D. (2008). The economics of place-making
  policies. *Brookings Papers on Economic Activity* 2008(1), 155–253.
- Kline, P., & Moretti, E. (2014). People, places, and public policy:
  Some simple welfare economics of local economic development.
  *Annual Review of Economics* 6, 629–662.
- Neumark, D., & Simpson, H. (2015). Place-based policies. In G. Duranton,
  J.V. Henderson, & W.C. Strange (Eds.), *Handbook of Regional and Urban
  Economics, Vol. 5B* (Ch. 18). Elsevier.

### Identification methodology

- Chetty, R., Friedman, J., Olsen, T., & Pistaferri, L. (2011). Adjustment
  costs, firm responses, and micro vs. macro labor supply elasticities:
  Evidence from Danish tax records. *QJE* 126(2), 749–804.
- Imbens, G., & Lemieux, T. (2008). Regression discontinuity designs: A
  guide to practice. *J. Econometrics* 142(2), 615–635.
- Kleven, H.J. (2016). Bunching. *Annual Review of Economics* 8, 435–464.
- Kleven, H.J., & Waseem, M. (2013). Using notches to uncover optimization
  frictions and structural elasticities: Theory and evidence from Pakistan.
  *QJE* 128(2), 669–723.

### Blended-finance literature (the framing this paper imports)

- Attridge, S., & Engen, L. (2019). *Blended Finance in the Poorest
  Countries.* ODI.
- Convergence Finance. (2024). *State of Blended Finance 2024.*
- Lankes, H.P. (2021). Blended Finance: When to Use Which Instrument?
  *Centre for Economic Policy Research.*

---

## Appendices

- A. Data construction details (extends `DATA_DICTIONARY.md` and `PROVENANCE.md`)
- B. Robustness tables
- C. Plots of CDE-level non-metro shares and leverage
- D. Reproducibility statement and code repository link

---

## Outstanding tasks before SSRN

| task | est. time | status |
|---|---|---|
| ACS tract-level merge | 2 days | not started |
| LIC-eligibility RDD (§6) | 3 days | needs ACS |
| Robustness tables (5.3) | 1 day | partial |
| Refine bunching test (5.4) | 1 day | first pass done |
| Write Sections 1–4, 7, 8 | 5 days | outline only |
| Internal review by Gonchar | 1 day | scheduled |
| SSRN preprint upload | 0.5 day | dependent on above |

**Realistic preprint date:** 4 weeks from now, sole-authored.
