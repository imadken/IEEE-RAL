"""E3 selection in an isolated process with neither outcomes nor explanations."""

import argparse
from pathlib import Path

from dsre_closure_common import (
    INPUTS,
    ROOT,
    TASKS,
    output,
    passed,
    read,
    route,
    save,
)
from dsre_closure_evaluate import select_sample


def prepare():
    registration = read(ROOT / "registration.json")
    frozen = read(ROOT / "E1/calibration_freeze.json")["tasks"]
    original = read(ROOT / "E0/recount/independent_numbers.json")["results"]
    for task in TASKS:
        model = frozen[task]["model"]
        summaries = []
        for query in frozen[task]["queries"]:
            if query["obligation"] != "useful":
                continue
            x = query["x"]
            cell = route(model["partition"], x)
            good = passed(model["leaves"][str(cell)]["bounds"], "useful")
            summaries.append(
                {
                    "x": x,
                    "action": "r" if good else "c",
                    "withholding": None
                    if good
                    else {
                        "reasons": output(model, x, "useful", None)["withholding"][
                            "reasons"
                        ]
                    },
                }
            )
        save(
            ROOT / "E3/selection_inputs" / (task + ".json"),
            {
                "registration": {"sample_namespace": registration["sample_namespace"]},
                "parents": [
                    {"parent_id": r["parent_id"], "x": r["x"]}
                    for r in original[task]["paired_test"]
                ],
                "summary": summaries,
                "no_explanation_or_outcome_fields": True,
            },
        )


def select():
    from dual_rec.evidence_aware.views import guard_data_access

    allowed = [ROOT / "E3/selection_inputs" / (task + ".json") for task in TASKS]
    accesses = guard_data_access(Path("results"), allowed, additional_roots=(ROOT,))
    for task, path in zip(TASKS, allowed, strict=True):
        packet = read(path)
        assert all(set(p) == {"parent_id", "x"} for p in packet["parents"])
        assert all(set(q) == {"x", "action", "withholding"} for q in packet["summary"])
        table = {
            ("useful", tuple(q["x"])): {
                "output": {"action": q["action"], "withholding": q["withholding"]}
            }
            for q in packet["summary"]
        }
        _, selection = select_sample(
            task, packet["parents"], table, packet["registration"]
        )
        selection["successful_reads"] = list(accesses)
        selection["input_sha256"] = dict(INPUTS)
        selection["isolation"] = (
            "Selector cannot open original outcomes, E1 certificate text, E0 future labels, or evaluator traces"
        )
        save(ROOT / "E3" / (task + "_sample_selection.json"), selection)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("prepare", "select"))
    args = parser.parse_args()
    (prepare if args.stage == "prepare" else select)()
