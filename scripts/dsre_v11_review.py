"""Derived wrapper identities, physical witnesses and supervisor figures."""

import argparse
import csv
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from dual_rec.dsre.calibration import FrozenRouter, gate


def load(path):
    return json.loads(path.read_text())


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def review(root):
    config = load(Path("config/dsre_v11.json"))
    old = Path(config["input_root"])
    pairs = {
        r["id"]: r
        for r in (
            json.loads(s)
            for s in (old / "qualified_pairs.jsonl").read_text().splitlines()
        )
    }
    rows = {}
    support_diagnostics = []
    times = {}
    for p in sorted((root / "crossfit").glob("*.json")):
        part = load(p)
        signatures = {tuple(r["features"]) for r in part["table"]["rows"]}
        checked = set()
        for prediction in part["predictions"]:
            d = part["decisions"][prediction["decision_id"]]
            if prediction["id"] not in checked:
                checked.add(prediction["id"])
                x = d["query"]["features"]
                compatible = [
                    r
                    for r in part["table"]["rows"]
                    if all(
                        v is None or r["features"][i] is None or v == r["features"][i]
                        for i, v in enumerate(x)
                    )
                ]
                support_diagnostics.append(
                    {
                        "id": prediction["id"],
                        "task": prediction["task"],
                        "fold": prediction["fold"],
                        "unseen_exact_signature": tuple(x) not in signatures,
                        "conservative_full_support": len(compatible),
                        "full_support_below_two": len(compatible) < 2,
                        "missing_query_values": sum(v is None for v in x),
                    }
                )
            name = (
                d["method"]
                + "/"
                + (f"{d['beta']:g}" if d["beta"] is not None else "boundary")
            )
            rows.setdefault(prediction["id"], {})[name] = d["result"]
        for d in part["decisions"].values():
            name = (
                d["method"]
                + "/"
                + (f"{d['beta']:g}" if d["beta"] is not None else "boundary")
            )
            times.setdefault(name, []).append(d["cold_latency_ms"])
    identities = {}
    for task in ("PickCube-v1", "PushCube-v1"):
        for beta in (0.1, 0.05):
            equal = total = provisional = provisional_b5 = 0
            differences = []
            for id, methods in rows.items():
                if pairs[id]["task"] != task:
                    continue
                s = methods["S_strict/0"]
                b = methods[f"B1_two_v11/{beta:g}"]
                actual = methods[f"DSRE_v11/{beta:g}"]
                wrapper = s if s["action"] or not b["action"] else b
                fields = ("action", "evidence", "support")
                same = all(actual[f] == wrapper[f] for f in fields)
                equal += same
                total += 1
                if not same:
                    differences.append(id)
                if actual["tier"] == "PROVISIONAL_RISK_RULE":
                    provisional += 1
                    provisional_b5 += all(
                        actual[f] == methods[f"B5_v11/{beta:g}"][f] for f in fields
                    )
            identities[task + f"/beta={beta:g}"] = {
                "checkpoints": total,
                "strict_then_two_literal_equal_decisions": equal,
                "differences": differences,
                "risk_tier_cases": provisional,
                "risk_tier_exact_B5_matches": provisional_b5,
                "claim": "Same deterministic S-first wrapper and same witnesses/calibration can reproduce this output. Not a new trained baseline or a new hypothesis.",
            }
    save(root / "wrapper_equivalence.json", identities)
    save(
        root / "query_support_diagnostics.json",
        {
            "records": support_diagnostics,
            "task_counts": {
                task: {
                    "queries": sum(r["task"] == task for r in support_diagnostics),
                    "unseen_exact_signature": sum(
                        r["task"] == task and r["unseen_exact_signature"]
                        for r in support_diagnostics
                    ),
                    "full_support_below_two": sum(
                        r["task"] == task and r["full_support_below_two"]
                        for r in support_diagnostics
                    ),
                }
                for task in ("PickCube-v1", "PushCube-v1")
            },
            "note": "An unseen or sparse full signature is a data/support diagnostic, not proof of physical incompatibility; a supported broader rule may still qualify.",
        },
    )
    profiles = load(root / "observability.json")
    witness_examples = []
    for name, p in profiles.items():
        for group in p["signatures"]:
            causes = group["compatible_causes"]
            for kind, ids in (
                ("INADEQUATE_REPERTOIRE", causes["inadequate_witness"]),
                ("OBSERVATION_AMBIGUITY", causes["ambiguity_witness"]),
            ):
                if ids:
                    witness_examples.append(
                        {
                            "scope": name,
                            "signature": group["signature"],
                            "kind": kind,
                            "records": [
                                {
                                    "id": id,
                                    "features": pairs[id][
                                        {
                                            "pose_proprioception": "features",
                                            "plus_privileged": "privileged_features",
                                            "coarse_geometry": "coarse_features",
                                        }[name.split("/")[1]]
                                    ],
                                    "outcomes": pairs[id]["outcomes"],
                                }
                                for id in ids
                            ],
                            "explanation": "At least one compatible row has neither adequate action."
                            if kind == "INADEQUATE_REPERTOIRE"
                            else "Two compatible rows require disjoint actions; no common deterministic action is universally adequate.",
                        }
                    )
    old_certificate = load(old / "witness_examples.json")
    save(
        root / "witness_examples.json",
        {
            "signature_witnesses": witness_examples,
            "historical_examples_preserved": str(old / "witness_examples.json"),
            "historical_examples_sha256": hashlib.sha256(
                (old / "witness_examples.json").read_bytes()
            ).hexdigest(),
            "historical_examples": old_certificate,
        },
    )
    definition = {
        "source_freeze_sha256": hashlib.sha256(
            (root / "experiment_freeze.json").read_bytes()
        ).hexdigest(),
        "full_table_outputs_sha256": hashlib.sha256(
            (root / "full_table_router.json").read_bytes()
        ).hexdigest(),
        "beta": 0.1,
        "tier_priority": "S then R then U",
        "calibration": "NO_INDEPENDENT_COHORT",
        "new_model_fits": 0,
        "future_observations_per_parent": 1,
    }
    router_hash = hashlib.sha256(
        json.dumps(definition, sort_keys=True).encode()
    ).hexdigest()
    frozen = FrozenRouter(
        sha256=router_hash,
        training_parent_ids=tuple(sorted({r["group"] for r in pairs.values()})),
        strata=tuple(config["calibration"]["strata"]),
        alpha=0.1,
        delta=0.05,
    )
    save(
        root / "frozen_router.json",
        {
            "definition": definition,
            "router": frozen.model_dump(mode="json"),
            "current_gates": [
                gate(t, a, router_hash, None).model_dump(mode="json")
                for t in ("PickCube-v1", "PushCube-v1")
                for a in ("continue", "recover")
            ],
        },
    )
    directory = root / "figures"
    directory.mkdir(exist_ok=True)
    with (root / "frontier.csv").open() as stream:
        points = list(csv.DictReader(stream))
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6), constrained_layout=True)
    styles = {
        "S_strict": ("black", "X"),
        "DSRE_v11": ("tab:blue", "*"),
        "B5_v11": ("tab:orange", "o"),
        "B1_two_v11": ("tab:brown", "+"),
        "CART_depth1": ("tab:green", "s"),
        "CART_depth2": ("tab:red", "^"),
        "CART_depth3": ("tab:purple", "v"),
        "full_signature": ("tab:gray", "D"),
    }
    for ax, task in zip(axes, ("PickCube-v1", "PushCube-v1"), strict=True):
        for method, (color, marker) in styles.items():
            selected = [
                p
                for p in points
                if p["task"] == task
                and p["method_point"].split("/")[0] == method
                and p["unacceptable_rate"]
            ]
            ax.scatter(
                [100 * float(p["coverage"]) for p in selected],
                [100 * float(p["unacceptable_rate"]) for p in selected],
                s=[35 + 25 * float(p["mean_literals"]) for p in selected],
                label=method,
                c=color,
                marker=marker,
                alpha=0.8,
                zorder=10 if method == "DSRE_v11" else 9 if method == "S_strict" else 3,
            )
        ax.set(
            title=task,
            xlabel="Recommended checkpoints (%)",
            ylabel="Unacceptable / recommended (%)",
            xlim=(-3, 103),
            ylim=(-0.5, 31),
        )
        ax.grid(alpha=0.2)
    axes[1].legend(fontsize=7, loc="upper left")
    fig.suptitle(
        "Exploratory frozen operating points; size indicates evidence length; no calibration"
    )
    fig.savefig(directory / "joint_frontier.png", dpi=160)
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), constrained_layout=True)
    for ax, task in zip(axes, ("PickCube-v1", "PushCube-v1"), strict=True):
        labels = ["primary", "privileged", "coarse"]
        values = [
            profiles[task + "/" + v]["summary"]
            for v in ("pose_proprioception", "plus_privileged", "coarse_geometry")
        ]
        adequate = [p["equal_adequate"]["mass"] for p in values]
        overlap = [p["equal_overlap"]["mass"] for p in values]
        inadequate = [
            p["equal_inadequate"]["mass"] - p["equal_overlap"]["mass"] for p in values
        ]
        ax.bar(labels, adequate, label="Universal adequate")
        ax.bar(labels, inadequate, bottom=adequate, label="Inadequacy only")
        ax.bar(
            labels,
            overlap,
            bottom=[a + b for a, b in zip(adequate, inadequate, strict=True)],
            label="Inadequacy + action ambiguity",
        )
        ax.set(title=task, ylabel="Checkpoint mass (N=422)", ylim=(0, 440))
    axes[1].legend(fontsize=7)
    fig.suptitle(
        "Finite exact-signature ceiling; diagnostic variants do not replace primary"
    )
    fig.savefig(directory / "observability_ceiling.png", dpi=160)
    plt.close(fig)
    save(
        root / "review_completed.json",
        {
            "status": "COMPLETE",
            "wrapper_comparisons": sum(x["checkpoints"] for x in identities.values()),
            "wrapper_equal": sum(
                x["strict_then_two_literal_equal_decisions"]
                for x in identities.values()
            ),
            "figures": 2,
            "signature_witnesses": len(witness_examples),
        },
    )
    print(json.dumps(load(root / "review_completed.json")), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    if (args.root / "completion_manifest.json").exists():
        raise SystemExit("Evidence sealed")
    review(args.root)
