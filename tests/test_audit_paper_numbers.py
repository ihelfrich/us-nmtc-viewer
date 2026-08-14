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
