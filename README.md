# US NMTC — Blended-Finance First Look

**Author:** Ian Helfrich · **Date:** 2026-04-22 · **Status:** Working paper, pre-submission

This folder is a drag-and-drop starter package for our US blended-finance
empirical setting. Everything you need to tell the story — cleaned data,
figures, numbers, and the full research brief — lives here. The raw source
files and every cleaning step are documented so we (or anyone else) can
rebuild this from scratch with one command.

> **TL;DR for the brief:** US federal NMTC deployed **\$66.6B of public
> tax-credit capital** into **8,024 projects** worth **\$120.9B** total over
> FY2001–FY2022. That's **\$0.82 of private capital mobilized per federal
> dollar.** Non-metro tracts received **19.6% of dollars** (≈ the 20%
> statutory target) but each public dollar there pulled in *less* private
> capital than in metro tracts. The **non-metro leverage gap** (~0.12 at
> the median, ~0.26 at the mean) is our headline empirical object.

---

## Start here — the interactive viewer

For the quickest, most visual intro, open the browser-based presentation:

```bash
cd us_nmtc/
python3 -m http.server 8765
# then open http://localhost:8765/viewer/
```

It walks through the whole story: plain-English explainer, Cesium Earth
map with all 8,019 projects plotted, the leverage-gap figures, a CDE
leaderboard, and the econometric specifications rendered in KaTeX.

See [`viewer/README.md`](viewer/README.md) for details.

---

## Or — the narrative in 5 figures

| # | File | What it shows |
|---|---|---|
| 1 | `figures/1_allocation_timeseries.png` | Annual NMTC \$ deployed, stacked metro vs. non-metro — program ramps up through 2010, then ~\$3–5 B/yr |
| 2 | `figures/2_non_metro_share_timeseries.png` | Non-metro share of \$ each year vs. the 20% statutory line — the mandate binds early, over-achieves 2013+ |
| 3 | `figures/3_leverage_distribution.png` | Leverage ratio (project cost / QLICI) — non-metro mass sits at the 1.0× floor; metro has a fatter right shoulder |
| 4 | `figures/4_qalicb_type_by_metro.png` | QALICB-type mix — metro skews Real-Estate (~40%); non-metro skews operating-business NRE (~65%) |
| 5 | `figures/5_leverage_by_qalicb_metro.png` | Leverage gap persists **within every QALICB type**, so the gap isn't a composition artefact |

Drop any of them straight into slides or a memo.

---

## Headline numbers at a glance

| metric | value |
|---|---:|
| Program years covered | FY 2001–2022 |
| QLICI transactions | **19,907** |
| Unique projects | **8,024** |
| Total QLICI deployed | **\$66.6 B** |
| Total project cost | **\$120.9 B** |
| **Mobilization ratio** (private \$ / public \$) | **0.82×** |
| Non-metro share (transactions / \$) | 19.3% / 19.6% |
| Statutory non-metro target | 20.0% |
| Median leverage — metro | **1.19×** |
| Median leverage — non-metro | **1.07×** |
| **Leverage gap (metro − non-metro)** | **+0.12** |

All machine-readable in [`data/processed/headline.json`](data/processed/headline.json).

---

## Folder layout

```
us_nmtc/
├── README.md                       ← you are here
├── DATA_DICTIONARY.md              ← every column in every CSV, explained
├── PROVENANCE.md                   ← how to rebuild from scratch, SHA256s, licenses
├── requirements.txt                ← Python dependencies
│
├── briefs/
│   └── katia_nmtc_v1.md            ← full first-look research brief (read first)
│
├── data/
│   ├── raw/                        ← unmodified source files from CDFI Fund
│   │   ├── NMTC_Public_Data_Release_FY2003-FY2022.xlsx
│   │   └── NMTC_Public_Data_Release_Summary_FY2003-FY2022.pdf
│   ├── cache/                      ← gazetteer cache (downloaded on demand)
│   └── processed/                  ← cleaned outputs (all derived, all reproducible)
│       ├── nmtc_transactions.csv       19,907 QLICI-level rows
│       ├── nmtc_projects.csv            8,024 project-level rows (with leverage)
│       ├── summary_by_metro.csv         metro vs non-metro rollup (projects)
│       ├── summary_by_metro_tx.csv      same rollup at QLICI level
│       ├── summary_by_qalicb_type.csv   RE / NRE / SPE / CDE × metro
│       ├── summary_by_year.csv          annual series, metro-split
│       ├── top_cdes.csv                 top 20 CDEs by $ with non-metro share
│       ├── leverage_distribution.csv    leverage-ratio summary by metro
│       ├── multi_cde_by_metro.csv       deal-complexity proxy × metro
│       └── headline.json                the headline table above, as JSON
│
├── scripts/
│   ├── describe_nmtc.py                 raw → processed pipeline
│   ├── make_figures.py                  processed → figures
│   ├── build_viewer_data.py             processed → viewer JS bundles
│   └── explore_nmtc_walkthrough.py      annotated learning walkthrough
│
├── figures/
│   ├── 1_allocation_timeseries.png
│   ├── 2_non_metro_share_timeseries.png
│   ├── 3_leverage_distribution.png
│   ├── 4_qalicb_type_by_metro.png
│   └── 5_leverage_by_qalicb_metro.png
│
└── viewer/                         ← the interactive browser presentation
    ├── index.html
    ├── css/style.css
    ├── js/{app.js, map.js}
    └── data/{headline,projects,states,top_cdes}.js
```

---

## How to run it (one-time setup)

```bash
cd us_nmtc/
python3 -m venv .venv                       # optional but recommended
source .venv/bin/activate
pip install -r requirements.txt
```

Then to rebuild everything:

```bash
python3 scripts/describe_nmtc.py            # raw .xlsx  →  cleaned CSVs + headline.json
python3 scripts/make_figures.py             # cleaned CSVs  →  5 PNG figures
python3 scripts/build_viewer_data.py        # cleaned CSVs  →  viewer JS bundles
python3 -m http.server 8765                 # serve the viewer at localhost:8765/viewer/
```

To learn what the data looks like interactively:

```bash
python3 scripts/explore_nmtc_walkthrough.py
```

That walkthrough is over-commented on purpose — every block explains what
it's doing and why. Treat it as a readable tutorial, not production code.

---

## Where to look next, in order

1. **[`briefs/katia_nmtc_v1.md`](briefs/katia_nmtc_v1.md)** — the full research brief: what we can say, what we *can't* say with NMTC alone, the identification strategy, and the proposed next three moves.
2. **[`DATA_DICTIONARY.md`](DATA_DICTIONARY.md)** — before you interpret any number, check here for the column definition and units.
3. **[`PROVENANCE.md`](PROVENANCE.md)** — the paranoia file: URLs, SHA256 hashes, license, every cleaning decision, every software version. Needed to cite or replicate.

---

## Key caveats (read before quoting numbers)

- **All dollars are nominal.** No deflator applied yet. If we want real \$2022, we'll need a CPI join — easy but not done.
- **`year` is origination year** of the QLICI, not fiscal year of the allocation. The data release is titled "FY2003–FY2022" because that's the allocation-award window, but some QLICIs originate as early as 2001.
- **Leverage is capped (winsorized) at 1×–20×** in `leverage_win`. The raw `leverage_ratio` is also preserved. A ~1% of projects report cost < QLICI (ratio < 1), which is likely a reporting quirk; we clip to 1.0 for the summary stats.
- **Metro/non-metro is CDFI's 2020-census designation**, not USDA RUCA. A finer rurality gradient is the next merge (see brief).
- **CDE identity is as-reported**; affiliated CDEs (e.g. bank subsidiaries, multiple vehicles per sponsor) are not yet consolidated.

---

## Data citation

CDFI Fund, U.S. Department of the Treasury. *New Markets Tax Credit Public
Data Release, FY2003–FY2022.* Released June 2024.
<https://www.cdfifund.gov/documents/data-releases>

Full provenance, SHA256 hashes, and license terms in
[`PROVENANCE.md`](PROVENANCE.md).
