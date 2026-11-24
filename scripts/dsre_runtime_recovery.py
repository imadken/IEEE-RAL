"""Bounded, process-local native diagnostics for the frozen DSRE source.

No simulator, policy, driver or installed package is modified by this module.
"""

import argparse
import fcntl
import hashlib
import json
import os
import resource
import signal
import subprocess
import sys
import time
from pathlib import Path

from pydantic import BaseModel, Field

REBOOT_PACKAGES = (
    "results/reboot-phase/20261111T204459Z/env/lib/python3.12/site-packages"
)
ENV_FIELDS = (
    "PYTHONPATH",
    "LD_LIBRARY_PATH",
    "LD_PRELOAD",
    "VK_ICD_FILENAMES",
    "VK_DRIVER_FILES",
    "VK_LAYER_PATH",
    "VK_LOADER_DRIVERS_SELECT",
    "DISPLAY",
    "CUDA_VISIBLE_DEVICES",
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "XDG_RUNTIME_DIR",
    "SAPIEN_VULKAN_LIBRARY_PATH",
    "__EGL_VENDOR_LIBRARY_FILENAMES",
    "__EGL_VENDOR_LIBRARY_DIRS",
    "MPLCONFIGDIR",
)


class ProbeRecord(BaseModel):
    label: str
    command: list[str]
    process_configuration: dict[str, str | None]
    configuration_sha256: str
    started_epoch: float
    finished_epoch: float
    returncode: int
    timed_out: bool
    wall_seconds: float = Field(ge=0)
    cpu_seconds: float = Field(ge=0)
    peak_child_rss_kib: int
    invocation_domain: str


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def configured_environment(overrides=None, minimal=False):
    env = os.environ.copy()
    env.update(
        UV_CACHE_DIR="/tmp/dual-rec-uv-cache",
        PYTHONPATH="src:scripts:" + str(Path(REBOOT_PACKAGES).resolve()),
        OMP_NUM_THREADS="2",
        OPENBLAS_NUM_THREADS="1",
        MKL_NUM_THREADS="1",
        CUDA_VISIBLE_DEVICES="",
        PYTHONDONTWRITEBYTECODE="1",
        MPLCONFIGDIR="/tmp/dsre-source-risk-mpl",
    )
    if minimal:
        env["PYTHONPATH"] = "src:scripts"
    for key, value in (overrides or {}).items():
        if key not in ENV_FIELDS:
            raise ValueError("Unsupported process-local override: " + key)
        if value is None:
            env.pop(key, None)
        else:
            env[key] = value
    return env


def prevent_core_dump():
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))


def probe(
    root, label, command, timeout=90, overrides=None, minimal=False, domain="restricted"
):
    if not label.replace("_", "").replace("-", "").isalnum():
        raise ValueError("Simple unique label required")
    if not command or not 1 <= timeout <= 360:
        raise ValueError("Explicit foreground command and bounded timeout required")
    folder = root / "diagnostics"
    folder.mkdir(exist_ok=True)
    target = folder / (label + ".json")
    if target.exists() or target.with_suffix(".log").exists():
        raise ValueError("Prior diagnostic evidence is immutable")
    env = configured_environment(overrides, minimal)
    selected = {key: env.get(key) for key in ENV_FIELDS}
    signature = hashlib.sha256(
        json.dumps([command, selected, domain], sort_keys=True).encode()
    ).hexdigest()
    repeats = sum(
        json.loads(p.read_text())["configuration_sha256"] == signature
        for p in folder.glob("*.json")
    )
    if repeats >= 2:
        raise ValueError("At most two trials per diagnostic configuration")
    began = time.time()
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    prevent_core_dump()
    with Path("/tmp/reboot-overnight-ieeeral.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with target.with_suffix(".log").open("x") as log:
            child = subprocess.Popen(
                command,
                env=env,
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            timed_out = False
            try:
                status = child.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
                os.killpg(child.pid, signal.SIGTERM)
                try:
                    status = child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid, signal.SIGKILL)
                    status = child.wait()
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    record = ProbeRecord(
        label=label,
        command=command,
        process_configuration=selected,
        configuration_sha256=signature,
        started_epoch=began,
        finished_epoch=time.time(),
        returncode=status,
        timed_out=timed_out,
        wall_seconds=time.time() - began,
        cpu_seconds=after.ru_utime + after.ru_stime - before.ru_utime - before.ru_stime,
        peak_child_rss_kib=after.ru_maxrss,
        invocation_domain=domain,
    )
    target.write_text(record.model_dump_json(indent=2) + "\n")
    print(record.model_dump_json(), flush=True)
    return record


def emit(value):
    print(json.dumps(value), flush=True)


def child(mode):
    emit(
        {
            "phase": "child_started",
            "epoch": time.time(),
            "executable": sys.executable,
            "sys_path": sys.path,
            "environment": {key: os.environ.get(key) for key in ENV_FIELDS},
        }
    )
    if mode == "imports":
        import importlib
        import importlib.metadata

        loaded = {}
        for name in ("numpy", "torch", "sapien", "mani_skill", "pydantic"):
            module = importlib.import_module(name)
            loaded[name] = {
                "file": module.__file__,
                "version": importlib.metadata.version(
                    "mani-skill" if name == "mani_skill" else name
                ),
            }
            emit({"import_complete": name, **loaded[name]})
        import sapien.pysapien

        emit(
            {
                "native_extension": sapien.pysapien.__file__,
                "sha256": sha(Path(sapien.pysapien.__file__)),
            }
        )
        maps = sorted(
            {
                line.split()[-1]
                for line in Path("/proc/self/maps").read_text().splitlines()
                if ".so" in line and line.split()[-1].startswith("/")
            }
        )
        emit({"loaded_native_paths": maps})
    elif mode == "material":
        import sapien

        emit(
            {
                "phase": "before_material",
                "sapien": sapien.__file__,
                "constructor": sapien.render.RenderMaterial.__init__.__doc__,
            }
        )
        material = sapien.render.RenderMaterial(base_color=[1, 0, 0, 1])
        emit({"phase": "material_complete", "type": str(type(material))})
    elif mode == "scene":
        from mani_runner import make_env

        emit({"phase": "before_original_make_env"})
        env = make_env("PickCube-v1")
        try:
            emit({"phase": "original_make_env_complete"})
            env.reset(seed=13000000)
            emit({"phase": "explicit_old_seed_reset_complete"})
        finally:
            env.close()
    elif mode == "prefix":
        from overnight_pick import initial

        from dual_rec.overnight_pick import PickFault

        emit({"phase": "before_original_inspected_prefix"})
        case, frames = initial(13000000, PickFault(name="nominal", offset_x=0))
        emit(
            {
                "phase": "original_prefix_complete",
                "frames": len(frames),
                "initial_success": case["initial_success"],
            }
        )
    else:
        raise ValueError("Unknown isolated diagnostic")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    c = sub.add_parser("child")
    c.add_argument("kind", choices=("imports", "material", "scene", "prefix"))
    p = sub.add_parser("probe")
    p.add_argument("root", type=Path)
    p.add_argument("label")
    p.add_argument("--kind", choices=("imports", "material", "scene", "prefix"))
    p.add_argument("--timeout", type=int, default=90)
    p.add_argument("--minimal", action="store_true")
    p.add_argument("--domain", choices=("restricted", "host"), default="restricted")
    p.add_argument("--overrides", type=json.loads, default={})
    p.add_argument("command", nargs=argparse.REMAINDER)
    a = parser.parse_args()
    if a.mode == "child":
        child(a.kind)
    else:
        command = a.command[1:] if a.command[:1] == ["--"] else a.command
        if a.kind:
            if command:
                parser.error("Use --kind or an explicit command")
            command = [
                sys.executable,
                "-X",
                "faulthandler",
                str(Path(__file__).resolve()),
                "child",
                a.kind,
            ]
        probe(a.root, a.label, command, a.timeout, a.overrides, a.minimal, a.domain)
