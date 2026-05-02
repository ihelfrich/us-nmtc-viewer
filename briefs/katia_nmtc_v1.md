# Blended Finance Pilot — New Markets Tax Credit (NMTC)

**For: Katia** · **From: Ian** · **Date: 2026-04-22** · **Status: First-look, for discussion**

---

## One-paragraph summary

The New Markets Tax Credit is the US federal program whose mechanics most closely
match the "blended finance" story you want to tell: the federal government
concessionally subsidizes private investors (39% tax credit) on condition that
those investors put their money into low-income tracts. Over 2001–2022 the
program deployed **$66.6B of public-credit QLICI capital** into **8,024 projects**
whose total cost was **$120.9B**, meaning **$0.82 of private capital was mobilized
per dollar of public credit**. Non-metro tracts received **19.6% of dollars** —
right at the statutory 20% target — but each dollar there mobilized *less*
private capital than in metro tracts. The **non-metro leverage gap (~0.12
at the median, ~0.26 at the mean)** is our core empirical object.

This answers your core research question in a narrow, identifiable form: **among
the structures that investors and CDEs actually use, which mobilize more
private capital per federal dollar, and does the ranking flip in rural markets?**

---

## Headline numbers (FY2003–FY2022 data release, CDFI Fund)

| metric | value |
|---|---:|
| Total QLICI transactions | **19,907** |
| Unique projects | **8,024** |
| Total QLICI deployed | **$66.6 B** |
| Total project cost (public + private) | **$120.9 B** |
| **Implied mobilization ratio** (private $ / public $) | **0.82×** |
| Non-metro transaction share | 19.3% |
| Non-metro dollar share | 19.6% |
| Statutory non-metro target | 20.0% |

### Rural vs. metro leverage gap

| | median leverage | mean leverage | mobilization ratio |
|---|---:|---:|---:|
| Metro | 1.19× | 1.99× | 0.81× |
| Non-metro | 1.07× | 1.73× | 0.82× |
| **Gap (metro − non-metro)** | **+0.12** | **+0.26** | (≈ flat on aggregate; see caveat) |

The aggregate mobilization ratios are almost identical across metro and
non-metro because a few very high-leverage metro deals pull the metro mean up.
At the *median* and through the deal-size distribution, metro consistently
mobilizes more private capital per public dollar than non-metro. This is the
story — and because the 20% allocation mandate bunches CDEs against the target,
we have a plausible identification strategy.

---

## Within-NMTC structural variation (your "compare structures" angle)

The program mandates one tax-credit instrument, but CDEs implement it via four
within-program structural choices that we can treat as the "structures" to
compare:

| structural margin | observed variation | is there a metro gap? |
|---|---|---|
| **Leverage ratio** (private debt stacked on the QEI) | 10th %ile 1.0×, median 1.16×, 90th %ile 3.37× | yes — metro medians 10% higher |
| **QALICB type** — Real Estate vs. Non-RE vs. Special-purpose vs. CDE-to-CDE | RE: 2,862 projects; NRE: 3,775; SPE: 1,296; CDE: 91 | RE much more metro-skewed (91% metro); NRE more balanced |
| **Multi-CDE deal** (stacked allocations) | 20.8% metro, 19.9% non-metro | basically flat — complexity is not rural-specific |
| **CDE identity** (bank-subsidiary vs. nonprofit vs. specialized) | top-20 CDEs do 50%+ of $; non-metro shares vary 5%–60% | huge CDE-level variation — this is the mechanism candidate |

The **CDE-level variation** is where I think the most interesting paper sits.
If rural mobilization is lower on average but specific CDEs deliver high-leverage
rural deals, then the "structure" driving the gap isn't NMTC itself — it's
*which institutional intermediary deploys it*. That's a testable hypothesis.

---

## Why this specifically answers your question

Your original framing: *which blended-finance structure mobilizes most private
capital?*

NMTC lets us operationalize "structure" as **(leverage arrangement × QALICB type ×
CDE institutional form)** — three real, observable dimensions — and "mobilize"
as the project-level **total cost / QLICI** ratio, which is directly disclosed.
The rural–non-rural contrast is statutorily binary, yielding a clean interaction
term.

What we **won't** be able to say with this paper alone: how NMTC compares to
Opportunity Zones, USDA guarantees, or IRA Energy Communities as alternative
structures. That's Paper 2. Paper 1 establishes the within-program mechanism
and the rural gap; Paper 2 puts NMTC in context against other US instruments.

---

## Identification strategy (for when we go formal)

1. **Low-Income Community eligibility RDD** — tracts qualify if poverty ≥ 20%
   OR median family income ≤ 80% of area median. Sharp cutoffs, both sides
   observable in Census ACS. Compare just-eligible to just-ineligible tracts.
2. **Rural × LIC interaction** — the RDD done separately for metro and
   non-metro subsets. If the discontinuity size differs, that's the rural gap
   we need to explain.
3. **CDE fixed effects** — within-CDE comparison of metro vs. non-metro deals
   absorbs the "which intermediary" selection problem.
4. **20% mandate bunching** — CDEs that bind against the 20% non-metro target
   reveal willingness-to-deploy. Those that exceed 20% are voluntary; identify
   the marginal rural deal from the bunching point.

---

## Data in hand (delivered with this brief)

Under `us_nmtc/data/`:

- `raw/NMTC_Public_Data_Release_FY2003-FY2022.xlsx` — the CDFI Fund source file
- `raw/NMTC_Public_Data_Release_Summary_FY2003-FY2022.pdf` — CDFI's own codebook
- `processed/nmtc_transactions.csv` — cleaned QLICI-level panel (19,907 rows)
- `processed/nmtc_projects.csv` — cleaned project-level panel (8,024 rows, with leverage)
- `processed/summary_by_metro.csv` — metro vs. non-metro rollup
- `processed/summary_by_qalicb_type.csv` — RE / NRE / SPE / CDE × metro
- `processed/summary_by_year.csv` — annual deployment series, metro-split
- `processed/top_cdes.csv` — top 20 CDEs by $ with non-metro share
- `processed/leverage_distribution.csv` — percentile breakdown × metro
- `processed/headline.json` — the numbers above as machine-readable

---

## Proposed next three moves

1. **Census-tract merge** (this week). Join NMTC tract FIPS to 2016–2020 ACS
   poverty + MFI + population + RUCA codes. Gives us the RDD running variable
   and a continuous rurality measure (RUCA 1–10), not just metro/non-metro.

2. **CDE-type classification** (this week). Pull the CDE Certification list
   from CDFI Fund, hand-classify the top-50 CDEs by institutional form
   (bank subsidiary / nonprofit CDFI / for-profit specialized / government).
   That turns "CDE variation" from a name into a structural variable.

3. **First-look figure** (next week). Binned scatter of project-level leverage
   vs. tract poverty rate, metro and non-metro overlaid. If the discontinuity
   is visible at the 20% poverty threshold for both subgroups but the rural
   slope is flatter, the paper is real.

---

## Citation for the data

CDFI Fund, U.S. Department of the Treasury. *New Markets Tax Credit Public
Data Release, FY2003–FY2022.* Released June 2024.
<https://www.cdfifund.gov/documents/data-releases>

The Summary PDF is our stand-in for the codebook / methodology note until we
want something formal.
