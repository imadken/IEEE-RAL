"""The study supervisor leaves no timed-out subprocess and honors sealing."""

import json
import subprocess
import sys
import time


def test_bounded_command_preserves_timeout_and_refuses_sealed_evidence(tmp_path):
    (tmp_path / "initial.json").write_text(json.dumps({"started_epoch": time.time()}))
    command = [
        sys.executable,
        "scripts/monitoring_command.py",
        "--root",
        str(tmp_path),
        "--name",
        "timeout",
        "--timeout",
        "1",
        "--",
        sys.executable,
        "-c",
        "import time; time.sleep(20)",
    ]
    result = subprocess.run(
        command, check=False, capture_output=True, text=True, timeout=8
    )
    assert result.returncode == 124
    row = json.loads((tmp_path / "commands.jsonl").read_text())
    assert row["termination_reason"] == "timeout"
    assert row["cpu_seconds"] >= 0
    assert row["wall_seconds"] < 5
    assert row["exit_status"] == 124
    (tmp_path / "completion_manifest.json").write_text("{}")
    result = subprocess.run(
        command, check=False, capture_output=True, text=True, timeout=5
    )
    assert result.returncode != 0
    assert "sealed" in result.stderr
    assert len((tmp_path / "commands.jsonl").read_text().splitlines()) == 1
