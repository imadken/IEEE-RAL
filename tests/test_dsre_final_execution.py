"""Representation repair must preserve physical and provenance rejection guards."""

import copy
import gzip
import json
import time
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.fixture(autouse=True)
def script_path(monkeypatch):
    """Exercise entrypoints independently of the caller's PYTHONPATH."""
    monkeypatch.syspath_prepend(str(Path("scripts").resolve()))


@pytest.fixture
def recorded():
    from dsre_final_verify import load_trace
    from dsre_followup_batch import read

    summary = read(
        Path(
            "results/dsre-operational/20261114T140659Z/fresh/PickCube-v1/8000000-nominal/summary.json"
        )
    )
    raw = load_trace(summary)
    trace = raw["traces"]["continue"]
    execution = {
        "prefix_states": copy.deepcopy(raw["prefix"]),
        "start": copy.deepcopy(trace["start"]),
        "frames": copy.deepcopy(trace["frames"]),
        "controller_memory": copy.deepcopy(trace["controller_memory"]),
        "model_edit": copy.deepcopy(trace["model_edit"]),
        "initial_tcp": trace["initial_tcp"],
        "terminal_success": raw["outcomes"]["continue_value"],
    }
    return summary, raw, execution


def test_independent_verifier_accepts_full_recorded_execution(recorded):
    from dsre_final_verify import verify_execution

    summary, raw, execution = recorded
    proof = verify_execution(raw, execution, summary["task"], "continue")
    assert proof["future_states"] == 70 and proof["nonempty_contact_states"] > 0


@pytest.mark.parametrize(
    "mutation",
    ["contact", "numeric", "memory", "model", "source_action", "terminal", "future"],
)
def test_independent_verifier_rejects_physical_and_source_mutations(recorded, mutation):
    from dsre_final_verify import verify_execution

    summary, raw, execution = recorded
    if mutation == "contact":
        execution["prefix_states"][-1]["contacts"] = [["wrong", "contact"]]
    elif mutation == "numeric":
        execution["prefix_states"][-1]["position"][0] += 0.1
    elif mutation == "memory":
        execution["controller_memory"]["_elapsed_steps"][0] += 1
    elif mutation == "model":
        execution["model_edit"]["step"] += 1
    elif mutation == "source_action":
        raw["prefix_actions"][0][0] += 0.1
    elif mutation == "terminal":
        execution["terminal_success"] = not execution["terminal_success"]
    elif mutation == "future":
        execution["frames"][20]["state"]["qpos"][0][0] += 0.1
    with pytest.raises(AssertionError):
        verify_execution(raw, execution, summary["task"], "continue")


@pytest.mark.parametrize(
    "mutation",
    [
        None,
        "contact",
        "numeric",
        "memory",
        "model",
        "source_hash",
        "terminal",
        "future",
    ],
)
def test_actual_selected_executor_keeps_fail_closed_guards(
    recorded, tmp_path, monkeypatch, mutation
):
    import dsre_operational_batch as batch

    summary, raw, execution = recorded
    source = tmp_path / "source.json.gz"
    with gzip.open(source, "wt") as stream:
        json.dump(raw, stream)
    summary = summary | {"source": str(source), "source_sha256": batch.sha(source)}
    if mutation == "source_hash":
        summary["source_sha256"] = "0" * 64
    if mutation == "terminal":
        summary["outcomes"] = summary["outcomes"] | {"continue_value": False}
    frozen = {"tasks": {"PickCube-v1": {"1": {"selected": [0]}}}}
    batch.atomic(tmp_path / "frozen_routers.json", frozen)
    batch.atomic(tmp_path / "calibration_decision.json", {})

    class FakeWorld:
        def __init__(self, *args):
            self.index = 0
            self.env = SimpleNamespace(
                agent=SimpleNamespace(
                    tcp=SimpleNamespace(
                        pose=SimpleNamespace(p=execution["initial_tcp"])
                    )
                )
            )
            self.wrapped = SimpleNamespace()
            self.edit = copy.deepcopy(execution["model_edit"])
            if mutation == "model":
                self.edit["step"] += 1
            memory = copy.deepcopy(execution["controller_memory"])
            if mutation == "memory":
                memory["_elapsed_steps"][0] += 1
            self.adapter = SimpleNamespace(
                capture=lambda: SimpleNamespace(custom=memory)
            )

        def state(self, refresh=False):
            state = copy.deepcopy(
                execution["prefix_states"][min(self.index, len(raw["prefix"]) - 1)]
                if self.index < len(raw["prefix"])
                else execution["frames"][self.index - len(raw["prefix"])]["state"]
            )
            state["contacts"] = [tuple(c) for c in state["contacts"]]
            if mutation == "contact" and self.index == len(raw["prefix"]) - 1:
                state["contacts"] = [("wrong", "contact")]
            if mutation == "numeric" and self.index == len(raw["prefix"]) - 1:
                state["position"][0] += 0.1
            if mutation == "future" and self.index == len(raw["prefix"]) + 20:
                state["position"][0] += 0.1
            return state

        def step(self, command):
            self.index += 1
            return self.state()

        def close(self):
            pass

    monkeypatch.setattr(batch, "World", FakeWorld)
    monkeypatch.setattr(
        batch,
        "action_for",
        lambda world, action, i, tcp: raw["traces"]["continue"]["frames"][i]["action"],
    )
    router = SimpleNamespace(
        route=lambda p: {"DSRE_risk": {"action": "continue", "evidence": []}}
    )
    calibration = {"strata": {"DSRE_risk|PickCube-v1|continue": {"enabled": True}}}
    cell = batch.Cell(
        task=summary["task"], seed=summary["seed"], condition=summary["condition"]
    )
    directory = tmp_path / "selected" / cell.task / f"{cell.seed}-{cell.condition}"
    if mutation:
        with pytest.raises((ValueError, AssertionError)):
            batch.selected_branch(
                cell, summary, tmp_path, router, calibration, time.monotonic() + 30
            )
        assert (directory / "failure.json").exists()
    else:
        batch.selected_branch(
            cell, summary, tmp_path, router, calibration, time.monotonic() + 30
        )
        assert (
            batch.read(directory / "execution.json")["status"]
            == "QUALIFIED_SELECTED_EXECUTION"
        )


def test_duplicate_parent_is_rejected_before_physics(monkeypatch, tmp_path):
    import dsre_operational_batch as batch

    monkeypatch.setattr(batch, "verify_freeze", lambda root: None)
    batch.atomic(
        tmp_path / "fresh_seed_manifest.json",
        {"parents": [{"group": "PickCube-v1/1", "split": "test"}]},
    )
    (tmp_path / "parent_attempts").mkdir()
    (tmp_path / "parent_progress").mkdir()
    batch.atomic(tmp_path / "parent_attempts/0000.json", {})
    batch.atomic(tmp_path / "parent_progress/0000.json", {"status": "COMPLETE"})
    monkeypatch.setattr(
        batch, "World", lambda *a: pytest.fail("Repeated parent reached physics")
    )
    with pytest.raises(ValueError, match="repeated"):
        batch.parent_child(tmp_path, 0)


def test_clean_interruption_preserves_partial_and_only_allows_unused(
    monkeypatch, tmp_path
):
    import dsre_final_analysis as analysis
    import dsre_final_batch as batch

    for name in ("chunks", "parent_attempts", "parent_progress", "selected"):
        (tmp_path / name).mkdir()
    parent = {
        "index": 0,
        "group": "PickCube-v1/1",
        "task": "PickCube-v1",
        "seed": 1,
        "split": "test",
        "conditions": ["nominal", "offset002"],
    }
    batch.atomic(
        tmp_path / "fresh_seed_manifest.json",
        {
            "parents": [
                parent,
                parent | {"index": 1, "group": "PickCube-v1/2", "seed": 2},
            ]
        },
    )
    batch.atomic(tmp_path / "chunks/0000_started.json", {"sequence": 0})
    batch.atomic(tmp_path / "parent_attempts/0000.json", parent)
    monkeypatch.setattr(analysis, "audit_rows", lambda root, rows: {"status": "PASS"})
    batch.resume_interruption(tmp_path)
    assert (
        batch.read(tmp_path / "parent_progress/0000.json")["status"]
        == "PROCESS_INTERRUPTION_PARTIAL"
    )
    assert not (tmp_path / "parent_attempts/0001.json").exists()
    assert batch.read(tmp_path / "chunks/0000_complete.json")[
        "never_started_only_after_resume"
    ]


def test_interruption_does_not_clear_scientific_failure(tmp_path):
    import dsre_final_batch as batch

    for name in ("chunks", "parent_progress"):
        (tmp_path / name).mkdir()
    batch.atomic(tmp_path / "chunks/0000_started.json", {"sequence": 0})
    batch.atomic(tmp_path / "study_halt.json", {"reason": "selected parity failed"})
    with pytest.raises(AssertionError, match="Scientific halt"):
        batch.resume_interruption(tmp_path)


def test_noise_replicates_remain_two_parents_and_empty_proximity_is_unestimated(
    monkeypatch,
):
    monkeypatch.syspath_prepend(str(Path("scripts").resolve()))
    from dsre_final_analysis import sensitivity_intervals

    records = []
    for p in range(2):
        for scenario in ("clean", "noise005_r0", "noise005_r1", "noise005_r2"):
            records.append(
                {
                    "task": "PickCube-v1",
                    "method": "DSRE_risk",
                    "mode": "calibrated",
                    "scenario": scenario,
                    "group": str(p),
                    "id": str(p),
                    "action": None,
                    "proposed_action": "recover" if scenario != "clean" else None,
                    "successful": 0,
                    "unacceptable": 0,
                    "deferred": 1,
                    "action_stable": scenario == "clean",
                    "certificate_stable": True,
                    "false_confidence": 0,
                    "threshold_proximal": False,
                }
            )
    result = sensitivity_intervals(records)
    noise = result["PickCube-v1|DSRE_risk|calibrated|noise005|all"]
    assert noise["parents"] == 2 and noise["effective_checkpoints"] == 2
    assert noise["noise_replicates_averaged_within_parent"] == 3
    assert noise["action_unstable"]["value"] == 0  # Both gated actions remain STOP.
    assert noise["deferred"]["value"] == 1
    assert (
        result["PickCube-v1|DSRE_risk|calibrated|noise005|threshold_proximal"]["status"]
        == "NOT_ESTIMABLE_EMPTY_SUBGROUP"
    )
