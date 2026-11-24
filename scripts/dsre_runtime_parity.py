"""Independent full recorded-channel parity audit; no selector or simulator import."""

import argparse
import json
import time
from collections import Counter
from pathlib import Path

from dsre_source_risk_audit import audit_cell, difference, gz, read, sha, state_equal


def exact_memory_and_model(old, new):
    assert old["model"] == new["model"], "model provenance/readback drift"
    keys = {
        "rng_states",
        "rng_aliases",
        "torch",
        "controller",
        "controller_transient",
        "drive_targets",
        "drive_velocities",
        "_episode_seed",
        "_main_seed",
        "_elapsed_steps",
    }
    assert keys <= old["canonical_controller_memory"].keys(), (
        "historical memory channel absent"
    )
    assert keys <= new["canonical_controller_memory"].keys(), (
        "new memory channel absent"
    )
    assert old["canonical_controller_memory"] == new["canonical_controller_memory"], (
        "controller/RNG/drive memory drift"
    )


def compare_cell(old_dir, new_dir):
    old = gz(old_dir / "screen.json.gz")
    new = gz(new_dir / "screen.json.gz")
    exact_memory_and_model(old, new)
    assert old["prefix_actions"] == new["prefix_actions"], (
        "prefix action ordering drift"
    )
    assert old["cell"] == new["cell"] and old["offset_x_m"] == new["offset_x_m"]
    counts, _ = audit_cell(new, new_dir)
    for index, (left, right) in enumerate(
        zip(old["prefix"], new["prefix"], strict=True)
    ):
        try:
            state_equal(left, right)
        except AssertionError as error:
            raise AssertionError(
                f"Historical prefix state/contact/time/observation mismatch at {index}"
            ) from error
        counts["historical_prefix_states"] += 1
    state_equal(old["canonical_start"], new["canonical_start"])
    labels = []
    for action in ("continue", "recover"):
        original = gz(old_dir / "repeat0" / (action + ".json.gz"))
        current = gz(new_dir / (action + ".json.gz"))
        assert original["model_edit"] == current["model_edit"]
        assert original["controller_memory"] == current["controller_memory"]
        assert original["terminal_success"] == current["terminal_success"]
        assert original["initial_tcp"] == current["initial_tcp"]
        state_equal(original["start"], current["start"])
        for index, (left, right) in enumerate(
            zip(original["prefix_states"], current["prefix_states"], strict=True)
        ):
            try:
                state_equal(left, right)
            except AssertionError as error:
                raise AssertionError(
                    f"Historical {action} reconstruction mismatch at {index}"
                ) from error
        for index, (left, right) in enumerate(
            zip(original["frames"], current["frames"], strict=True)
        ):
            try:
                state_equal(left["state"], right["state"])
                assert difference(left["action"], right["action"]) < 2e-6
                assert (
                    difference(left["before_observation"], right["before_observation"])
                    <= 1e-4
                )
            except AssertionError as error:
                raise AssertionError(
                    f"Historical {action} future/action/observation mismatch at {index}"
                ) from error
            counts["historical_future_states"] += 1
        labels.append(current["terminal_success"])
    return counts, labels


def audit_parent(root, index, namespace=None):
    plan = read(root / "study_plan.json")
    space = namespace or root
    seed = plan["qualification_seeds"][index]
    progress_path = space / "progress" / f"qualification-{index:04d}.json"
    progress = read(progress_path)
    assert progress["status"] == "COMPLETE" and progress["seed"] == seed
    directory = space / "qualification" / str(seed)
    assert sha(directory / "decision.json") == progress["decision_sha256"]
    decision = read(directory / "decision.json")
    assert decision["source_freeze_sha256"] == sha(root / "source_freeze.json")
    counts = Counter()
    hashes = {}
    labels = []
    for condition, _ in plan["profiles"]:
        current = directory / condition
        original = Path(plan["qualification_reference"]) / str(seed) / condition
        try:
            assert sha(current / "screen.json.gz") == decision["screens"][condition]
            cell_counts, cell_labels = compare_cell(original, current)
        except (AssertionError, KeyError, FileNotFoundError, ValueError) as error:
            failure = {
                "seed": seed,
                "condition": condition,
                "error": str(error),
                "historical": str(original),
                "new": str(current),
                "epoch": time.time(),
            }
            target = root / "first_parity_disagreement.json"
            if not target.exists():
                target.write_text(json.dumps(failure, indent=2) + "\n")
            raise
        counts.update(cell_counts)
        labels += cell_labels
        for path in (
            list(current.glob("*.json.gz"))
            + list(original.glob("screen.json.gz"))
            + list((original / "repeat0").glob("*.json.gz"))
        ):
            hashes[str(path)] = sha(path)
    assert counts["cells"] == 5 and counts["continuations"] == 10
    result = {
        "passed": True,
        "seed": seed,
        "namespace": str(space),
        "counts": dict(counts),
        "terminal_labels": labels,
        "model": "PASS",
        "contact": "PASS",
        "controller": "PASS",
        "saved_simulator_and_torch_rng": "PASS",
        "observations": "PASS",
        "full_recorded_physics_trajectory": "PASS",
        "terminal_success": "PASS",
        "global_python_numpy_rng_scope": "Historical seed setup preserved; historical raw packets store simulator/batched and Torch RNG, not separate global Python/NumPy states.",
        "source_sha256": hashes,
        "epoch": time.time(),
    }
    target = space / f"parity-{index:04d}.json"
    assert not target.exists(), "Do not overwrite an earlier parity attempt"
    target.write_text(json.dumps(result, indent=2) + "\n")
    return result


def seal(root):
    registration = read(root / "qualification_registration.json")
    reports = [root / f"parity-{i:04d}.json" for i in range(3)]
    reports += [root / "stability" / f"repeat{i}" / "parity-0000.json" for i in (1, 2)]
    assert registration["seeds"] == [13000000, 13000001, 13000002]
    assert not (root / "first_parity_disagreement.json").exists()
    counts = Counter()
    for path in reports:
        report = read(path)
        assert report["passed"] and report["epoch"] >= registration["registered_epoch"]
        counts.update(report["counts"])
    freeze = read(root / "source_freeze.json")
    for kind in ("source_sha256", "input_sha256"):
        for name, digest in freeze[kind].items():
            assert sha(Path(name)) == digest, name
    assert counts["cells"] == 25 and counts["continuations"] == 50
    result = {
        "passed": True,
        "parents": 3,
        "unique_inspected_parents": 3,
        "additional_fresh_process_repetitions": 2,
        "counts": dict(counts),
        "reports_sha256": {str(p): sha(p) for p in reports},
        "old_failed_root": read(root / "initial.json")["old_failed_root"],
        "process_configuration_sha256": sha(root / "execution_configuration.json"),
        "production_selector_imported": False,
        "epoch": time.time(),
    }
    assert not (root / "qualification_audit.json").exists()
    (root / "qualification_audit.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("parent", "seal"))
    p.add_argument("root", type=Path)
    p.add_argument("--index", type=int, default=0)
    p.add_argument("--namespace", type=Path)
    a = p.parse_args()
    result = (
        audit_parent(a.root, a.index, a.namespace)
        if a.mode == "parent"
        else seal(a.root)
    )
    print(
        json.dumps(
            {
                k: v
                for k, v in result.items()
                if k not in ("source_sha256", "reports_sha256")
            }
        )
    )
