"""Independent audit must detect ledger tampering and unequal paired states."""

import gzip
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "recoverbench_audit", ROOT / "scripts/recoverbench_audit.py"
)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def fixture(root, *, unequal=False):
    directory = root / "transfer-audit"
    (directory / "traces").mkdir(parents=True)
    data = root / "data"
    data.mkdir()
    actions = np.zeros((2, 7))
    np.savez(data / "source.npz", actions=actions, states=np.zeros((2, 3)))
    target_dir = data / "training_scenes/stack/scenes"
    target_dir.mkdir(parents=True)
    np.savez(target_dir / "target.npz", post_sim_state=np.zeros(3))
    rows = []
    for number in range(2):
        initial = np.array([0.05, float(number) if unequal else 0.0, 0.0])
        path = directory / "traces" / f"trace-{number}.jsonl.gz"
        with gzip.open(path, "wt") as stream:
            stream.write(
                json.dumps(
                    {
                        "kind": "initial",
                        "state": initial.tolist(),
                        "official_success": True,
                    }
                )
                + "\n"
            )
            for step in (1, 2):
                stream.write(
                    json.dumps(
                        {
                            "kind": "step",
                            "step": step,
                            "action": actions[step - 1].tolist(),
                            "state": [0.05 + step * 0.05, initial[1], 0.0],
                            "official_success": False,
                            "contacts": 0,
                        }
                    )
                    + "\n"
                )
        # Two source records can share one target; initial true is diagnostic only.
        source_member = f"source-{number}.npz"
        (data / source_member).write_bytes((data / "source.npz").read_bytes())
        rows.append(
            {
                "pair": {
                    "target_task": "stack",
                    "target_scene": "target",
                    "target_error": "error",
                    "target_degree": "D0",
                    "source_member": source_member,
                    "source_scene": "source",
                    "source_degree": "D0",
                },
                "source_sha256": module.digest(data / source_member),
                "target_sha256": module.digest(target_dir / "target.npz"),
                "trace_path": str(path.relative_to(root)),
                "trace_sha256": module.digest(path),
                "initial_success": True,
                "success": False,
                "first_success_step": None,
                "executed_steps": 2,
                "contacts_total": 0,
                "post_neutral_state_sha256": hashlib.sha256(
                    initial.astype("<f8").tobytes()
                ).hexdigest(),
                "fingerprint_matches": False,
            }
        )
    (directory / "status.json").write_text(json.dumps({"pairs": 2}))
    (directory / "outcomes.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in rows)
    )
    return rows


def test_initial_goal_is_not_itself_an_executed_recovery(tmp_path):
    fixture(tmp_path)
    result = module.audit(tmp_path, "transfer-audit")
    assert result["status"] == "PASS"
    assert not any(row["success"] for row in result["recomputed"])


def test_false_success_ledger_is_detected(tmp_path):
    rows = fixture(tmp_path)
    rows[0]["success"] = True
    (tmp_path / "transfer-audit/outcomes.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in rows)
    )
    result = module.audit(tmp_path, "transfer-audit")
    assert result["status"] == "FAIL"
    assert any("Outcome differs" in str(error) for error in result["mismatches"])


def test_unequal_target_restorations_cannot_be_called_paired(tmp_path):
    fixture(tmp_path, unequal=True)
    result = module.audit(tmp_path, "transfer-audit")
    assert result["status"] == "FAIL"
    assert any("identical post-neutral" in str(error) for error in result["mismatches"])
