"""
Tests for the manuscript numbers audit.

The audit is a guard, and a guard that has never been observed to fire is
indistinguishable from a guard that cannot fire. These tests confirm it
passes on the real manuscript, that it rejects a value that has drifted
from its source, and that its rounding convention is the one a printed
number implies.

Run: uv run --no-project --with pytest python -m pytest tests/ -q
"""
from __future__ import annotations

import importlib.util
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location(
    "audit", ROOT / "scripts" / "audit_paper_numbers.py")
audit = importlib.util.module_from_spec(spec)
sys.modules["audit"] = audit
spec.loader.exec_module(audit)


def test_manuscript_passes_its_own_audit():
    assert audit.main() == 0


def test_every_claim_resolves_to_a_real_source_field():
    for stem, literal, jf, path, xform in audit.CLAIMS:
        value = xform(audit.dig(audit.src(jf), path))
        assert isinstance(value, (int, float)), f"{literal!r} -> {jf}:{path}"


def test_every_claim_anchor_appears_exactly_once():
    for stem, literal, *_ in audit.CLAIMS:
        body = (ROOT / "paper" / "sections" / f"{stem}.tex").read_text()
        assert body.count(literal) == 1, (
            f"{literal!r} appears {body.count(literal)} times in {stem}.tex; "
            "an audit anchor must be unique")


def test_source_loader_reads_processed_csv_and_figure_sidecars():
    """Manifest claims may use pipeline outputs outside regressions/*.json."""
    headline = audit.src("headline.json")
    metro_rows = audit.src("summary_by_metro.csv")["rows"]
    switchboard = audit.src("figures/7_switcher_spines.json")

    assert headline["n_transactions_total"] == 19_907
    assert metro_rows[1]["metro"] == "non_metro"
    assert metro_rows[1]["leverage_mean"] == 1.73
    assert switchboard["n_switchers_shown"] == 104


def test_cde_profile_recomputes_background_counts_from_transaction_output():
    rows = audit.src("nmtc_transactions.csv")["rows"]
    profile = audit.cde_transaction_profile(rows)

    assert profile == {
        "n_cdes": 345,
        "n_cdes_at_least_five": 310,
        "top_twenty_qlici_share_pct": 23.869316845039652,
        "never_nonmetro_pct": 38.70967741935484,
        "at_least_four_fifths_nonmetro_pct": 6.451612903225806,
        "min_nonmetro_share_pct": 0.0,
        "max_nonmetro_share_pct": 100.0,
    }


def test_manifest_covers_c9_load_bearing_inventory():
    """Removing one of the audited empirical anchors must expose a coverage gap."""
    required = {
        # Repeated headline results are independently protected where stale copies matter.
        ("00-abstract", "received 19.6\\%\nof dollars"),
        ("00-abstract", "there (median 1.07$\\times$"),
        ("00-abstract", "1.19$\\times$ metro"),
        ("00-abstract", "raw gap is\na precise $-0.262$"),
        ("00-abstract", "within-CDE estimate is $-0.047$"),
        ("00-abstract", "median-regression analog is $-0.001$"),
        ("00-abstract", "decomposition assigns $-0.185$"),
        ("00-abstract", "86\\% of the explained"),
        ("01-intro", "roughly 8{,}000 projects"),
        ("01-intro", "leverage is $-0.262$"),
        ("01-intro", "effects move it to $-0.172$"),
        ("01-intro", "the 163 of 343 CDEs"),
        ("01-intro", "point estimate falls to $-0.047$"),
        ("01-intro", "effects gives $-0.060$"),
        ("01-intro", "95\\% CI $[-0.245,"),
        ("01-intro", ", +0.152]$) and can"),
        ("01-intro", "larger than $0.21$"),
        ("01-intro", "penalty is $-0.001$"),
        ("01-intro", "(SE $0.008$)"),
        ("07-conclusion", "assigns $-0.185$"),
        ("07-conclusion", "raw $-0.262$ gap"),
        ("07-conclusion", "returns $-0.060$"),

        # Descriptive pipeline outputs in the background and data sections.
        ("02-background", "received 19.6\\% of QLICI dollars"),
        ("02-background", "names 345 distinct CDEs"),
        ("02-background", "(343 at the project level)"),
        ("02-background", "310 executed five or more transactions"),
        ("02-background", "account for 23.9\\% of QLICI dollars"),
        ("02-background", "from 0\\% to 100\\%"),
        ("02-background", "with 39\\% of such CDEs"),
        ("02-background", "6.5\\% deploying there"),
        ("03-data", "reports 19{,}907"),
        ("03-data", "across 8{,}024 projects"),
        ("03-data", "The aggregates show the difference. \\$120.9"),
        ("03-data", "billion of project cost against \\$66.6"),
        ("03-data", "leaves \\$54.3"),
        ("03-data", "or \\$0.82 for every dollar"),
        ("03-data", "and about \\$2.09"),
        ("03-data", "Non-metro projects are 19.5\\%"),
        ("03-data", "mean (1.73 versus"),
        ("03-data", "versus 1.99)"),
        ("03-data", "median (1.07 versus"),
        ("03-data", "versus 1.19) leverage"),
        ("04-strategy", "over the 310 CDEs"),

        # Main estimates, uncertainty, margins, and identifying sample.
        ("05-results", "standard error of\n$0.060$"),
        ("05-results", "column 2, $-0.249$"),
        ("05-results", "shrink it to\n$-0.186$"),
        ("05-results", "further to $-0.172$"),
        ("05-results", "standard error of $0.101$"),
        ("05-results", "interval, $[-0.245,"),
        ("05-results", ", +0.152]$,"),
        ("05-results", "penalty at $-0.001$"),
        ("05-results", "(SE $0.008$)"),
        ("05-results", "returns $-0.060$"),
        ("05-results", "(SE $0.099$"),
        ("05-results", "$p = 0.54$)"),
        ("05-results", "95\\% CI\n$[-0.347,"),
        ("05-results", ", -0.023]$)"),
        ("05-results", "interval ($[25\\%,"),
        ("05-results", ", 255\\%]$)"),
        ("05-results", "from $0.013$ to $0.016$"),
        ("05-results", "leave the bound at $0.013$"),
        ("05-results", "Among the 104"),
        ("05-results", "from\n1.0$\\times$"),
        ("05-results", "to 4.0$\\times$"),
        ("05-results", "(median $-0.12$"),
        ("05-results", "interquartile range\n$[-0.46,"),
        ("05-results", ", +0.36]$)"),
        ("05-results", "(SE $1.8$pp"),
        ("05-results", "$p = 0.34$)"),
        ("05-results", "($p = 0.77$)"),
        ("05-results", "the 163 of\n343 CDEs"),
        ("05-results", "originate 94\\%"),
        ("05-results", "effect is $0.091$"),
        ("05-results", "(SE $0.621$)"),

        # Robustness, composition, subgroup scan, and bunching diagnostics.
        ("05-results", "($-0.338$, $p = 0.01$)"),
        ("05-results", "($-0.216$, $p = 0.48$)"),
        ("05-results", "($p = 0.18$)"),
        ("05-results", "gives $-0.100$"),
        ("05-results", "(SE $0.148$)"),
        ("05-results", "from $0.101$ to $0.105$"),
        ("05-results", "sample; 7.4\\% of projects"),
        ("05-results", "median dominant share is 100\\%"),
        ("05-results", "accounts for 28.1\\% of metro"),
        ("05-results", "and 12.8\\% of rural ones"),
        ("05-results", "($p = 0.043$)"),
        ("05-results", "at $+0.349$"),
        ("05-results", "($p = 0.048$)"),
        ("05-results", "or about 15\\% in logs"),
        ("05-results", "lies between\n$-0.403$"),
        ("05-results", "and $-0.463$"),
        ("05-results", "($p = 0.0002$)"),
        ("05-results", "within\n$[-0.478,"),
        ("05-results", ", -0.380]$"),
        ("05-results", "($p = 0.74$)"),
        ("05-results", "($p = 0.63$)"),
        ("05-results", "interval of $[-0.014,"),
        ("05-results", ", +0.013]$;"),
        ("05-results", "47\\% of bootstrap\ndraws are positive"),
        ("05-results", "interval of $[-0.008,"),
        ("05-results", ", +0.020]$."),
        ("05-results", "gives\n$-0.003$ in counts"),
        ("05-results", "and $+0.001$ in dollars"),
        ("05-results", "intervals of\n$[-0.016,"),
        ("05-results", ", +0.011]$"),
        ("05-results", "and $[-0.013,"),
        ("05-results", ", +0.016]$ across"),
        ("05-results", "period ($n = 310$)"),
        ("05-results", "($n = 291$),"),
    }
    actual = {(stem, literal) for stem, literal, *_ in audit.CLAIMS}
    missing = sorted(required - actual)
    assert not missing, "uncovered load-bearing manuscript anchors: " + repr(missing)


def test_rounding_is_half_up_at_the_displayed_precision():
    # -0.1845 printed to three places is -0.185, not -0.184. Python's
    # built-in round() gives the wrong answer here, which is why the audit
    # uses Decimal.
    def r(v, ndp):
        return float(Decimal(repr(float(v))).quantize(
            Decimal(1).scaleb(-ndp), rounding=ROUND_HALF_UP))

    assert r(-0.1845, 3) == -0.185
    assert r(0.815, 2) == 0.82
    assert r(-0.2155, 3) == -0.216
    assert round(0.815, 2) == 0.81          # the trap this avoids


def test_audit_rejects_a_drifted_value():
    """Point one claim at a value that has moved and confirm the audit
    fails rather than passing quietly."""
    stem, literal, jf, path, xform = audit.CLAIMS[0]
    original = audit.CLAIMS[0]
    audit.CLAIMS[0] = (stem, literal, jf, path, lambda v: xform(v) + 1.0)
    try:
        assert audit.main() == 1
    finally:
        audit.CLAIMS[0] = original
    assert audit.main() == 0        # and recovers cleanly
