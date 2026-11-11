"""A transient cache file must not crash the meter or leave a child running."""

import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def command_module(monkeypatch):
    monkeypatch.syspath_prepend(str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(
        "reboot_command", SCRIPTS / "reboot_command.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_disk_meter_tolerates_disappearing_temporary_files(tmp_path, monkeypatch):
    module = command_module(monkeypatch)
    present, vanished = tmp_path / "present", tmp_path / "vanished"
    present.write_bytes(b"123")
    monkeypatch.setattr(module, "new_files", lambda root: [present, vanished])
    assert module.logical_bytes(tmp_path) == 3


def test_driver_cleanup_terminates_and_reaps_child(monkeypatch):
    module = command_module(monkeypatch)
    child = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(30)"], start_new_session=True
    )
    try:
        module.stop_child(child)
        assert child.returncode is not None and child.poll() is not None
    finally:
        if child.poll() is None:
            child.kill()
        child.wait()


def test_driver_error_still_records_cpu_exit_and_reaps_worker(tmp_path, monkeypatch):
    module = command_module(monkeypatch)
    (tmp_path / "initial.json").write_text(json.dumps({"started_epoch": time.time()}))
    children = []
    original_popen = subprocess.Popen

    def launch(*args, **kwargs):
        child = original_popen(*args, **kwargs)
        children.append(child)
        return child

    def fail_monitor(*args, **kwargs):
        raise ValueError("injected monitor failure")

    monkeypatch.setattr(module.subprocess, "Popen", launch)
    monkeypatch.setattr(module.psutil, "Process", fail_monitor)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "reboot_command.py",
            "--root",
            str(tmp_path),
            "--name",
            "failure",
            "--",
            sys.executable,
            "-c",
            "import time; time.sleep(30)",
        ],
    )
    assert module.main() == 124
    row = json.loads((tmp_path / "commands.jsonl").read_text())
    assert row["termination_reason"] == "driver_error:ValueError"
    assert row["cpu_seconds"] > 0
    assert children and all(child.poll() is not None for child in children)
