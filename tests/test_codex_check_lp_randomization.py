"""Focused behavior tests for the canonical C4--C6 audit artifact."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import platform
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import scipy
import statsmodels


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "codex_check_lp_randomization.py"
RESULT_PATH = (
    ROOT / "data" / "processed" / "regressions"
    / "codex_check_lp_randomization.json"
)


def load_module():
    spec = importlib.util.spec_from_file_location(
        "codex_check_lp_randomization", MODULE_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def audit():
    return load_module()


@pytest.fixture(scope="module")
def sample(audit):
    return audit.load_sample()


def test_full_covariate_cell_summary_matches_real_sample(audit, sample):
    """Catches omission of rural or use of a point median instead of its set."""
    assert audit.full_covariate_cell_summary(sample) == {
        "minimum_cell_size": 5,
        "total_cells": 3715,
        "eligible_cells": 284,
        "eligible_observations": 2631,
        "cells_with_one_in_empirical_median_set": 85,
        "observations_in_one_median_cells": 974,
        "share_eligible_cells_one_in_median_set": pytest.approx(
            0.2992957746478873
        ),
        "share_eligible_observations_in_one_median_cells": pytest.approx(
            0.37020144431774993
        ),
        "share_full_sample_observations_in_one_median_cells": pytest.approx(
            0.12138584247258226
        ),
    }


def test_run_provenance_records_artifact_hashes_and_runtime_versions(audit):
    """Catches a result that cannot identify its input, code, or environment."""
    provenance = audit.run_provenance()

    assert provenance == {
        "input_sha256": hashlib.sha256(audit.INPUT.read_bytes()).hexdigest(),
        "script_sha256": hashlib.sha256(MODULE_PATH.read_bytes()).hexdigest(),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "dependencies": {
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scipy": scipy.__version__,
            "statsmodels": statsmodels.__version__,
        },
    }


def test_refresh_uses_stored_records_without_refitting(audit, sample):
    """Catches stale summaries when deterministic evidence is refreshed."""
    completed = json.loads(RESULT_PATH.read_text())
    completed["permutations"]["real_within_cde"]["coefficient_pinning"][
        "abs_lt_1e-07"
    ]["share"] = -1.0

    refreshed = audit.refresh_completed_results(completed, sample)

    assert refreshed["status"] == "complete"
    assert refreshed["permutations"]["real_within_cde"][
        "coefficient_pinning"
    ]["abs_lt_1e-07"]["share"] == 0.9
    assert refreshed["C4"]["observed_fe_cell_atoms"][
        "cde_year_type_rural"
    ]["cells_with_one_in_empirical_median_set"] == 85
    assert refreshed["provenance"] == audit.run_provenance()
