"""Independent raw-state verifier for the postmortem-qualified continuation."""

import gzip
import json
from pathlib import Path

from dsre_followup_batch import read, sha
from dsre_paper_confirmation import difference, expected_action, state_equal
from dsre_paper_physics import sha as object_sha


def verify_execution(raw, execution, task, action):
    """Use the earlier independent equations, never the production comparator."""
    assert execution["controller_memory"] == raw["canonical_controller_memory"], (
        "controller memory"
    )
    assert execution["model_edit"] == raw["model"]["edit"], "model edit"
    assert object_sha(raw["model"]) == raw["model_sha256"], "model hash"
    assert object_sha(raw["prefix_actions"]) == raw["prefix_sha256"], (
        "source actions/hash"
    )
    actual_prefix = execution["prefix_states"]
    assert len(actual_prefix) == len(raw["prefix"]), "prefix length"
    for expected, actual in zip(raw["prefix"], actual_prefix, strict=True):
        state_equal(expected, actual)
    state_equal(raw["canonical_start"], execution["start"])
    assert len(execution["frames"]) == 70, "future length"
    previous = execution["start"]
    for i, (expected, actual) in enumerate(
        zip(raw["traces"][action]["frames"], execution["frames"], strict=True)
    ):
        command = expected_action(
            task, action, i, actual["before_observation"], execution["initial_tcp"]
        )
        assert difference(command, actual["action"]) <= 2e-6, "source action equation"
        assert difference(expected["action"], actual["action"]) <= 2e-6, "paired action"
        assert difference(previous["observation"], actual["before_observation"]) <= 1e-8
        state_equal(expected["state"], actual["state"])
        previous = actual["state"]
    assert (
        bool(previous["success"])
        == bool(execution["terminal_success"])
        == bool(raw["outcomes"][action + "_value"])
    ), "selected terminal success"
    return {
        "prefix_states": len(actual_prefix),
        "future_states": 70,
        "nonempty_contact_states": sum(bool(s["contacts"]) for s in actual_prefix),
    }


def verify_sources(root, filename="confirmation_freeze.json"):
    frozen = read(root / filename)
    for kind in ("source_sha256", "input_sha256"):
        for name, expected in frozen[kind].items():
            assert sha(Path(name)) == expected, name


def load_trace(summary):
    assert sha(Path(summary["source"])) == summary["source_sha256"], "source trace hash"
    with gzip.open(summary["source"], "rt") as stream:
        return json.load(stream)
