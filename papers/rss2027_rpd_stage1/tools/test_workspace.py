"""Meaningful offline regression checks for paper integrity and inference."""

import itertools
import math
import shutil
import tempfile
import unittest
from pathlib import Path

import numpy as np
import protocol_math as protocol
import workspace
from scipy.optimize import minimize_scalar
from scipy.special import xlogy


class ProtocolChecks(unittest.TestCase):
    def test_candidate_namespaces_are_fixed_and_disjoint(self):
        config = protocol.Protocol()
        rows = protocol.candidate_manifest(config)
        self.assertEqual(len(rows), 588)
        self.assertEqual(len({r["native_geometry_seed"] for r in rows}), 588)
        self.assertEqual(rows, protocol.candidate_manifest(config))
        self.assertEqual(sum(r["phase"] == "confirmation" for r in rows), 512)

    def test_goal_and_wrapper_clocks_include_boundaries(self):
        spec = protocol.Protocol()
        self.assertEqual((spec.dwell_samples - 1) / spec.sim_hz, 0.25)
        self.assertEqual(spec.prefix_ticks + spec.remaining_ticks, 110)
        self.assertEqual(spec.prefix_ticks + spec.long_remaining_ticks, 190)
        with self.assertRaises(ValueError):
            protocol.Protocol(episode_limit_ticks=100)

    def test_missing_exact_interval_contains_every_possible_completion(self):
        n, plus, minus, missing = 32, 5, 2, 4
        lo, hi = protocol.paired_exact(plus, minus, n, missing)
        for assignments in itertools.product((-1, 0, 1), repeat=missing):
            actual = protocol.paired_exact(
                plus + assignments.count(1), minus + assignments.count(-1), n
            )
            self.assertLessEqual(lo, actual[0])
            self.assertGreaterEqual(hi, actual[1])

    def test_missing_score_envelope_contains_variance_sensitive_bounds(self):
        b = -math.log(0.001)
        observed = [-0.4, 0.2, 0.8]
        envelope = protocol.eb_lower(observed, missing=2)
        for additions in itertools.product(np.linspace(-b, b, 7), repeat=2):
            self.assertLessEqual(
                envelope, protocol.eb_lower(observed + list(additions)) + 1e-10
            )

    def test_binomial_margin_and_zero_event_limit(self):
        self.assertLess(protocol.lower(65, 512), 0.1)
        self.assertGreater(protocol.lower(66, 512), 0.1)
        self.assertAlmostEqual(protocol.upper(0, 512), 1 - 0.025 ** (1 / 512))

    def test_independent_profile_likelihood_at_interval_endpoints(self):
        plus, minus, n = 76, 26, 512
        low, high = protocol.profile_interval(plus, minus, n)
        counts = np.array([plus, minus, n - plus - minus])
        unconstrained = float(sum(xlogy(counts, counts / n)))
        for delta in (low, high):
            # Independent parameterization is p_plus, not the implementation's p_minus.
            def objective(p_plus, delta=delta):
                probabilities = np.array(
                    [p_plus, p_plus - delta, 1 - 2 * p_plus + delta]
                )
                return -float(sum(xlogy(counts, np.maximum(0.0, probabilities))))

            fit = minimize_scalar(
                objective, bounds=(max(0.0, delta), (1 + delta) / 2), method="bounded"
            )
            self.assertAlmostEqual(2 * (unconstrained + fit.fun), 3.841459, places=5)

    def test_zero_discordance_has_uncertainty(self):
        lo, hi = protocol.paired_exact(0, 0, 512)
        self.assertLess(lo, 0)
        self.assertGreater(hi, 0)
        with self.assertRaises(ValueError):
            protocol.eb_lower([0.0])

    def test_complete_tree_oracle_matches_responsewise_control(self):
        result = protocol.brute_tree_example()
        self.assertEqual(result["brute_policy_tree_completion"]["coarse"], 1.0)
        self.assertEqual(result["brute_policy_tree_completion"]["fine"], 2 / 3)


class PaperChecks(unittest.TestCase):
    def test_immutable_originals_and_official_template(self):
        self.assertTrue(workspace.originals()["class_unmodified"])

    def test_info_removal_preserves_pdf_text_and_fonts(self):
        source = workspace.BASE / "original_v2/paper.pdf"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.pdf"
            shutil.copyfile(source, path)
            before = workspace.run(["pdftotext", str(path), "-"])
            fonts = workspace.run(["pdffonts", str(path)])
            workspace.remove_pdf_information(path)
            self.assertEqual(workspace.run(["pdftotext", str(path), "-"]), before)
            self.assertEqual(workspace.run(["pdffonts", str(path)]), fonts)
            info = workspace.run(["pdfinfo", str(path)])
            for label in (
                "Author:",
                "Title:",
                "Creator:",
                "Producer:",
                "CreationDate:",
                "ModDate:",
                "Subject:",
            ):
                self.assertNotIn(label, info)

    def test_info_removal_rejects_non_pdf_input(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.pdf"
            path.write_bytes(b"not a PDF")
            with self.assertRaises(AssertionError):
                workspace.remove_pdf_information(path)


if __name__ == "__main__":
    unittest.main()
