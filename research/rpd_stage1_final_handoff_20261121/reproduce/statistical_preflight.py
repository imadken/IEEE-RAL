"""Independent, physics-free verification of the public November 21 design.

The missing private V4.4 implementation is not imported or certified here.
The null certificate uses integer arithmetic; hypothetical powers use SciPy.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from decimal import Decimal, localcontext
from fractions import Fraction
from pathlib import Path

from scipy.stats import beta, binom


def rejects(n: int, m: int, plus: int, critical: Fraction) -> bool:
    """Exact Z <= -critical, epsilon=1/50; no floating boundary test."""
    if n < 1 or not 0 <= plus <= m <= n or critical <= 0:
        raise ValueError("Require n>0, 0<=plus<=m<=n, critical>0")
    left = n - 50 * (2 * plus - m)
    variance = max(2500 * m - n, 49 * n)
    return left >= 0 and (
        critical.denominator**2 * left**2 >= critical.numerator**2 * variance
    )


def cutoffs(n: int, critical: Fraction) -> list[int]:
    thresholds = []
    for m in range(n + 1):
        lower, upper = -1, m + 1
        while upper - lower > 1:
            middle = (lower + upper) // 2
            if rejects(n, m, middle, critical):
                lower = middle
            else:
                upper = middle
        thresholds.append(lower)
    return thresholds


def bernstein_numerators(n: int, critical: Fraction) -> tuple[list[int], int]:
    """Exact Bernstein coefficients on r in [.02,1], denominator 100**n.

    k draws use endpoint B=(51/100,49/100,0); n-k endpoint A=(1/50,0,49/50).
    The integer cumulative binomial sums avoid claiming certification from a grid.
    """
    cuts = cutoffs(n, critical)
    numerators = []
    for k in range(n + 1):
        weight = 49**k
        cumulative = [weight]
        for j in range(k):
            numerator = weight * (k - j) * 51
            divisor = (j + 1) * 49
            weight, remainder = divmod(numerator, divisor)
            if remainder:
                raise ArithmeticError("Noninteger binomial coefficient recurrence")
            cumulative.append(cumulative[-1] + weight)
        if cumulative[-1] != 100**k:
            raise ArithmeticError("Endpoint B mass does not sum to one")
        a_count = n - k
        weight = 49**a_count
        numerator_sum = 0
        a_mass = 0
        for y in range(a_count + 1):
            a_mass += weight
            cutoff = cuts[k + y] - y
            if cutoff >= 0:
                numerator_sum += weight * cumulative[min(cutoff, k)]
            if y < a_count:
                numerator = weight * (a_count - y)
                weight, remainder = divmod(numerator, (y + 1) * 49)
                if remainder:
                    raise ArithmeticError("Noninteger endpoint A recurrence")
        if a_mass != 50**a_count:
            raise ArithmeticError("Endpoint A mass does not sum to one")
        numerators.append(numerator_sum * 2**a_count)
    return numerators, 100**n


def direct_null_probability(n: int, critical: Fraction, t: Fraction) -> Fraction:
    """Separately enumerate every trinomial count, using a rational Z^2 oracle."""
    eps = Fraction(1, 50)
    discordance = eps + (1 - eps) * t
    p_plus, p_minus = (discordance + eps) / 2, (discordance - eps) / 2
    total = Fraction(0)
    for plus in range(n + 1):
        for minus in range(n - plus + 1):
            zero = n - plus - minus
            numerator = Fraction(plus - minus) - n * eps
            variance = n * (max(Fraction(plus + minus, n), eps) - eps**2)
            # Implemented without calling rejects() or its integer rearrangement.
            if numerator <= 0 and numerator**2 >= critical**2 * variance:
                ways = math.comb(n, plus) * math.comb(n - plus, minus)
                total += (
                    ways * p_plus**plus * p_minus**minus * (1 - discordance) ** zero
                )
    return total


def small_oracles() -> list[dict]:
    checks = []
    for n in (3, 5, 8):
        for critical in (Fraction(1), Fraction(3, 2), Fraction(11, 5)):
            nums, denominator = bernstein_numerators(n, critical)
            for t in (Fraction(1, 3), Fraction(1, 2), Fraction(2, 3)):
                polynomial = sum(
                    Fraction(num, denominator)
                    * math.comb(n, k)
                    * t**k
                    * (1 - t) ** (n - k)
                    for k, num in enumerate(nums)
                )
                oracle = direct_null_probability(n, critical, t)
                if polynomial != oracle:
                    raise AssertionError((n, critical, t, polynomial, oracle))
                checks.append(
                    {
                        "n": n,
                        "critical": str(-critical),
                        "t": str(t),
                        "exact_rational_equality": True,
                    }
                )
    return checks


def cp_lower(successes: int, n: int, alpha: float) -> float:
    return (
        0.0 if successes == 0 else float(beta.ppf(alpha, successes, n - successes + 1))
    )


def cp_upper(successes: int, n: int, alpha: float) -> float:
    return (
        1.0
        if successes == n
        else float(beta.ppf(1 - alpha, successes + 1, n - successes))
    )


def required_successes(n: int, null: float, alpha: float = 0.025) -> int:
    for s in range(n + 1):
        if binom.sf(s - 1, n, null) <= alpha:
            return s
    return n + 1


def cp_product_power(n: int, discordance: float, delta: float, endpoint: str) -> float:
    """Explicit independent-CP product reconstruction, not private code parity.

    Each factor receives alpha=.0125; select the rectangle's correct product
    corner according to the sign of 2*theta-1. Completion lower>.05;
    violation upper<.02. These definitions are fully disclosed in the receipt.
    """
    total = 0.0
    theta = (1 + delta / discordance) / 2
    for m in range(n + 1):
        r_lower, r_upper = cp_lower(m, n, 0.0125), cp_upper(m, n, 0.0125)
        if endpoint == "completion":
            # The lower bound increases with the number of positive discordances.
            lo, hi = -1, m + 1
            while hi - lo > 1:
                j = (lo + hi) // 2
                sign = 2 * cp_lower(j, m, 0.0125) - 1
                bound = (r_lower if sign >= 0 else r_upper) * sign
                if bound > 0.05:
                    hi = j
                else:
                    lo = j
            probability = binom.sf(hi - 1, m, theta)
        elif endpoint == "violation":
            lo, hi = -1, m + 1
            while hi - lo > 1:
                j = (lo + hi) // 2
                sign = 2 * cp_upper(j, m, 0.0125) - 1
                bound = (r_upper if sign >= 0 else r_lower) * sign
                if bound < 0.02:
                    lo = j
                else:
                    hi = j
            probability = binom.cdf(lo, m, theta)
        else:
            raise ValueError(endpoint)
        total += binom.pmf(m, n, discordance) * probability
    return float(total)


def hypothetical_powers(n: int, critical: Fraction) -> dict:
    q_cut = required_successes(n, 0.10)
    h1 = sum(
        binom.pmf(m, n, 0.15) * binom.sf(required_successes(m, 0.5) - 1, m, 0.8)
        for m in range(q_cut, n + 1)
    )
    cuts = cutoffs(n, critical)
    violation = sum(
        binom.pmf(m, n, 0.025) * binom.cdf(cuts[m], m, 0.5) for m in range(n + 1)
    )
    completion = cp_product_power(n, 0.20, 0.12, "completion")
    return {
        "scope": "HYPOTHETICAL_DESIGN_RATES_NOT_PHYSICAL_RESULTS",
        "n": n,
        "q_alternative": 0.15,
        "eta_alternative": 0.8,
        "completion_discordance": 0.20,
        "completion_delta": 0.12,
        "violation_discordance": 0.025,
        "violation_delta": 0,
        "h1_min_erasures": q_cut,
        "h1_joint_power": float(h1),
        "zero_event_CP_upper_alpha_025": cp_upper(0, n, 0.025),
        "h2_completion_CP_product_power": completion,
        "h2_violation_exact_score_power": float(violation),
        "h2_old_CP_product_power": cp_product_power(n, 0.025, 0, "violation"),
        "h2_joint_union_lower": max(0, float(completion + violation - 1)),
        "CP_product_scope": "Explicit reconstruction; private V4.4 code absent",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--n", type=int, default=1024)
    args = parser.parse_args()
    if not 1 <= args.n <= 1024:
        parser.error(
            "This bounded checker supports 1..1024; no automatic cohort registration"
        )
    start = time.monotonic()
    oracle_results = small_oracles()
    critical = Fraction(11, 5)
    nums, denominator = bernstein_numerators(args.n, critical)
    peak = max(nums)
    with localcontext() as ctx:
        ctx.prec = 50
        upper = str(Decimal(peak) / Decimal(denominator))
    compact = {
        "common_denominator": str(denominator),
        "numerators": [str(num) for num in nums],
    }
    encoded = (json.dumps(compact, sort_keys=True) + "\n").encode()
    certificate_path = args.output.with_name("bernstein_integer_certificate.json")
    certificate_path.parent.mkdir(parents=True, exist_ok=True)
    certificate_path.write_bytes(encoded)
    result = {
        "status": "INDEPENDENT_PUBLIC_DESIGN_CHECK_NOT_MANUSCRIPT_VERIFICATION",
        "n": args.n,
        "epsilon": "1/50",
        "critical": "-11/5",
        "bernstein_coefficients": len(nums),
        "all_nonnegative": min(nums) >= 0,
        "maximum_coefficient": upper,
        "argmax_k": nums.index(peak),
        "exact_integer_type_I_below_025": 40 * peak < denominator,
        "integer_certificate_sha256": hashlib.sha256(encoded).hexdigest(),
        "small_n_exhaustive_oracles": oracle_results,
        "independent_rational_oracles_passed": len(oracle_results),
        "hypothetical_powers": hypothetical_powers(args.n, critical),
        "old_CP_product_n640_power": cp_product_power(640, 0.025, 0, "violation"),
        "known_signal_116_of_128_CP_lower_95": cp_lower(116, 128, 0.05),
        "known_signal_pipeline_executed": False,
        "realized_n_warning": "Critical value must be independently recalibrated/registered for any other n before outcomes",
        "wall_seconds": time.monotonic() - start,
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {k: v for k, v in result.items() if k != "small_n_exhaustive_oracles"},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
