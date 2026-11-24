"""Independent numerical audit isolation and signed/undefined interval cases."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def script_path(monkeypatch):
    monkeypatch.syspath_prepend(str(Path("scripts").resolve()))


def test_independent_auditor_never_imports_production_selector_or_simulator():
    env = dict(os.environ, PYTHONPATH="src:scripts", OPENBLAS_NUM_THREADS="1")
    child = subprocess.run(
        [
            sys.executable,
            "-c",
            "from dsre_source_risk_numerical import isolated_imports; assert not isolated_imports()['production_selector_or_simulator_imported']",
        ],
        env=env,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert child.returncode == 0, child.stderr


def test_direct_index_audit_matches_parent_bootstrap_with_harm_and_zero_support(
    tmp_path,
):
    from dsre_source_risk_analysis import metrics, summarize
    from dsre_source_risk_numerical import intervals

    records, rows = [], []
    for parent, action, c, r in (
        ("a", "recover", True, False),
        ("b", None, False, False),
    ):
        for condition in (
            "nominal",
            "offset001",
            "offset002",
            "offset003",
            "offset_minus002",
        ):
            row = {
                "outcomes": {"continue_value": c, "recover_value": r},
                "initial_success": True,
                "features": [True] * 6,
                "optional_features": [True] * 6,
                "condition": condition,
            }
            rows.append(row)
            records.append(
                {
                    "group": parent,
                    "scenario": "clean",
                    "mode": "gated",
                    "method": "m",
                    "condition": condition,
                    "counts": metrics(row, action),
                }
            )
    tables, parents = summarize(records)
    categories = {}
    for condition in (
        "ALL",
        "nominal",
        "offset001",
        "offset002",
        "offset003",
        "offset_minus002",
    ):
        factor = 5 if condition == "ALL" else 1
        categories[condition] = {
            "continue_only": factor,
            "neither_success": factor,
            "rows": 2 * factor,
        }
    (tmp_path / "test_analysis.json").write_text(
        json.dumps(
            {
                "tables": tables,
                "paired_contrasts": {},
                "paired_outcome_categories": categories,
            }
        )
    )
    checked = intervals(tmp_path, parents, rows)
    assert checked["independent_direct_index_intervals"] == 6 * 8
    assert (
        tables["clean|gated|m|ALL"]["intervals"]["matched_recovery_effect"]["estimate"]
        == -1
    )
    assert (
        tables["clean|gated|m|ALL"]["intervals"]["required_recovery_recall"]["estimate"]
        is None
    )
