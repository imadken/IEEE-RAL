"""Recompute language syntax/coverage and exact reused-input counts without an LM."""

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


def read(path):
    return json.loads(path.read_text())


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def schema_valid(text):
    try:
        value = json.loads(text)
        if not isinstance(value, dict) or set(value) - {"facts", "unresolved"}:
            return False
        facts, unresolved = value.get("facts", []), value.get("unresolved", [])
        if not isinstance(facts, list) or not isinstance(unresolved, list):
            return False
        if not all(isinstance(s, str) for s in unresolved):
            return False
        return all(
            isinstance(f, dict)
            and set(f) == {"entity", "predicate", "value"}
            and isinstance(f["entity"], str)
            and bool(f["entity"])
            and isinstance(f["predicate"], str)
            and bool(f["predicate"])
            and type(f["value"]) in (str, bool)
            for f in facts
        )
    except (ValueError, TypeError):
        return False


def run(root):
    folder = root / "language"
    frozen = read(folder / "frozen_language_inputs.json")
    config = frozen["config"]
    assert (
        sha(Path("scripts/explanation_repair_language.py")) == frozen["source_sha256"]
    )
    assert (
        sha(Path("config/explanation_repair_language.json")) == frozen["config_sha256"]
    )
    previous = root / "language_attempt01_source_provenance"
    original = read(previous / "frozen_language_inputs.json")
    assert sha(previous / "frozen_runner.py") == original["source_sha256"]
    old_cases = {r["id"]: r for r in original["inputs"]}
    new_cases = {r["id"]: r for r in frozen["inputs"]}
    assert set(old_cases) == set(new_cases)
    for key in [
        "methods",
        "model",
        "revision",
        "device",
        "threads",
        "dtype",
        "max_new_tokens",
        "do_sample",
        "num_beams",
        "sampling_salt",
    ]:
        assert original["config"][key] == config[key]
    changed = []
    for identifier, case in new_cases.items():
        old = old_cases[identifier]
        assert old["original"] == case["original"] and old["bundle"] == case["bundle"]
        if case["evidence"] != old["evidence"]:
            assert case["source"] == "reused-physical-development"
            before, after = old["evidence"], case["evidence"]
            assert (
                before["action_model"] == after["action_model"]
                and before["query"] == after["query"]
            )
            assert [
                {
                    k: r[k]
                    for k in ["id", "fact", "window", "visibility", "kind", "action"]
                }
                for r in before["records"]
            ] == after["records"]
            assert all("source" not in r for r in after["records"])
            changed.append(identifier)
    assert len(changed) == 1
    old_outputs = {
        (r["input_id"], r["method"]): r
        for r in map(json.loads, (previous / "outputs.jsonl").read_text().splitlines())
    }
    counts, reused, generated, capped, tokens = defaultdict(Counter), 0, 0, 0, 0
    seen = set()
    for row in map(json.loads, (folder / "outputs.jsonl").read_text().splitlines()):
        key = (row["input_id"], row["method"])
        assert key not in seen
        seen.add(key)
        assert row["input_id"] in new_cases and row["method"] in config["methods"]
        assert row["input_truncated"] is False
        if row["status"] == "NOT_RUN_CONTEXT_LIMIT":
            counts[row["method"]][row["status"]] += 1
            continue
        assert 0 < row["output_tokens"] <= config["max_new_tokens"]
        tokens += row["output_tokens"]
        valid = schema_valid(row["raw_output"].strip())
        assert valid == row["status"].startswith(("PARSED", "EMPTY_UNEXPLAINED"))
        capped += row["cap_reached"]
        if "reused_from" in row:
            assert row["input_id"] not in changed
            assert (
                new_cases[row["input_id"]]["evidence"]
                == old_cases[row["input_id"]]["evidence"]
            )
            assert all(row[k] == v for k, v in old_outputs[key].items())
            reused += 1
        else:
            assert row["input_id"] in changed
            generated += 1
        counts[row["method"]][row["status"]] += 1
    assert len(seen) == len(new_cases) * len(config["methods"])
    assert reused == 40 and generated == 4
    assert dict(counts) == read(folder / "summary.json")["counts"]
    backend = read(folder / "backend.json")
    assert backend["device"] == "cpu" and backend["training"] is False
    for name, expected in backend["files"].items():
        assert sha(Path(name)) == expected["sha256"]
    result = {
        "status": "PASS",
        "inputs": len(new_cases),
        "canonical_output_rows": len(seen),
        "reused_exact_valid_input_outputs": reused,
        "recomputed_sanitized_same_case_outputs": generated,
        "preserved_excluded_metadata_tainted_outputs": 4,
        "retained_prior_generation_rows": len(old_outputs),
        "counts": {m: dict(c) for m, c in counts.items()},
        "cap_reached_rows": capped,
        "canonical_generated_tokens_recorded": tokens,
        "model_weight_hashes_unchanged": True,
        "raw_json_schema_checked_independently": True,
        "semantic_gold_quality": "NOT_ASSESSED; invalid or cap-limited outputs are not repair successes",
        "generation_budget_scope": "Recorded token counts checked against cap; inference not independently repeated",
        "base_model_limit": "Cached Pythia160M is not an instruction-tuned RARR reproduction. No complete paper comparison claimed.",
    }
    (folder / "independent_audit.json").write_text(json.dumps(result, indent=2) + "\n")
    print(result)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    a = p.parse_args()
    if (a.root / "completion_manifest.json").exists():
        raise SystemExit("Evidence sealed")
    run(a.root)
