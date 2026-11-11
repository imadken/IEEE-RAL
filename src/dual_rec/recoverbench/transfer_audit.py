"""Execute the bounded training-only release-interface fallback, without selectors."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, field_validator

from .replay import SourceCase, load_original, validate_arrays

_LOGGER = logging.getLogger(__name__)


class AuditPair(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    target_task: Literal["pick_place", "stack"]
    target_scene: str
    target_error: str
    target_degree: Literal["D0", "D1"]
    target_source_group: str
    source_member: str
    source_scene: str
    source_degree: Literal["D0", "D1"]

    @field_validator("source_member")
    @classmethod
    def local_source(cls, value: str) -> str:
        return SourceCase.local_member(value)

    @field_validator("source_scene", "target_scene")
    @classmethod
    def local_scene(cls, value: str) -> str:
        return SourceCase.local_scene(value)


class TransferRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    pair: AuditPair
    source_sha256: str
    target_sha256: str
    post_neutral_state_sha256: str
    fingerprint_matches: bool
    fingerprint_error: str | None
    initial_success: bool
    success: bool
    first_success_step: int | None
    executed_steps: int = Field(ge=0, le=500)
    source_actions: int = Field(ge=1)
    termination: str
    contacts_total: int = Field(ge=0)
    max_contact_penetration_m: float = Field(ge=0)
    initial_eef: list[float]
    final_eef: list[float]
    trace_path: str
    trace_sha256: str
    wall_seconds: float = Field(ge=0)


def execute_pair(root, output, env, wrapper, pair, pair_index):
    before = time.perf_counter()
    source_path = root / "data" / pair.source_member
    target_path = (
        root
        / "data/training_scenes"
        / pair.target_task
        / "scenes"
        / (pair.target_scene + ".npz")
    )
    metadata = json.loads(target_path.with_suffix(".json").read_text())
    with np.load(source_path, allow_pickle=False) as source:
        actions = source["actions"].copy()
        validate_arrays(actions, source["states"])
    with np.load(target_path, allow_pickle=False) as target:
        initial = target["post_sim_state"].copy()
    np.random.seed(3101)
    env.reset()
    wrapper.set_sim_state_flat(initial)
    try:
        wrapper.verify_fingerprint(
            wrapper.get_fingerprint(), metadata["env_fingerprint"]
        )
        matches, mismatch = True, None
    except Exception as exc:
        _LOGGER.exception("Retaining fingerprint rejection in diagnostic transfer")
        matches, mismatch = False, str(exc)
    # The only uncounted physics action is prescribed by the release protocol.
    env.step(wrapper.get_neutral_action())
    initial_success = bool(env._check_success())
    state = wrapper.get_sim_state_flat()
    state_hash = hashlib.sha256(np.asarray(state, dtype="<f8").tobytes()).hexdigest()
    initial_eef = wrapper.get_eef_pos().tolist()
    trace_path = output / "traces" / f"pair-{pair_index:04d}.jsonl.gz"
    first_success = None
    contacts = steps = 0
    penetration = 0.0
    termination = (
        "source_controls_exhausted" if len(actions) <= 500 else "action_budget"
    )
    with gzip.open(trace_path, "xt") as trace:
        trace.write(
            json.dumps(
                {
                    "kind": "initial",
                    "state": state.tolist(),
                    "official_success": initial_success,
                }
            )
            + "\n"
        )
        for action in actions[:500]:
            env.step(action)
            steps += 1
            state = wrapper.get_sim_state_flat()
            if not np.isfinite(state).all():
                raise ValueError("Nonfinite state during actual transfer execution")
            success = bool(env._check_success())
            contacts += int(env.sim.data.ncon)
            for contact in env.sim.data.contact[: env.sim.data.ncon]:
                penetration = max(penetration, max(0.0, -float(contact.dist)))
            trace.write(
                json.dumps(
                    {
                        "kind": "step",
                        "step": steps,
                        "action": action.tolist(),
                        "state": state.tolist(),
                        "eef": wrapper.get_eef_pos().tolist(),
                        "official_success": success,
                        "contacts": int(env.sim.data.ncon),
                    }
                )
                + "\n"
            )
            if success:
                first_success, termination = steps, "first_official_success"
                break
    return TransferRecord(
        pair=pair,
        source_sha256=hashlib.sha256(source_path.read_bytes()).hexdigest(),
        target_sha256=hashlib.sha256(target_path.read_bytes()).hexdigest(),
        post_neutral_state_sha256=state_hash,
        fingerprint_matches=matches,
        fingerprint_error=mismatch,
        initial_success=initial_success,
        success=first_success is not None,
        first_success_step=first_success,
        executed_steps=steps,
        source_actions=len(actions),
        termination=termination,
        contacts_total=contacts,
        max_contact_penetration_m=penetration,
        initial_eef=initial_eef,
        final_eef=wrapper.get_eef_pos().tolist(),
        trace_path=str(trace_path.relative_to(root)),
        trace_sha256=hashlib.sha256(trace_path.read_bytes()).hexdigest(),
        wall_seconds=time.perf_counter() - before,
    )


def run(root: Path, output: Path):
    if output.exists():
        raise FileExistsError("Do not replace unsuccessful transfer audits")
    registration = json.loads(
        (root / "fallback_transfer_registration.json").read_text()
    )
    pairs = [AuditPair.model_validate(p) for p in registration["pairs"]]
    output.mkdir(parents=True)
    (output / "traces").mkdir()
    count = errors = 0
    for task in ("pick_place", "stack"):
        np.random.seed(3101)
        env, wrapper = load_original(root, task)
        try:
            for pair in (p for p in pairs if p.target_task == task):
                count += 1
                try:
                    row = execute_pair(
                        root, output, env, wrapper, pair, count
                    ).model_dump(mode="json")
                except Exception as exc:
                    _LOGGER.exception("Retaining failed diagnostic transfer")
                    row = {"pair": pair.model_dump(), "error": repr(exc)}
                    errors += 1
                with (output / "outcomes.jsonl").open("a") as stream:
                    stream.write(json.dumps(row, allow_nan=False) + "\n")
                print(
                    json.dumps(
                        {
                            "pairs": count,
                            "task": task,
                            "success": row.get("success"),
                            "steps": row.get("executed_steps"),
                            "error": row.get("error"),
                        }
                    ),
                    flush=True,
                )
        finally:
            env.close()
    status = {
        "status": "COMPLETED_TRAINING_INTERFACE_DIAGNOSTIC",
        "pairs": count,
        "errors": errors,
        "registration_sha256": hashlib.sha256(
            (root / "fallback_transfer_registration.json").read_bytes()
        ).hexdigest(),
        "scope": "Identity control-tape transfer; no policy comparison; fingerprint mismatches invalidate official benchmark claims; contact counts/penetration are diagnostics, not proven safety violations",
    }
    (output / "status.json").write_text(json.dumps(status, indent=2))
    return status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.root.resolve(), args.output.resolve())))


if __name__ == "__main__":
    main()
