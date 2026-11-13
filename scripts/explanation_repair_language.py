"""Frozen, small, offline-weight language smoke; no training or model search."""

import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
import sys
import time
from pathlib import Path

from pydantic import Field, model_validator

from dual_rec.contracts.checks import Evidence
from dual_rec.explanation_repair.core import edit
from dual_rec.explanation_repair.schemas import Claim, Fact, RepairInput


class LanguageClaims(Evidence):
    facts: list[Fact] = Field(default_factory=list)
    unresolved: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def explicit_value_types(cls, value):
        if isinstance(value, dict) and isinstance(value.get("facts", []), list):
            for fact in value.get("facts", []):
                if isinstance(fact, dict) and type(fact.get("value")) not in (
                    bool,
                    str,
                ):
                    raise ValueError(
                        "Do not coerce numeric/null generation into a Boolean observation"
                    )
        return value


def read(path):
    return json.loads(path.read_text())


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def load_backend(root, config):
    # The main project supplies Torch; the supplementary uv environment supplies
    # the explicitly compatible language dependencies. Prefer its actual packages
    # over incidental versions exposed through the project PYTHONPATH.
    spec = importlib.util.find_spec("transformers")
    if spec is None or spec.origin is None:
        raise RuntimeError("Supplementary Transformers runtime was not supplied")
    package_site = str(Path(spec.origin).parent.parent)
    if package_site in sys.path:
        sys.path.remove(package_site)
    sys.path.insert(0, package_site)
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    torch.set_num_threads(config["threads"])
    torch.set_num_interop_threads(1)
    torch.manual_seed(20261113)
    snapshot = (
        Path.home()
        / ".cache/huggingface/hub"
        / ("models--" + config["model"].replace("/", "--"))
        / "snapshots"
        / config["revision"]
    )
    assert snapshot.is_dir(), "Pinned local weights unavailable; do not download"
    files = {
        str(p): {"sha256": sha(p), "bytes": p.stat().st_size}
        for p in sorted(snapshot.iterdir())
        if p.is_file()
    }
    tokenizer = AutoTokenizer.from_pretrained(
        snapshot, local_files_only=True, trust_remote_code=False
    )
    model = (
        AutoModelForCausalLM.from_pretrained(
            snapshot,
            local_files_only=True,
            trust_remote_code=False,
            torch_dtype=torch.float32,
        )
        .to("cpu")
        .eval()
    )
    info = {
        "status": "AVAILABLE_LOADED_OFFLINE",
        "model": config["model"],
        "revision": config["revision"],
        "files": files,
        "device": str(next(model.parameters()).device),
        "training": model.training,
        "parameters": sum(p.numel() for p in model.parameters()),
        "versions": {
            p: importlib.metadata.version(p)
            for p in [
                "torch",
                "transformers",
                "tokenizers",
                "huggingface-hub",
                "numpy",
                "pydantic",
            ]
        },
        "context_limit": model.config.max_position_embeddings,
        "runtime_prefix": str(Path(sys.prefix)),
        "supplementary_site": package_site,
        "supplementary_runtime_packages": {
            d.metadata["Name"]: d.version
            for d in importlib.metadata.distributions(path=[package_site])
        },
        "runtime_scope": "Small supplementary uv environment; unchanged project CPU Torch reused by declared PYTHONPATH; no weights installed/downloaded, no lock mutation",
    }
    save(root / "language" / "backend.json", info)
    return torch, tokenizer, model


def cases(root, config):
    target = Path(read(root / "latest_development.json")["path"])
    result = []
    for case in read(target / "worked_cases.json"):
        if case["id"] != "temporal-and-conflicting":
            bundle = case["input"]
            result.append(
                {
                    "id": "authored/" + case["id"],
                    "source": "authored-development",
                    "bundle": bundle,
                    "evidence": {
                        "records": bundle["records"],
                        "action_model": bundle["model"],
                        "query": bundle["query"],
                    },
                    "original": bundle["original_text"],
                }
            )
    traces = [
        json.loads(s)
        for s in (target / "trace_inputs.jsonl").read_text().splitlines()
        if json.loads(s)["variant"] == "partial_flip"
    ]
    rank = lambda identifier: hashlib.sha256(
        (config["sampling_salt"] + identifier).encode()
    ).hexdigest()
    trace = min(traces, key=lambda r: rank(r["id"]))
    bundle = trace["input"]
    result.append(
        {
            "id": "trace/" + trace["id"],
            "source": "reused-physical-development",
            "bundle": bundle,
            "evidence": {
                "records": [
                    {
                        k: r[k]
                        for k in [
                            "id",
                            "fact",
                            "window",
                            "visibility",
                            "kind",
                            "action",
                        ]
                    }
                    for r in bundle["records"]
                ],
                "action_model": bundle["model"],
                "query": bundle["query"],
            },
            "original": bundle["original_text"],
            "raw_source": trace["source"],
        }
    )
    public = [
        json.loads(s) for s in (target / "public_inputs.jsonl").read_text().splitlines()
    ]
    for dataset in ["RoboFail", "CounterFactual"]:
        selected = sorted(
            [r for r in public if r["dataset"] == dataset], key=lambda r: rank(r["id"])
        )[: config["public_per_source"]]
        for row in selected:
            source = row["original"]
            result.append(
                {
                    "id": row["id"],
                    "source": "public-development-no-gold-repairs",
                    "bundle": row["input"],
                    "evidence": {
                        "plan_commands_not_observed_effects": source[
                            "plan_until_failure"
                        ],
                        "current_observations": source["observation"],
                        "action_model": None,
                        "query": row["input"]["query"],
                    },
                    "original": source["explanation"],
                }
            )
    return result


def prompt(case, instruction):
    example = '{"facts":[{"entity":"beacon","predicate":"powered","value":true}],"unresolved":[]}'
    return (
        "Return one JSON object only, with facts (entity, predicate, Boolean or string value) and unresolved (strings). Only current observation claims belong in facts. Causes, unknowns, action-model implications and historical assertions belong in unresolved. Do not treat commands as observed effects. Do not invent times. Example current assertion: beacon is powered. JSON: "
        + example
        + "\nInstruction: "
        + instruction
        + "\nSupplied evidence: "
        + json.dumps(case["evidence"], sort_keys=True)
        + "\nOriginal explanation: "
        + case["original"]
        + "\nJSON:"
    )


def run(root, stage, reuse=None):
    target = root / "language"
    target.mkdir(exist_ok=True)
    config = read(Path("config/explanation_repair_language.json"))
    if stage == "run":
        selected = cases(root, config)
        assert not (target / "outputs.jsonl").exists(), (
            "Do not overwrite language evidence"
        )
        save(
            target / "frozen_language_inputs.json",
            {
                "config": config,
                "inputs": selected,
                "source_sha256": sha(Path(__file__)),
                "config_sha256": sha(Path("config/explanation_repair_language.json")),
                "prompt_scope": "Single shared one-shot format demonstration, one greedy candidate, total96 new-token cap per condition; no after-output prompt tuning",
            },
        )
    prior_inputs = {}
    prior_rows = {}
    if reuse is not None:
        old = read(reuse / "frozen_language_inputs.json")
        assert old["config"]["methods"] == config["methods"]
        for key in [
            "max_new_tokens",
            "do_sample",
            "num_beams",
            "model",
            "revision",
            "sampling_salt",
        ]:
            assert old["config"][key] == config[key]
        prior_inputs = {c["id"]: c for c in old["inputs"]}
        prior_rows = {
            (r["input_id"], r["method"]): r
            for r in map(json.loads, (reuse / "outputs.jsonl").read_text().splitlines())
        }
    torch, tokenizer, model = load_backend(root, config)
    if reuse is not None:
        current_backend = read(target / "backend.json")
        old_backend = read(reuse / "backend.json")
        assert all(
            current_backend[k] == old_backend[k]
            for k in ["versions", "files", "device", "parameters"]
        )
    if stage == "qualify":
        tokens = tokenizer(
            "Robot observation: cube is grasped. Explanation:", return_tensors="pt"
        )
        started = time.perf_counter()
        with torch.inference_mode():
            output = model.generate(
                **tokens,
                do_sample=False,
                max_new_tokens=16,
                pad_token_id=tokenizer.eos_token_id,
            )
        save(
            target / "qualification.json",
            {
                "status": "PASS_OFFLINE_GENERATION",
                "seconds": time.perf_counter() - started,
                "input_tokens": tokens["input_ids"].shape[-1],
                "output": tokenizer.decode(
                    output[0, tokens["input_ids"].shape[-1] :], skip_special_tokens=True
                ),
                "meaning": "Backend execution only, not instruction following or semantic quality",
            },
        )
        print(read(target / "qualification.json"))
        return
    counters = {}
    with (target / "outputs.jsonl").open("x") as stream:
        for case in selected:
            encoded = {
                m: tokenizer(
                    prompt(case, instruction), return_tensors="pt", truncation=False
                )
                for m, instruction in config["methods"].items()
            }
            context_ok = all(
                e["input_ids"].shape[-1] + config["max_new_tokens"]
                <= model.config.max_position_embeddings
                for e in encoded.values()
            )
            for method, inputs in encoded.items():
                row = {
                    "input_id": case["id"],
                    "source": case["source"],
                    "method": method,
                    "input_tokens": inputs["input_ids"].shape[-1],
                    "input_truncated": False,
                    "status": "NOT_RUN_CONTEXT_LIMIT",
                }
                current_prompt = prompt(case, config["methods"][method])
                row["prompt_sha256"] = hashlib.sha256(
                    current_prompt.encode()
                ).hexdigest()
                old_case = prior_inputs.get(case["id"])
                if (
                    old_case is not None
                    and prompt(old_case, config["methods"][method]) == current_prompt
                ):
                    old_row = prior_rows[(case["id"], method)]
                    row = old_row | {
                        "prompt_sha256": row["prompt_sha256"],
                        "reused_from": str(reuse / "outputs.jsonl"),
                    }
                    counters.setdefault(method, {})[row["status"]] = (
                        counters.setdefault(method, {}).get(row["status"], 0) + 1
                    )
                    stream.write(json.dumps(row, allow_nan=False) + "\n")
                    stream.flush()
                    continue
                if context_ok:
                    started = time.perf_counter()
                    with torch.inference_mode():
                        ids = model.generate(
                            **inputs,
                            do_sample=False,
                            num_beams=1,
                            max_new_tokens=config["max_new_tokens"],
                            pad_token_id=tokenizer.eos_token_id,
                        )
                    new = ids[0, inputs["input_ids"].shape[-1] :]
                    text = tokenizer.decode(new, skip_special_tokens=True)
                    row.update(
                        output_tokens=len(new),
                        seconds=time.perf_counter() - started,
                        raw_output=text,
                        cap_reached=len(new) == config["max_new_tokens"]
                        and new[-1].item() != tokenizer.eos_token_id,
                    )
                    try:
                        parsed = LanguageClaims.model_validate_json(text.strip())
                        row.update(status="PARSED_JSON", parsed=parsed.model_dump())
                        if not parsed.facts and not parsed.unresolved:
                            row["status"] = "EMPTY_UNEXPLAINED_COVERAGE"
                        if method == "proposed_language_adapter":
                            original = RepairInput.model_validate(case["bundle"])
                            claims = [
                                Claim(
                                    id=f"lm/{i}",
                                    kind="observation",
                                    fact=f,
                                    window=original.query,
                                )
                                for i, f in enumerate(parsed.facts)
                            ]
                            adapted = original.model_copy(
                                update={"claims": claims, "unparsed": parsed.unresolved}
                            )
                            row["repair"] = edit(adapted).model_dump()
                        if row["cap_reached"]:
                            row["status"] = "PARSED_BUT_GENERATION_CAP_REACHED"
                    except ValueError as exc:
                        row.update(
                            status="PARSE_ERROR_CAP_REACHED"
                            if row["cap_reached"]
                            else "PARSE_ERROR",
                            parser_error=str(exc),
                        )
                counters.setdefault(method, {})[row["status"]] = (
                    counters.setdefault(method, {}).get(row["status"], 0) + 1
                )
                stream.write(json.dumps(row, allow_nan=False) + "\n")
                stream.flush()
                print(case["id"], method, row["status"], flush=True)
    save(
        target / "summary.json",
        {
            "status": "COMPLETED_BOUNDED_LANGUAGE_DIAGNOSTIC",
            "inputs": len(selected),
            "conditions": len(config["methods"]),
            "counts": counters,
            "quality": "Gold semantic repair quality unavailable; parse failures and cap-limited outputs are not factual successes. No complete paper-baseline comparison claimed.",
            "backend": read(target / "backend.json"),
        },
    )
    print({"inputs": len(selected), "counts": counters})


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--stage", choices=["qualify", "run"], required=True)
    p.add_argument("--reuse-valid-prior", type=Path)
    a = p.parse_args()
    if (a.root / "completion_manifest.json").exists():
        raise SystemExit("Evidence sealed")
    run(a.root, a.stage, a.reuse_valid_prior)
