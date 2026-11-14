"""Raw-source-linked illustrative cases; no example-driven method changes."""

import argparse
import gzip
import json
from pathlib import Path

from dsre_followup_batch import atomic, read, sha
from dsre_paper_confirmation import predicates

from dual_rec.dsre.repair import ParentIndex, RepairQuery, RepairTable
from dual_rec.dsre.repair_oracle import Oracle


def inspect_source(row):
    assert sha(Path(row["source"])) == row["source_sha256"]
    with gzip.open(row["source"], "rt") as stream:
        raw = json.load(stream)
    p, o = predicates(raw["prefix"][0]["observation"], raw["prefix"][-1]["observation"])
    outcomes = {
        a + "_value": bool(
            raw["traces"][a + "/reference"]["frames"][-1]["state"]["success"]
        )
        for a in ("continue", "recover")
    }
    assert tuple(p) == tuple(row["features"]) and tuple(o) == tuple(
        row["optional_features"]
    )
    assert outcomes == row["outcomes"]
    return {
        "id": row["id"],
        "source": row["source"],
        "source_sha256": row["source_sha256"],
        "features": p,
        "optional_features": o,
        "outcomes": outcomes,
        "initial_success": bool(raw["prefix"][-1]["success"]),
        "checkpoint_time": raw["prefix"][-1]["time"],
    }


def examples(root):
    old = Path("results/dsre-followup/20261113T205403Z")
    previous = read(old / "physical_examples.json")["cases"]
    cases = []
    for row in previous:
        cases.append(
            inspect_source(row)
            | {
                "case": row["case"],
                "observed": row["observed"],
                "dx": row["dx"],
                "finite_reference_diagnoses": row["finite_reference_diagnoses"],
            }
        )
    assert (
        cases[0]["features"] == cases[1]["features"]
        and cases[0]["optional_features"][0] != cases[1]["optional_features"][0]
    )
    assert (
        cases[3]["features"] + cases[3]["optional_features"]
        == cases[4]["features"] + cases[4]["optional_features"]
    )
    dataset = [
        json.loads(s)
        for s in Path(
            "results/dsre-evidence-repair/20261113T180828Z/qualified_pairs.jsonl"
        )
        .read_text()
        .splitlines()
    ]
    indexed = {r["id"]: r for r in dataset}
    frozen = read(root / "frozen_routers.json")
    # First lexicographic real full-vocabulary reference-support obstruction.
    candidates = []
    for budgets in frozen["tasks"].values():
        s = budgets["1"]
        table = RepairTable.model_validate(s["full_table"])
        index = ParentIndex(table, s["parent_groups"], 2)
        for row in sorted(table.rows, key=lambda r: r.id):
            q = RepairQuery(scope=table.scope, features=row.features)
            d = index.diagnose(q)
            if d.status == "REFERENCE_INSUFFICIENT":
                Oracle(s["full_table"], s["parent_groups"]).verify(
                    q.model_dump(mode="json"), d.model_dump(mode="json")
                )
                candidates.append(
                    inspect_source(indexed[row.id])
                    | {
                        "case": "F",
                        "scope": "Registered full12-fact reference scope; illustrative, not a changed primary runtime",
                        "diagnosis": d.model_dump(mode="json"),
                        "overlap": "Reference insufficiency and repertoire inadequacy may both apply; neither is exclusive.",
                    }
                )
                break
    cases.extend(candidates[:1])
    # Preserve the adverse unseen-signature cross-fit case as a different limit.
    error = next(
        r
        for r in read(
            Path("results/dsre-rss2027/20261113T193554Z/reused_error_inspection.json")
        )
        if r["training_exact_signature_rows"] == 0
    )
    model = read(Path(error["reference"]))
    table = RepairTable.model_validate(model["table"])
    row = indexed[error["id"]]
    values = tuple(row["features"]) + tuple(
        row["optional_features"][i] for i in model["selected"]
    )
    assert not any(tuple(r.features) == values for r in table.rows)
    d = ParentIndex(table, model["parent_groups"], 2).diagnose(
        RepairQuery(scope=table.scope, features=values)
    )
    assert d.action == "continue" and row["outcomes"] == {
        "continue_value": False,
        "recover_value": True,
    }
    cases.append(
        inspect_source(row)
        | {
            "case": "G",
            "scope": "Preserved inspected fold1 cross-fit reference, not new held-out confirmation",
            "reference": error["reference"],
            "reference_sha256": sha(Path(error["reference"])),
            "exact_signature_support": 0,
            "diagnosis": d.model_dump(mode="json"),
            "limit": "The supported broader pure rule acts despite unseen exact signature and is physically inadequate. This is NOT labeled an emitted reference-insufficiency obstruction; finite support diagnostics cannot detect every unrepresented adverse state.",
        }
    )
    atomic(
        root / "physical_examples.json",
        {
            "status": "PASS",
            "cases": cases,
            "selection": "A--E preserved; F first lexicographic full-vocabulary real reference obstruction; G original unseen-signature adverse cross-fit case",
            "no_new_physics_or_thresholds": True,
        },
    )
    print(
        {
            "status": "PASS",
            "raw_physical_cases": len(cases),
            "full_vocabulary_reference_gap_found": bool(candidates),
        },
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    examples(parser.parse_args().root)
