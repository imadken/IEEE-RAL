"""Inspect the sealed strongest baseline and freeze a diverse review subset."""

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from dual_rec.explanation_repair.audit import factual_claims, raw_truth, true_claim
from dual_rec.explanation_repair.experiment import read, save, sha


def rows(path):
    return [json.loads(s) for s in path.read_text().splitlines()]


def run(root):
    old = Path("results/explanation-repair/20261113T091510Z")
    data = old / "development05"
    seal = read(old / "completion_manifest.json")["sha256"]
    used = {}

    def verified(path):
        assert sha(path) == seal[str(path.relative_to(old))]
        used[str(path)] = sha(path)
        return path

    inputs = {r["id"]: r for r in rows(verified(data / "trace_inputs.jsonl"))}
    outputs = defaultdict(dict)
    for row in rows(verified(data / "trace_outputs.jsonl")):
        if row["result"] is not None:
            outputs[row["input_id"]][row["method"]] = row["result"]
    cells = read(verified(data / "physical_sources.json"))
    truth = {}
    import gzip

    for cell in cells:
        p = Path(cell["source"])
        assert sha(p) == cell["source_sha256"]
        used[str(p)] = cell["source_sha256"]
        with gzip.open(p, "rt") as stream:
            truth[cell["id"]] = (
                cell["task"],
                raw_truth(json.load(stream), cell["task"]),
            )
    totals, examples = Counter(), []
    for identifier, row in inputs.items():
        task, oracle = truth[row["cell"]]
        original = factual_claims(row["input"]["claims"])
        supported = {
            k for k, c in original.items() if true_claim(c, oracle, task) is True
        }
        regen = factual_claims(
            [g["claim"] for g in outputs[identifier]["regenerate"]["claims"]]
        )
        edit = factual_claims(
            [g["claim"] for g in outputs[identifier]["proposed"]["claims"]]
        )
        errors = sum(true_claim(c, oracle, task) is not True for c in regen.values())
        assert errors == 0 and supported <= set(regen)
        assert set(edit) <= set(regen)
        totals.update(
            inputs=1,
            regenerated_facts=len(regen),
            unsupported=errors,
            original_supported=len(supported),
            retained=len(supported & set(regen)),
            informative=int(bool(regen)),
            editor_facts=len(edit),
            editor_informative=int(bool(edit)),
            editor_information_subset=1,
            strict_information_superset=int(set(edit) < set(regen)),
        )
        if len(examples) < 8 and row["variant"] in [
            "unsupported",
            "unparseable",
            "action_model",
        ]:
            examples.append(
                {
                    "id": identifier,
                    "variant": row["variant"],
                    "original": row["input"]["original_text"],
                    "editor": outputs[identifier]["proposed"]["text"],
                    "regeneration": outputs[identifier]["regenerate"]["text"],
                    "additional_true_facts": [
                        list(map(str, k)) for k in set(regen) - set(edit)
                    ],
                    "scope": "Oracle checked; more facts does not establish audience utility",
                }
            )
    save(
        root / "strongest_baseline_investigation.json",
        {
            "status": "PASS_INDEPENDENT_RAW_ORACLE_RECOMPUTATION",
            "counts": dict(totals),
            "examples": examples,
            "explanation": "B3 enumerates the same entire visible observation history and both model-applicability values, emitting only those accepted by the same support semantics. B4 restricts replacements to original slots and keeps no new unrelated facts. Both use no LM, no future outcomes and the same ledger/model; B3 is not a hidden oracle. Its emitted sets include all B4 facts on every input. Semantic correct-explanation damage is zero when rewriting adds only true facts and loses none; exact text changes alone are not diagnostic damage. No demonstrated information or recovery advantage beyond textual preservation.",
            "budget": "B3 single finite pass over ledger/model; B4 at-most4-option groups of4. Same evidence and permitted primitive reasoning; actual runtime/work will be measured separately, without forcing a weaker output budget on B3.",
        },
    )
    public = rows(verified(data / "public_inputs.jsonl"))
    strata = defaultdict(list)
    for row in public:
        source = row["dataset"]
        identifier = row["original"]["task_id"]
        task = identifier.split("-", 1)[0]
        if source == "RoboFail":
            key = (source, task, row["generation"])
        else:
            family = identifier.split("autogen_", 1)[-1][:-2]
            key = (source, task, family)
        strata[key].append(row)
    subset = []
    rank = lambda s: hashlib.sha256(("week2-review-v1/" + s).encode()).hexdigest()
    for key, values in sorted(strata.items()):
        count = 2 if key[0] == "RoboFail" else 1
        for row in sorted(values, key=lambda r: rank(r["id"]))[:count]:
            subset.append(
                {
                    "id": row["id"],
                    "dataset": row["dataset"],
                    "generation": row["generation"],
                    "original_task": row["original"]["task_id"].split("-", 1)[0],
                    "alias_group": row["group"],
                    "original_sha256": hashlib.sha256(
                        json.dumps(row["original"], sort_keys=True).encode()
                    ).hexdigest(),
                    "stratum": list(key),
                }
            )
    save(
        root / "review_subset_freeze.json",
        {
            "status": "MEMBERSHIP_FROZEN_BEFORE_WEEK2_METHOD_EVALUATION",
            "selection": "first2 SHA per RF task/origin, first1 per CF task/template family; no method outcome or coherence label selection",
            "count": len(subset),
            "rows": subset,
            "note": "Previously used development corpus; not an untouched held-out set. Claim labels require independent adjudication.",
        },
    )
    save(root / "source_members.json", used)
    print({"baseline": dict(totals), "frozen_review_rows": len(subset)})


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, required=True)
    a = p.parse_args()
    run(a.root)
