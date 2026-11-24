"""Independent closure algebra and exhaustive ordinary-rule instrumentation.

No production inference or simulator imports. Original experiments are read-only.
"""

import gzip
import hashlib
import itertools
import json
import lzma
import os
import time
import zlib
from pathlib import Path
from typing import Literal

import numpy as np
from pydantic import BaseModel, ConfigDict
from scipy.optimize import brentq, linprog
from scipy.stats import binom

ROOT = Path(os.environ.get("DSRE_CLOSURE_OUTPUT", "research/dsre_experimental_closure"))
OLD = Path("results/dsre-evidence-aware/20261117-prospective")
NEW = Path("results/dsre-evidence-aware/20261118-final-science")
TASKS = ("PickCube-v1", "PushCube-v1")
OBLIGATIONS = ("harm_only", "completion", "useful")
INPUTS = {}
ASSUMPTIONS = [
    "independent parents",
    "stationary observation protocol",
    "fixed macros",
    "randomized assignment and overlap",
    "discovery independent of calibration",
]
FAMILY = "per-task .025 logged + .025 paired, simultaneous frozen leaves"


class ClosureRegistration(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    base_commit: str
    branch: str
    created_epoch: float
    alpha: Literal[0.1] = 0.1
    eta: Literal[0.05] = 0.05
    max_wall_hours: Literal[12] = 12
    max_new_artifact_bytes: int = 2 * 1024**3
    new_physics_allowed: Literal[False] = False
    new_controller_fits_allowed: Literal[False] = False
    source_budgets: tuple[int, ...] = (128, 256, 512, 1024)
    source_order_namespace: str = "DSRE-CLOSURE-E2-PARENT-v1"
    source_arm_namespace: str = "DSRE-CLOSURE-E2-ARM-v1"
    sample_namespace: str = "DSRE-CLOSURE-E3-SAMPLE-v1"
    finite_sample_namespace: str = "DSRE-CLOSURE-E4-SMALL-C-v1"
    radii_mm: tuple[int, ...] = (0, 5, 10)
    contract_source: str = "Full scientific-supervisor closure contract supplied in this conversation, 18 November 2026"
    absent_editorial_inputs: tuple[str, ...] = (
        "V4 REVIEWER_RISK_REGISTER.md",
        "DSRE_RSS2027_METHOD_FIRST_STAGE1_REVISION_20261118.zip",
        "latest methodology-first blueprint distinct from the available scientific story lock",
    )


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    path = Path(path)
    if path.exists():
        b = path.read_bytes()
        INPUTS[str(path)] = hashlib.sha256(b).hexdigest()
        return json.loads(gzip.decompress(b) if path.suffix == ".gz" else b)
    assert path.suffix == ".gz", path
    meta_path = Path(str(path) + ".archive.json")
    meta = read(meta_path)
    xz = path.with_suffix(".xz")
    compressed = xz.read_bytes()
    INPUTS[str(xz)] = hashlib.sha256(compressed).hexdigest()
    assert INPUTS[str(xz)] == meta["xz_sha256"]
    b = lzma.decompress(compressed)
    assert hashlib.sha256(b).hexdigest() == meta["decoded_sha256"]
    # Cryptographically link decoded traces to the ORIGINAL sealed gzip bytes.
    compressor = zlib.compressobj(6, zlib.DEFLATED, -15)
    rebuilt = bytes.fromhex(meta["header"]) + compressor.compress(b)
    if meta["sync_flush"]:
        rebuilt += compressor.flush(zlib.Z_SYNC_FLUSH)
    rebuilt += compressor.flush(zlib.Z_FINISH) + bytes.fromhex(meta["footer"])
    INPUTS[str(path)] = hashlib.sha256(rebuilt).hexdigest()
    assert INPUTS[str(path)] == meta["original_gzip_sha256"]
    return json.loads(b)


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(value, indent=2, allow_nan=False) + "\n").encode()
    if path.exists():
        assert path.read_bytes() == data, f"IMMUTABLE_CLOSURE_COLLISION: {path}"
    else:
        with path.open("xb") as stream:
            stream.write(data)


def hashed(namespace, task, parent):
    return hashlib.sha256(f"{namespace}:{task}:{parent}".encode()).hexdigest()


def paths(task):
    push = task == "PushCube-v1"
    base = NEW if push else OLD / "prospective" / task
    return {
        "base": base,
        "model": base / ("model_frozen.json" if push else "models/logged.json"),
        "calibration": base
        / ("learner/calibration.json" if push else "learner_records/calibration"),
        "discovery": base / "discovery_freeze.json",
        "test": base / ("records/test" if push else "test"),
        "physics": NEW / "physics" if push else OLD / "physics" / task,
    }


def cp(k, n, tail):
    if not n:
        return {"lo": 0.0, "hi": 1.0}
    low = (
        0.0
        if not k
        else brentq(lambda p: binom.sf(k - 1, n, p) - tail, 0, 1, xtol=1e-14)
    )
    high = (
        1.0 if k == n else brentq(lambda p: binom.cdf(k, n, p) - tail, 0, 1, xtol=1e-14)
    )
    return {"lo": low, "hi": high}


def lp(e):
    if e.get("source_type") == "uncontrolled_observational" or not e.get(
        "assumptions_supported", True
    ):
        raise ValueError("IDENTIFICATION_ASSUMPTION_UNSUPPORTED")
    if not e.get("overlap", True):
        raise ValueError("NO_OVERLAP")
    if (e.get("harm") or e.get("rescue")) and e.get(
        "source_type"
    ) != "qualified_simulator_pair":
        raise ValueError("COUNTERPART_SOURCE_MISMATCH")
    A, b = [], []
    for field, coefficient in [
        ("p0", [0, 0, 1, 1]),
        ("p1", [0, 1, 0, 1]),
        ("harm", [0, 0, 1, 0]),
        ("rescue", [0, 1, 0, 0]),
    ]:
        if e.get(field) is not None:
            A += [coefficient, [-v for v in coefficient]]
            b += [e[field]["hi"], -e[field]["lo"]]
    bounds, worlds = {}, {}
    for name, c, sign in [
        ("harm_lower", [0, 0, 1, 0], 1),
        ("harm_upper", [0, 0, 1, 0], -1),
        ("gain_lower", [0, 1, -1, 0], 1),
        ("gain_upper", [0, 1, -1, 0], -1),
        ("failure_upper", [1, 0, 1, 0], -1),
    ]:
        result = linprog(
            np.array(c) * sign,
            A_ub=A,
            b_ub=b,
            A_eq=[[1] * 4],
            b_eq=[1],
            bounds=(0, None),
            method="highs",
        )
        if not result.success:
            raise ValueError("INCONSISTENT_BOUNDS")
        assert result.x.min() >= -1e-9 and abs(result.x.sum() - 1) < 1e-9
        assert np.max(np.asarray(A) @ result.x - b) <= 1e-8
        assert abs(np.dot(c, result.x) - result.fun * sign) < 1e-9
        bounds[name] = float(result.fun * sign)
        worlds[name] = result.x.tolist()
    return dict(bounds, optimizers=worlds)


def calibrated(rows, pairs, k, leaf):
    if len({r["parent_id"] for r in rows}) != len(rows) or len(
        {r["parent_id"] for r in pairs}
    ) != len(pairs):
        raise ValueError("DUPLICATE_PARENT_IN_EVIDENCE_BLOCK")
    if any(r.get("propensity") != 0.5 for r in rows):
        raise ValueError("UNSUPPORTED_PROPENSITY")
    scopes = {
        json.dumps(r["source_scope"], sort_keys=True)
        for r in rows + pairs
        if "source_scope" in r
    }
    if len(scopes) > 1:
        raise ValueError("SCOPE_MISMATCH")
    arms = [[int(r["y"]) for r in rows if r["action"] == a] for a in ("c", "r")]
    tail = 0.025 / (4 * k)
    e = {
        "p0": cp(sum(arms[0]), len(arms[0]), tail),
        "p1": cp(sum(arms[1]), len(arms[1]), tail),
        "harm": cp(sum(r["yc"] and not r["yr"] for r in pairs), len(pairs), tail)
        if pairs
        else None,
        "rescue": cp(sum(not r["yc"] and r["yr"] for r in pairs), len(pairs), tail)
        if pairs
        else None,
        "source_type": "uncontrolled_observational"
        if any(r.get("source_type") == "uncontrolled_observational" for r in rows)
        else "qualified_simulator_pair"
        if pairs
        else "randomized_single_action",
        "scope": f"frozen_leaf:{leaf}",
        "assumptions_supported": True,
        "overlap": bool(pairs) or all(arms),
    }
    try:
        b = lp(e)
        reason = None
    except ValueError as error:
        b, reason = None, str(error)
    return {
        "evidence": e,
        "bounds": b,
        "failure": reason,
        "counts": [len(a) for a in arms] + [len(pairs)],
        "successes": [sum(a) for a in arms],
        "tail": tail,
        "parent_ids": {
            "c": [r["parent_id"] for r in rows if r["action"] == "c"],
            "r": [r["parent_id"] for r in rows if r["action"] == "r"],
            "pairs": [r["parent_id"] for r in pairs],
        },
    }


def passed(b, obligation):
    if b is None:
        return False
    if obligation == "completion":
        return b["failure_upper"] <= 0.1 + 1e-12
    if obligation == "harm_only":
        return b["harm_upper"] <= 0.1 + 1e-12
    assert obligation == "useful"
    return b["harm_upper"] <= 0.1 + 1e-12 and b["gain_lower"] >= 0.05 - 1e-12


def route(partition, x):
    if any(v is None for v in x):
        return None
    return partition["cells"][sum(int(v) << (len(x) - i - 1) for i, v in enumerate(x))]


def matching_scope(partition, literals):
    groups = {}
    for x, leaf in zip(
        itertools.product((False, True), repeat=len(partition["vocabulary"])),
        partition["cells"],
        strict=True,
    ):
        groups.setdefault(leaf, set()).add(all(x[i] == value for i, value in literals))
    if any(len(flags) != 1 for flags in groups.values()):
        return None
    return sorted(leaf for leaf, flags in groups.items() if True in flags)


def rule_library(partition, approved):
    # B7 enumerates all ternary feature states (absent, false, true), not DSRE's
    # per-query subset search. Complete Boolean-space membership is mandatory.
    rules = []
    for pattern in itertools.product(
        (None, False, True), repeat=len(partition["vocabulary"])
    ):
        literals = tuple((i, v) for i, v in enumerate(pattern) if v is not None)
        scope = matching_scope(partition, literals)
        if scope and set(scope) <= approved:
            rules.append((literals, scope))
    return sorted(
        rules,
        key=lambda r: (len(r[0]), tuple(i for i, _ in r[0]), tuple(v for _, v in r[0])),
    )


def b7_certificate(model, x, obligation, rules=None):
    partition, leaves = model["partition"], model["leaves"]
    if route(partition, x) is None:
        return None
    approved = {int(c) for c, v in leaves.items() if passed(v["bounds"], obligation)}
    rules = rule_library(partition, approved) if rules is None else rules
    for literals, scope in rules:
        if not all(x[i] == value for i, value in literals):
            continue
        removals = {}
        for i, _ in literals:
            other = matching_scope(partition, tuple(t for t in literals if t[0] != i))
            removals[partition["vocabulary"][i]] = (
                "conjunction splits a calibrated leaf"
                if other is None
                else "unqualified leaves admitted: "
                + str(sorted(set(other) - approved))
            )
        source = (
            "qualified_simulator_pair"
            if any(
                leaves[str(c)]["evidence"]["source_type"] == "qualified_simulator_pair"
                for c in scope
            )
            else "randomized_single_action"
        )
        return {
            "action": "r",
            "obligation": obligation,
            "evidence": [[partition["vocabulary"][i], bool(v)] for i, v in literals],
            "selected_leaf_scope": scope,
            "harm_upper": max(leaves[str(c)]["bounds"]["harm_upper"] for c in scope),
            "gain_lower": min(leaves[str(c)]["bounds"]["gain_lower"] for c in scope),
            "failure_upper": max(
                leaves[str(c)]["bounds"]["failure_upper"] for c in scope
            ),
            "source_type": source,
            "outcome_scope": model["source_scope"],
            "confidence_family": FAMILY,
            "assumptions": ASSUMPTIONS,
            "removal_witnesses": removals,
        }
    return None


def canonical(value):
    if isinstance(value, dict):
        return {k: canonical(v) for k, v in sorted(value.items())}
    if isinstance(value, (list, tuple)):
        return [canonical(v) for v in value]
    if isinstance(value, float):
        return round(value, 10)
    return value


def output(model, x, obligation, certificate, *, prefilter=False):
    """The IDENTICAL declared witness postprocessor for every compared method."""
    cell = route(model["partition"], x)
    if cell is None:
        return {
            "action": "c",
            "certificate": None,
            "withholding": {
                "reasons": ["UNAVAILABLE_OBSERVATIONS"],
                "unknown_channels": [i for i, v in enumerate(x) if v is None],
                "scope": None,
            },
        }
    leaf = model["leaves"][str(cell)]
    if prefilter:
        certificate = None
    if certificate is not None:
        return {"action": "r", "certificate": certificate, "withholding": None}
    b = leaf["bounds"]
    reasons = [leaf["failure"]] if b is None else []
    if b:
        if obligation in ("harm_only", "useful") and b["harm_upper"] > 0.1 + 1e-12:
            reasons.append(
                "HARM_UNAVOIDABLE_WITHIN_MODEL"
                if b["harm_lower"] > 0.1
                else "HARM_NOT_CERTIFIED"
            )
        if obligation == "useful" and b["gain_lower"] < 0.05 - 1e-12:
            reasons.append(
                "BENEFIT_UNSUPPORTED"
                if b["gain_upper"] < 0.05
                else "GAIN_NOT_CERTIFIED"
            )
        if obligation == "completion" and b["failure_upper"] > 0.1 + 1e-12:
            reasons.append("ABSOLUTE_RECOVERY_SUCCESS_NOT_CERTIFIED")
    if prefilter:
        reasons.append("FROZEN_DISCOVERY_GAIN_PREFILTER")
    return {
        "action": "c",
        "certificate": None,
        "withholding": {
            "reasons": reasons,
            "scope": [cell],
            "source_type": leaf["evidence"]["source_type"],
            "obligation": obligation,
            "support": leaf["counts"],
            "evidence": leaf["evidence"],
            "bounds": b,
        },
    }


def metrics(rows, actions):
    result = {
        "parents": len(rows),
        "recover": 0,
        "rescue": 0,
        "harm": 0,
        "futile": 0,
        "redundant": 0,
        "completion": 0,
    }
    for row, action in zip(rows, actions, strict=True):
        c, r = row["yc"], row["yr"]
        result["completion"] += int(r if action == "r" else c)
        if action == "r":
            result["recover"] += 1
            result[
                {
                    (False, False): "futile",
                    (False, True): "rescue",
                    (True, False): "harm",
                    (True, True): "redundant",
                }[c, r]
            ] += 1
    result["withheld"] = len(rows) - result["recover"]
    return result


def timed(call):
    start = time.perf_counter()
    result = call()
    return result, time.perf_counter() - start
