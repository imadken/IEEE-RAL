"""No empirical rates can be claimed after native source initialization fails."""

from pathlib import Path


def test_native_block_does_not_become_zero_risk_or_measured_coverage(monkeypatch):
    monkeypatch.syspath_prepend(str(Path("scripts").resolve()))
    from dsre_source_risk_blocked import unobserved_strata

    strata = unobserved_strata(["m", "cart"])
    assert len(strata) == 4
    assert all(x["assigned_parents"] == 0 and x["upper"] == 1 for x in strata.values())
    assert all(
        x["risk_point_estimate"] is None and not x["enabled"] for x in strata.values()
    )
