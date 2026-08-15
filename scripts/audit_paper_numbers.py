"""
Tie every load-bearing number in the manuscript back to the pipeline output
that produced it.

The standing rule on this project is that nothing is taken as given and
every displayed number originates in the repository pipeline. That rule was
enforced by care rather than by machinery, which is the same as not being
enforced: a number can be correct when written and become stale the moment
an upstream script is re-run, and nothing in the build notices.

This script closes that hole. Each entry in CLAIMS names a string exactly
as it appears in a .tex source and the JSON field it must equal. A claim
passes when the source value, rounded half-up to the precision the
manuscript prints, equals the printed number exactly. The audit fails if the string is missing from the file, if it
appears more than once where a unique anchor was intended, or if the value
disagrees with its source. A failure is either a stale manuscript or a
changed result, and both are things the author must see.

Numbers deliberately excluded, because no pipeline output backs them or they
describe the procedure rather than a result: statutory facts (the 39% credit
rate, the 20% target), dates, citation years, specification labels,
conventional significance thresholds, procedural replication counts, and
round counts stated in words.

Exit status is 0 when every claim passes and 1 otherwise, so this can gate
a build.

Run:  uv run --no-project --with numpy python scripts/audit_paper_numbers.py
"""
from __future__ import annotations

import csv
import json
import re
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEC = ROOT / "paper" / "sections"
REG = ROOT / "data" / "processed" / "regressions"
PROCESSED = ROOT / "data" / "processed"

_cache: dict[str, dict] = {}


def _csv_value(value: str):
    """Coerce numeric CSV cells while leaving identifiers and labels alone."""
    if re.fullmatch(r"[-+]?\d+", value):
        return int(value)
    if re.fullmatch(r"[-+]?(?:\d+\.\d*|\d*\.\d+)(?:[Ee][-+]?\d+)?", value):
        return float(value)
    return value


def src(name: str) -> dict:
    if name not in _cache:
        candidates = (REG / name, PROCESSED / name, ROOT / name)
        path = next((p for p in candidates if p.is_file()), None)
        if path is None:
            raise FileNotFoundError(f"pipeline source not found: {name}")
        if path.suffix == ".csv":
            with path.open(newline="") as handle:
                rows = [
                    {key: _csv_value(value) for key, value in row.items()}
                    for row in csv.DictReader(handle)
                ]
            _cache[name] = {"rows": rows}
        else:
            _cache[name] = json.loads(path.read_text())
    return _cache[name]


def cde_transaction_profile(rows: list[dict]) -> dict[str, float | int]:
    """Recompute the CDE-distribution descriptives from the transaction output."""
    books: dict[str, dict[str, float | int]] = {}
    for row in rows:
        book = books.setdefault(
            row["cde_name"], {"n": 0, "n_nonmetro": 0, "qlici": 0.0})
        book["n"] += 1
        book["n_nonmetro"] += row["metro"] == "non_metro"
        book["qlici"] += row["qlici_amount"]

    eligible = [book for book in books.values() if book["n"] >= 5]
    qlici = sorted((book["qlici"] for book in books.values()), reverse=True)
    nonmetro_shares = [book["n_nonmetro"] / book["n"] for book in eligible]
    return {
        "n_cdes": len(books),
        "n_cdes_at_least_five": len(eligible),
        "top_twenty_qlici_share_pct": 100 * sum(qlici[:20]) / sum(qlici),
        "never_nonmetro_pct": (
            100 * sum(book["n_nonmetro"] == 0 for book in eligible) / len(eligible)
        ),
        "at_least_four_fifths_nonmetro_pct": (
            100
            * sum(share >= 0.8 for share in nonmetro_shares)
            / len(eligible)
        ),
        "min_nonmetro_share_pct": 100 * min(nonmetro_shares),
        "max_nonmetro_share_pct": 100 * max(nonmetro_shares),
    }


def dig(obj, path: str):
    """Follow a dotted path with [i] indexing."""
    cur = obj
    for part in path.split("."):
        m = re.match(r"^([^\[]+)(?:\[(\d+)\])?$", part)
        assert m, f"bad path part {part!r}"
        key, idx = m.group(1), m.group(2)
        cur = cur[key]
        if idx is not None:
            cur = cur[int(idx)]
    return cur


# (file, literal as typeset, json file, path, transform)
# transform: how the pipeline value is turned into the displayed number.
# A claim passes when the source value, rounded half-up to the precision
# the manuscript prints, equals the printed number exactly.
CLAIMS: list[tuple] = [
    # ── the decomposition, Section 5.1 ─────────────────────────────────
    ("05-results", "$-0.262$", "referee_fixes.json", "F1_gelbach.beta_M0",
     lambda v: v),
    ("05-results", "collapses the rural coefficient\nto $-0.047$", "referee_fixes.json",
     "F1_gelbach.beta_full", lambda v: v),
    ("05-results", "the $-0.216$ movement", "referee_fixes.json",
     "F1_gelbach.beta_M0", lambda v: v - src("referee_fixes.json")["F1_gelbach"]["beta_full"]),
    ("05-results", "CDE identity\ncontributes $-0.185$", "referee_fixes.json",
     "F1_gelbach.contrib_cde", lambda v: v),
    ("05-results", "(86\\% of the movement", "referee_fixes.json",
     "F1_gelbach.share_of_gap_from_cde", lambda v: v * 100),
    ("05-results", "QALICB type $-0.041$", "referee_fixes.json",
     "F1_gelbach.contrib_qalicb", lambda v: v),
    ("05-results", "origination year a small\noffsetting $+0.010$", "referee_fixes.json",
     "F1_gelbach.contrib_year", lambda v: v),
    ("05-results", "82\\% of the raw\ngap", "referee_fixes.json",
     "F2_bootstrap.selection_share_hat", lambda v: v * 100),

    # ── precision and margins, Section 5.2 ─────────────────────────────
    ("05-results", "larger than $0.213$", "referee_fixes.json",
     "F3_power.mean_rejectable_penalty", lambda v: v),
    ("05-results", "CDE-clustered standard error of $0.101$", "referee_fixes.json",
     "F3_power.mean_se_cde_cluster", lambda v: v),
    ("05-results", "27.4\\% of projects record no capital", "referee_fixes.json",
     "F4_floor_1p001.share_at_floor", lambda v: v * 100),
    ("05-results", "$1.8$ percentage points less likely", "referee_fixes.json",
     "F4_floor_1p001.extensive_beta", lambda v: abs(v) * 100),
    ("05-results", "the rural coefficient is\n$-0.039$", "referee_fixes.json",
     "F4_floor_1p001.intensive_beta", lambda v: v),

    # ── robustness, Section 5.4 ────────────────────────────────────────
    ("05-results", "\\emph{larger} ($-0.338$", "robustness.json",
     "R1_raw_M0.beta", lambda v: v),
    ("05-results", "remains null ($-0.216$", "robustness.json",
     "R1_raw_M4.beta", lambda v: v),
    ("05-results", "within-CDE penalty at $-3.2\\%$", "robustness.json",
     "R2_log_M4.beta", lambda v: v * 100),

    # ── the residual scan, Section 5.5 ─────────────────────────────────
    ("05-results", "projects at $-0.395$", "residual_analysis.json",
     "cells", lambda v: next(c["beta"] for c in v
                             if c.get("estimated") and c["cell"] == "QALICB type RE")),
    ("05-results", "a $p$-value of $1.6 \\times 10^{-5}$", "residual_analysis.json",
     "min_p", lambda v: v * 1e5),

    # ── the mandate test, Section 5.6 ──────────────────────────────────
    ("05-results", "$\\hat B = -0.0006$", "bunching_stats.json",
     "excess_mass_B", lambda v: v),
    ("05-results", "$-2.2\\%$ of the counterfactual mass", "bunching_stats.json",
     "excess_mass_pct", lambda v: v),
    ("05-results", "gives excess mass of $+0.005$", "review_round2.json",
     "G2_full_dollar.B", lambda v: v),
    ("05-results", "across 291 intermediaries", "review_round2.json",
     "G3_post2007_count.n_cde", lambda v: v),

    # ── the abstract, which is what most readers will check ────────────
    ("00-abstract", "\\$66.6 billion", "review_round2.json",
     "G4_denominators.qlici_total_musd", lambda v: v / 1000),
    ("00-abstract", "\\$120.9 billion", "review_round2.json",
     "G4_denominators.project_cost_total_musd", lambda v: v / 1000),
    ("00-abstract", "\\$0.82 of other capital", "review_round2.json",
     "G4_denominators.other_capital_per_qlici_dollar", lambda v: v),
    ("00-abstract", "roughly \\$2.09", "review_round2.json",
     "G4_denominators.other_capital_per_credit_dollar", lambda v: v),
    ("00-abstract", "8{,}024 projects", "referee_fixes.json",
     "n_analysis", lambda v: v),
    ("05-results", "$+0.001$ in dollars", "review_round2.json",
     "G3_post2007_dollar.B", lambda v: v),

    # ── median inference, Section 5.2 (added with the bootstrap) ───────
    ("05-results", "larger than $0.016$", "median_inference.json",
     "equivalence_bound_cluster_bootstrap", lambda v: v),
    ("05-results", "a standard error of $0.0093$", "median_inference.json",
     "se_cluster_bootstrap", lambda v: v),
    ("05-results", "against the asymptotic\n$0.0076$", "median_inference.json",
     "se_asymptotic", lambda v: v),
    ("05-results", "returns a two-sided $p$ of $0.085$", "median_inference.json",
     "randomization_p_two_sided", lambda v: v),
    ("05-results", "a $26.9\\%$\npoint mass at exactly $1.0$", "median_inference.json",
     "outcome_mass_at_one", lambda v: v * 100),
    ("05-results", "unconditional median of\n$1.159$", "median_inference.json",
     "outcome_median", lambda v: v),
    ("05-results", "where $91\\%$ of permutations", "median_inference.json",
     "randomization_share_pinned_at_zero", lambda v: v * 100),
    ("05-results", "reaching $-0.129$ at the $0.90$ quantile",
     "median_inference.json", "quantile_sweep",
     lambda v: next(r["beta"] for r in v if r["q"] == 0.90)),
    ("05-results", "and $-0.200$ at $0.95$", "median_inference.json",
     "quantile_sweep", lambda v: next(r["beta"] for r in v if r["q"] == 0.95)),
    ("05-results", "standard errors of $0.125$", "median_inference.json",
     "quantile_sweep",
     lambda v: next(r["se_cluster_bootstrap"] for r in v if r["q"] == 0.90)),
    ("05-results", "$0.215$ at those two quantiles", "median_inference.json",
     "quantile_sweep",
     lambda v: next(r["se_cluster_bootstrap"] for r in v if r["q"] == 0.95)),

    # ── purpose of investment, Section 5.6 ─────────────────────────────
    ("05-results", "coefficient to $-0.2279$", "purpose_channel.json",
     "ladder.M2b_year_purpose.beta", lambda v: v),
    ("05-results", "the other way, to $-0.1946$", "purpose_channel.json",
     "ladder.M3_year_type_purpose.beta", lambda v: v),
    ("05-results", "its contribution is\n$+0.0153$", "purpose_channel.json",
     "gelbach_with_purpose.contrib_purpose", lambda v: v),
    ("05-results", "rises to $-0.1824$", "purpose_channel.json",
     "gelbach_with_purpose.contrib_cde", lambda v: v),
    ("05-results", "or 88.1\\% of the explained movement", "purpose_channel.json",
     "gelbach_with_purpose.share_from_cde", lambda v: v * 100),
    ("05-results", "coefficient moves from $-0.0467$", "purpose_channel.json",
     "ladder.M5_within_cde_no_purpose.beta", lambda v: v),
    ("05-results", "to $-0.0551$ and remains", "purpose_channel.json",
     "ladder.M6_within_cde_with_purpose.beta", lambda v: v),
    ("05-results", "zero ($p = 0.578$)", "purpose_channel.json",
     "ladder.M6_within_cde_with_purpose.p", lambda v: v),
    ("05-results", "at $1.044$", "purpose_channel.json",
     "leverage_by_purpose.business.median", lambda v: v),
    ("05-results", "median of\n$1.271$", "purpose_channel.json",
     "leverage_by_purpose.re_rehab.median", lambda v: v),
    ("05-results", "59.5\\% of rural projects", "purpose_channel.json",
     "composition_by_rural_pct.business.rural", lambda v: v),
    ("05-results", "against 34.8\\% of\nmetro projects", "purpose_channel.json",
     "composition_by_rural_pct.business.metro", lambda v: v),

    ("00-abstract", "leaves 88.1\\%", "purpose_channel.json",
     "gelbach_with_purpose.share_from_cde", lambda v: v * 100),

    # ── the rehabilitation cell, Section 5.6 ──────────────────────────
    ("05-results", "coefficient of $-0.4393$", "rehab_cell_verification.json",
     "R1.beta", lambda v: v),
    ("05-results", "standard error of $0.1019$", "rehab_cell_verification.json",
     "R1.se_cde_cluster", lambda v: v),
    ("05-results", "statistic of\n$-4.31$", "rehab_cell_verification.json",
     "R1.t", lambda v: v),
    ("05-results", "the log specification gives $-0.155$",
     "rehab_cell_verification.json", "R2_outcome_variants.log.beta", lambda v: v),
    ("05-results", "each of the 256 intermediaries", "rehab_cell_verification.json",
     "R3_influence.n_cde_dropped_tested", lambda v: v),
    ("05-results", "within $[-0.481, -0.410]$", "rehab_cell_verification.json",
     "R3_influence.leave_one_cde_min", lambda v: v),
    ("05-results", "returns $p = 0.0055$", "rehab_cell_verification.json",
     "R4_randomization.p_two_sided", lambda v: v),
    ("05-results", "returns $p = 0.0005$", "rehab_cell_verification.json",
     "R5_wild_cluster.p_two_sided", lambda v: v),
    ("05-results", "financing gives $+0.053$", "rehab_cell_verification.json",
     "R6_other_purposes.business.beta", lambda v: v),
    ("05-results", "construction gives\n$-0.068$", "rehab_cell_verification.json",
     "R6_other_purposes.re_construction.beta", lambda v: v),
    ("00-abstract", "coefficient of\n$-0.439$", "rehab_cell_verification.json",
     "R1.beta", lambda v: v),
    ("00-abstract", "SE $0.102$", "rehab_cell_verification.json",
     "R1.se_cde_cluster", lambda v: v),

    ("07-conclusion", "rehabilitation, at $-0.439$", "rehab_cell_verification.json",
     "R1.beta", lambda v: v),

    # ── repeated headline results, independently guarded ──────────────
    ("00-abstract", "received 19.6\\%\nof dollars", "headline.json",
     "non_metro_qlici_dollar_share_pct", lambda v: v),
    ("00-abstract", "there (median 1.07$\\times$", "summary_by_metro.csv",
     "rows", lambda v: next(r["leverage_median"] for r in v
                            if r["metro"] == "non_metro")),
    ("00-abstract", "1.19$\\times$ metro", "summary_by_metro.csv",
     "rows", lambda v: next(r["leverage_median"] for r in v
                            if r["metro"] == "metro")),
    ("00-abstract", "raw gap is\na precise $-0.262$", "referee_fixes.json",
     "F1_gelbach.beta_M0", lambda v: v),
    ("00-abstract", "within-CDE estimate is $-0.047$", "referee_fixes.json",
     "F1_gelbach.beta_full", lambda v: v),
    ("00-abstract", "median-regression analog is $-0.001$", "referee_fixes.json",
     "F3_power.median_beta", lambda v: v),
    ("00-abstract", "decomposition assigns $-0.185$", "referee_fixes.json",
     "F1_gelbach.contrib_cde", lambda v: v),
    ("00-abstract", "86\\% of the explained", "referee_fixes.json",
     "F1_gelbach.share_of_gap_from_cde", lambda v: 100 * v),

    ("01-intro", "roughly 8{,}000 projects", "headline.json",
     "n_projects_total", lambda v: 1000 * round(v / 1000)),
    ("01-intro", "leverage is $-0.262$", "referee_fixes.json",
     "F1_gelbach.beta_M0", lambda v: v),
    ("01-intro", "effects move it to $-0.172$", "review_round2.json",
     "G1_specs.M3_state_only.beta", lambda v: v),
    ("01-intro", "the 163 of 343 CDEs", "referee_fixes.json",
     "F5_switchers.n_cde_switchers", lambda v: v),
    ("01-intro", "of 343 CDEs that work", "referee_fixes.json",
     "F5_switchers.n_cde_total", lambda v: v),
    ("01-intro", "point estimate falls to $-0.047$", "referee_fixes.json",
     "F1_gelbach.beta_full", lambda v: v),
    ("01-intro", "effects gives $-0.060$", "review_round2.json",
     "G1_specs.M4S_nested.beta", lambda v: v),
    ("01-intro", "95\\% CI $[-0.245,", "referee_fixes.json",
     "F3_power.mean_ci95[0]", lambda v: v),
    ("01-intro", ", +0.152]$) and can", "referee_fixes.json",
     "F3_power.mean_ci95[1]", lambda v: v),
    ("01-intro", "larger than $0.21$", "referee_fixes.json",
     "F3_power.mean_rejectable_penalty", lambda v: v),
    ("01-intro", "penalty is $-0.001$", "referee_fixes.json",
     "F3_power.median_beta", lambda v: v),
    ("01-intro", "(SE $0.008$)", "referee_fixes.json",
     "F3_power.median_se_iid", lambda v: v),

    ("07-conclusion", "assigns $-0.185$", "referee_fixes.json",
     "F1_gelbach.contrib_cde", lambda v: v),
    ("07-conclusion", "raw $-0.262$ gap", "referee_fixes.json",
     "F1_gelbach.beta_M0", lambda v: v),
    ("07-conclusion", "returns $-0.060$", "review_round2.json",
     "G1_specs.M4S_nested.beta", lambda v: v),

    # ── institutional and data descriptives ───────────────────────────
    ("02-background", "received 19.6\\% of QLICI dollars", "headline.json",
     "non_metro_qlici_dollar_share_pct", lambda v: v),
    ("02-background", "names 345 distinct CDEs", "nmtc_transactions.csv",
     "rows", lambda v: cde_transaction_profile(v)["n_cdes"]),
    ("02-background", "(343 at the project level)", "referee_fixes.json",
     "F5_switchers.n_cde_total", lambda v: v),
    ("02-background", "310 executed five or more transactions", "nmtc_transactions.csv",
     "rows", lambda v: cde_transaction_profile(v)["n_cdes_at_least_five"]),
    ("02-background", "account for 23.9\\% of QLICI dollars", "nmtc_transactions.csv",
     "rows", lambda v: cde_transaction_profile(v)["top_twenty_qlici_share_pct"]),
    ("02-background", "from 0\\% to 100\\%", "nmtc_transactions.csv",
     "rows", lambda v: cde_transaction_profile(v)["max_nonmetro_share_pct"]),
    ("02-background", "span the full range\nfrom 0\\%", "nmtc_transactions.csv",
     "rows", lambda v: cde_transaction_profile(v)["min_nonmetro_share_pct"]),
    ("02-background", "with 39\\% of such CDEs", "nmtc_transactions.csv",
     "rows", lambda v: cde_transaction_profile(v)["never_nonmetro_pct"]),
    ("02-background", "6.5\\% deploying there", "nmtc_transactions.csv",
     "rows", lambda v: cde_transaction_profile(v)["at_least_four_fifths_nonmetro_pct"]),

    ("03-data", "reports 19{,}907", "headline.json",
     "n_transactions_total", lambda v: v),
    ("03-data", "across 8{,}024 projects", "headline.json",
     "n_projects_total", lambda v: v),
    ("03-data", "The aggregates show the difference. \\$120.9", "review_round2.json",
     "G4_denominators.project_cost_total_musd", lambda v: v / 1000),
    ("03-data", "billion of project cost against \\$66.6", "review_round2.json",
     "G4_denominators.qlici_total_musd", lambda v: v / 1000),
    ("03-data", "leaves \\$54.3", "review_round2.json",
     "G4_denominators.project_cost_total_musd",
     lambda v: (v - src("review_round2.json")["G4_denominators"]["qlici_total_musd"]) / 1000),
    ("03-data", "or \\$0.82 for every dollar", "review_round2.json",
     "G4_denominators.other_capital_per_qlici_dollar", lambda v: v),
    ("03-data", "and about \\$2.09", "review_round2.json",
     "G4_denominators.other_capital_per_credit_dollar", lambda v: v),
    ("03-data", "Non-metro projects are 19.5\\%", "headline.json",
     "non_metro_project_share_pct", lambda v: v),
    ("03-data", "mean (1.73 versus", "summary_by_metro.csv", "rows",
     lambda v: next(r["leverage_mean"] for r in v if r["metro"] == "non_metro")),
    ("03-data", "versus 1.99)", "summary_by_metro.csv", "rows",
     lambda v: next(r["leverage_mean"] for r in v if r["metro"] == "metro")),
    ("03-data", "median (1.07 versus", "summary_by_metro.csv", "rows",
     lambda v: next(r["leverage_median"] for r in v if r["metro"] == "non_metro")),
    ("03-data", "versus 1.19) leverage", "summary_by_metro.csv", "rows",
     lambda v: next(r["leverage_median"] for r in v if r["metro"] == "metro")),
    ("04-strategy", "over the 310 CDEs", "bunching_stats.json",
     "n_cde_active", lambda v: v),

    # ── uncovered main-estimate and uncertainty anchors ───────────────
    ("05-results", "standard error of\n$0.060$", "main_table.csv", "rows",
     lambda v: next(r["rural_se"] for r in v if r["spec"] == "M0")),
    ("05-results", "column 2, $-0.249$", "main_table.csv", "rows",
     lambda v: next(r["rural_beta"] for r in v if r["spec"] == "M1")),
    ("05-results", "shrink it to\n$-0.186$", "main_table.csv", "rows",
     lambda v: next(r["rural_beta"] for r in v if r["spec"] == "M2")),
    ("05-results", "further to $-0.172$", "review_round2.json",
     "G1_specs.M3_state_only.beta", lambda v: v),
    ("05-results", "standard error of $0.101$", "referee_fixes.json",
     "F3_power.mean_se_cde_cluster", lambda v: v),
    ("05-results", "interval, $[-0.245,", "referee_fixes.json",
     "F3_power.mean_ci95[0]", lambda v: v),
    ("05-results", ", +0.152]$,", "referee_fixes.json",
     "F3_power.mean_ci95[1]", lambda v: v),
    ("05-results", "penalty at $-0.001$", "referee_fixes.json",
     "F3_power.median_beta", lambda v: v),
    ("05-results", "(SE $0.008$)", "referee_fixes.json",
     "F3_power.median_se_iid", lambda v: v),
    ("05-results", "returns $-0.060$", "review_round2.json",
     "G1_specs.M4S_nested.beta", lambda v: v),
    ("05-results", "(SE $0.099$", "review_round2.json",
     "G1_specs.M4S_nested.se", lambda v: v),
    ("05-results", "$p = 0.54$)", "review_round2.json",
     "G1_specs.M4S_nested.p", lambda v: v),
    ("05-results", "95\\% CI\n$[-0.347,", "referee_fixes.json",
     "F2_bootstrap.cde_contrib_ci95[0]", lambda v: v),
    ("05-results", ", -0.023]$)", "referee_fixes.json",
     "F2_bootstrap.cde_contrib_ci95[1]", lambda v: v),
    ("05-results", "interval ($[25\\%,", "referee_fixes.json",
     "F2_bootstrap.selection_share_ci95[0]", lambda v: 100 * v),
    ("05-results", ", 255\\%]$)", "referee_fixes.json",
     "F2_bootstrap.selection_share_ci95[1]", lambda v: 100 * v),
    ("05-results", "from $0.013$ to $0.016$", "median_inference.json",
     "equivalence_bound_asymptotic", lambda v: v),
    ("05-results", "leave the bound at $0.013$", "median_inference.json",
     "equivalence_bound_asymptotic", lambda v: v),

    # ── switchboard, margins, and identifying support ─────────────────
    ("05-results", "Among the 104", "figures/7_switcher_spines.json",
     "n_switchers_shown", lambda v: v),
    ("05-results", "from\n1.0$\\times$", "figures/7_switcher_spines.json",
     "pooled_level_range[0]", lambda v: v),
    ("05-results", "to 4.0$\\times$", "figures/7_switcher_spines.json",
     "pooled_level_range[1]", lambda v: v),
    ("05-results", "(median $-0.12$", "figures/7_switcher_spines.json",
     "median_within_gap", lambda v: v),
    ("05-results", "interquartile range\n$[-0.46,", "figures/7_switcher_spines.json",
     "iqr_within_gap[0]", lambda v: v),
    ("05-results", ", +0.36]$)", "figures/7_switcher_spines.json",
     "iqr_within_gap[1]", lambda v: v),
    ("05-results", "(SE $1.8$pp", "referee_fixes.json",
     "F4_floor_1p001.extensive_se", lambda v: 100 * v),
    ("05-results", "$p = 0.34$)", "referee_fixes.json",
     "F4_floor_1p001.extensive_p", lambda v: v),
    ("05-results", "($p = 0.77$)", "referee_fixes.json",
     "F4_floor_1p001.intensive_p", lambda v: v),
    ("05-results", "the 163 of\n343 CDEs", "referee_fixes.json",
     "F5_switchers.n_cde_switchers", lambda v: v),
    ("05-results", "of\n343 CDEs that deploy", "referee_fixes.json",
     "F5_switchers.n_cde_total", lambda v: v),
    ("05-results", "originate 94\\%", "referee_fixes.json",
     "F5_switchers.rural_share_covered_by_switchers", lambda v: 100 * v),
    ("05-results", "effect is $0.091$", "main_table.csv", "rows",
     lambda v: next(r["rural_beta"] for r in v if r["spec"] == "M5")),
    ("05-results", "(SE $0.621$)", "main_table.csv", "rows",
     lambda v: next(r["rural_se"] for r in v if r["spec"] == "M5")),

    # ── robustness and purpose composition ────────────────────────────
    ("05-results", "($-0.338$, $p = 0.01$)", "robustness.json",
     "R1_raw_M0.beta", lambda v: v),
    ("05-results", "$p = 0.01$), while", "robustness.json",
     "R1_raw_M0.p", lambda v: v),
    ("05-results", "($-0.216$, $p = 0.48$)", "robustness.json",
     "R1_raw_M4.beta", lambda v: v),
    ("05-results", "$p = 0.48$). Winsorization", "robustness.json",
     "R1_raw_M4.p", lambda v: v),
    ("05-results", "($p = 0.18$)", "robustness.json",
     "R2_log_M4.p", lambda v: v),
    ("05-results", "gives $-0.100$", "referee_fixes.json",
     "F6_top50.beta", lambda v: v),
    ("05-results", "(SE $0.148$)", "referee_fixes.json",
     "F6_top50.se", lambda v: v),
    ("05-results", "from $0.101$ to $0.105$", "referee_fixes.json",
     "F6_twoway.se_cde", lambda v: v),
    ("05-results", "to $0.105$.", "referee_fixes.json",
     "F6_twoway.se_twoway_cgm", lambda v: v),
    ("05-results", "sample; 7.4\\% of projects", "purpose_channel.json",
     "purpose_construction.share_projects_mixed_purpose", lambda v: 100 * v),
    ("05-results", "median dominant share is 100\\%", "purpose_channel.json",
     "purpose_construction.median_dominant_share", lambda v: 100 * v),
    ("05-results", "accounts for 28.1\\% of metro", "purpose_channel.json",
     "composition_by_rural_pct.re_rehab.metro", lambda v: v),
    ("05-results", "and 12.8\\% of rural ones", "purpose_channel.json",
     "composition_by_rural_pct.re_rehab.rural", lambda v: v),

    # ── subgroup scan and the rehabilitation cell ─────────────────────
    ("05-results", "($p = 0.043$)", "residual_analysis.json", "cells",
     lambda v: next(r["p"] for r in v if r["cell"] == "QALICB type RE")),
    ("05-results", "at $+0.349$", "residual_analysis.json", "cells",
     lambda v: float(f'{next(r["beta"] for r in v
                             if r["cell"] == "CDE size quartile 3 (13<n<=30)"):.3f}')),
    ("05-results", "($p = 0.048$)", "residual_analysis.json", "cells",
     lambda v: next(r["p"] for r in v
                    if r["cell"] == "CDE size quartile 3 (13<n<=30)")),
    ("05-results", "or about 15\\% in logs", "rehab_cell_verification.json",
     "R2_outcome_variants.log.beta", lambda v: 100 * abs(v)),
    ("05-results", "lies between\n$-0.403$", "rehab_cell_verification.json",
     "R2_outcome_variants", lambda v: max(r["beta"] for r in v.values()
                                           if r != v["log"])),
    ("05-results", "and $-0.463$", "rehab_cell_verification.json",
     "R2_outcome_variants", lambda v: min(r["beta"] for r in v.values()
                                           if r != v["log"])),
    ("05-results", "($p = 0.0002$)", "rehab_cell_verification.json",
     "R2_outcome_variants.log.p", lambda v: v),
    ("05-results", "within\n$[-0.478,", "rehab_cell_verification.json",
     "R3_influence.leave_one_state_min", lambda v: v),
    ("05-results", ", -0.380]$", "rehab_cell_verification.json",
     "R3_influence.leave_one_state_max", lambda v: v),
    ("05-results", "($p = 0.74$)", "rehab_cell_verification.json",
     "R6_other_purposes.business.p", lambda v: v),
    ("05-results", "($p = 0.63$)", "rehab_cell_verification.json",
     "R6_other_purposes.re_construction.p", lambda v: v),

    # ── bunching confidence intervals and post-rule estimates ─────────
    ("05-results", "interval of $[-0.014,", "review_round2.json",
     "G2_full_count.ci95[0]", lambda v: v),
    ("05-results", ", +0.013]$;", "review_round2.json",
     "G2_full_count.ci95[1]", lambda v: v),
    ("05-results", "47\\% of bootstrap\ndraws are positive", "robustness.json",
     "R6_bunching.share_boots_positive", lambda v: 100 * v),
    ("05-results", "interval of $[-0.008,", "review_round2.json",
     "G2_full_dollar.ci95[0]", lambda v: v),
    ("05-results", ", +0.020]$.", "review_round2.json",
     "G2_full_dollar.ci95[1]", lambda v: v),
    ("05-results", "gives\n$-0.003$ in counts", "review_round2.json",
     "G3_post2007_count.B", lambda v: v),
    ("05-results", "and $+0.001$ in dollars", "review_round2.json",
     "G3_post2007_dollar.B", lambda v: v),
    ("05-results", "intervals of\n$[-0.016,", "review_round2.json",
     "G3_post2007_count.ci95[0]", lambda v: v),
    ("05-results", ", +0.011]$", "review_round2.json",
     "G3_post2007_count.ci95[1]", lambda v: v),
    ("05-results", "and $[-0.013,", "review_round2.json",
     "G3_post2007_dollar.ci95[0]", lambda v: v),
    ("05-results", ", +0.016]$ across", "review_round2.json",
     "G3_post2007_dollar.ci95[1]", lambda v: v),
    ("05-results", "period ($n = 310$)", "review_round2.json",
     "G2_full_count.n_cde", lambda v: v),
    ("05-results", "($n = 291$),", "review_round2.json",
     "G3_post2007_dollar.n_cde", lambda v: v),

    # ── bootstrap-scheme sensitivity, surfaced by cross-model audit ────
    ("05-results", "returns $0.0075$", "codex_check_bootstrap_equivalence.json",
     "cluster_exponential_multiplier.se", lambda v: v),
]


def load_tex(stem: str) -> str:
    return (SEC / f"{stem}.tex").read_text()


def main() -> int:
    texts = {s: load_tex(s) for s in {c[0] for c in CLAIMS}}
    fails: list[str] = []
    passes = 0

    for stem, literal, jf, path, xform in CLAIMS:
        body = texts[stem]
        n_hits = body.count(literal)
        if n_hits == 0:
            fails.append(f"MISSING  {stem}.tex does not contain {literal!r}")
            continue
        if n_hits > 1:
            fails.append(f"AMBIGUOUS {stem}.tex contains {literal!r} {n_hits} times")
            continue

        # the number the manuscript actually prints, taken from the literal
        m = re.findall(r"[-+]?\d+(?:\.\d+)?(?:\{,\})?\d*", literal.replace("{,}", ""))
        if not m:
            fails.append(f"NO NUMBER in literal {literal!r}")
            continue
        shown_txt = max(m, key=len)
        shown = float(shown_txt)
        ndp = len(shown_txt.split(".")[1]) if "." in shown_txt else 0

        try:
            expected = xform(dig(src(jf), path))
        except StopIteration:
            fails.append(f"SOURCE   {literal!r} -> {jf}:{path} matched no record")
            continue
        except Exception as exc:                                # noqa: BLE001
            fails.append(f"SOURCE   {literal!r} -> {jf}:{path} raised {exc!r}")
            continue

        # A printed number is a rounded number. Compare on those terms:
        # round the source half-up to the precision the manuscript shows.
        quant = Decimal(1).scaleb(-ndp)
        rounded = float(Decimal(repr(float(expected))).quantize(
            quant, rounding=ROUND_HALF_UP))

        if rounded == shown:
            passes += 1
        else:
            fails.append(f"MISMATCH {stem}.tex shows {shown} for {literal!r}; "
                         f"{jf}:{path} gives {expected:.6g} -> rounds to {rounded}")

    print(f"{passes}/{len(CLAIMS)} claims tied to a pipeline output")
    for f in fails:
        print("  " + f)
    if fails:
        print(f"\n{len(fails)} claim(s) failed the audit.")
        return 1
    print("every audited claim matches its source.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
