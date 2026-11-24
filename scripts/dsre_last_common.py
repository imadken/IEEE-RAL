"""Immutable final-campaign bookkeeping; no physics or inference imports."""

import hashlib
import json
import time
from pathlib import Path

ROOT = Path("results/dsre-evidence-aware/20261118-final-science")


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, indent=2, allow_nan=False) + "\n"
    if path.exists():
        assert path.read_text() == text, f"IMMUTABLE_COLLISION: {path}"
        return
    with path.open("x") as stream:
        stream.write(text)


def arm(seed):
    bit = hashlib.sha256(f"DSRE-FINAL-PUSH-ARM-v1:{seed}".encode()).digest()[0] >> 7
    return ("c", "r")[bit]


def pid(spec):
    return hashlib.sha256(
        f"DSRE-FINAL-PARENT-v1:{spec['task']}:{spec['seed']}".encode()
    ).hexdigest()


def timestamp():
    return time.time()
