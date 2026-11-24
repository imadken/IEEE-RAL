"""Whitelisted single-action serialization and instrumented learner processes."""

import hashlib
import json
import os
import sys
from pathlib import Path

from .schema import OneAction


def hashed(namespace: str) -> int:
    return int.from_bytes(hashlib.sha256(namespace.encode()).digest(), "big")


def seed(task: str, phase: str, index: int) -> int:
    return (
        int.from_bytes(
            hashlib.sha256(
                f"dsre-evidence-v2:{task}:{phase}:{index}".encode()
            ).digest()[:4],
            "big",
        )
        >> 1
    )


def arm(task: str, parent: str) -> str:
    return ("c", "r")[hashed(f"dsre-evidence-v2:arm:{task}:{parent}") % 2]


def split(task: str, parent: str) -> str:
    value = hashed(f"dsre-evidence-v2:split:{task}:{parent}") % 10
    return "discovery" if value < 4 else "calibration" if value < 7 else "evaluation"


def condition(task: str, parent: str, count=5) -> int:
    return hashed(f"dsre-evidence-v2:condition:{task}:{parent}") % count


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def save(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def load_logs(path: Path) -> list[OneAction]:
    return [OneAction.model_validate(r) for r in json.loads(path.read_text())]


def guard_data_access(root: Path, allowed: list[Path], *, additional_roots=()):
    """Enforce experiment-data whitelist through CPython's nonremovable hook.

    This audits trusted research code, rather than sandboxing malicious Python.
    Libraries and source imports are separate from protected experiment data.
    """
    roots = (root.resolve(), *(p.resolve() for p in additional_roots))
    whitelist = {p.resolve() for p in allowed}
    reads = []

    def audit(event, args):
        if event != "open" or not isinstance(args[0], (str, bytes, os.PathLike)):
            return
        path = Path(os.fsdecode(args[0])).resolve()
        mode = args[1]
        flags = args[2]
        reading = (isinstance(mode, str) and ("r" in mode or "+" in mode)) or (
            mode is None and flags & os.O_ACCMODE != os.O_WRONLY
        )
        if reading and any(path.is_relative_to(root) for root in roots):
            if path not in whitelist:
                raise PermissionError("UNASSIGNED_OUTCOME_ACCESS: " + str(path))
            reads.append(str(path))

    sys.addaudithook(audit)
    return reads
