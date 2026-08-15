"""Focused behavior checks for conditioned paired quantile gaps."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import verify_quantile_tail as tail  # noqa: E402


def test_conditioned_paired_gaps_remove_year_and_type_composition() -> None:
    """Protects production T4 from raw gaps or omitted year/type adjustment."""
    rows = []
    # Outcome is exactly a year effect (10) plus a type effect (2). Rural
    # projects occur in the high-year cell, while type differs across CDEs.
    cells = [
        ("A", 0, 2020, "base", 0.0),
        ("A", 1, 2021, "premium", 12.0),
        ("B", 0, 2020, "premium", 2.0),
        ("B", 1, 2021, "base", 10.0),
    ]
    for cde, rural, year, qalicb_type, outcome in cells:
        rows.extend(
            {
                "cde_name": cde,
                "rural": rural,
                "year": year,
                "qalicb_type": qalicb_type,
                "leverage_win": outcome,
            }
            for _ in range(5)
        )
    frame = pd.DataFrame(rows)

    np.testing.assert_allclose(tail.paired_gaps(frame, 0.5), [12.0, 8.0])
    np.testing.assert_allclose(
        tail.conditioned_paired_gaps(frame, 0.5), [0.0, 0.0], atol=1e-10
    )
