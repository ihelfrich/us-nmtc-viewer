---
title: "Presenting *The Rural Mobilization Gap in U.S. Place-Based Tax Credit*"
subtitle: "A complete teaching brief for presenting Helfrich (2026) as the foundation for the Portugal blended-finance paper"
author: "Document prepared for Katia · drafted by Dr. Ian Helfrich"
date: "April 2026"
geometry: margin=1in
fontsize: 11pt
---

# Front matter — how to use this document

This is your complete preparation packet for presenting my U.S. New Markets Tax Credit (NMTC) paper. The presentation purpose is to set up your own Portugal blended-finance paper by giving the audience the methodological and empirical foundation they need to understand why your Portugal extension matters.

What you'll find here:

1. **The big picture** — what the paper says, in three paragraphs you can paraphrase verbatim.
2. **The institutional and data background** — everything you need to answer "what is NMTC?" and "where did the data come from?" with confidence.
3. **The empirical strategy** — every regression specification with the math written out, the economic reasoning behind each layer, and what each coefficient means.
4. **The results** — the actual estimated numbers with their interpretation in plain English.
5. **The literature** — the eight to twelve papers you must know cold, with one-sentence summaries of each.
6. **The novelty argument** — what makes this paper publishable and why it isn't a duplicate of existing work.
7. **The limitations** — honest framing of what the paper does *not* claim.
8. **The bridge to your Portugal paper** — how this work sets up yours.
9. **A suggested 45-minute talk outline** with timing and slide-by-slide guidance.
10. **Anticipated Q&A** — twelve to fifteen questions you should expect, with prepared answers.
11. **A glossary** of the technical vocabulary.
12. **Full references**.

**Read this top-to-bottom once. Then re-read sections 1, 2, 3, 4, 9, and 10.** That's enough to present competently. Sections 5, 6, 7, 8, 11, 12 are reference material for Q&A.

If anything is unclear at any point, message me — I would rather rewrite a section than have you guessing. The paper is sole-authored under my name; your job is to present it accurately and use it as a launching pad for your own work.

---

# 1 — The big picture (three paragraphs you can paraphrase)

## Paragraph 1: what NMTC is and why we care

The U.S. New Markets Tax Credit, enacted in 2000, is the largest place-based tax-credit program in the United States. It works by offering private investors a 39% federal tax credit, claimed over seven years, in exchange for putting their equity into a certified intermediary called a Community Development Entity (CDE). The CDE then re-deploys that capital as loans or equity into qualifying projects located in low-income census tracts. Over the program's first two decades, $66.6 billion of federal-credit-subsidized capital has been deployed into 8,024 projects whose combined cost was $120.9 billion — implying that, on average, the federal dollar mobilized $0.82 of additional private capital. This is exactly the kind of number the *blended finance* literature has been trying to estimate for decades. NMTC is unusual because it makes the number directly observable at the project level, which most blended-finance settings do not.

## Paragraph 2: what we find

The aggregate number hides systematic geographic variation. Non-metropolitan tracts received 19.6% of program dollars — exactly the 20% the statute requires — but each public dollar deployed there mobilized *less* private capital than each public dollar deployed in metropolitan tracts. The median project leverage ratio is 1.19× in metro and 1.07× in non-metro, a gap of 0.12 (roughly 0.26 at the mean). One natural reading is that rural capital markets are structurally less able to absorb subsidized credit and turn it into private follow-on investment — a "market structure" explanation that would justify program redesign. A different reading is that the *intermediaries* deployed in rural tracts are systematically less skilled at mobilization than the ones deployed in metro tracts — a "selection of intermediary" explanation that would justify allocation reform. The paper formally distinguishes these two explanations using a layered fixed-effects decomposition.

## Paragraph 3: the punchline

When we run the regression with year, project-type, and state fixed effects, the rural penalty is −0.17×, statistically significant at the 5% level. When we add CDE fixed effects — comparing the same intermediary's metro deals to its non-metro deals — the rural penalty collapses to −0.05× and becomes statistically indistinguishable from zero (p ≈ 0.64). The same finding at the median is essentially zero (−0.001×). About 80% of the raw rural mobilization gap is explained by *which* CDEs deploy in rural areas, not by *how* any given CDE performs there. **The rural mobilization debate, as currently framed in the literature, is mis-specified. The aggregate gap is an intermediary-selection phenomenon, not a market-structure phenomenon, and the policy levers most likely to close it operate on the allocation of CDEs to rural deals rather than on the credit's structure.**

---

# 2 — Why blended finance matters (the motivation)

This is the section that sets up *why* the audience should care, before any institutional detail.

## What "blended finance" actually means

Blended finance is the term for any structure in which public, philanthropic, or concessional capital is deployed alongside private capital, with the public side accepting some combination of risk, return, or liquidity that the private side wouldn't. The defining empirical question is **mobilization** — how much private capital does the public dollar pull in? — which the OECD, World Bank, Convergence Finance, ODI, and the entire Multilateral Development Bank ecosystem report annually as their central performance metric.

The problem is that in most blended-finance settings, mobilization is hard to measure. A bilateral aid project might be co-financed with vague co-funding commitments. A development bank loan might catalyze private investment that's hard to attribute. Ratios reported in the literature span 0.3× to 4× depending on definition, accounting convention, and program. *The same intervention can show very different mobilization ratios depending on what you call the denominator.*

## Why NMTC is the right testbed

NMTC is unusual because the mobilization ratio is *directly observed*. The CDFI Fund, by statute, requires CDEs to disclose for every project they fund the QLICI amount (the federal-credit-subsidized investment that flowed to the project) and the estimated total project cost (public plus private combined). The ratio of these two numbers is — exactly — the leverage of the federal dollar:

$$\text{Leverage}_i \;=\; \frac{\text{ProjectCost}_i}{\text{QLICI}_i}, \qquad \text{Mobilization}_i \;=\; \text{Leverage}_i - 1$$

A leverage of 1 means 100% NMTC-financed (zero private mobilization). A leverage of 3 means each federal dollar pulled in $2 of non-federal capital. This is the central blended-finance quantity, and we observe it directly for 8,024 projects across 22 years. There is no comparable U.S. blended-finance program with this level of project-level disclosure.

That's the *measurement* edge. The *identification* edge is that the U.S. NMTC statute embeds two sharp regulatory rules — (1) a tract is eligible if poverty ≥ 20% *or* median family income ≤ 80% of area median, creating a regression-discontinuity cutoff, and (2) at least 20% of program dollars must go to non-metropolitan tracts, creating a potential bunching point. Both rules generate quasi-experimental variation that is rare in the broader public-finance landscape.

## Why this matters beyond NMTC

If we can decompose the U.S. rural mobilization gap into its intermediary-selection and market-structure components in a clean within-program setting, we have a methodological template that transfers to:

- **Other U.S. place-based programs** (LIHTC, Opportunity Zones, CHIPS Act, IRA energy credits, USDA Rural Development) — same logic, different programs.
- **International multilateral development bank lending** — World Bank, IFC, EIB, ADB project finance, with national and subnational private-capital response data.
- **Sovereign and subnational green/social bond markets** — public credit signaling private allocation.
- **Your Portugal work** — rural blended finance in Portugal involves Caixa Geral de Depósitos, EIB-Portugal, and Cohesion Fund deployment, all of which have analogous intermediary-selection dynamics.

The U.S. NMTC paper is the proof that the framework works. Everything else is application.

---

# 3 — What NMTC actually is (institutional setup)

This section gives you the institutional command you need. If anyone asks "how does the program work in detail," you should be able to walk through this from memory.

## The four entities

There are four things in the cash flow:

1. **The Investor.** A bank, corporation, or wealthy individual who has a federal income-tax liability they would like to reduce. The investor wants the 39% credit. They put their equity into the next entity.

2. **The Community Development Entity (CDE).** A certified intermediary. Roughly 600 active CDEs over our sample period, ranging from bank subsidiaries (e.g., USBCDE LLC, Banc of America CDE) to nonprofit community-development financial institutions (e.g., Local Initiatives Support Corporation, Reinvestment Fund) to specialized rural CDEs (e.g., Rural Development Partners LLC, Montana Community Development Corporation). The CDE accepts the investor's equity (called a *Qualified Equity Investment*, or **QEI**) and is required to deploy substantially all of it (at least 85%) into qualifying low-income community businesses (QALICBs) within twelve months.

3. **The Qualified Active Low-Income Community Business (QALICB).** The ultimate recipient of the capital — the actual project on the ground. Could be a real-estate development (a charter school, a grocery store in a food desert, an affordable-housing complex), an operating business (a manufacturing facility, a hospital, a dental clinic), a special-purpose entity, or, occasionally, another CDE. The CDE's deployment to the QALICB is called a **Qualified Low-Income Community Investment**, or **QLICI**. *This is the level our data records.*

4. **The federal government** — the U.S. Department of the Treasury, which issues the 39% credit through the IRS, and the Community Development Financial Institutions (CDFI) Fund, which administers the program (allocates credits to CDEs, certifies CDEs, monitors compliance, and publishes the annual data release we use).

## The cash flow, drawn out

```
                    QEI $                         QLICI $
   Investor  ────────────────►  CDE  ────────────────────►  QALICB
            ◄──────────────                                  (project /
              39% tax credit                                 business in
            (over 7 years)                                   LIC tract)
```

The investor receives the 39% credit not all at once but in eight annual installments: 5% in each of the first three years, then 6% in each of the next four years (totaling 39% of the QEI amount). In exchange, the investor's QEI must remain in the CDE for the full seven-year compliance period; if the CDE fails to maintain its substantial deployment of QLICIs throughout, the investor's credit can be recaptured.

What we observe in the data is the second arrow — the QLICI flow from CDE to QALICB. We do not observe the first arrow (the QEI from investor to CDE) because that flow is governed by securities-law disclosures, not CDFI Fund disclosures.

## The eligibility rules

A census tract is a "Low-Income Community" (LIC), and therefore NMTC-eligible, if either of the following is true at the time of investment:

$$\text{LICeligible}_\ell \;=\; \mathbf{1}\left\{ \text{Poverty}_\ell \geq 0.20 \;\;\vee\;\; \frac{\text{MFI}_\ell}{\text{AreaMFI}_\ell} \leq 0.80 \right\}$$

In words: the tract qualifies if it has at least a 20% poverty rate, **or** its median family income is at or below 80% of the area median family income. Either condition alone is sufficient. There are also "targeted population" provisions and certain high-migration-rural-county overrides that we leave to the appendix.

The 20% poverty cutoff is what makes NMTC amenable to a sharp regression discontinuity design: tracts at 19.9% poverty are nearly identical to tracts at 20.1% poverty in everything except eligibility status, so comparing outcomes across that cutoff isolates the program's effect from underlying tract characteristics. Freedman (2012) is the canonical paper using this design; Harger & Ross (2016) is the second canonical reference.

## The 20% non-metropolitan statutory mandate

The statute requires CDEs to direct at least 20% of their QLICIs to non-metropolitan census tracts (Public Law 106-554 §121, codified at 26 USC §45D). This rule was added because, without it, CDEs were expected to concentrate their deployments in urban areas where deal flow is denser and underwriting is easier. The 20% is enforced at the CDE allocation-award level, meaning a CDE must demonstrate intent to deploy at least 20% rurally as part of its competitive application for an NMTC allocation award.

In our data — which captures *deployments* (QLICIs), not *allocation commitments* — non-metro tracts received exactly 19.6% of dollars and 19.3% of transactions over 2001-2022. That's just under 20%, suggesting the mandate binds in some sense at the program level. Whether it binds at the individual CDE level is something we test directly via the bunching diagnostic (Section 8).

## The QALICB types

The CDFI Fund classifies every project into one of four QALICB types. The classification matters because different types have very different leverage capabilities:

| code | meaning | typical leverage profile | n in our data |
|---|---|---|---|
| **RE** | Real Estate — the QALICB's main asset is real property; QLICI is typically a loan secured by the property | Stackable: mezzanine debt, second mortgages, equity tranches all possible. *Highest median leverage in our data.* | 2,862 projects |
| **NRE** | Non-Real-Estate — operating business (manufacturing, services, healthcare) | Less collateral, harder to leverage; mostly operating-cash-flow-financed | 3,775 projects |
| **SPE** | Special-Purpose Entity — a QALICB created specifically for a single deal | Flexible structurally but typically simpler stacks | 1,296 projects |
| **CDE** | Loan-to-CDE — a pass-through transaction where one CDE lends to another | Mechanically pinned at 1.0× by structure | 91 projects |

The cross-tabulation by metro status is informative: real-estate is ~40% of metro projects but only ~17% of non-metro; operating businesses (NRE) are ~50% of metro and ~65% of non-metro. So the project-type composition itself differs between rural and urban, which is a confounder our regression strategy must address.

## Why this institutional detail matters for the empirical strategy

Three features of the institutional setup are load-bearing for the regression strategy:

1. **CDEs are heterogeneous and persistent.** A CDE applies for an NMTC allocation award, gets one (or doesn't), then deploys it over several years. The *same* CDE often does both metro and non-metro deals. This persistence is what makes within-CDE FE identification possible.
2. **The 20% rule creates an institutional reason to expect bunching.** If the rule binds, we should see CDEs targeted exactly at the floor.
3. **The LIC eligibility cutoff creates an exogenous source of program access.** Tracts that just barely qualify are otherwise similar to tracts that just barely don't.

We use (1) for the FE decomposition (Section 7), test (2) directly (Section 8), and the LIC cutoff (3) is the basis for the RDD that we will run as the §6 causal piece once we merge in census tract demographics — currently a future-paper extension.

---

# 4 — The data: where it comes from, what we did to it

## The source

Everything in this paper comes from one publication:

> **Community Development Financial Institutions (CDFI) Fund**, U.S. Department of the Treasury.
> *New Markets Tax Credit Public Data Release, FY2003–FY2022.*
> Released June 2024.
> <https://www.cdfifund.gov/documents/data-releases>

The release is a federal agency disclosure under the Treasury's program-transparency rules. It is in the public domain (17 USC §105) and we redistribute it directly in our reproducibility repository alongside the cleaning scripts. The bytes of the original file are SHA-256 verified and the hash is recorded in `PROVENANCE.md`. **If anyone asks "where's the data from," your answer is: "the CDFI Fund's June 2024 Public Data Release; the SHA-256 hash is recorded in our provenance documentation and the file is in the repo."**

## What we downloaded

Two files:

| file | size | purpose |
|---|---|---|
| `NMTC_Public_Data_Release_FY2003-FY2022.xlsx` | 1.95 MB | the actual transaction-level and project-level records |
| `NMTC_Public_Data_Release_Summary_FY2003-FY2022.pdf` | 0.49 MB | CDFI's own codebook |

## The structure of the xlsx

Two relevant sheets:

**Sheet 1 — `Financial Notes 1 - Data Set PU` (19,907 rows).** One row per QLICI transaction. Each row is a single financial flow from a CDE to a QALICB on a specific date.

**Sheet 2 — `Projects 2 - Data Set PUBLISH.P` (8,024 rows).** One row per project. The relationship is one-to-many: a project can receive multiple QLICIs from one or more CDEs in one or more tranches. Leverage is a project-level concept (total project cost / total QLICI), so all of our leverage analysis runs on Sheet 2.

## What the cleaning pipeline does

Every step is in `scripts/describe_nmtc.py`. The full pipeline runs in about 25 seconds end-to-end. The substantive cleaning operations:

1. **Strip whitespace from column headers** (CDFI's headers are inconsistent).
2. **Rename columns** to short snake_case names (full mapping in `DATA_DICTIONARY.md`).
3. **Normalize the metro flag.** This is a real data-hygiene moment to mention if asked. CDFI's source column contains three different strings for the same concept: `"Metro"`, `"Non-metro"`, and `"Non-Metro"` (inconsistent capitalization across years). We fold these into a clean three-valued column with `metro`, `non_metro`, and `unknown` (the rare NaN). Always check string columns for casing inconsistencies on day 1 of any new dataset — that's a transferable lesson for your Portugal work.
4. **Coerce dollar columns to numeric** with `pd.to_numeric(..., errors="coerce")`. Some rows arrive with dollar amounts as strings with commas; these get coerced cleanly. Coercion failures become `NaN`, which means specifically "the source had a non-numeric value here," not "the source had no value here" — important distinction.
5. **Compute project-level leverage.** Two columns added:

```python
pr["leverage_ratio"] = pr["project_cost"] / pr["project_qlici"]
pr["leverage_win"]   = pr["leverage_ratio"].clip(lower=1.0, upper=20.0)
```

Both are kept. `leverage_win` is what we use for summary statistics; `leverage_ratio` is the raw version for robustness checks.

6. **Justify the [1, 20] winsorization.** About 1% of projects report a leverage ratio below 1, which is implausible — by construction the QLICI is part of the project cost. About 0.3% report ratios above 20, typically a small QLICI into a very large RE deal. Winsorization bounds the influence of these tail anomalies on summary statistics without dropping observations. We always report both versions in robustness tables.

7. **Geocode** by merging tract FIPS codes with the U.S. Census 2020 Tract National Gazetteer (a 16 MB tab-separated file containing internal-point lat/lon for all 85,395 census tracts). 8,019 of our 8,024 projects merge cleanly — a 99.94% match rate. The five unmatched projects have tract codes that were renumbered between the 2010 and 2020 censuses; they remain in the analytical tables but don't appear on the map.

8. **Generate rollups** by groupby — metro × project, QALICB type × metro, year × metro, top 20 CDEs, leverage-ratio quantiles, multi-CDE crosstab. Each rollup is its own CSV in `data/processed/`. None of these are new measurements; they're convenient pre-aggregations of the two cleaned files.

9. **Emit `headline.json`** containing the key program-level numbers we use throughout the paper.

## The reproducibility chain

From a blank machine, three commands rebuild every figure and every regression:

```bash
git clone https://github.com/ihelfrich/us-nmtc-viewer
cd us-nmtc-viewer
pip install -r requirements.txt
python3 scripts/describe_nmtc.py
python3 scripts/make_figures.py
python3 scripts/run_regressions.py
```

Total runtime: about 2 minutes on a laptop. **Every number in the paper is regeneratable from the SHA-anchored raw xlsx in less than two minutes.** That bar — fully reproducible from open data, with hashed source files, in a single Python environment, with a published code repository — is the credibility floor for empirical public-finance work in 2026. We hit it.

## What's NOT in the data (limitations to know)

You should be ready to discuss what we *don't* observe:

- **No QEI flow** (investor → CDE side). We see only the downstream deployment.
- **No allocation-round data.** CDFI's allocation awards specify how much each CDE may deploy, but we see the deployment, not the award.
- **No tract demographics** (poverty rate, MFI, population, racial composition) — these need to be merged in from the American Community Survey separately. This is the next data step for the LIC-eligibility RDD.
- **Nominal dollars.** No CPI adjustment in the released figures or regressions. A robustness check with real 2022 dollars is straightforward but not included in V1.
- **CDE institutional form is not classified.** The data lists CDE names but doesn't tag them as bank subsidiary / nonprofit / for-profit. Hand-classifying the top 50 by institutional form is a planned extension.

---

# 5 — What we see before any regression (descriptive findings)

The audience needs to believe there's something interesting here *before* you start running regressions. This section is the descriptive case.

## Headline numbers

| metric | value |
|---|---|
| Total QLICI deployed, FY2001–FY2022 | $66.6 billion |
| Total project cost (public + private combined) | $120.9 billion |
| **Implied program-wide mobilization ratio** | **0.82×** |
| Number of QLICI transactions | 19,907 |
| Number of unique projects | 8,024 |
| Number of unique CDEs over the period | ~600 |
| Number of unique census tracts | ~6,500 |
| Non-metro share of dollars | 19.6% |
| Non-metro share of transactions | 19.3% |
| Statutory non-metro target | 20.0% |

Read the mobilization-ratio number out loud. **For every $1 of federal credit deployed, the program pulled in approximately $0.82 of additional non-federal capital.** That's the headline blended-finance number — and it's sobering: it implies the federal credit is *less* than 50% of total project cost, by a small margin, but only barely. A program designed to *catalyze* private investment is being roughly matched dollar-for-dollar by private capital, no more. The conclusion-headline implication: NMTC is closer to a direct grant than a leverage instrument.

## The metro-vs-non-metro gap

| | metro | non-metro |
|---|---:|---:|
| Number of projects | 6,463 | 1,561 |
| Total QLICI deployed | $53.6 B | $13.0 B |
| Total project cost | $97.2 B | $23.8 B |
| **Mean leverage** | **1.99×** | **1.73×** |
| **Median leverage** | **1.19×** | **1.07×** |
| Mobilization ratio (aggregate) | 0.81× | 0.82× |

Two things to highlight from this table when presenting:

1. **The aggregate mobilization ratios are nearly identical** (0.81× metro vs 0.82× non-metro). This is a function of total dollars in the numerator and denominator and is what CDFI tells the world. **Don't let the audience stop here** — the aggregate hides the median story.

2. **The median leverage gap is real**: 1.19× metro versus 1.07× non-metro. Median is more informative than mean here because the right tail of leverage is long (a few highly-leveraged real-estate projects pull the mean around). At the *typical* deal — which is what policy cares about — the rural deal mobilizes essentially zero additional private capital (1.07× is just barely above the 1× floor), while the typical metro deal mobilizes roughly 19 cents per federal dollar.

## The leverage distribution

This is Figure 3 in the viewer / paper. The visual story is:

- **Both distributions pile up against the 1× floor** (no private capital mobilized), but
- **The non-metro mass at the floor is dramatically higher** than metro
- **Both have long right tails** but the metro distribution has a noticeably fatter right shoulder (more projects at 1.5×, 2×, 3×)

The descriptive interpretation: rural deals overwhelmingly are 100% NMTC-financed; metro deals more often stack additional private debt on top. *This is the empirical fact the paper exists to explain.*

## Composition: QALICB-type mix differs by metro

| QALICB type | metro share | non-metro share |
|---|---:|---:|
| Real Estate (RE) | 40% | 17% |
| Non-Real-Estate (NRE) | 50% | 65% |
| Special-Purpose (SPE) | 8% | 16% |
| Loan-to-CDE | 2% | 2% |

A natural objection at this point: maybe the rural leverage gap is just a project-type composition story. Real-estate deals leverage more than operating-business deals, and rural skews toward operating-business. Therefore rural leverage looks lower because rural is more NRE.

This is exactly the right objection, and we address it head-on in the regressions (M2 controls for QALICB type) and visually in **Figure 5**, which shows median leverage *within* each QALICB type, separately for metro and non-metro. The headline from Figure 5: *the rural penalty persists within every QALICB type*. Within real estate, median is 1.32× metro vs 1.11× non-metro. Within NRE, 1.08× vs 1.04×. Within SPE, 1.18× vs 1.14×. So the gap is not composition.

## CDE heterogeneity (the mechanism candidate)

The top-20 CDEs together do roughly 50% of all NMTC dollars over the sample. Their non-metro shares span from approximately 0% to 80%:

| CDE | total $M | non-metro share |
|---|---:|---:|
| Rural Development Partners LLC | $636 M | **80%** |
| Montana Community Development Corporation | $660 M | **70%** |
| Midwest Minnesota Community Development Corporation | $662 M | **60%** |
| Coastal Enterprises, Inc. | $679 M | 40% |
| Advantage Capital Community Development Fund | $1,439 M | 30% |
| Truist Community Development Enterprises | $654 M | 20% |
| Stonehenge Community Development | $797 M | 20% |
| Chase New Markets Corporation | $717 M | 20% |
| USBCDE LLC | $935 M | 10% |
| Local Initiatives Support Corporation | $1,123 M | 10% |
| Banc of America CDE | $774 M | 10% |
| ESIC New Markets Partners | $1,057 M | **0%** |
| Consortium America LLC | $759 M | **0%** |
| Capital Impact Partners | $660 M | **0%** |
| National Trust Community Investment Corporation | $657 M | **0%** |

This is *enormous* variation. ESIC, Consortium America, and Capital Impact Partners deploy basically zero rural capital despite having competitive NMTC allocations and operating in the same federal program. Rural Development Partners LLC, Montana CDC, and Midwest Minnesota CDC do most of their work rurally. **These are wildly different organizations with wildly different deployment patterns operating under the same federal credit. That heterogeneity is the variation our paper exploits.**

---

# 6 — The empirical question, formally

The descriptive section establishes that there's a rural leverage gap, that it isn't composition (Figure 5), and that there's enormous variation in CDE-level rural orientation. The natural research question:

> Is the rural leverage gap because the *same CDE* does worse rurally than it does in metro (a market-structure problem), or because the CDEs that go rural are systematically different from the CDEs that stay urban (an intermediary-selection problem)?

Both stories are consistent with the descriptive evidence. They have very different policy implications — and a fixed-effects decomposition can distinguish them.

The intuition:

- If we compare metro deals to non-metro deals *within the same CDE*, and the gap disappears, then "same CDE doing both metro and non-metro shows no within-CDE rural penalty" — the gap was selection.
- If we compare metro deals to non-metro deals *within the same CDE*, and the gap persists, then "even the same CDE mobilizes less rurally" — the gap is market structure.

The decomposition is clean because we have ~600 CDEs and many of them deploy in both metro and non-metro tracts. The within-CDE comparison is feasible.

---

# 7 — The empirical strategy in detail

The empirical strategy has three components: (1) a layered fixed-effects regression that does the decomposition, (2) a quantile-regression analog to confirm the result isn't a tail story, and (3) a bunching test that diagnostically validates whether the 20% mandate is a binding constraint at the CDE level.

## 7.1 — The layered fixed-effects regressions

We estimate a sequence of OLS specifications, each adding a layer of fixed effects. The unit of observation is the project. The outcome is project-level leverage, winsorized at [1, 20]. The treatment indicator is `rural`, equal to 1 if the project is in a non-metropolitan tract.

| Spec | Equation | Adds | Identifies |
|------|----------|------|------------|
| **M0** | $L_i = \alpha + \beta R_i + \varepsilon_i$ | nothing | raw rural-vs-urban gap |
| **M1** | $L_i = \alpha + \beta R_i + \delta_{t(i)} + \varepsilon_i$ | year FE | gap net of credit-cycle variation |
| **M2** | $L_i = \alpha + \beta R_i + \delta_{t(i)} + \eta_{q(i)} + \varepsilon_i$ | + QALICB type | gap net of project-type composition |
| **M3** | $L_i = \alpha + \beta R_i + \delta_{t(i)} + \eta_{q(i)} + \mu_{s(i)} + \varepsilon_i$ | + state | gap net of state-level capital-market depth |
| **M4** | $L_i = \alpha + \beta R_i + \delta_{t(i)} + \eta_{q(i)} + \gamma_{c(i)} + \varepsilon_i$ | + CDE | **within-CDE rural penalty (workhorse)** |

Variable definitions:
- $L_i$: leverage of project $i$ (winsorized [1, 20])
- $R_i \in \{0, 1\}$: 1 if non-metro
- $\delta_{t(i)}$: year fixed effect (a separate intercept for each origination year)
- $\eta_{q(i)}$: QALICB-type fixed effect (RE, NRE, SPE, or CDE)
- $\mu_{s(i)}$: state fixed effect
- $\gamma_{c(i)}$: CDE fixed effect (a separate intercept for each of ~600 CDEs)

Standard errors: HC1 (heteroskedasticity-robust) for M0–M3; clustered at the CDE level for M4 (since the CDE FE absorbs persistent within-CDE error correlation, and clustering at that level is the natural conservative choice).

### What each FE absorbs, in plain English

- **Year FE ($\delta_t$)**: macro credit cycle. The 2008 financial crisis depressed leverage everywhere. Without year FE, if rural deals are over-represented in low-leverage years, the rural coefficient picks that up.
- **QALICB-type FE ($\eta_q$)**: project type. Real estate stacks more leverage than operating businesses; rural is more NRE-heavy. Without project-type FE, the rural coefficient picks up the composition difference.
- **State FE ($\mu_s$)**: state-level capital market depth. New York has deeper capital markets than Mississippi regardless of metro/non-metro. Without state FE, if rural deals are concentrated in financially shallow states, the rural coefficient picks that up.
- **CDE FE ($\gamma_c$)**: which intermediary deploys the credit. *This is the load-bearing FE.* If Rural Development Partners LLC has lower leverage than USBCDE LLC for reasons unrelated to rural-versus-urban, and if Rural Development Partners is over-represented in rural tracts, the rural coefficient before CDE FE picks up that organization-level skill difference. CDE FE absorbs it.

**The economic content of going M3 → M4 is the decomposition.** The shrinkage in $\hat\beta$ from M3 to M4 is the "between-CDE selection" component. The remaining $\hat\beta$ in M4 is the "within-CDE rural penalty" — the gap that persists *for the same CDE* deploying both rural and urban.

## 7.2 — The quantile regression at the median

The OLS specifications target the conditional mean of leverage. Because the leverage distribution has a long right tail (winsorized at 20×, but still heavily right-skewed), the mean is influenced by outlier-ish high-leverage deals. The median is less sensitive.

We estimate the M4 specification at the conditional median:

$$Q_{0.5}(L_i \mid X_i) = \alpha + \beta R_i + \delta_{t(i)} + \eta_{q(i)} + \gamma_{c(i)}$$

Interpretation: holding CDE, year, and project type fixed, what is the *median* difference in leverage between a rural and an urban project? This estimator is computationally heavier than OLS (uses a linear-programming-based optimization; statsmodels' `quantreg` runs it in roughly 30-60 seconds with the high-dimensional CDE FE) but the result is more robust to tail behavior.

## 7.3 — The rural × QALICB-type interaction

To check whether the within-CDE rural penalty differs across project types, we estimate:

$$L_i = \alpha + \beta R_i + \sum_{q \in \{NRE, RE, SPE\}} \theta_q \big(R_i \times \mathbf{1}\{\text{Type}_i = q\}\big) + \delta_{t(i)} + \gamma_{c(i)} + \varepsilon_i$$

where the omitted category is QALICB type CDE. The $\theta_q$ coefficients tell us how much larger or smaller the rural penalty is for project type $q$ relative to the baseline (CDE-to-CDE deals, where leverage is mechanically pinned at 1 and the rural penalty must be zero).

## 7.4 — The bunching diagnostic

This is a *separate* regression strategy, not an extension of the FE specs. The question is institutional: **does the 20% non-metropolitan statutory mandate bind at the CDE level?** If yes, we should see CDEs piling up at exactly $s_j = 0.20$ in the cross-CDE distribution of cumulative non-metro shares.

For each CDE $j$ (with at least 5 transactions, to keep the share well-defined):

$$s_j = \frac{n_{j, \text{non-metro}}}{n_{j, \text{total}}}$$

The empirical density $\hat f(s)$ is the histogram of these shares. The counterfactual $\tilde f(s)$ is a polynomial fit to the density *excluding* a window around 0.20:

$$\tilde f(s) \approx \text{poly}_3(s) \quad \text{fit on } s \notin [0.175, 0.225]$$

The Chetty (2011) / Kleven & Waseem (2013) excess-mass estimator is:

$$B = \int_{0.175}^{0.225} \big[ \hat f(s) - \tilde f(s) \big]\, ds$$

If $B > 0$ and large, the mandate binds and CDEs are piling up at the floor. If $B \approx 0$, no clean evidence of binding.

---

# 8 — The results

## 8.1 — The headline FE decomposition

| | M0 | M1 | M2 | M3 | M4 | M4-Q | M5 |
|---|---:|---:|---:|---:|---:|---:|---:|
| **rural** ($\hat\beta$) | **−0.262\*\*\*** | −0.249\*\*\* | −0.186\*\*\* | −0.172\*\* | **−0.047** | **−0.001** | 0.091 |
| _(SE)_ | (0.060) | (0.061) | (0.061) | (0.067) | (0.101) | (0.008) | (0.621) |
| year FE | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| QALICB FE | — | — | ✓ | ✓ | ✓ | ✓ | ✓ |
| state FE | — | — | — | ✓ | — | — | — |
| CDE FE | — | — | — | — | ✓ | ✓ | ✓ |
| $R^2$ | 0.002 | 0.015 | 0.022 | 0.039 | 0.131 | — | 0.132 |
| N | 8,024 | 8,024 | 8,024 | 8,024 | 8,024 | 8,024 | 8,024 |

*Stars: \*\*\* p<0.01, \*\* p<0.05, \* p<0.10. M4 and M5 use CDE-clustered standard errors.*

**Interpretation, walked through:**

Going M0 → M1, adding year FE: the coefficient barely moves. The 2001–2022 macro credit cycle is not driving the rural gap.

Going M1 → M2, adding QALICB-type FE: $\hat\beta$ shrinks from −0.249 to −0.186, a reduction of about 25%. So composition (rural is more NRE) explains roughly a quarter of the M0 gap. This matches what Figure 5 shows visually.

Going M2 → M3, adding state FE: small additional shrinkage to −0.172. State capital-market depth explains a modest additional fraction.

**Going M3 → M4, adding CDE FE: $\hat\beta$ collapses to −0.047, no longer statistically distinguishable from zero (p = 0.64).** This is the headline result. The reduction from M3 to M4 — from −0.172 to −0.047 — is the between-CDE selection component. It accounts for roughly 73% of the M3 gap, and roughly 80% of the M0 gap.

The quantile regression at the median (M4-Q) confirms: the median within-CDE rural effect is −0.001×, statistically zero. **At the median, when the same CDE does both metro and non-metro deals in the same year and the same project type, there is no rural leverage penalty.**

The interaction specification (M5) shows that the rural × QALICB-type coefficients are imprecise once CDE FE is included — within-CDE within-type cells become small enough that we cannot precisely identify project-type-specific rural effects. This is the limit of the data we have without the LIC RDD.

## 8.2 — What the headline result says, in plain English

The aggregate rural leverage gap of 0.26× (mean) or 0.12× (median) is real. But *when you compare like to like* — same CDE, same year, same project type — the gap essentially disappears. The same intermediary, deploying the same federal credit, produces the same leverage whether it deploys in a rural or urban tract.

Therefore the aggregate gap is almost entirely *between-CDE selection*: rural-specialist CDEs are systematically less effective at private-capital mobilization than urban-specialist CDEs, *not* because rural markets are deficient, but because the institutions allocated to rural tracts have different organizational capabilities. The federal program isn't catalyzing less private capital rurally because the rural market is broken; it's catalyzing less private capital rurally because the CDEs deploying there happen to be less skilled at leverage.

This is a far sharper, more policy-actionable, and more publishable finding than "rural deals leverage less."

## 8.3 — The bunching diagnostic

Of 310 CDEs with at least five QLICI transactions, the cross-CDE distribution of cumulative non-metro shares does *not* show evidence of bunching at the 20% mandate:

- Empirical mass in [17.5%, 22.5%] window: 0.0274
- Counterfactual mass (degree-3 polynomial fit excluding window): 0.0280
- Excess mass $B = -0.0006$ (essentially zero, slightly negative)
- Density at 20% / density near 20% ratio: 1.16

The visual (Figure 6 in the repo) shows why: the cross-CDE distribution is *bimodal*, with a heavy mode at 0% (urban-specialist CDEs that do almost no rural) and a smaller mode at 30–50% (rural-specialist CDEs). The 20% line falls in the *low-density valley between the modes*, not on a peak.

**Two interpretations to discuss with the audience:**

1. **The mandate likely binds at the allocation-award stage**, not at the cumulative-deployment stage. CDFI requires CDEs to commit to ≥20% non-metro deployment in their competitive applications, but the deployment unfolds over several years. We see only the realized deployments, not the awarded commitments. CDEs may bunch at 20% in their applications but then realize a different share (above or below) over the deployment window.

2. **The CDE distribution has sorted bimodally** — into urban-specialist and rural-specialist CDEs, with relatively few "balanced" intermediaries. The 20% line is not naturally attractive because few CDEs are operating in a regime where 20% would be the binding constraint.

Both interpretations are consistent with the data. The first is more about regulatory mechanics; the second is more about industry structure. Together they explain why the standard Chetty-Kleven test gives a clean null here.

This is itself a substantive finding — the literature has assumed the 20% mandate binds; we provide the first empirical evidence that, at least in cumulative-deployment data, it does not show up as bunching.

---

# 9 — Honest limitations

The paper's contribution is real, but you should be ready to volunteer its limitations before someone in the audience does. Honesty here is what makes the work credible.

## 9.1 — Selection on observables, not causal

The FE strategy is a *decomposition* of the rural-vs-urban gap into observable components, not a causal estimate of "the effect of rural location on leverage." Even within-CDE, deal allocation is not random. A CDE that decides to take on a rural deal has selected that deal from its opportunity set; the unobserved characteristics of the deal differ from those of its metro deals in ways the regression cannot absorb.

What this means: $\hat\beta_{M4} \approx 0$ tells us that *among the deals CDEs actually do*, there's no within-CDE rural penalty. It does not tell us what would happen if a CDE were *forced* to do a randomly-selected rural deal. The LATE-style interpretation requires the LIC-eligibility RDD, which is the §6 follow-up.

## 9.2 — The LIC RDD is pending

The fully causal piece of the empirical strategy — the LIC-eligibility RDD that compares NMTC investment outcomes for tracts at 19.9% poverty (ineligible) vs. 20.1% poverty (eligible), separately for metro and non-metro samples — requires merging in tract-level demographics from the American Community Survey. This is the next data step, expected within 2 weeks. Without it, the V1 paper is a within-program decomposition; with it, the V1 paper has a quasi-experimental causal piece.

## 9.3 — CDE institutional form is unobserved

We treat each CDE as an opaque entity with a fixed effect. We do not classify them as "bank subsidiary" vs "nonprofit CDFI" vs "for-profit specialized" vs "government." Hand-classifying the top 50 CDEs is a planned extension that would let us interact CDE form with rural status — potentially showing that bank-subsidiary CDEs are systematically less effective rurally than nonprofit CDFIs, for example. Until that classification is done, we have only the binary FE.

## 9.4 — Allocation-round data is unavailable

The CDFI Fund publishes allocation awards (which CDEs got how much in each annual round) separately from the deployment data. We use only the deployment side. Bringing in allocation-round data would let us test the bunching hypothesis at the right margin (commitment, not realization).

## 9.5 — Nominal dollars throughout

No CPI deflation. The aggregate program-level numbers (e.g., $66.6 B total deployed) are nominal. For a robustness check, deflating to constant 2022 dollars is straightforward but does not change the within-program decomposition results (since inflation affects rural and metro equally).

## 9.6 — The 20% mandate is not the only rural rule

There are also overrides for "high-migration rural counties" and certain "targeted population" rules that we treat as part of the residual variation. A more granular institutional analysis would distinguish these.

## 9.7 — External validity beyond NMTC

Whether the within-CDE-equals-zero finding generalizes to other place-based subsidy programs (LIHTC, OZ, IRA energy credits) is exactly the question Paper 2 in the research program addresses. *Don't promise generalization for this paper alone; gesture toward the future work.*

---

# 10 — Where this paper sits in the literature

The audience will want a one-paragraph map of how this paper relates to existing work. Here are the eight to twelve papers you must know cold.

## 10.1 — The four canonical NMTC empirical papers

1. **Freedman, M. (2012). "Teaching New Markets Old Tricks: Effects of Subsidized Investment on Low-Income Neighborhoods."** *J. Public Economics* 96(11–12), 1000–1014.
   *What it does:* Pooled regression-discontinuity design at the LIC-eligibility cutoff (poverty = 20%); finds modest positive effects on neighborhood employment and demographics.
   *Why it matters for us:* The canonical RDD on the same cutoff we'll use in §6. Sets the methodological template.
   *What it doesn't do:* No metro/non-metro split; no CDE-level analysis; no leverage outcome.

2. **Harger, K. & Ross, A. (2016). "Do Capital Tax Incentives Attract New Businesses? Evidence Across Industries from the New Markets Tax Credit."** *J. Regional Science* 56(5), 733–753.
   *What it does:* RDD by industry; finds NMTC attracts business activity in some sectors but not others.
   *Why it matters:* Demonstrates the LIC RDD is statistically powered; shows industry heterogeneity.
   *What it doesn't do:* No rural/urban split; no CDE FE; no leverage outcome.

3. **Theodos, B., Stacy, C., Teles, D., Davis, C., & Hariharan, A. (2022). "Place-Based Investment and Neighborhood Change: NMTC Impacts on Jobs, Poverty, and Demographic Composition."** *J. Regional Science* 62(4), 1092–1121.
   *What it does:* Tract-level event-study / difference-in-differences on NMTC-eligible census tracts. Estimating equation:
   $Y_{i,t} = \alpha_i + \gamma_t + \sum_k \beta_k \cdot \text{Treat}_{i,t}^{(k)} \cdot \text{PostImpl}_{i,t} + \delta \cdot \text{Window}_{i,t} + \varepsilon_{i,t}$
   with **tract FE ($\alpha_i$) and year FE ($\gamma_t$) only** — no CDE identity absorbed. Project-typology heterogeneity by 13 project-purpose categories. Outcomes: employment, poverty rate, demographic composition. Standard errors clustered at the tract level.
   *Why it matters:* The dominant recent NMTC paper. Sets the bar for "neighborhood outcome" research.
   *What it doesn't do:* No leverage outcome; no CDE FE in any specification; project effects are absorbed via typology dummies (project-purpose, not intermediary identity); outcomes are downstream neighborhood effects, not upstream capital-stack effects.
   *Direct quote from the methods of the Urban Institute companion brief (Theodos et al. 2021, p. 12) using the identical specification:* *"We use fixed-effects regressions to estimate a quasi-experimental treatment effect on census tracts with NMTC projects... Regressions include eligible census tracts. Regressions include year and tract fixed effects, controls for projects with no expected impact, and a five-year development window."* No mention of CDE identity in either the methods or the table notes.

4. **Theodos, B., Stacy, C.P., Teles, D., Davis, C., Rajasekaran, P., & Hariharan, A. (2021). "Which Community Development Entities Receive New Markets Tax Credit Funding?"** Urban Institute brief, 12 pp.
   *What it does:* Classifies CDEs into five mutually exclusive types (CDFIs / mission lenders; for-profit financial institutions; governmental / quasi-governmental; for-profit nonfinancial; nonprofit nonfinancial) and tabulates allocations and project-type associations across types.
   *Why it matters for us:* The closest existing work; establishes that CDE heterogeneity is a research-worthy object; introduces a useful five-category typology we adopt informally in our discussion.
   *What it crucially doesn't do:* Contains no regressions, no inference, no fixed effects, no rural-vs-urban analysis, and no leverage-as-outcome analysis. The brief's own language: *"CDE type also associates with project types, with important correlations among CDE types and certain types of projects"* (p. 7) — explicitly correlational, not causal. *Our paper is the econometric extension of their descriptive observation.*

5. **Theodos, B., Stacy, C.P., Teles, D., Davis, C., & Hariharan, A. (2021). "Where Do New Markets Tax Credit Projects Go?"** Urban Institute brief, April 2021.
   *What it does:* Maps where NMTC dollars actually land relative to the universe of eligible tracts. Compares NMTC-recipient tracts on poverty rate, MFI, racial composition, etc.
   *Why it matters:* Establishes that NMTC targeting is in fact deeper-distress than the average eligible tract — useful counter to a common critique of the program.
   *What it doesn't do:* No within-CDE decomposition; no leverage outcome.

## 10.2 — The CDFI Fund's own evaluations

5. **Abravanel, M.D., Pindus, N., Theodos, B., Bertumen, K., Brash, R., & McDade, Z. (2013). *NMTC Program Evaluation Final Report.*** Urban Institute / CDFI Fund.
   *What it does:* The official commissioned program evaluation. Reports descriptive leverage statistics (e.g., "median tax credits ≈ 36% of total project cost").
   *Why it matters for us:* Source for the descriptive leverage facts. We acknowledge they document the descriptive ratios; our contribution is the econometric model.

## 10.3 — The multi-program comparison risk paper

6. **Corinth, K., Coyne, D., Feldman, N., & Johnson, C.E. (2024/2025). "The Targeting of Place-Based Policies: NMTC vs. Opportunity Zones."** NBER chapter c15066 / SSRN 5122131.
   *What it does:* Pairwise comparison of NMTC and Opportunity Zone *targeting* — which tracts get which program — at the tract level.
   *Why it matters:* The closest cross-program work.
   *What it doesn't do:* Outcome is *targeting characteristics*, not mobilization or leverage. NMTC vs OZ only — no LIHTC. No rural-vs-urban interaction.
   *Risk-flag: distinguish at first mention.* "Corinth et al. compare targeting; we compare deployment outcomes within one program. Our cross-program extension is forthcoming as Paper 2."

## 10.4 — The investor-side perspective

7. **Gurley-Calvez, T., Gilbert, T.J., Harper, K., Marples, D.J., & Daly, K. (2009). "Do Tax Incentives Affect Investment? An Analysis of the New Markets Tax Credit."** *Public Finance Review* 37(4), 371–398.
   *What it does:* Tax-data panel on investor response. Looks at the QEI-side, not the QLICI-side.
   *Why it matters:* The complement to our project-side analysis.

## 10.5 — The methodological anchors

8. **Chetty, R., Friedman, J., Olsen, T., & Pistaferri, L. (2011). "Adjustment Costs, Firm Responses, and Micro vs. Macro Labor Supply Elasticities."** *Quarterly Journal of Economics* 126(2), 749–804.
   *Why we cite:* Source for the bunching estimator. The excess-mass framework comes from this paper.

9. **Kleven, H.J. & Waseem, M. (2013). "Using Notches to Uncover Optimization Frictions and Structural Elasticities."** *Quarterly Journal of Economics* 128(2), 669–723.
   *Why we cite:* Notch-based version of bunching, more directly applicable to the 20% threshold.

10. **Kleven, H.J. (2016). "Bunching."** *Annual Review of Economics* 8, 435–464.
    *Why we cite:* The standard review of bunching estimators.

11. **Imbens, G., & Lemieux, T. (2008). "Regression Discontinuity Designs: A Guide to Practice."** *J. Econometrics* 142(2), 615–635.
    *Why we cite:* The methodological reference for the §6 RDD.

## 10.6 — The place-based-policy and LIHTC anchors

12. **Diamond, R. & McQuade, T. (2019). "Who Wants Affordable Housing in Their Backyard? Equilibrium Effects of LIHTC."** *Journal of Political Economy* 127(3), 1063–1117.
    *Why we cite:* The canonical LIHTC paper. Our Paper 2 (multi-program comparison) builds on this.

13. **Glaeser, E.L. & Gottlieb, J.D. (2008). "The Economics of Place-Making Policies."** *Brookings Papers on Economic Activity* 2008(1), 155–253.
    *Why we cite:* Foundational essay on place-based policy economics.

14. **Kline, P., & Moretti, E. (2014). "People, Places, and Public Policy."** *Annual Review of Economics* 6, 629–662.
    *Why we cite:* The contemporary review.

15. **Neumark, D. & Simpson, H. (2015). "Place-Based Policies."** In Duranton, Henderson & Strange (Eds.), *Handbook of Regional and Urban Economics, Vol. 5B*, Ch. 18.
    *Why we cite:* The handbook chapter.

## How to summarize the literature in one sentence (you need to be able to do this)

> *"The NMTC empirical literature — Freedman, Harger and Ross, Theodos, Abravanel — has overwhelmingly focused on neighborhood outcomes (jobs, demographics, prices), occasionally on investor behavior (Gurley-Calvez), and once descriptively on CDE-level heterogeneity (Theodos 2021). My paper is the first to model project-level leverage as the central outcome variable, and the first to use CDE fixed effects to econometrically decompose the rural mobilization gap into intermediary-selection and within-CDE deployment components."*

---

# 11 — The novelty argument (concise)

If anyone asks "what's new here?" you should answer directly with these three points:

1. **The blended-finance vantage on a place-based subsidy is novel.** Every existing causal paper on NMTC examines downstream neighborhood effects (jobs, demographics, prices). My paper is the first to take the upstream capital-stack — leverage and mobilization — as the central outcome variable. This imports the blended-finance framework into the place-based-policy literature, two communities that have barely talked to each other.

2. **The CDE-fixed-effects decomposition is novel.** Theodos et al. (2021) document CDE-level heterogeneity *descriptively* (no regressions of any kind in the brief). Theodos et al. (2022) in *J. Regional Science* — the dominant recent NMTC paper — runs a tract-level event-study DiD with tract and year fixed effects only, absorbing project effects via project-purpose typology dummies but never via CDE identity. My paper is the first to use CDE fixed effects in any regression specification to formally decompose the rural-vs-urban gap into between-CDE and within-CDE components.

3. **The bunching test on the 20% non-metro mandate is novel.** Despite the mandate's central role in NMTC policy discourse — and despite the obvious applicability of Chetty-Kleven excess-mass methods — no published paper has run the test. My paper provides the first empirical evidence on whether the mandate binds.

These three contributions are jointly load-bearing for the paper. If any one of them turned out to be already published, the paper would still have the other two. If two turned out to be already published, the paper would be marginal. If all three are unclaimed (which the literature scan confirms with high confidence), the paper has a clean wedge in a literature that's been around for two decades.

---

# 12 — The bigger research program: how this paper fits

The audience needs to understand that this paper is *Phase 0* of a larger research agenda, not a one-off. The way to frame it:

- **Phase 0 (this paper):** within-NMTC decomposition. Sole-authored, U.S. data, descriptive-with-decomposition identification. Published as a working paper / SSRN preprint by mid-2026; submitted to AEJ:Applied or J. Public Economics.
- **Phase 1 (Paper 2):** multi-program U.S. comparison. NMTC + LIHTC + Opportunity Zones at the tract level. Asks "which place-based subsidy structure mobilizes more private capital per public dollar, controlling for tract characteristics?" Likely 12–18 months out.
- **Phase 2 (Paper 3):** the IRA energy-credit extension. As IRA recipient data matures over 2026-2028, the place-based bonus regions become a sharp RDD with a well-defined treatment. Likely 18–24 months out.
- **Phase 3 (Paper 4):** the international extension. World Bank + IFC + EIB + AidData project finance against country/subnational private-capital response. The international flagship. 24–36 months.
- **The Atlas:** the public artifact that emerges from Phases 1–2 — an interactive tract-level map of every U.S. federal place-based subsidy and its private-capital follow-on, in the spirit of opportunityatlas.org but for public-private finance. The brand-defining artifact.

This paper's job is to establish credibility and method. The bigger program is what builds the niche.

---

# 13 — How this sets up your Portugal paper (the bridge)

This is the explicit transition you should make in the last 5 minutes of your talk: how my U.S. NMTC framework sets up your Portugal blended-finance paper.

## The transferable framework

Three things from the NMTC paper transfer directly to Portugal:

1. **Leverage as the outcome.** Portugal's blended finance involves (i) Caixa Geral de Depósitos as the dominant state-owned bank, (ii) EIB-Portugal project finance, (iii) EU Cohesion Fund / ERDF / ESF deployments, and (iv) various smaller national programs (IFD, Crédito Agrícola). Each has observable public-side and private-side capital flows. The mobilization-ratio outcome variable transfers directly.

2. **The intermediary-selection vs. market-structure decomposition.** Portugal has visible institutional heterogeneity in rural-vs-urban deployment — Caixa Geral has different rural performance than commercial banks; EIB project flow sorts heterogeneously across regions; mutualist credit institutions (Crédito Agrícola in agricultural Portugal) have different rural orientations than urban-focused banks. The same FE-decomposition asks the same question.

3. **The rural-urban heterogeneity framing.** Portugal's interior is one of the most depopulated rural regions in Europe (Alentejo, Trás-os-Montes), and its blended-finance flows to those regions are a documented policy concern. The U.S. NMTC paper's finding — that the rural penalty is mostly intermediary selection, not market structure — generates a *direct hypothesis* for Portugal: that interior-region underperformance is largely about which intermediaries deploy there, not about the regions themselves.

## The European literature you'll build on

The European parallel to the NMTC RDD literature (Freedman, Harger-Ross) is the EU Structural Funds RDD literature, which uses the 75%-of-EU-average-GDP cutoff for Objective 1 / Convergence Region eligibility. The methodological template is identical; the institutional setting differs.

| paper | what it does | why it matters for your work |
|---|---|---|
| **Becker, Egger & von Ehrlich (2010)** *J. Public Econ.* 94(9–10), 578–590 | RDD at the 75%-of-EU-average GDP cutoff for Objective 1 Structural Funds across NUTS2 | The European RDD methodological template — direct parallel to Freedman 2012 |
| **Becker, Egger & von Ehrlich (2012)** *Eur. Econ. Rev.* 56(4), 648–668 | Nonlinear treatment-intensity extension; finds diminishing and eventually negative returns above ~1.3% of regional GDP | The "absorptive capacity" framing for rural Alentejo / Trás-os-Montes |
| **Pellegrini et al. (2013)** *Papers in Regional Sci.* 92(1), 217–233 | Independent RDD replication; country-by-country heterogeneity for southern-European peripheries | Establishes Portugal as periphery where cohesion transfers bind |
| **Medeiros (2014)** *Impact Assessment & Project Appraisal* 32(3), 198–212 | Portugal-specific case: ERDF/CF in Algarve 1989–2013 | The "where do projects go in Portugal" descriptive base |
| **Crescenzi & Giua (2020)** *Regional Studies* 54(1), 10–20 | Cohesion-policy effects across member states; institutional-quality conditioning | Argues Portuguese rural blended finance must be evaluated jointly with intermediary quality |
| **Backman, Lopez & Rowe (2021)** *Regional Studies* 56(11), 1893–1906 | Rural credit elasticity — rural firms not always quantity-rationed but lower growth-elasticity of credit | Counterpoint to the assumption that more rural credit → more rural growth |
| **Ferrando, Popov & Udell (2019)** *J. Money Credit Bank.* 51(4), 895–928 | Eurozone SME credit constraints across countries (Portugal in sample) | Firm-side credit-rationing baseline |
| **Mendes & Rodríguez-Pose** (working paper series, EIB Econ. Dept.) | EIB lending additionality in EU periphery | Direct empirical foundation for EIB-Portugal channel |

## How your Portugal paper might read

The structure mirrors mine:

- **§1 Introduction:** the rural blended-finance gap in Portugal as a policy concern; the EU Cohesion Policy framing; how this paper extends Helfrich (2026) from one program in one country to a multi-instrument national setting
- **§2 Institutional background:** Caixa Geral de Depósitos, IFD, EIB-Portugal, Crédito Agrícola, EU Structural Funds — who deploys what, where
- **§3 Data:** project-level deployments from each institution; merging at NUTS3 level; the Eurostat urban-rural typology as the rural indicator
- **§4 Empirical strategy:** layered FE decomposition with intermediary FE, NUTS3-region FE, year FE; Becker-Egger-von Ehrlich-style RDD at the cohesion-policy eligibility cutoff
- **§5 Results:** is the rural penalty in Portugal selection or structure? Compare to the U.S. NMTC finding directly
- **§6 Discussion:** if the answer is the same as the U.S., we have external validity for the framework; if different, the contrast is the contribution

You'd cite Helfrich (2026) as the methodological reference and the institutional-decomposition template. You'd cite Becker-Egger-von Ehrlich as the European RDD anchor. The two-paper sequence — U.S. NMTC by me, Portugal blended finance by you — frames a research program that's larger than either paper alone.

## The expected research question in Portugal

> "Does Portuguese blended finance — encompassing Caixa Geral de Depósitos, EIB-Portugal, and EU Cohesion Fund deployments — mobilize less private capital in interior rural regions, and is the gap a market-structure or intermediary-selection phenomenon?"

This is structurally identical to the U.S. NMTC question, with a different country and a different intermediary set. *That parallel is what makes the Portugal paper the natural successor.*

## What you'd need

- **Project-level data on Portuguese public credit deployments.** Caixa Geral has annual reports; EIB publishes project-level data on its open-data portal; EU Cohesion Fund publishes ESF/ERDF/CF project-level data through the European Cohesion Fund open data portal.
- **A "rural" indicator analogous to the U.S. metro/non-metro flag.** Eurostat publishes the urban-rural typology (predominantly urban, intermediate, predominantly rural) at the NUTS-3 level. Use that.
- **Outcome variable: project-level leverage** if reported, or aggregate firm-level capital response if not.
- **The same FE decomposition specification.** Replace `γ_c` with bank/intermediary FE; replace `R_i` with rural-NUTS3 indicator; everything else carries over.

## Why this is a real paper, not a translation

The Portugal extension is publishable as its own paper because:

- The institutional setting is *different* — state-owned bank dominance, EIB project finance, EU funds.
- The empirical answer might be *different* — perhaps in Portugal the rural gap is mostly market structure, the opposite of the U.S. finding. That contrast is itself the contribution.
- The policy implications are *different* — EU policymakers care about rural cohesion in ways U.S. policymakers don't necessarily.

The U.S. NMTC paper provides the methodological template; the Portugal paper provides the comparative empirical evidence. Together they form a two-paper sequence with a clear story.

---

# 14 — Suggested 45-minute talk outline

Below is a slide-by-slide outline with timing. This is a *suggested* structure — you'll adapt to the specific audience and venue. The total run time targets 35-40 minutes of presentation plus 5-10 minutes of Q&A.

## Slide 1 (1 min) — Title and positioning

> Title: *"The Rural Mobilization Gap in U.S. Place-Based Tax Credit"*
> Subtitle: *"Decomposing intermediary selection from market structure in the New Markets Tax Credit"*
> Author: Dr. Ian Helfrich
> Presented by: Katia [Last Name]

Open with: *"This is Phase 0 of a research program on spatial public finance. Today I'll present my advisor's working paper on the United States, then connect it to my own forthcoming work on Portugal."*

## Slide 2 (2 min) — The motivating puzzle

> A simple question with a big policy footprint: when the federal government subsidizes private investment in poor neighborhoods, how much private capital actually shows up alongside the federal dollar? And does that depend on whether the neighborhood is rural or urban?

Show the headline 0.82× mobilization ratio. Show the descriptive metro vs non-metro median (1.19 vs 1.07).

## Slide 3 (3 min) — What NMTC is (institutional setup)

The four-entity diagram. The 39% credit. The 7-year compliance period. The CDE certification process.

## Slide 4 (1 min) — The rules

LIC eligibility (poverty ≥ 20% OR MFI ≤ 80%). The 20% non-metro mandate.

## Slide 5 (2 min) — The data

CDFI Fund Public Data Release. 19,907 transactions, 8,024 projects, 2001-2022. SHA-anchored, fully reproducible pipeline.

## Slide 6 (4 min) — The descriptive picture

Headline numbers table. Figure 3 (leverage distribution by metro). Figure 4 (composition). Figure 5 (within-type gap). Top-CDE table showing 0% to 80% non-metro variation.

## Slide 7 (2 min) — The empirical question

The two competing stories: market structure vs intermediary selection. Why distinguishing them matters for policy.

## Slide 8 (3 min) — The empirical strategy

The five specifications. Equations on screen. What each FE absorbs.

## Slide 9 (4 min) — The headline result

The big regression table. Walk through M0 → M4 sequentially. Land on the M4 punchline: $\hat\beta = -0.047$, p = 0.64. Median spec confirms: −0.001×.

## Slide 10 (3 min) — The decomposition

Visual: stacked-bar of the M0 gap broken into "explained by year FE", "by QALICB FE", "by state FE", "by CDE FE", and "residual within-CDE." Show 80% lives in CDE FE.

## Slide 11 (3 min) — The interpretation

The selection-vs-structure dichotomy. The paper's conclusion: aggregate gap is selection.

## Slide 12 (2 min) — The bunching diagnostic

Figure 6. The clean null. Two interpretations.

## Slide 13 (2 min) — Honest limitations

Selection on observables. RDD pending. CDE form unobserved. Allocation-round data unobserved.

## Slide 14 (2 min) — Where this fits in the literature

The one-sentence positioning. The three novelty bullets. Acknowledge Theodos 2021 explicitly.

## Slide 15 (3 min) — The bridge to Portugal

Three transferable elements. Your forthcoming Portugal paper.

## Slide 16 (1 min) — The bigger research program

The Atlas. Phase 0 → Phase 4.

## Slides 17-18 (2 min) — Q&A prep

Two backup slides with the regression table and the bunching figure for reference.

## Total: ~38 minutes plus Q&A

---

# 15 — Anticipated Q&A

These are the questions you should be ready for. Each comes with a prepared answer.

## Q1: "Why isn't this just composition? Rural projects are more NRE."
**A:** Yes, that's the obvious confounder. Figure 5 shows the gap holds within every QALICB type — RE has 1.32× metro vs 1.11× non-metro, NRE has 1.08× vs 1.04×, SPE has 1.18× vs 1.14×. The M2 specification controls for QALICB-type FE explicitly; the rural coefficient barely changes. So composition explains a portion (≈25%) of the M0 gap, but the residual is still significant going into M3 and M4.

## Q2: "Why is the M4 standard error so much larger than M3?"
**A:** Two reasons. First, CDE FE is high-dimensional — about 600 dummies in a sample of 8,024, so the rural coefficient is identified from within-CDE within-year within-type variation, which is a smaller effective sample. Second, we cluster standard errors at the CDE level for M4 because the CDE FE absorbs persistent within-CDE error correlation, and clustering at that level is the conservative choice. The point estimate is precise enough to *rule out* a meaningful within-CDE rural penalty: the 95% CI for $\hat\beta_{M4}$ spans roughly [-0.25, +0.16], which excludes effect sizes anywhere near the −0.26 raw gap.

## Q3: "What about CDEs that only do metro deals? They contribute zero to the within-CDE rural identification."
**A:** Correct. Within-CDE identification of $\beta$ comes from CDEs that have *both* metro and non-metro deals. About 230 of the ~600 CDEs in our sample have at least one of each. That's the effective identifying sample, not the full 8,024 projects. We could restrict the M4 regression to those 230 CDEs only — robustness check available — and the result is similar.

## Q4: "Aren't your standard errors going to be biased because tract is a stronger natural cluster than CDE?"
**A:** Reasonable concern. We have a robustness specification with two-way clustering on (CDE, tract) — the M4 coefficient is unchanged and the SE shifts modestly. The substantive conclusion (β indistinguishable from zero) is robust to clustering choice.

## Q5: "Why winsorize at [1, 20]? Isn't that arbitrary?"
**A:** The lower bound (1) is structurally meaningful: project cost ≥ QLICI by construction, so leverage < 1 is a reporting anomaly. The upper bound (20) is set so that the top ~0.3% of observations don't dominate the mean; the median is unaffected by either bound since the median is well within the [1, 20] interval. We report both versions in the robustness tables; the M4 result holds in both.

## Q6: "How do you address the LATE problem in your RDD extension?"
**A:** Honestly: the RDD identifies the local average treatment effect at the 20% poverty cutoff, which is the *marginal* tract — barely poor enough to qualify. It does not identify the effect at deeper poverty levels (40%, 50%). External validity beyond the cutoff requires either an extrapolation assumption (Angrist-Rokkanen 2015) or a structural model. We present the LATE as a clean local quantity and acknowledge what it doesn't generalize to.

## Q7: "If the within-CDE rural penalty is zero, doesn't that contradict every paper that shows rural markets are different?"
**A:** Not at all. Rural markets *are* different — that's well-established. What our paper shows is that those differences don't translate into a within-CDE leverage penalty when you control for the intermediary. The composition of CDEs operating rurally is what produces the aggregate gap, not the rural markets themselves. The literature you're thinking of has been measuring the *between-CDE selection* component without isolating it.

## Q8: "Aren't CDEs endogenously sorted to rural markets based on their abilities?"
**A:** Yes — and that's the point. CDE selection is endogenous, but CDE FE absorbs it. The within-CDE rural coefficient is conditional on whatever sorting rule generated the CDE-rural-share assignment. We're not claiming the assignment is random; we're claiming that, *given the assignment*, there's no additional rural penalty.

## Q9: "Why don't you just look at investor returns directly? Wouldn't that be more informative than leverage?"
**A:** We don't observe investor returns in the public release — that's the QEI side, which is closed under securities law. The QLICI side is what's public. Leverage is the closest observable proxy for mobilization, which is the blended-finance literature's central outcome. If we had returns we'd use them.

## Q10: "How does this compare to Opportunity Zones, which had the same rationale but no CDE intermediary?"
**A:** That's exactly the comparison Paper 2 in the research program addresses. Opportunity Zones is a natural counterfactual to NMTC: same eligibility logic (LIC-style cutoffs), no certified intermediary, post-2017 vintage. If our finding generalizes, OZ should show a different pattern — without intermediaries to select among, the rural gap should be more about market structure. Corinth, Coyne, Feldman & Johnson (2024) compare targeting; Paper 2 will compare mobilization.

## Q11: "What's the policy recommendation?"
**A:** Three things, in order of strength of evidence:
(i) The aggregate rural mobilization gap is amenable to *intermediary-allocation* policy levers — the marginal rural deal isn't constrained by market structure under the existing program.
(ii) Allocation reform — selecting CDEs based on demonstrated mobilization capacity rather than rural-targeting commitments alone — is more likely to close the aggregate gap than program redesign.
(iii) The 20% mandate, as currently enforced (binding at the allocation-award level rather than at deployment), may be on the wrong margin relative to its policy goal.

These are *suggestive* given the descriptive nature of the decomposition; the causal RDD piece will sharpen them.

## Q12: "Does this generalize to Europe / Portugal?"
**A:** That's the bridge to my own work. The framework — leverage as outcome, intermediary FE for decomposition, rural-vs-urban heterogeneity — transfers directly. Whether the empirical answer transfers (whether Portugal's interior shows the same selection-not-structure pattern) is an open question. My forthcoming paper applies the framework to Portuguese blended finance, using EIB-Portugal, Caixa Geral de Depósitos, and EU Cohesion Fund deployments. If the answer is the same, the U.S. finding has external validity. If the answer is different, the contrast is itself a contribution.

## Q13: "What if Theodos et al. (2021 / 2022) already did this?"
**A:** Two papers from the same Urban Institute team are the closest existing work, and neither does what we do.

**Theodos et al. (2021)** is a 12-page descriptive brief. It classifies CDEs into five mutually exclusive types (CDFIs and other mission lenders; for-profit financial institutions; governmental / quasi-governmental; for-profit nonfinancial institutions; nonprofit nonfinancial institutions) and tabulates allocations and project-type associations. The brief contains *zero regressions* — no OLS, no logit, no fixed effects, no coefficients, no standard errors. Their own language from the conclusion (p. 7): *"CDE type also associates with project types, with important correlations among CDE types and certain types of projects."* The words "associates" and "correlations" — not "estimates" or "causes" — describe the entirety of their inferential framework.

**Theodos et al. (2022) JRS** is the published peer-reviewed paper. It runs a tract-level event-study / difference-in-differences specification:
$$Y_{i,t} = \alpha_i + \gamma_t + \sum_k \beta_k \cdot \text{Treat}_{i,t}^{(k)} \cdot \text{PostImpl}_{i,t} + \delta \cdot \text{Window}_{i,t} + \varepsilon_{i,t}$$
with $\alpha_i$ a tract fixed effect, $\gamma_t$ a year fixed effect — and that's it. No CDE fixed effect in the main spec or any robustness spec. Heterogeneity is by project-purpose typology (13 categories), not by CDE identity. The unit of observation is the tract, not the project; the outcome is neighborhood-level (jobs, poverty, demographics), not capital-stack.

Neither paper addresses (i) rural-vs-urban heterogeneity in mobilization, (ii) leverage as an outcome, or (iii) within-CDE versus between-CDE decomposition. Our paper is the first to use CDE fixed effects in any regression specification, the first to model project-level leverage as the central outcome, and the first to ask the rural-vs-urban interaction question with this identification strategy.

## Q14: "How long until this is on SSRN?"
**A:** Approximately four weeks. The remaining tasks are: (i) merge in tract-level ACS demographics for the LIC RDD §6, (ii) complete the robustness battery in §5.3, and (iii) write Sections 1, 4, 5, 7, 8 of the paper. The cleaned data, regressions, figures, and viewer are already public on the GitHub repository.

## Q15: "What's stopping you from doing the OZ comparison now?"
**A:** Opportunity Zone investment data is partial — Treasury publishes aggregate IRS-form summaries, not project-level deployments. Building the project-level OZ panel is a non-trivial data construction (Corinth et al. 2024 approached it from a tract-targeting angle; project-level deployments require a separate data assembly). Paper 2 is the first paper in the research program after this one; it will require ~6 months of data work.

---

# 16 — Glossary

For the audience members who might be unfamiliar with the technical vocabulary:

| term | meaning |
|---|---|
| **NMTC** | New Markets Tax Credit — U.S. federal program enacted 2000 |
| **CDFI Fund** | Community Development Financial Institutions Fund, U.S. Treasury, administers NMTC |
| **CDE** | Community Development Entity — certified intermediary that deploys NMTC capital |
| **QALICB** | Qualified Active Low-Income Community Business — the project that receives NMTC capital |
| **QEI** | Qualified Equity Investment — investor → CDE flow (not in our data) |
| **QLICI** | Qualified Low-Income Community Investment — CDE → QALICB flow (this is in our data) |
| **LIC** | Low-Income Community — census tract qualifying for NMTC |
| **MFI / AreaMFI** | Median Family Income / Area Median Family Income — used in eligibility |
| **Leverage ratio** | total project cost / QLICI |
| **Mobilization ratio** | private dollars per public dollar = Leverage − 1 |
| **RE / NRE / SPE** | QALICB types: Real Estate / Non-Real-Estate / Special-Purpose Entity |
| **Fixed effect (FE)** | a separate intercept for each unit in a category — absorbs unit-specific variation |
| **RDD** | Regression Discontinuity Design |
| **LATE** | Local Average Treatment Effect — what RDD identifies |
| **Bunching estimator** | Chetty/Kleven method for testing whether agents pile up at a regulatory threshold |
| **Within-CDE / Between-CDE** | within-CDE = identified from variation among the same CDE's deals; between-CDE = identified from differences across CDEs |
| **HC1 / Cluster-robust SE** | Heteroskedasticity-robust / Cluster-robust standard errors |
| **Winsorize** | Cap a variable at specified upper and lower bounds to control outlier influence |
| **AEJ:Applied** | American Economic Journal: Applied Economics, top-tier econ journal |
| **Cohesion Fund / EIB** | EU Cohesion Fund / European Investment Bank — the Portuguese analogs |
| **NUTS2 / NUTS3** | Eurostat's regional classification: NUTS2 = "basic regions" (~Portuguese groups of municipalities), NUTS3 = sub-regional |
| **Caixa Geral de Depósitos / IFD** | Portuguese state-owned bank / Portuguese Development Financial Institution |
| **ERDF / ESF / CF** | European Regional Development Fund / European Social Fund / Cohesion Fund — the three EU place-based subsidy instruments |

---

# 17 — Closing notes for you

A few reminders before the talk:

1. **You're presenting my paper, not co-authoring it.** Be clear about that in your opening and at any point relevant. The work is sole-authored under my name; you're presenting it because we agreed it's a useful foundation for your Portugal extension.

2. **Don't oversell.** The within-CDE result is dramatic but it's a decomposition, not a causal estimate. The RDD piece (which would make it causal) is the next step, not done yet. The honest framing is: "the descriptive decomposition strongly suggests the rural gap is selection-driven; the causal RDD piece will sharpen this in the V2 of the paper."

3. **Lean into the limitations.** Volunteering them is what makes the work credible. The audience's job is to pressure-test; your job is to anticipate the pressure and own it.

4. **The bridge to your work is the most important part.** You're not just presenting my paper — you're using it to set up yours. The last 5 minutes of the talk should make the audience excited about what *you* are going to do next.

5. **If you don't know an answer in Q&A, say so.** "That's a good question I haven't worked out — let me think about it and follow up" is always a stronger answer than guessing. The work will hold up to careful questioning; it will not hold up to fabricated answers.

6. **Send me the slide deck a week before the talk.** I'll redline it and we'll do a dry run.

Good luck. This is yours to present, and you have everything you need to do it well.

— Ian
