# 1. FACT-CHECK

I checked every substantive number in `sections/*.tex`. Citation years, section and column numbers, figure widths, significance-key cutoffs, and script filenames are not empirical assertions. Apart from the items below and the explicitly unsupported items, all source-covered quantities agree with the designated files after ordinary rounding. This includes the sample totals, dollar totals, metro shares, main coefficients and standard errors, Gelbach terms, bootstrap intervals, power calculations, switcher statistics, margin estimates, robustness estimates, and bunching statistics.

## Mismatches

- `paper/sections/00-abstract.tex:14-15` | M4 is described as adding CDE fixed effects after the state-FE specification | `main_table.csv` has `fe_state=False, fe_cde=True` for M4; CDE effects replace state effects.
- `paper/sections/01-intro.tex:34-38` | M4 is described as the next layer after year, type, and state effects | `main_table.csv` has no state effects in M4.
- `paper/sections/04-strategy.tex:7-18` | the displayed workhorse model and prose include year, QALICB, state, and CDE effects together | `main_table.csv` has year, QALICB, and CDE effects in M4, with `fe_state=False`.
- `paper/sections/05-results.tex:16-17` | column 5 “adds” CDE effects to column 4 | M4 drops the state effects present in M3, so the M3-to-M4 change is not a nested addition.
- `paper/sections/00-abstract.tex:16` | CI upper endpoint `+0.151` | `referee_fixes.json:F3_power.mean_ci95[1] = 0.152`.
- `paper/sections/01-intro.tex:40` | CI upper endpoint `+0.151` | source value `+0.152`.
- `paper/sections/05-results.tex:19` | CI upper endpoint `+0.151` | source value `+0.152`.
- `paper/sections/05-results.tex:43` | column 6 clusters at the CDE level | `referee_fixes.json:F3_power.caveat` says its SE is the quantile-regression asymptotic kernel SE and is not CDE-clustered.
- `paper/sections/05-results.tex:96-98` | `27.4%` is said to sit “exactly” at leverage 1 | `referee_fixes.json:F4_floor_1p001.share_at_floor = 0.2738`; the supplied statistic uses the 1.001 threshold and does not establish exact equality.
- `paper/sections/05-results.tex:123` | unwinsorized M4 coefficient `-0.215` | `robustness.json:R1_raw_M4.beta = -0.2155`, which rounds to `-0.216` at three decimals.
- `paper/sections/05-results.tex:122-131` | robustness proceeds in “eight directions” | the designated files report nine concrete variants: unwinsorized, log, two caps, two eras, single-CDE projects, top-50 CDEs, and two-way clustering.
- `paper/sections/05-results.tex:17-18` | M4 is “an order of magnitude smaller” than M0 | `|-0.2623/-0.0467| = 5.6`, not approximately 10.
- `paper/sections/07-conclusion.tex:8` | the mean estimate is “an order of magnitude below” the raw gap | the source coefficients imply a 5.6-fold reduction.

## Numbers not verifiable from the designated ground truth

- `paper/sections/02-background.tex:5-7,30-37`: enactment details, seven-year schedule, eligibility thresholds, statutory citation, and mandate implementation.
- `paper/sections/02-background.tex:43-49`: 345 transaction-ledger CDEs, top-20 share of 23.9%, 39% never-rural share, and 6.5% heavily rural share. The sources support only 343 project-level CDEs and 310 active CDEs.
- `paper/sections/03-data.tex:4`: FY2003 award-year start and June 2024 release date. `headline.json` supports 2001 to 2022 project years, not award years or release date.
- `paper/sections/03-data.tex:20,26`: the baseline winsorization rule and group means 1.73 and 1.99. The supplied files support the group medians, but contain no fields for these means.
- `paper/sections/05-results.tex:42-44,53-54`: HC1 labeling for columns 1 to 4 and the `10^{-14}` identity check.
- `paper/sections/05-results.tex:71-72`: “roughly six hundred fixed effects.” The caveat repeats this number, but another source reports only 343 CDEs; adding the reported year and type categories does not reconcile the count.
- `paper/sections/05-results.tex:111-116`: the reported M5 main effect and SE match `main_table.csv`, but the files contain no type-specific interaction coefficients with which to verify the claim that none is distinguishable from zero.

## Institutional and bibliographic claims

- **High confidence:** `00-abstract.tex:6-8`, `01-intro.tex:13-16`, and `03-data.tex:13-19` misidentify QLICI principal as a federal or public dollar. The federal subsidy is the 39% tax credit on QEI basis; a QLICI is an investment made by a CDE and can embody private leverage before it reaches the project. `ProjectCost/QLICI` is a financing multiple, not an exact measure of private dollars mobilized per federal dollar.
- **High confidence:** `04-strategy.tex:45-52` defines the mandate variable using project counts, `n_nonmetro/n_total`, while `00-abstract.tex:8-9`, `02-background.tex:35-39`, and `03-data.tex:43-44` describe a dollar or investment-share requirement. The bunching estimand and the stated institutional threshold use different units.
- **High confidence:** `02-background.tex:35-37` appears to attribute the nonmetropolitan proportional-allocation rule to the original 2000 authorizing provision. That rule was added later to IRC section 45D, and the operational 20% requirement did not govern the full 2001 to 2022 period uniformly. The legal citation and effective period need primary-source support.
- **High confidence:** `04-strategy.tex:43` calls the mandate a “notch,” but the paper specifies no discontinuity in the CDE objective or budget set at 20%. The Chetty and Kleven citations support bunching methods generally; they do not by themselves make this institutional constraint a notch.
- **Medium confidence:** `00-abstract.tex:4-5` states that NMTC capital is conditional on projects being in low-income census tracts. Targeted-population rules permit qualifying activity outside that simple tract-location description, which the background later acknowledges only briefly.
- **High confidence that support is inadequate; low confidence that the claims are false:** `01-intro.tex:55-67` claims both the first econometric treatment of project leverage in NMTC and the first 20% bunching test. The bibliography lists titles and metadata but contains no literature search capable of establishing either negative claim. Qualify these claims unless a documented search covers NMTC evaluation, community-development finance, tax-credit syndication, and administrative bunching studies.

# 2. LATEX/PROJECT

- The labels and bibliography are internally clean: no undefined citations or references, no duplicate labels, and no unused bibliography entries. Every referenced table, figure, and TeX fragment exists.
- `sections/05-results.tex:43` is a substantive table-caption error: column 6 is labeled CDE-clustered even though the designated source explicitly says the median SE is an unclustered kernel SE.
- `sections/04-strategy.tex:7-18` does not describe the source specification. The equation includes state and CDE effects together, while M4 omits state effects. This is more than exposition because it changes the interpretation of the M3-to-M4 coefficient movement.
- `main.tex:8,11,27,40-51` assumes compilation from the `paper/` directory. A root-level invocation such as `pdflatex paper/main.tex` can fail to locate the style, sections, tables, and bibliography. Document the required working directory or make paths root-stable for the intended Overleaf layout.
- `helfrich-wp.sty:11-15` hard-wires `fontenc` and the Type 1 `newpxtext/newpxmath` stack. This is predictable under pdfLaTeX and Tectonic. XeLaTeX may use the legacy font path, but the project does not provide engine-guarded font parity. Either declare pdfLaTeX as required or branch with `iftex` and an explicit XeLaTeX font setup.
- `main.tex:48-51` places the bibliography before the appendix. This compiles, but it leaves substantive appendix material after the references and conflicts with many journal workflows. Place the appendix before the bibliography unless the target outlet requires the current order.
- `helfrich-wp.sty:69-92` loads `hyperref` before TikZ. This usually works, and natbib correctly precedes hyperref, but hyperref is safest near the end of the package stack. No current package conflict is evident from static inspection.

# 3. WRITING

1. `01-intro.tex:15-19`

   > Their ratio is exactly the leverage that the literature otherwise infers indirectly. The NMTC is therefore an unusually clean within-country laboratory for measurement-driven blended-finance research: a single instrument, a single country, twenty-two years of deployment, and roughly 8{,}000 projects.

   Rewrite: The CDFI Fund reports each project's QLICI and total cost, whose ratio directly measures the paper's project-level financing multiple. This single-instrument, single-country panel covers 22 years and roughly 8,000 projects, allowing unusually direct measurement of that outcome.

2. `01-intro.tex:31-32`

   > In this data the answer is composition, and the layers of the argument sit in plain view.

   Rewrite: Across the reported specifications, intermediary composition accounts for most of the rural leverage gap, and the coefficient changes most when the model introduces CDE effects.

3. `01-intro.tex:41-45`

   > The precision lives elsewhere, and the paper reports it where it lives: the median within-CDE penalty is $-0.001$ (SE $0.008$), rural deals within a CDE are no less likely to mobilize any private capital at all, and mobilize no less when they do. What differs across space is \emph{which} intermediaries show up.

   Rewrite: The median within-CDE estimate is $-0.001$ with an SE of $0.008$. The extensive- and intensive-margin estimates also show no detectable rural penalty within CDE, while the composition of active intermediaries differs across locations.

4. `02-background.tex:15-17`

   > Figure~\ref{fig:mechanics} draws the plumbing as it operates: capital walks left to right, the credit walks back along the top, and the CDE sits at the joint where every deployment decision is made.

   Rewrite: Figure~\ref{fig:mechanics} maps the transaction chain: investors supply QEI capital, CDEs deploy QLICIs to eligible projects, and tax credits accrue to investors. The diagram locates the CDE at the point where each deployment is structured.

5. `04-strategy.tex:33-41`

   > One further caution belongs here, because it constrains the language the paper is entitled to use. The between-CDE component is a composition fact; its ``selection'' reading is an interpretation. Rural market conditions could in principle cause low-leverage intermediaries to specialize in rural deployment, in which case part of the between-CDE component is market structure operating through intermediary business models. The paper's secure claim is the within-CDE null; the decomposition locates the gap, and the discussion section is explicit about which readings of its location the data can and cannot separate.

   Rewrite: The decomposition identifies a between-CDE composition component, while its interpretation as intermediary selection requires an additional assumption. Rural conditions may induce low-leverage CDEs to specialize in rural projects, allowing market structure to operate through CDE business models. The design locates the observed gap but cannot distinguish those mechanisms.

6. `05-results.tex:120-122`

   > Because a null this central should not depend on any single analytic choice, Table~\ref{tab:robust} probes the workhorse specification from eight directions.

   Rewrite: Table~\ref{tab:robust} evaluates the within-CDE estimate across alternative outcome transformations, caps, periods, samples, and clustering schemes.

7. `05-results.tex:74-82`

   > Figure~\ref{fig:switch} shows the identifying variation itself, and it is the paper's argument in a single drawing. Restricting to the 104 dual-market intermediaries with at least three projects on each side of the rural line, each vertical spine connects a CDE's urban-book mean leverage to its rural-book mean. The spines climb a staircase from 1.0$\times$ to 4.0$\times$ across intermediaries, while the within-spine gaps distribute tightly around zero (median $-0.12$, interquartile range $[-0.46, +0.36]$): the between-CDE range dwarfs the typical within-CDE gap by an order of magnitude.

   Rewrite: Figure~\ref{fig:switch} displays 104 CDEs with at least three urban and three rural projects. Each spine connects the CDE's two group means; pooled mean leverage ranges from 1.0 to 4.0, while the within-CDE gap has a median of $-0.12$ and an interquartile range of $[-0.46,+0.36]$. The figure therefore shows greater dispersion across CDE levels than within CDEs across metro status.

8. `05-results.tex:96-106`

   > The margins address a second way a mean could mislead: 27.4\% of projects sit exactly at the leverage floor of one, meaning zero private mobilization, so a within-CDE penalty could in principle hide in the probability of mobilizing at all. It does not. Within CDE, rural deals are $1.8$ percentage points less likely to clear the floor (SE $1.8$pp, $p = 0.34$), and among deals that mobilize, the rural coefficient is $-0.039$ ($p = 0.77$). Both margins are stable when the floor is moved to $1.05$. Identification for all within-CDE results comes from the 163 of 343 CDEs that deploy on both sides of the rural line; these switchers originate 94\% of all rural projects, so the comparison is broad, not a boutique subsample.

   Rewrite: Using the 1.001 threshold, 27.4% of projects have no measured mobilization. Within CDE, rural projects are 1.8 percentage points less likely to exceed that threshold (SE 1.8 points, $p=0.34$), and the intensive-margin coefficient is $-0.039$ ($p=0.77$). Results remain similar at 1.05. The within-CDE estimates draw identifying variation from 163 of 343 CDEs, which account for 94% of rural projects.

9. `06-discussion.tex:24-25`

   > Reading the evidence this way carries three implications, in ascending order of specificity.

   Rewrite: The estimates motivate three policy hypotheses concerning rural deal constraints, the allocation of credits across CDEs, and the margin on which the 20% requirement operates.

10. `06-discussion.tex:39-44`

    > This paper is the first phase of a sequence: the NMTC alone here; a multi-program U.S. comparison (NMTC, LIHTC, Opportunity Zones) next; and an international extension to development-bank project finance where the same mobilization framework applies. The LIC-eligibility regression discontinuity, which requires the ACS tract merge, is the immediate companion piece.

    Rewrite: This paper analyzes the NMTC. Planned extensions compare the NMTC with LIHTC and Opportunity Zones, apply the framework to development-bank projects, and estimate an LIC-eligibility regression discontinuity after merging tract-level ACS data.

# 4. REFEREE

## 1. The outcome does not identify private mobilization per public dollar

The paper treats a QLICI as public expenditure and interprets `ProjectCost/QLICI - 1` as private capital mobilized by one federal dollar. That accounting is invalid because the tax expenditure is 39% of QEI basis, QLICIs are CDE investments, and project cost can include financing whose incrementality is unknown. The paper can credibly study project-cost financing multiples, but the current blended-finance and policy interpretation requires a defensible subsidy denominator and an additionality argument.

## 2. The headline within-CDE conclusion outruns the specification and inference

M4 replaces state effects with CDE effects, so the M3-to-M4 movement cannot isolate the addition of CDE identity. The mean CI still admits a penalty near the raw estimate, while the “precise zero” rests on an unclustered quantile-regression SE despite CDE-level dependence. The paper needs a genuinely nested full model and cluster-valid inference for the median before it can make the headline claim.

## 3. The bunching test does not map to the mandate it interprets

The test uses project-count shares over 2001 to 2022, while the paper describes a dollar-based requirement that applies through allocation agreements and did not govern the entire period uniformly. Discrete count shares, a low-density bimodal distribution, and a polynomial counterfactual further weaken power near 20%. A null in this statistic cannot establish that the mandate fails to bind or targets the wrong policy margin.
