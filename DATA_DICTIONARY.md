# Data Dictionary — US NMTC First-Look Package

Every column in every file under `data/processed/`, plus the source columns
from the CDFI Fund release that feed them. Read this before quoting any
number off a CSV.

All monetary fields are in **nominal US dollars** unless otherwise noted.
Totals ending in `_m` are in **millions of USD**; totals ending in `_b` are
in **billions of USD**.

---

## 1. `data/raw/NMTC_Public_Data_Release_FY2003-FY2022.xlsx`

The CDFI Fund publishes the data as a single workbook with two relevant sheets.
We only touch the columns we rename; the rest are preserved in the processed
CSVs under their original names.

### Sheet `Financial Notes 1 - Data Set PU` (19,907 rows)

One row per QLICI (Qualified Low-Income Community Investment), i.e. one row per
financial transaction between a CDE and a QALICB. A single project can have
multiple QLICIs (multiple CDEs, multiple tranches).

| raw column | renamed to | type | description |
|---|---|---|---|
| `Project ID` | `project_id` | int | Foreign key to the project sheet |
| `Transaction ID` | `transaction_id` | string | Unique identifier for the QLICI |
| `2020 Census Tract` | `tract_fips` | int64 | 11-digit 2020-census tract GEOID (state + county + tract) |
| `Metro/Non-Metro, 2020 Census` | `metro_flag` | string | `"Metro"` or `"Non-metro"` / `"Non-Metro"` (inconsistent capitalization in source — we normalize to lowercase `metro`/`non_metro` in the added `metro` column) |
| `Origination Year` | `year` | int | Calendar year the QLICI was originated (2001–2022) |
| `Community Development Entity (CDE) Name` | `cde_name` | string | Legal name of the CDE that made the QLICI |
| `QLICI Amount` | `qlici_amount` | float | Dollars of NMTC-financed capital deployed in this transaction |
| `City`, `State`, `Zip Code` | `city`, `state`, `zip` | string / int | QALICB location |
| `Purpose of Investment` | `purpose` | string | CDFI's 9-category classification of what the QLICI funded (e.g. `"Real Estate – Construction/Permanent/Acquisition w/o Rehab – Commercial"`) |
| `QALICB Type` | `qalicb_type` | string | One of `"RE"`, `"NRE"`, `"SPE"`, `"CDE"` — see below |

### Sheet `Projects 2 - Data Set PUBLISH.P` (8,024 rows)

One row per project. Projects are the economic unit: the physical development
or business. One project can aggregate multiple QLICIs.

| raw column | renamed to | type | description |
|---|---|---|---|
| `Project ID` | `project_id` | int | Primary key |
| `2020 Census Tract` | `tract_fips` | int64 | 11-digit 2020-census tract GEOID |
| `Metro/Non-Metro, 2020 Census` | `metro_flag` | string | As above |
| `Origination Year` | `year` | int | Year of first QLICI for this project |
| `Community Development Entity (CDE) Name` | `cde_name` | string | First / reporting CDE |
| `Project QLICI Amount` | `project_qlici` | float | Sum of all QLICIs to this project |
| `Estimated Total Project Cost` | `project_cost` | float | CDE's estimate of total project cost (public + private) |
| `City`, `State`, `Zip Code` | `city`, `state`, `zip` | string / int | Project location |
| `QALICB Type` | `qalicb_type` | string | One of `"RE"`, `"NRE"`, `"SPE"`, `"CDE"` |
| `Multi-CDE` | `multi_cde` | string (`YES`/`NO`) | Whether multiple CDEs participated |
| `Multi-Tract Project` | `multi_tract` | string (`YES`/`NO`) | Whether project spans multiple census tracts |

### QALICB type codes (from CDFI's summary PDF)

| code | meaning | count of projects |
|---|---|---:|
| `RE` | Real Estate QALICB — the business's main asset is real property | 2,862 |
| `NRE` | Non-Real-Estate — operating business (manufacturing, services) | 3,775 |
| `SPE` | Special-Purpose Entity — a QALICB formed specifically for one deal | 1,296 |
| `CDE` | Loan to another CDE (a rare pass-through structure) | 91 |

---

## 2. `data/processed/nmtc_transactions.csv` — 19,907 rows

Every column from the raw transaction sheet, plus:

| added column | type | description |
|---|---|---|
| `metro` | string | Normalized metro flag: `"metro"` / `"non_metro"` / `"unknown"` |

---

## 3. `data/processed/nmtc_projects.csv` — 8,024 rows

Every column from the raw project sheet, plus:

| added column | type | description |
|---|---|---|
| `metro` | string | Normalized metro flag (as above) |
| `leverage_ratio` | float | `project_cost / project_qlici` — raw, unwinsorized |
| `leverage_win` | float | `leverage_ratio` clipped to [1.0, 20.0] — used for all summary statistics |

**Definition of leverage here:** *total project cost per dollar of NMTC
tax-credit-subsidized QLICI capital.* A leverage ratio of 1.0 means the
project was 100% NMTC-financed; a ratio of 2.0 means NMTC provided half the
capital and other sources provided the other half. The implied **mobilization
ratio** (private dollars per public dollar) is `leverage_ratio − 1`.

**Why winsorize at [1, 20]?** Roughly 1% of rows report `project_cost <
project_qlici` (ratio < 1), which is a reporting artefact — the project
cost estimate should bound the QLICI by construction. About 0.3% of rows
report ratios > 20, typically from very small QLICIs into very large
real-estate stacks; these dominate the mean if left unclipped. Capping
at [1, 20] preserves the shape of the distribution but keeps the summary
statistics comparable.

---

## 4. `data/processed/summary_by_metro.csv` — 2 rows (project-level)

| column | type | description |
|---|---|---|
| `metro` | string | `metro` / `non_metro` |
| `n_projects` | int | Number of projects |
| `qlici_total_m` | float | Sum of `project_qlici`, in \$M |
| `project_cost_total_m` | float | Sum of `project_cost`, in \$M |
| `leverage_mean` | float | Mean of `leverage_win` |
| `leverage_median` | float | Median of `leverage_win` |
| `mobilization_ratio` | float | `(project_cost_total_m − qlici_total_m) / qlici_total_m` — private \$ mobilized per public \$ |

---

## 5. `data/processed/summary_by_metro_tx.csv` — 2 rows (transaction-level)

| column | type | description |
|---|---|---|
| `metro` | string | `metro` / `non_metro` |
| `n_transactions` | int | Number of QLICIs |
| `qlici_total_m` | float | Sum of `qlici_amount`, in \$M |
| `qlici_mean_m` | float | Mean QLICI amount, in \$M |
| `qlici_median_m` | float | Median QLICI amount, in \$M |

---

## 6. `data/processed/summary_by_qalicb_type.csv` — 8 rows (project-level)

| column | type | description |
|---|---|---|
| `qalicb_type` | string | One of `RE` / `NRE` / `SPE` / `CDE` |
| `metro` | string | `metro` / `non_metro` |
| `n` | int | Number of projects in cell |
| `qlici_total_m` | float | Sum of `project_qlici`, in \$M |
| `leverage_mean` | float | Mean of `leverage_win` within cell |

---

## 7. `data/processed/summary_by_year.csv` — ~44 rows (year × metro)

| column | type | description |
|---|---|---|
| `year` | int | Origination year (2001–2022) |
| `metro` | string | `metro` / `non_metro` |
| `n` | int | Number of QLICIs |
| `qlici_m` | float | Sum of `qlici_amount`, in \$M |

---

## 8. `data/processed/top_cdes.csv` — 20 rows

Top 20 CDEs by total QLICI \$ deployed.

| column | type | description |
|---|---|---|
| `cde_name` | string | Legal name of the CDE |
| `n_tx` | int | Number of QLICIs |
| `total_qlici_m` | float | Sum of `qlici_amount`, in \$M |
| `n_non_metro` | int | Number of QLICIs in non-metro tracts |
| `non_metro_share` | float | `n_non_metro / n_tx` — CDE's rural-allocation share |

Note: the non_metro_share varies wildly across the top 20 (from <5% for
some big-bank subsidiaries to >70% for Montana Community Development Corp
and Rural Development Partners LLC). This is the **CDE-level heterogeneity**
we flag as the mechanism candidate in the brief.

---

## 9. `data/processed/leverage_distribution.csv`

Output of `pandas.DataFrame.describe()` on `leverage_win`, split by metro.

| column | type | description |
|---|---|---|
| `metro` | string | `metro` / `non_metro` (index) |
| `count` | int | Number of projects |
| `mean` | float | Mean of `leverage_win` |
| `std` | float | Standard deviation |
| `min` | float | Min (= 1.0 by winsorization floor) |
| `25%`, `50%`, `75%` | float | Quartiles |
| `max` | float | Max (≤ 20 by winsorization cap) |

---

## 10. `data/processed/multi_cde_by_metro.csv` — 2 rows

Crosstab of project-level `multi_cde` flag by `metro`, row-normalized.

| column | type | description |
|---|---|---|
| (index: `metro`) | string | `metro` / `non_metro` |
| `NO` | float | Share of projects with one CDE |
| `YES` | float | Share of projects with multiple CDEs |

---

## 11. `data/processed/headline.json`

The headline table from the brief, as a flat JSON object. Keys:

| key | type | description |
|---|---|---|
| `program_years` | `[int, int]` | Min and max observed origination year |
| `n_transactions_total` | int | 19,907 |
| `n_projects_total` | int | 8,024 |
| `total_qlici_billion_usd` | float | 66.61 |
| `total_project_cost_billion_usd` | float | 120.9 |
| `non_metro_transaction_share_pct` | float | 19.31 |
| `non_metro_project_share_pct` | float | 19.45 |
| `non_metro_qlici_dollar_share_pct` | float | 19.57 |
| `statutory_non_metro_target_pct` | float | 20.0 |
| `median_leverage_metro` | float | 1.19 |
| `median_leverage_non_metro` | float | 1.07 |
| `leverage_gap_metro_minus_nonmetro` | float | 0.12 |

---

## What we did NOT keep

To keep the processed CSVs compact we dropped a handful of operational
columns from the raw release that don't affect the first-look analysis
(e.g. QEI ID cross-references, some administrative flags that are
constant or near-constant). Nothing is lost — the raw xlsx is in
`data/raw/` unmodified, and the pipeline (`scripts/describe_nmtc.py`)
is a single file you can grep for any column.
