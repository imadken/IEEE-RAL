"""Execute released recovery controls through the original benchmark interface."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import logging
import sys
import time
import traceback
from pathlib import Path
from typing import Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, field_validator

_LOGGER = logging.getLogger(__name__)


class SourceCase(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)
    archive_member: str
    task_name: Literal["pick_place", "stack"]
    scene_id: str
    error_name: str
    degree: Literal["D0", "D1"]

    @field_validator("archive_member")
    @classmethod
    def local_member(cls, value: str) -> str:
        path = Path(value)
        if (
            path.is_absolute()
            or ".." in path.parts
            or "\\" in value
            or ":" in value
            or path.suffix != ".npz"
        ):
            raise ValueError("Source archive member must be a relative NPZ path")
        return value

    @field_validator("scene_id")
    @classmethod
    def local_scene(cls, value: str) -> str:
        if (
            not value
            or Path(value).name != value
            or value in {".", ".."}
            or "\\" in value
        ):
            raise ValueError("Scene identity must be a local basename")
        return value


class ReplayRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    record_id: str
    case: SourceCase
    variant: Literal["recorded_start_no_neutral", "official_start_one_neutral"]
    repeat: int = Field(ge=0)
    source_sha256: str
    action_horizon: int = Field(ge=0)
    executed_steps: int = Field(ge=0)
    official_success_observed: bool
    initial_success: bool
    first_success_step: int | None
    fingerprint_matches: bool
    fingerprint_error: str | None
    current_fingerprint: dict
    expected_fingerprint: dict
    state_alignment: Literal["T_pre_action", "T_plus_one"]
    stored_eef_axis_std: list[float]
    physical_reference_axis_std: list[float]
    initial_eef_error_m: float = Field(ge=0)
    reference_max_eef_error_m: float = Field(ge=0)
    reference_mean_eef_error_m: float = Field(ge=0)
    initialization_max_state_error: float = Field(ge=0)
    source_scene_max_state_difference: float = Field(ge=0)
    final_official_success: bool
    physics_time_advance: float
    action_dimensions: int
    trace_path: str
    trace_sha256: str
    measured_wall_seconds: float = Field(ge=0)
    error: str | None = None


def validate_arrays(actions: np.ndarray, states: np.ndarray) -> str:
    if actions.ndim != 2 or actions.shape[1] != 7 or len(actions) == 0:
        raise ValueError("Expected a nonempty T by 7 OSC/gripper action array")
    if states.ndim != 2 or len(states) not in {len(actions), len(actions) + 1}:
        raise ValueError("State alignment must be T pre-action states or T+1 states")
    if not np.isfinite(actions).all() or not np.isfinite(states).all():
        raise ValueError("Nonfinite source controls or states")
    return "T_pre_action" if len(states) == len(actions) else "T_plus_one"


def load_original(root: Path, task: str):
    """Import the separate pinned simulator only in a worker using that environment."""
    source = next((root / "upstream/source").iterdir())
    sys.path.insert(0, str(source))
    import mujoco
    import robosuite
    import yaml
    from error_benchmark.framework.env_wrapper import EnvWrapper
    from error_benchmark.scripts.utils.script_utils import create_env

    if mujoco.__version__ != "2.3.2" or robosuite.__version__ != "1.4.1":
        raise ValueError("Original MuJoCo 2.3.2 / robosuite 1.4.1 required")
    config = yaml.safe_load(
        (source / "error_benchmark/configs/tasks" / f"{task}.yaml").read_text()
    )
    env = create_env(
        config,
        str(root / "data/seed_demos" / f"{task}.hdf5"),
        enable_camera=False,
        has_renderer=False,
    )
    return env, EnvWrapper(env, config)


def replay_one(root, output, env, wrapper, case, variant, repeat, references):
    before = time.perf_counter()
    path = root / "data" / case.archive_member
    with np.load(path, allow_pickle=False) as arrays:
        actions = arrays["actions"].copy()
        states = arrays["states"].copy()
        eef = arrays["eef_positions"].copy()
    alignment = validate_arrays(actions, states)
    if len(actions) > 1500:
        raise ValueError("Registered source action cap exceeded; do not replace")
    scene = root / "data/training_scenes" / case.task_name / "scenes" / case.scene_id
    metadata = json.loads(scene.with_suffix(".json").read_text())
    with np.load(scene.with_suffix(".npz"), allow_pickle=False) as arrays:
        registered_scene_state = arrays["post_sim_state"].copy()
    if case.archive_member not in references:
        # This is an offline kinematic audit, never a control rollout or recovery.
        env.reset()
        reference = []
        for state in states:
            wrapper.set_sim_state_flat(state)
            reference.append(wrapper.get_eef_pos().copy())
        references[case.archive_member] = np.asarray(reference)
    reference = references[case.archive_member]
    np.random.seed(3101)
    env.reset()
    wrapper.set_sim_state_flat(states[0])
    residual = float(np.max(np.abs(wrapper.get_sim_state_flat() - states[0])))
    current = wrapper.get_fingerprint()
    try:
        wrapper.verify_fingerprint(current, metadata["env_fingerprint"])
        matches, mismatch = True, None
    except Exception as exc:
        _LOGGER.exception("Retaining source fingerprint mismatch")
        matches, mismatch = False, str(exc)
    if variant == "official_start_one_neutral":
        env.step(wrapper.get_neutral_action())
    initial_success = bool(env._check_success())
    start_time = float(env.sim.data.time)
    initial_error = float(np.linalg.norm(wrapper.get_eef_pos() - reference[0]))
    record_id = f"{case.task_name}-{Path(case.archive_member).stem}-{variant}-{repeat}"
    trace_path = output / "traces" / (record_id + ".jsonl.gz")
    trace_path.parent.mkdir(exist_ok=True)
    errors = []
    first_success = None
    execution_error = None
    steps = 0
    with gzip.open(trace_path, "xt") as trace:
        trace.write(
            json.dumps(
                {
                    "kind": "initial",
                    "state": wrapper.get_sim_state_flat().tolist(),
                    "eef": wrapper.get_eef_pos().tolist(),
                    "official_success": initial_success,
                }
            )
            + "\n"
        )
        for index, action in enumerate(actions):
            try:
                env.step(action)
                state = wrapper.get_sim_state_flat()
                if not np.isfinite(state).all():
                    raise ValueError("Nonfinite executed simulator state")
                success = bool(env._check_success())
                steps += 1
                if success and first_success is None:
                    first_success = steps
                if index + 1 < len(reference):
                    errors.append(
                        float(
                            np.linalg.norm(wrapper.get_eef_pos() - reference[index + 1])
                        )
                    )
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
            except Exception as exc:
                _LOGGER.exception("Retaining source control failure")
                execution_error = repr(exc)
                break
    return ReplayRecord(
        record_id=record_id,
        case=case,
        variant=variant,
        repeat=repeat,
        source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        action_horizon=len(actions),
        executed_steps=steps,
        official_success_observed=first_success is not None,
        initial_success=initial_success,
        first_success_step=first_success,
        fingerprint_matches=matches,
        fingerprint_error=mismatch,
        current_fingerprint=current,
        expected_fingerprint=metadata["env_fingerprint"],
        state_alignment=alignment,
        stored_eef_axis_std=np.std(eef, axis=0).tolist(),
        physical_reference_axis_std=np.std(reference, axis=0).tolist(),
        initial_eef_error_m=initial_error,
        reference_max_eef_error_m=max(errors, default=initial_error),
        reference_mean_eef_error_m=float(np.mean(errors)) if errors else initial_error,
        initialization_max_state_error=residual,
        source_scene_max_state_difference=float(
            np.max(np.abs(states[0] - registered_scene_state))
        ),
        final_official_success=bool(env._check_success()),
        physics_time_advance=float(env.sim.data.time) - start_time,
        action_dimensions=env.action_dim,
        trace_path=str(trace_path.relative_to(root)),
        trace_sha256=hashlib.sha256(trace_path.read_bytes()).hexdigest(),
        measured_wall_seconds=time.perf_counter() - before,
        error=execution_error,
    )


def run(root: Path, output: Path):
    if output.exists():
        raise FileExistsError("Preserve every source-qualification attempt")
    output.mkdir(parents=True)
    registration = json.loads(
        (root / "source_qualification_registration.json").read_text()
    )
    cases = [
        SourceCase.model_validate(row)
        for row in registration["selected_source_records"]
    ]
    count = errors = 0
    for task in registration["tasks"]:
        np.random.seed(3101)
        env, wrapper = load_original(root, task)
        references = {}
        try:
            for case_index, case in enumerate(c for c in cases if c.task_name == task):
                for variant in registration["source_variants"]:
                    for repeat in range(3 if case_index == 0 else 1):
                        try:
                            record = replay_one(
                                root,
                                output,
                                env,
                                wrapper,
                                case,
                                variant,
                                repeat,
                                references,
                            ).model_dump(mode="json")
                        except Exception as exc:
                            _LOGGER.exception("Retaining source record failure")
                            errors += 1
                            record = {
                                "case": case.model_dump(),
                                "variant": variant,
                                "repeat": repeat,
                                "error": repr(exc),
                                "traceback": traceback.format_exc(),
                            }
                        with (output / "outcomes.jsonl").open("a") as stream:
                            stream.write(json.dumps(record, allow_nan=False) + "\n")
                        count += 1
                        print(
                            json.dumps(
                                {
                                    "count": count,
                                    "task": task,
                                    "variant": variant,
                                    "success": record.get("official_success_observed"),
                                    "error": record.get("error"),
                                    "fingerprint": record.get("fingerprint_matches"),
                                }
                            ),
                            flush=True,
                        )
        finally:
            env.close()
    status = {
        "status": "COMPLETED_DIAGNOSTIC_REPLAY",
        "records": count,
        "record_errors": errors,
        "source_candidates": len(cases),
        "registration_sha256": hashlib.sha256(
            (root / "source_qualification_registration.json").read_bytes()
        ).hexdigest(),
        "scope": "Source control replay; fingerprint failures are not waived or official benchmark outcomes",
    }
    (output / "status.json").write_text(json.dumps(status, indent=2))
    return status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.root.resolve(), args.output.resolve())))


if __name__ == "__main__":
    main()
