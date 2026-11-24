"""Independent fixed-prefix audit of predecision grasp controller/RNG memory."""

import gzip
import hashlib
import json
import os
from pathlib import Path


def load(path):
    with gzip.open(path, "rt") if str(path).endswith(".gz") else path.open() as f:
        return json.load(f)


def first_difference(a, b, path="controller_memory"):
    if type(a) is not type(b):
        return {"path": path, "screen": a, "assigned": b}
    if isinstance(a, dict):
        if a.keys() != b.keys():
            return {"path": path, "screen_keys": list(a), "assigned_keys": list(b)}
        for k in a:
            diff = first_difference(a[k], b[k], path + "." + k)
            if diff:
                return diff
    elif isinstance(a, list):
        if len(a) != len(b):
            return {"path": path, "screen_length": len(a), "assigned_length": len(b)}
        for i, (x, y) in enumerate(zip(a, b, strict=True)):
            diff = first_difference(x, y, f"{path}[{i}]")
            if diff:
                return diff
    elif a != b:
        return {"path": path, "screen": a, "assigned": b}
    return None


def main():
    root = Path("results/dsre-evidence-aware/20261117-prospective")
    out = root / "prospective/PickCube-v1"
    paths = sorted(
        (out / "calibration").glob("*.json"), key=lambda p: load(p)["spec"]["index"]
    )
    paths = [p for p in paths if load(p)["spec"]["index"] < 256]
    assert len(paths) == 256
    checked = 0
    failure = None
    for path in paths:
        record = load(path)
        spec = record["spec"]
        d = root / "physics/PickCube-v1/calibration" / str(spec["index"])
        if record["status"] != "COMPLETE":
            continue
        screen = load(d / "acquisition_screen.json.gz")
        assigned = load(d / "randomized_assigned.json.gz")
        difference = first_difference(
            screen["controller_memory"], assigned["controller_memory"]
        )
        if difference:
            failure = {
                "stage": "calibration_predecision_memory",
                "spec": spec,
                "status": "CONTROLLER_MEMORY_REPLAY_FAILURE",
                "first_difference": difference,
                "reason": "Independent predecision controller/RNG mismatch; halt entire task without selecting a complete-case calibration population.",
            }
            witness = (
                out
                / "guard_witnesses"
                / f"{spec['seed']}-calibration_predecision_memory.json"
            )
            witness.parent.mkdir(parents=True, exist_ok=True)
            with witness.open("x") as f:
                json.dump(failure, f, indent=2)
            try:
                os.link(witness, out / "SOURCE_GUARD_FAILURE.json")
            except FileExistsError:
                pass
            break
        checked += 1
    result = {
        "passed": failure is None,
        "fixed_registered_indices": [0, 255],
        "checked": checked,
        "failure": failure,
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "production_inference_imported": False,
    }
    with (root / "Pick_fixed256_controller_memory_audit.json").open("x") as f:
        json.dump(result, f, indent=2)
        f.write("\n")
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
