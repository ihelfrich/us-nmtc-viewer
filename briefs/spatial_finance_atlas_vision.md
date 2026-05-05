# A Spatial Public-Finance Atlas — strategic vision memo

**Author:** Ian Helfrich · **Date:** 2026-04-22 · **Status:** Internal scoping memo

---

## The positioning problem (one paragraph)

The Opportunity Atlas (Chetty–Hendren–Friedman 2018) made one observation
into a research dynasty: **outcomes vary at the neighborhood level in
ways nobody had previously measured at scale, because the measurement
infrastructure didn't exist.** They built the infrastructure, made it
public, and a literature followed. The analogous gap in *finance* is
that we have very good data on **public capital deployment** (every
federal subsidy is, by law, eventually disclosed) and on **private
capital flows** (SEC, HMDA, CRA, EDGAR, county recorders) but they
sit in incompatible silos and almost nobody has stitched them together
spatially across programs. **A research portfolio that built the stitch
— and made it public — would occupy a category that currently has no
incumbent.**

The natural niche for me, given my thesis tooling (network centrality,
spatial heterogeneity, optimal transport), the Mining Externality Atlas
remote-sensing infrastructure, and the existing trade-data pipeline, is
to be **the person who treats the public-private finance interaction as
a spatial object** — not just at the U.S. tract level (Opportunity Atlas
analog) but globally, where MDB project finance, sovereign green bonds,
and bilateral aid create the same public-private dance.

NMTC is Phase 0 — a single program, single country, well-bounded — and
proves the workflow. The atlas is the multi-program, multi-country
expansion.

---

## The data universe, in priority order

### Tier 1 — programs already at my fingertips, U.S.

| program | source | granularity | status | what it's good for |
|---|---|---|---|---|
| **NMTC** | CDFI Fund Public Data Release | tract-level, transaction-level, 2001–2022 | **in hand** | leverage / mobilization measurement, rural-urban RDD |
| **LIHTC** | HUD LIHTC Database | project-level address, 1987–present, ~52,000 projects | freely downloadable | the largest U.S. place-based subsidy by $; same leverage measurement framework |
| **CRA bank lending** | FFIEC | tract-level small-business loan disclosures by bank | free, annual files since 1996 | private-capital response measurement; pairs with NMTC/LIHTC location |
| **HMDA** | CFPB | every U.S. mortgage origination, geocoded | free, ~10M obs/yr | residential capital flow; complements LIHTC |
| **SBA 7(a) and 504 loans** | SBA FOIA datasets | loan-level, geocoded | freely downloadable | private follow-on capital, ~700K loans/yr |

These five alone are enough for a first paper that compares NMTC and
LIHTC mobilization side-by-side at the tract level — a question Lerner
and others have asked but not in the integrated way the data actually
permits.

### Tier 2 — high-value U.S. programs that need pulling

| program | source | challenge | why pull it |
|---|---|---|---|
| **Opportunity Zones** | Treasury QOZ designations + IRS aggregate filings (Form 8997) | project-level investment is partial; tract OZ status is public | counterfactual to NMTC — same poverty-floor logic, no CDE intermediary, post-2017; cleaner test of "does the federal stamp matter without the CDE" |
| **IRA energy tax credits** | Treasury Section 6418 transfer registrations + DOE/EPA recipient lists | very fragmented; some recipient data published, some not | the largest active U.S. subsidy regime; manufacturing 45X, hydrogen 45V, clean-electricity 45Y/48E all have place-based bonus components |
| **CHIPS Act awards** | Commerce/NIST disclosure | concentrated in a few mega-deals | useful as case studies, not panel |
| **USDA Rural Development** | RD ProgressPRT, B&I Loan Guarantees | scattered across sub-programs | rural counterfactual to NMTC (USDA does what NMTC's rural mandate aspires to) |
| **EDA grants** | EDA quarterly award reports | annual workbooks, manual cleanup | small but place-based; pairs with infrastructure outcome data |
| **DOT BUILD/RAISE/INFRA** | DOT discretionary grant disclosures | per-project; need to merge across solicitations | infrastructure follow-on capital is identifiable through later GO-bond issuance |
| **EPA Brownfields** | EPA ACRES public download | site-level, geocoded | pre-development public spend; brownfield → NMTC stacking is a documented pattern |
| **Federal R&D obligations** | USAspending + NSF/NIH/DOD | already integrated on USAspending | spillovers / agglomeration story |

### Tier 3 — international, public side

| program | source | granularity |
|---|---|---|
| **World Bank IBRD/IDA** | World Bank Project & Operations Portal | project-level, much geocoded; AidData has the cleanest geocoded extension |
| **IFC private-sector arm** | IFC Project Disclosure Portal | project-level, country, sometimes geocoded |
| **EIB** | EIB Open Data | project-level, EU + neighborhood, very detailed |
| **ADB / AIIB / AfDB / IDB** | each MDB's own disclosure portal | project-level, varying quality |
| **AidData GeoQuery** | William & Mary AidData | every aid-funded project geocoded across a dozen donors, especially China |
| **EU Cohesion Funds** | EU Open Data Portal | project-level for ESF, ERDF, CF, ~1.4M projects |
| **OECD CRS** | OECD Creditor Reporting System | bilateral aid disaggregated by sector and country |
| **Green Climate Fund** | GCF Open Data | project-level climate finance |
| **Sovereign green/social bonds** | Climate Bonds Initiative free DB; ICMA tagged issuances | issuance-level, country-level, sometimes use-of-proceeds |

### Tier 4 — international, private side

| dataset | source | notes |
|---|---|---|
| **BIS Locational Banking Statistics** | BIS public + restricted | cross-border bank claims by counterparty country |
| **UNCTAD FDI** | UNCTAD Stat | bilateral country-pair FDI stocks + flows |
| **EMNES bond issuance** | restricted | EM corporate bond panel — paid but partial scrapes possible |
| **CEPII Gravity** | already in my data assets | trade + GDP + dyadic distance — use as gravity foundation for finance gravity |
| **fDi Markets** | FT subsidiary, paid | cross-border greenfield FDI, project-level — the gold standard for international |
| **Pitchbook / Crunchbase** | paid + partial public | venture / PE flow, founder-locatable |

### Tier 5 — outcome measurement (the spatial backbone)

These are needed to turn "money went here" into "did anything happen":

- **Census ACS, LEHD, QCEW, BEA local area** — U.S. demographics, jobs, business births/deaths
- **World Bank WDI + IMF subnational** — country / subnational outcomes
- **OECD subnational** — small-area economic indicators for OECD
- **GHSL, Hansen GFC, VIIRS / DMSP nightlights, GHS-POP** — remote-sensing outcome proxies for places where official statistics are missing or lagging *(already pulled in mita_viewer)*
- **GADM admin boundaries** — global administrative geometry

---

## Five papers that would write themselves with this stack

1. **NMTC vs. LIHTC: which subsidy mobilizes more private capital per public dollar, and where?** — Phase 0+1, U.S., uses Tier 1 alone.
2. **The Opportunity Zone counterfactual to NMTC.** — Same eligibility framework (LIC-style cutoffs), no intermediary CDE; isolates the role of the certified intermediary.
3. **Bank-level CRA lending response to federal place-based subsidy.** — Use NMTC/LIHTC location to identify exogenous variation in subsidized investment, then trace bank-level CRA loan response (HMDA + CRA disclosures). Speaks to the bank-local-public-good literature.
4. **The geography of MDB project finance and its private-capital crowding-in.** — World Bank + IFC + EIB project locations vs. country-level FDI / portfolio inflows. Spatial gravity model for project finance.
5. **The IRA spatial allocation: did the place-based bonus work?** — Once the IRA Section 45X / 45V / 48E credits have 3 years of recipient data, the energy-community bonus regions become a sharp RDD.

Papers 1 and 5 are the most immediately fundable (active U.S. policy debate). Paper 4 is the international flagship that establishes the global vantage. Papers 2 and 3 are within-U.S. mechanistic pieces.

---

## Phasing

**Phase 0 (now → 6 weeks):** finish NMTC paper. Pull ACS at tract level for the RDD. Run the FE specification, the bunching test, and the rural-interaction RDD. Submit to AEJ:Applied or J. Public Econ.

**Phase 1 (months 2–4):** pull LIHTC + HMDA + CRA bank disclosures. Build the *NMTC-LIHTC tract panel* (every tract × year × program × $). This is the data backbone for Papers 1, 2, 3.

**Phase 2 (months 4–8):** add Opportunity Zone designations + IRS partial release. Run Paper 2.

**Phase 3 (months 6–12):** AidData + World Bank + EIB pull. Build the international project-finance panel. Begin Paper 4.

**Phase 4 (year 2):** IRA recipient data when it matures. Run Paper 5.

**The Atlas itself:** the public-facing artifact (analogous to opportunityatlas.org) is the union of Phases 1 + 2 — a tract-level interactive map of "every federal place-based subsidy ever, by year, by program, with its observable private-capital follow-on." That's the brand-defining artifact. It ships at the end of Phase 2 and gets refreshed annually.

---

## What "becoming the global expert" actually requires

Three things, in order of difficulty:

1. **Three published papers in the space within 24 months.** The data work is necessary but not sufficient. Papers 1, 2, and 4 above are the credibility markers.

2. **The Atlas being the canonical public artifact.** Every researcher in this space cites Opportunity Atlas because the tooling lives somewhere. The same has to be true for the public-private finance integration — the atlas is *how you get cited by people who don't read your papers*.

3. **An institutional anchor.** Either an affiliation (CEPR, NBER once tenured, BREAD for the international piece, IPA for fieldable extensions), or a repeated co-author cluster that signals school. The Gonchar collaboration is the start; the next layer is one senior public-finance person (Glaeser? Diamond? Kline?) co-authoring at least one paper — pure status signaling.

The first two are within my control with focused execution. The third is the longer game.

---

## What I should NOT do

- **Don't try to build the Atlas before papers 1 and 2 ship.** Building infrastructure without first publishing what the infrastructure enables is the trap that kills careers.
- **Don't get pulled into one-off consulting on individual subsidy programs.** The portfolio value is in the *integration*, not the program-by-program expertise.
- **Don't release any of the proprietary-data versions** (paid Pitchbook scrapes, paid CoreLogic) — that closes off the academic-publication path. Only the freely-rebuildable tier becomes the Atlas.
