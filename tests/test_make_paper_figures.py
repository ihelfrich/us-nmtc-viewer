from __future__ import annotations

import contextlib
import importlib.util
import io
import tempfile
import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "make_paper_figures.py"
OUTPUT_STEMS = (
    "paper_1_deployment",
    "paper_2_nonmetro_share",
    "paper_3_leverage_dist",
    "paper_6_bunching",
)


def load_module():
    spec = importlib.util.spec_from_file_location("make_paper_figures", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PaperFigureTests(unittest.TestCase):
    def test_bunching_estimator_matches_pipeline_results(self):
        """Catches changes to the binning, sample restriction, or counterfactual."""
        figures = load_module()
        transactions = pd.read_csv(
            ROOT / "data" / "processed" / "nmtc_transactions.csv"
        )

        result = figures.compute_bunching(transactions)

        self.assertEqual(result.n_cde_active, 310)
        self.assertAlmostEqual(result.empirical_mass, 0.0274, places=4)
        self.assertAlmostEqual(result.counterfactual_mass, 0.0280, places=4)
        self.assertAlmostEqual(result.excess_mass, -0.0006, places=4)
        self.assertAlmostEqual(result.excess_mass_pct, -2.2, places=1)
        self.assertAlmostEqual(result.density_at_20, 1.097, places=3)
        self.assertAlmostEqual(result.density_near_20, 0.946, places=3)
        self.assertAlmostEqual(result.ratio_at_to_near, 1.16, places=2)

    def test_render_all_writes_four_pdf_png_pairs_and_provenance(self):
        """Catches missing formats, wrong output names, and silent rendering."""
        figures = load_module()

        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(
            io.StringIO()
        ) as captured:
            provenance = figures.render_all(Path(tmp))
            output_dir = Path(tmp)
            for stem in OUTPUT_STEMS:
                png = output_dir / f"{stem}.png"
                pdf = output_dir / f"{stem}.pdf"
                self.assertTrue(png.is_file(), png)
                self.assertTrue(pdf.is_file(), pdf)
                self.assertEqual(png.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")
                self.assertEqual(pdf.read_bytes()[:5], b"%PDF-")

        self.assertEqual(len(provenance), 4)
        self.assertEqual(len(captured.getvalue().strip().splitlines()), 4)


if __name__ == "__main__":
    unittest.main()
