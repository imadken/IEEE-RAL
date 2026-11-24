"""Secondary binary-outcome obligations; does not modify DSRE adequacy or routing."""

from collections import defaultdict
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .calibration import upper_bound

METHODS = ("DSRE_risk", "CART2_beta10")
CLAIMS = tuple(
    (method, action, obligation)
    for method in METHODS
    for action, obligation in (
        ("recover", "absolute"),
        ("recover", "nondegradation"),
        ("continue", "absolute"),
    )
)
DELTA = 0.05 / 6
TARGET = 0.1


class ObligationBound(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    method: Literal["DSRE_risk", "CART2_beta10"]
    action: Literal["continue", "recover"]
    obligation: Literal["absolute", "nondegradation"]
    assigned_parents: int = Field(ge=0)
    error_parents: int = Field(ge=0)
    upper: float = Field(ge=0, le=1)
    delta: float = DELTA
    target: float = TARGET
    qualified: bool
    complete_calibration: bool


def claim_key(method: str, action: str, obligation: str) -> str:
    return f"{method}|{action}|{obligation}"


def calibrate(rows: list[dict], expected_parents: tuple[int, ...]) -> dict[str, dict]:
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["seed"]].append(row)
    complete = set(grouped) == set(expected_parents) and all(
        len(v) == 5 and len({r["condition"] for r in v}) == 5 for v in grouped.values()
    )
    output = {}
    for method, action, obligation in CLAIMS:
        assigned = errors = 0
        for group in grouped.values():
            selected = [r for r in group if r["proposals"][method] == action]
            if not selected:
                continue
            assigned += 1
            if obligation == "nondegradation":
                bad = any(r["c"] and not r["r"] for r in selected)
            else:
                bad = any(not r["r" if action == "recover" else "c"] for r in selected)
            errors += bad
        upper = upper_bound(errors, assigned, DELTA)
        output[claim_key(method, action, obligation)] = ObligationBound(
            method=method,
            action=action,
            obligation=obligation,
            assigned_parents=assigned,
            error_parents=errors,
            upper=upper,
            qualified=bool(complete and assigned and upper <= TARGET),
            complete_calibration=complete,
        ).model_dump(mode="json")
    return output


def annotated_action(
    proposal: str | None, method: str, mode: str, bounds: dict
) -> dict:
    if proposal is None:
        return {
            "action": None,
            "annotation": "UNQUALIFIED",
            "task_adequacy_status_unchanged": True,
        }
    absolute = bounds[claim_key(method, proposal, "absolute")]["qualified"]
    allowed = absolute
    annotation = "ABSOLUTE_SUCCESS_QUALIFIED" if absolute else "UNQUALIFIED"
    if proposal == "recover" and mode == "nondegradation" and not absolute:
        allowed = bounds[claim_key(method, proposal, "nondegradation")]["qualified"]
        if allowed:
            annotation = "TASK_NONDEGRADATION_QUALIFIED_ONLY"
    if mode not in ("absolute", "nondegradation"):
        raise ValueError("Only registered obligation modes are permitted")
    return {
        "action": proposal if allowed else None,
        "annotation": annotation,
        "task_adequacy_status_unchanged": True,
    }
