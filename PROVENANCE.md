# Provenance & Reproducibility — US NMTC Package

This file is the paranoia record: every file, its origin, its hash, its
license, and the exact steps to recreate all processed outputs from the raw
source. If anything in `data/processed/` or `figures/` ever disagrees with
what you think it should say, start here.

---

## 1. Data source

### Primary release

- **Dataset:** *New Markets Tax Credit Public Data Release, FY2003–FY2022*
- **Publisher:** Community Development Financial Institutions (CDFI) Fund,
  U.S. Department of the Treasury
- **Release date:** June 2024
- **Landing page:** <https://www.cdfifund.gov/documents/data-releases>
- **Direct XLSX URL (at time of access):**
  `https://www.cdfifund.gov/sites/cdfi/files/2024-06/NMTC_Public_Data_Release_FY2003-FY2022.xlsx`
- **Direct Summary PDF URL (at time of access):**
  `https://www.cdfifund.gov/sites/cdfi/files/2024-06/NMTC_Public_Data_Release_Summary_FY2003-FY2022.pdf`
- **Date we downloaded:** 2026-04-22
- **License:** US federal government public-domain work (17 U.S.C. § 105). No
  usage restrictions. CDFI Fund requests the attribution shown in the
  citation below.

### Integrity hashes (SHA-256)

These are the exact bytes we analyzed. If you redownload and the hashes
change, CDFI Fund has republished the release and our numbers may shift.

```
NMTC_Public_Data_Release_FY2003-FY2022.xlsx
  fa709714e93d67356b90a1c0f98dbed71ec1998d0b686e969ad3bacafc112683

NMTC_Public_Data_Release_Summary_FY2003-FY2022.pdf
  6e205240f31670fe66095d506f6db08fadd65575b2f198ab52d95882364a1433
```

Verify with:

```bash
shasum -a 256 data/raw/NMTC_Public_Data_Release_FY2003-FY2022.xlsx
shasum -a 256 data/raw/NMTC_Public_Data_Release_Summary_FY2003-FY2022.pdf
```

### Citation

> CDFI Fund, U.S. Department of the Treasury. *New Markets Tax Credit
> Public Data Release, FY2003–FY2022.* Released June 2024.
> <https://www.cdfifund.gov/documents/data-releases>

---

## 2. Software environment

Everything runs with a stock Python 3.9+ install and four packages.

| package | version we used | why |
|---|---|---|
| Python | 3.9.6 | system interpreter (macOS); any 3.9–3.13 should work |
| pandas | 2.3.3 | dataframe cleaning and rollups |
| numpy | 2.0.2 | numeric helpers (quantiles, histograms) |
| matplotlib | 3.9.4 | the 5 PNG figures |
| openpyxl | 3.1.5 | reading the CDFI `.xlsx` source |

All pinned as lower bounds in `requirements.txt`. Any reasonably recent
version of these four should reproduce the numbers exactly — the cleaning
uses only stable API surface (`read_excel`, `groupby`, `agg`, `clip`,
`quantile`, `describe`, `pd.crosstab`).

Install with:

```bash
pip install -r requirements.txt
```

---

## 3. The pipeline

Two scripts, run in this order:

### Step 1 — `scripts/describe_nmtc.py` (raw → processed)

**Reads:**
- `data/raw/NMTC_Public_Data_Release_FY2003-FY2022.xlsx`
  - Sheet `Financial Notes 1 - Data Set PU`  → QLICI-level (19,907 rows)
  - Sheet `Projects 2 - Data Set PUBLISH.P`   → project-level (8,024 rows)

**Cleaning steps applied (in order):**

1. **Strip whitespace from column headers** on both sheets.
2. **Rename** source columns to snake-case short names (full mapping in
   `DATA_DICTIONARY.md`, sections 1–3).
3. **Normalize the metro flag.** CDFI's source column
   `"Metro/Non-Metro, 2020 Census"` contains three literal strings —
   `"Metro"`, `"Non-metro"`, and `"Non-Metro"` (inconsistent capitalization).
   We fold them into a new lowercase `metro` column with three values:
   `metro`, `non_metro`, or `unknown` (for the rare NaN).
4. **Coerce dollar columns to numeric** with `pd.to_numeric(..., errors="coerce")`.
   This handles the handful of rows where CDFI exports dollars as strings
   with commas. Any coercion failure becomes NaN.
5. **Compute leverage ratio** at the project level:
   `leverage_ratio = project_cost / project_qlici`.
6. **Winsorize leverage** into `leverage_win = leverage_ratio.clip(1.0, 20.0)`.
   Both columns are preserved so you can un-winsorize at will.
7. **Write the cleaned transaction- and project-level CSVs.**
8. **Group-by rollups** produce the 7 summary CSVs (by metro, by qalicb_type,
   by year, top 20 CDEs, leverage distribution, multi-CDE).
9. **Emit `headline.json`** with the numbers quoted in the brief.

**Writes:**

```
data/processed/
├── nmtc_transactions.csv
├── nmtc_projects.csv
├── summary_by_metro.csv
├── summary_by_metro_tx.csv
├── summary_by_qalicb_type.csv
├── summary_by_year.csv
├── top_cdes.csv
├── leverage_distribution.csv
├── multi_cde_by_metro.csv
└── headline.json
```

### Step 2 — `scripts/make_figures.py` (processed → figures)

**Reads:**
- `data/processed/nmtc_projects.csv`
- `data/processed/nmtc_transactions.csv`

**Renders:** 5 PNGs at 160 DPI, white background, DejaVu Sans font, with a
fixed metro / non-metro colour palette (`#1f77b4` blue, `#d62728` red). Fully
deterministic — same inputs, pixel-identical outputs.

**Writes:**

```
figures/
├── 1_allocation_timeseries.png
├── 2_non_metro_share_timeseries.png
├── 3_leverage_distribution.png
├── 4_qalicb_type_by_metro.png
└── 5_leverage_by_qalicb_metro.png
```

---

## 4. Recreate everything from scratch

From a fresh machine with Python 3.9+ and an internet connection:

```bash
# 1. Clone or copy the us_nmtc/ folder
cd us_nmtc/

# 2. Create a virtualenv (optional but recommended)
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (If data/raw/ is empty) — re-download the source files
mkdir -p data/raw
curl -L -o data/raw/NMTC_Public_Data_Release_FY2003-FY2022.xlsx \
  "https://www.cdfifund.gov/sites/cdfi/files/2024-06/NMTC_Public_Data_Release_FY2003-FY2022.xlsx"
curl -L -o data/raw/NMTC_Public_Data_Release_Summary_FY2003-FY2022.pdf \
  "https://www.cdfifund.gov/sites/cdfi/files/2024-06/NMTC_Public_Data_Release_Summary_FY2003-FY2022.pdf"

# 5. Verify hashes
shasum -a 256 data/raw/NMTC_Public_Data_Release_FY2003-FY2022.xlsx
#   expect:  fa709714e93d67356b90a1c0f98dbed71ec1998d0b686e969ad3bacafc112683

# 6. Build processed data + headline numbers
python3 scripts/describe_nmtc.py

# 7. Render the 5 figures
python3 scripts/make_figures.py
```

Total wall time: ~20 seconds on a laptop.

---

## 5. Known quirks, caveats, and things I wish were cleaner

These are the footnotes we'll want in any paper draft:

1. **Year coverage is 2001–2022, not 2003–2022.** The release title says
   "FY2003–FY2022" because 2003 is the first allocation-award year, but some
   QLICIs originated earlier (2001–2002) under early allocation rounds and
   appear in the transaction sheet.
2. **Dollar amounts are nominal.** No CPI adjustment. If the brief needs to
   move to real 2022 dollars, join BLS-CPI-U and deflate; straightforward but
   not done here.
3. **~1% of projects report `project_cost < project_qlici`** (leverage < 1).
   This is likely cost-estimate staleness at reporting time. Winsorization to
   1.0 treats these as "100% NMTC-financed".
4. **~0.3% of projects report `leverage_ratio > 20`.** These are real but
   rare — small QLICIs into very large commercial RE stacks. Winsorization
   to 20 keeps them in the sample but stops them from dominating the mean.
5. **Metro / non-metro is CDFI's pre-classified flag** using the 2020 census
   MSA/CBSA definition. It is binary; a RUCA-based rurality gradient is
   the next merge (see brief §"Proposed next moves").
6. **CDE identity is as-reported** by the CDE itself; bank-affiliated CDEs
   often use multiple sub-entities (e.g. `USBCDE, LLC` vs. related US Bank
   subsidiaries) and are not consolidated. Hand-classification of the top 50
   is the next qualitative step.
7. **`tract_fips` is the 2020 census tract** for the project's primary
   address. For multi-tract projects the `multi_tract` flag is set but the
   secondary tracts are not in the public release.
8. **Sign convention for leverage.** Leverage = `total / QLICI` ≥ 1.0 means
   total project cost ≥ QLICI. The implied **private share** is
   `(total − QLICI) / total = 1 − 1/leverage`. The **mobilization ratio**
   is `(total − QLICI) / QLICI = leverage − 1`. Both are used in the brief
   and need the reader to know which is which.

---

## 6. What's NOT yet in this package

Items explicitly scoped out of this first-look release:

- **Census-ACS tract merge** — poverty rate, MFI, population, needed for the
  LIC-eligibility RDD running variable.
- **USDA RUCA codes** — continuous rurality rather than binary metro flag.
- **CDE institutional type** — hand-classified {bank subsidiary / nonprofit
  CDFI / for-profit specialized / government} for the top 50 CDEs.
- **Allocation-level data** — public release covers QLICIs (the downstream
  deployment). Upstream allocation awards to CDEs are in a separate dataset.
- **Deflation to real dollars.**

All five are in the brief's "next moves" section.

---

## 7. Version history

| date | change |
|---|---|
| 2026-04-22 | v1 first-look package: cleaning pipeline, 5 figures, brief, full docs. |
