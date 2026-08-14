from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "run_value_added.py"


def load_module():
    spec = importlib.util.spec_from_file_location("run_value_added", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ValueAddedTests(unittest.TestCase):
    def test_joint_fixed_effect_fit_recovers_centered_cde_effects(self):
        """Catches omitted controls, wrong dummy normalization, and bad FE extraction."""
        va = load_module()
        rows = []
        cde_effect = {"A": -1.0, "B": 0.0, "C": 1.0}
        year_effect = {2020: 0.0, 2021: 0.5}
        type_effect = {"business": 0.0, "real_estate": -0.25}
        for cde, alpha in cde_effect.items():
            for year, gamma in year_effect.items():
                for qalicb_type, delta in type_effect.items():
                    rows.append(
                        {
                            "cde_name": cde,
                            "year": year,
                            "qalicb_type": qalicb_type,
                            "leverage_win": 2.0 + alpha + gamma + delta,
                        }
                    )
        frame = pd.DataFrame(rows)

        result = va.fit_cde_effects(frame)
        got = result.effects.set_index("cde_name")["raw_va"].to_dict()

        self.assertAlmostEqual(got["A"], -1.0, places=10)
        self.assertAlmostEqual(got["B"], 0.0, places=10)
        self.assertAlmostEqual(got["C"], 1.0, places=10)
        self.assertLess(float(np.max(np.abs(result.fitted - frame.leverage_win))), 1e-10)

    def test_eb_decomposition_subtracts_sampling_variance_and_shrinks(self):
        """Catches adding sampling noise to signal or reversing the shrinkage weight."""
        va = load_module()

        result = va.eb_decompose(
            np.array([-1.0, 0.0, 1.0]), np.array([0.25, 0.25, 0.25])
        )

        self.assertAlmostEqual(result["total_variance"], 1.0)
        self.assertAlmostEqual(result["mean_sampling_variance"], 0.25)
        self.assertAlmostEqual(result["signal_variance"], 0.75)
        np.testing.assert_allclose(result["reliability"], [0.75, 0.75, 0.75])
        np.testing.assert_allclose(result["shrunk"], [-0.75, 0.0, 0.75])
        self.assertFalse(result["degenerate"])

    def test_eb_decomposition_reports_degenerate_nonnegative_signal(self):
        """Catches a negative prior variance leaking into reliabilities or posterior means."""
        va = load_module()

        result = va.eb_decompose(np.zeros(3), np.full(3, 0.5))

        self.assertEqual(result["signal_variance"], 0.0)
        self.assertTrue(result["degenerate"])
        np.testing.assert_array_equal(result["reliability"], np.zeros(3))
        np.testing.assert_array_equal(result["shrunk"], np.zeros(3))

    def test_disattenuation_uses_both_reliabilities(self):
        """Catches one-sided or multiplicative reliability corrections."""
        va = load_module()

        adjusted = va.reliability_adjusted_correlation(0.4, 0.64, 0.25)

        self.assertAlmostEqual(adjusted, 1.0)

    def test_cde_split_is_reproducible_disjoint_and_balanced(self):
        """Catches leakage between halves and unbalanced within-CDE splitting."""
        va = load_module()
        frame = pd.DataFrame(
            {
                "cde_name": ["A"] * 7 + ["B"] * 6 + ["C"] * 5,
                "value": np.arange(18),
            }
        )

        a1, b1, eligible1 = va.split_cde_indices(
            frame, np.random.default_rng(20260814), min_total=6
        )
        a2, b2, eligible2 = va.split_cde_indices(
            frame, np.random.default_rng(20260814), min_total=6
        )

        np.testing.assert_array_equal(a1, a2)
        np.testing.assert_array_equal(b1, b2)
        self.assertEqual(eligible1, eligible2)
        self.assertEqual(set(eligible1), {"A", "B"})
        self.assertFalse(set(a1) & set(b1))
        self.assertEqual(set(a1) | set(b1), set(range(13)))
        for cde in eligible1:
            na = int((frame.loc[a1, "cde_name"] == cde).sum())
            nb = int((frame.loc[b1, "cde_name"] == cde).sum())
            self.assertLessEqual(abs(na - nb), 1)
            self.assertGreaterEqual(min(na, nb), 3)

    def test_counterfactual_conserves_dollars_and_matches_hand_calculation(self):
        """Catches dollar creation and the wrong donor-to-recipient VA contrast."""
        va = load_module()
        effects = pd.Series({"low": -1.0, "high": 1.0})
        dollars = pd.Series({"low": 40.0, "high": 60.0})

        result = va.counterfactual_reallocation(effects, dollars, raw_gap=-0.25)

        self.assertAlmostEqual(result["observed_total_dollars"], 100.0)
        self.assertAlmostEqual(result["counterfactual_total_dollars"], 100.0)
        self.assertAlmostEqual(result["observed_weighted_va"], 0.2)
        self.assertAlmostEqual(result["counterfactual_weighted_va"], 1.0)
        self.assertAlmostEqual(result["leverage_gain"], 0.8)
        self.assertAlmostEqual(result["share_gap_closed"], 3.2)


if __name__ == "__main__":
    unittest.main()
