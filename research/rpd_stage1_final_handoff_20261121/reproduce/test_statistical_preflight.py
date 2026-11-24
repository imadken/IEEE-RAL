"""Scientific regression and independently evaluated rejection-region tests."""

import math
import unittest
from fractions import Fraction

from statistical_preflight import (
    bernstein_numerators,
    cp_lower,
    cutoffs,
    direct_null_probability,
    rejects,
    required_successes,
)


class StatisticalPreflightTests(unittest.TestCase):
    def test_integer_rejection_matches_original_score(self):
        for n in (3, 5, 8, 64, 1024):
            for m in sorted({0, 1, n // 2, n}):
                decisions = []
                for plus in range(m + 1):
                    score = (2 * plus - m - 0.02 * n) / math.sqrt(
                        n * (max(m / n, 0.02) - 0.02**2)
                    )
                    # Check non-boundary floats only; exact equality has its own test.
                    if abs(score + 2.2) > 1e-10:
                        self.assertEqual(
                            rejects(n, m, plus, Fraction(11, 5)), score <= -2.2
                        )
                    decisions.append(rejects(n, m, plus, Fraction(11, 5)))
                self.assertEqual(decisions, sorted(decisions, reverse=True))

    def test_inclusive_exact_score_boundary(self):
        # n=49,m=0: Z=-1 exactly; the inclusive boundary must reject.
        self.assertTrue(rejects(49, 0, 0, Fraction(1)))
        self.assertFalse(rejects(49, 0, 0, Fraction(1001, 1000)))

    def test_counts_are_validated(self):
        for n, m, plus in ((0, 0, 0), (1, 2, 0), (4, 2, 3), (4, -1, 0)):
            with self.assertRaises(ValueError):
                rejects(n, m, plus, Fraction(11, 5))

    def test_polynomial_equals_independent_exact_trinomial(self):
        for n in (3, 5, 8):
            for c in (Fraction(1), Fraction(3, 2), Fraction(11, 5)):
                nums, denom = bernstein_numerators(n, c)
                for t in (
                    Fraction(0),
                    Fraction(1, 3),
                    Fraction(1, 2),
                    Fraction(2, 3),
                    Fraction(1),
                ):
                    polynomial = sum(
                        Fraction(a, denom) * math.comb(n, k) * t**k * (1 - t) ** (n - k)
                        for k, a in enumerate(nums)
                    )
                    self.assertEqual(polynomial, direct_null_probability(n, c, t))

    def test_cp_targets_and_disclosed_technical_control(self):
        self.assertEqual(required_successes(1024, 0.10), 123)
        self.assertEqual(required_successes(0, 0.50), 1)
        self.assertGreater(cp_lower(116, 128, 0.05), 0.8)

    def test_nominal_critical_is_not_automatically_valid_at_other_n(self):
        # Illustrates why a nominal critical is not a general sample-size certificate.
        self.assertNotEqual(cutoffs(64, Fraction(11, 5)), cutoffs(63, Fraction(11, 5)))
        self.assertEqual(len(cutoffs(64, Fraction(11, 5))), 65)


if __name__ == "__main__":
    unittest.main()
