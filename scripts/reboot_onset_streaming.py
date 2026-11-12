"""Deterministic C0/C1 replay of the same frozen phase monitor."""

import argparse
import json
from pathlib import Path

import numpy as np
import torch

from dual_rec.reboot.onset_specificity import OLD, read
from dual_rec.reboot.overnight_data import save_json
from dual_rec.reboot.overnight_replay import replay


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    root = parser.parse_args().root
    if (root / "completion_manifest.json").exists():
        raise SystemExit("Evidence sealed")
    torch.set_num_threads(2)
    examples = read(root, "annotation_review.json")
    outcomes = read(root, "outcomes.json")
    destination = root / "streaming"
    destination.mkdir(exist_ok=True)
    results = []
    selected = sorted(
        {
            (r["variant"], r["examples"][0]["group"])
            for r in examples
            if r["method"] == "P1" and r["examples"]
        }
    )
    for variant, group in selected:
        both = {}
        for rule in ("C0", "C1"):
            traces = list(
                replay(
                    OLD,
                    group,
                    variant=variant,
                    method="P1",
                    calibration_root=root,
                    calibration=rule,
                    alpha=0.1,
                )
            )
            path = destination / f"{variant}_{group.split(':')[1]}_{rule}.jsonl"
            with path.open("w") as stream:
                for trace in traces:
                    stream.write(json.dumps(trace) + "\n")
            both[rule] = traces
        risks = np.array([r["risk"] for r in both["C0"]])
        np.testing.assert_array_equal(risks, [r["risk"] for r in both["C1"]])
        expected = {
            r["rule"]: r
            for r in outcomes
            if r["group"] == group
            and r["variant"] == variant
            and r["method"] == "P1"
            and r["stress"] == "clean"
            and r["alpha"] == 0.1
        }
        fold = expected["C0"]["fold"]
        with np.load(
            OLD
            / "predictions"
            / f"fold{fold}"
            / variant
            / "clean/evaluation"
            / (group.split(":")[1] + ".npz")
        ) as data:
            discrepancy = float(np.max(np.abs(risks - data["P1"])))
        assert discrepancy < 1e-6
        alarms = {}
        for rule, traces in both.items():
            first = next((r["timestamp"] for r in traces if r["first_alarm"]), None)
            assert first == expected[rule]["alarm_time"]
            alarms[rule] = {
                "first_alarm": first,
                "status": expected[rule]["status"],
                "threshold": traces[0]["explanation"]["threshold"],
            }
        results.append(
            {
                "variant": variant,
                "group": group,
                "fold": fold,
                "identical_c0_c1_scores": True,
                "alarms": alarms,
                "maximum_batch_stream_difference": discrepancy,
                "mean_inference_ms": 1000
                * float(np.mean([r["inference_seconds"] for r in both["C1"]])),
            }
        )
    save_json(
        root / "streaming_parity.json",
        {
            "status": "PASS",
            "selection": "First hash per available C0 P1 review category, deduplicated",
            "examples": results,
        },
    )
    print(json.dumps(results))


if __name__ == "__main__":
    main()
