"""Research-only reporting and small integrity seal using the existing job ledger."""

import argparse
import fcntl
import hashlib
import json
import subprocess
import time
from collections import Counter, defaultdict
from pathlib import Path

import psutil


def read(path):
    return json.loads(path.read_text())


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def maintained():
    return [
        Path("EXPLANATION_REPAIR_PROTOCOL.md"),
        Path("EXPLANATION_REPAIR_RESULTS.md"),
        Path("config/explanation_repair.json"),
        Path("config/explanation_repair_language.json"),
        Path("tests/test_explanation_repair.py"),
        *sorted(Path("src/dual_rec/explanation_repair").glob("*.py")),
        *sorted(Path("scripts").glob("explanation_repair_*.py")),
    ]


def preserve(root):
    initial = read(root / "initial.json")
    for name, expected in initial["prior_files"].items():
        assert (sha(Path(name)) if Path(name).is_file() else None) == expected, name
    for name, expected in initial["historical_seals"].items():
        assert sha(Path(name)) == expected, name
    target = Path(read(root / "latest_development.json")["path"])
    amendments = (
        read(root / "post_batch_source_amendments.json")
        if (root / "post_batch_source_amendments.json").exists()
        else {}
    )
    for name, expected in read(target / "frozen_specification.json")["sha256"].items():
        if name in amendments:
            amendment = amendments[name]
            assert name in [
                "src/dual_rec/explanation_repair/experiment.py",
                "EXPLANATION_REPAIR_PROTOCOL.md",
            ]
            original = root / amendment["original_copy"]
            assert sha(original) == expected == amendment["original_sha256"]
            text = original.read_text()
            if amendment["kind"] == "output_manifest_only":
                assert text.count(amendment["old"]) == 1
                text = text.replace(amendment["old"], amendment["new"], 1)
            else:
                assert amendment["kind"] == "append_language_diagnostic_scope"
                text += amendment["append"]
            assert (
                Path(name).read_text() == text
                and sha(Path(name)) == amendment["amended_sha256"]
            )
        else:
            assert sha(Path(name)) == expected, name
    return {
        "status": "PASS",
        "initial_paths_checked": len(initial["prior_files"]),
        "historical_seals_checked": len(initial["historical_seals"]),
        "gitignore_lockfile_and_user_document_moves": "Preserved exactly",
        "structured_scientific_logic": "Unchanged; exact output-manifest correction and appended language scope preserved separately",
    }


def validate(root):
    checks = []
    for argv in [
        ["uv", "run", "--no-sync", "pytest", "-q", "tests/test_explanation_repair.py"],
        ["uv", "run", "--no-sync", "pytest", "-q", "tests"],
        ["uv", "run", "--no-sync", "ruff", "check", "src", "scripts", "tests"],
        [
            "uv",
            "run",
            "--no-sync",
            "ruff",
            "format",
            "--check",
            "src",
            "scripts",
            "tests",
        ],
        ["git", "diff", "--check"],
    ]:
        started = time.monotonic()
        result = subprocess.run(argv, text=True, capture_output=True, check=False)
        check = {
            "command": argv,
            "exit_status": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "wall_seconds": time.monotonic() - started,
        }
        checks.append(check)
        print(result.stdout, result.stderr, flush=True)
        save(
            root / "validation.json",
            {
                "status": "PASS"
                if all(c["exit_status"] == 0 for c in checks)
                else "FAIL",
                "checks": checks,
            },
        )
        if result.returncode:
            raise SystemExit(result.returncode)


def table(headers, rows):
    lines = [headers, ["---"] * len(headers), *rows]
    return (
        "\n".join(
            "| "
            + " | ".join(
                "N/A" if c is None else str(c).replace("|", "/").replace("\n", " ")
                for c in line
            )
            + " |"
            for line in lines
        )
        + "\n"
    )


def language_resources(root):
    calls = []
    for folder in [root / "language_attempt01_source_provenance", root / "language"]:
        calls.extend(
            r
            for r in map(
                json.loads, (folder / "outputs.jsonl").read_text().splitlines()
            )
            if "output_tokens" in r and "reused_from" not in r
        )
    qualification = read(
        root / "language_attempt01_source_provenance/qualification.json"
    )
    return {
        "language_model_generation_calls": len(calls) + 1,
        "language_diagnostic_calls": len(calls),
        "language_qualification_calls": 1,
        "language_recorded_generated_tokens_excluding_probe": sum(
            r["output_tokens"] for r in calls
        ),
        "language_final_canonical_outputs": 44,
        "language_excluded_metadata_tainted_calls_preserved": 4,
        "language_qualification_seconds": qualification["seconds"],
    }


def report(root):
    target = Path(read(root / "latest_development.json")["path"])
    audit = read(target / "independent_audit.json")
    assert audit["status"] == "PASS"
    language = read(root / "language/independent_audit.json")
    assert language["status"] == "PASS"
    validation = read(root / "validation.json")
    assert validation["status"] == "PASS" and len(validation["checks"]) == 5
    measurements = read(target / "independent_claim_metrics.json")
    methods = [
        "original",
        "generic",
        "delete",
        "regenerate",
        "proposed",
        "no_temporal",
        "no_action_model",
    ]
    fields = [
        "inputs",
        "emitted_unique_claims",
        "unsupported_assertions",
        "contradicted_assertions",
        "unverified_assertions",
        "original_supported_unique",
        "original_supported_retained",
        "informative_outputs",
        "fallbacks",
        "temporal_errors",
        "correct_inputs",
        "correct_input_exact_text_preserved",
        "unassessed_original_text_spans",
        "causal_hypotheses_emitted",
    ]
    totals = defaultdict(Counter)
    per_task = defaultdict(Counter)
    for m in measurements:
        counts = {k: m[k] for k in fields}
        totals[m["method"]].update(counts)
        per_task[(m["task"], m["method"])].update(counts)
    public = read(target / "public_summary.json")
    observation_counts = defaultdict(Counter)
    unparsed_observations = []
    for line in (target / "public_inputs.jsonl").read_text().splitlines():
        item = json.loads(line)
        covered = {
            int(r["id"].split("/")[1])
            for r in item["input"]["records"]
            if r["id"].startswith("obs/")
        }
        stratum = item["dataset"] + "/" + item["generation"]
        observation_counts[stratum].update(
            total=len(item["original"]["observation"]), covered=len(covered)
        )
        unparsed_observations.extend(
            {
                "id": item["id"],
                "observation_index": i,
                "text": text,
                "status": "UNPARSED_NOT_A_GROUNDED_FACT",
            }
            for i, text in enumerate(item["original"]["observation"])
            if i not in covered
        )
    save(
        target / "public_observation_coverage.json",
        {
            "strata": {k: dict(v) for k, v in observation_counts.items()},
            "unparsed_observations": unparsed_observations,
            "scope": "Syntactic conversion accounting only, not independent semantic validation; all original observations also retained verbatim in public_inputs.jsonl",
        },
    )
    recovery = read(target / "independent_recovery_metrics.json")
    worked = read(target / "worked_cases.json")
    sensitivity = read(target / "sensitivity.json")
    runtime = read(target / "runtime.json")
    previous_attempts = sorted(
        p for p in root.glob("development[0-9][0-9]") if p != target
    )
    input_invariants = []
    for previous in previous_attempts:
        older = previous / "trace_outputs.jsonl"
        if older.exists():
            old_actions = {
                (r["input_id"], r["method"]): (
                    r["selected_action"],
                    r["actual_success"],
                )
                for r in map(json.loads, older.read_text().splitlines())
            }
            current = {
                (r["input_id"], r["method"]): (
                    r["selected_action"],
                    r["actual_success"],
                )
                for r in map(
                    json.loads,
                    (target / "trace_outputs.jsonl").read_text().splitlines(),
                )
            }
            assert old_actions == current
            original_inputs = {
                r["id"]: {
                    k: r["input"][k] for k in ["records", "model", "claims", "query"]
                }
                for r in map(
                    json.loads,
                    (previous / "trace_inputs.jsonl").read_text().splitlines(),
                )
            }
            final_inputs = {
                r["id"]: {
                    k: r["input"][k] for k in ["records", "model", "claims", "query"]
                }
                for r in map(
                    json.loads, (target / "trace_inputs.jsonl").read_text().splitlines()
                )
            }
            assert original_inputs == final_inputs
            input_invariants.append(
                {
                    "attempt": previous.name,
                    "same_structured_inputs_actions_and_outcomes": True,
                }
            )
    save(root / "attempt_comparison.json", input_invariants)
    text = f"""# Explanation repair: first-session measured results

The authorized first session is complete: a working typed ledger, finite-menu editor,
renderer, deterministic baselines, public adapter and development-only outcome-linked
demonstration. **No advantage over the strongest evidence-only controls is established.**
The natural-language comparisons and downstream hypothesis remain incomplete. This is
a research prototype, not a manuscript or a publication-readiness decision.

Reviewed base: `c17d5a7e9a08626f6c7e63f73e6d94cbf6c5e71d`. Branch:
`research/evidence-preserving-explanation-repair`. Final committed source SHA and
resource accounting are recorded in `{root}/completion_manifest.json` and
`resources.json` after the scoped local commit. No push is authorized or attempted.

## What actually ran

All 750 pinned public rows were processed: 130 RoboFail (91 expert, 39 GPT/REFLECT)
and 620 CounterFactual templates. E/C/N and both original pair labels are unchanged.
There are {public["groups"]} conservative alias groups; all rows are descriptive
development/interface data, with no train/test split. Counterfactual episode linkage
is unavailable, so shared template families are grouped across tasks. Imperfect SRL
was not used as truth. The four upstream Git blobs are byte-verified at revision
`730ba3200e84b6f1c140a4d7a6569f3a42fe1928` in `upstream_manifest.json`.

The simulator smoke used 20 old PickCube parents and 20 old PushCube parents, both
registered conditions, plus five nominal Lift parents: **45 task-parent seeds,
85 cells, 170 existing paired reference continuations**. All were used in the old
campaign and are DEVELOPMENT ONLY here. Seven fixed explanation variants yield
595 structured inputs. These repetitions are not independent physical trials.
There were **zero new physics rollouts, trained models, paid language calls or
GPU training jobs**. The exact same selected actions/outcomes were verified across
all preserved computational attempts; repeats never increase the sample size.

The declared privileged simulator state-observation projection is shared by every
method. It uses first/current state observations, the exposed contact flag and a
fixed 3 cm proximity predicate. This predicate is not task success; continuation
outcomes retain the old environment's unchanged success definition. Raw state,
fault conditions, caches and future outcomes are evaluator-only. Lift is a privileged
preservation control, not a third invented failure/recovery family. Grasp sensor and
recorder correctness remain trusted assumptions. The small transport precondition
model is an engineering abstraction, not proven necessary/sufficient robot physics.

## Public extraction and actual interface limits

"""
    text += table(
        [
            "Source",
            "Rows",
            "Fully extracted explanations",
            "Covered / total clauses",
            "Extracted claims",
            "Observation strings converted / supplied",
        ],
        [
            [
                k,
                v["rows"],
                v["fully_extracted"],
                f"{v['covered_spans']}/{v['spans']}",
                v["parsed_claims"],
                f"{observation_counts[k]['covered']}/{observation_counts[k]['total']}",
            ]
            for k, v in public["strata"].items()
        ],
    )
    text += """
The final whitelist extracts **zero complete public explanations** and zero atomic
explanation clauses from these released rows. All unparsed spans are retained.
Earlier lexical matching falsely reported four full rows and six clauses because
it swallowed causal/temporal prose into object-name slots. Inspection rejected all
six; the erroneous parses and parser fix remain preserved. This is an explicit
parser failure boundary, not successful end-to-end language coverage or a
successful natural-language repair evaluation. Regeneration can still emit observed
facts from the public snapshot, but they are not gold repairs or established causes.
Observation conversion is also incomplete: unsupported observation strings remain
verbatim in the original public inputs and `public_observation_coverage.json`, and
are not silently treated as grounded facts. Any generated public explanation is
conditional on this partial projection; semantic repair quality is unassessed.
There are no gold repair labels, complete historical observations/action models or
independent natural-language semantic judge here. Editor support labels are not
used as gold quality labels. Original coherence labels cannot validate new repairs.

The initial cache search missed existing weights. A deeper hidden/symlink-aware
search found Pythia-160M; its offline CPU runtime was qualified and a bounded
language diagnostic was executed. The earlier absence-of-weights statements are
preserved and superseded by `language_backend_discovery.json` and `language/`.
The generic comparator remains an adapted parent fallback using our deterministic
checker, not the parent's trained NLI classifier.

## Independent structured factual-error / retention tradeoff

Counts below aggregate the declared development mixture, including controlled
corruptions and unedited deterministic templates. They are software/grounded-data
diagnostics, not an IID population error estimate. Unique entity/predicate/value/time
facts are counted rather than repeated words. Declared causal hypotheses are counted
separately from asserted factual errors. Zero factual outputs have undefined accuracy,
not perfect performance. Informative coverage and retention are separate endpoints.

"""
    text += table(
        [
            "Method",
            "Unsupported / emitted unique factual assertions",
            "Supported original facts retained",
            "Informative / inputs",
            "Temporal errors",
            "Correct-input exact text preserved",
        ],
        [
            [
                m,
                f"{totals[m]['unsupported_assertions']}/{totals[m]['emitted_unique_claims']}",
                f"{totals[m]['original_supported_retained']}/{totals[m]['original_supported_unique']}",
                f"{totals[m]['informative_outputs']}/{totals[m]['inputs']}",
                totals[m]["temporal_errors"],
                f"{totals[m]['correct_input_exact_text_preserved']}/{totals[m]['correct_inputs']}",
            ]
            for m in methods
        ],
    )
    language_table = table(
        [
            "Frozen language condition",
            "Inputs",
            "Valid complete JSON",
            "Parse failures / token-cap reached",
        ],
        [
            [
                method,
                sum(counts.values()),
                sum(n for status, n in counts.items() if status == "PARSED_JSON"),
                sum(
                    n
                    for status, n in counts.items()
                    if status == "PARSE_ERROR_CAP_REACHED"
                ),
            ]
            for method, counts in language["counts"].items()
        ],
    )
    language_text = (
        """## Bounded cached-model language diagnostic

The same cached Pythia-160M checkpoint, one-shot formatting example, greedy candidate,
full visible evidence and 96-new-token cap were shared across four conditions.
Inputs were frozen before generation: four current authored examples, one first-SHA
current trace case, and three first-SHA public examples per source (11 total).
The historical worked case remains in the structured study; this limited language
interface only accepts current observational facts, leaving other claims unresolved.
No input was truncated or skipped. There was no model or prompt search after outputs.

"""
        + language_table
        + """
All 44 canonical outputs failed strict JSON parsing at the token cap. No complete
language repair was obtained; factual repair accuracy is **unassessed**, not 100%.
This does not demonstrate superiority of the structured editor over a competent
language editor. The [model card](https://huggingface.co/EleutherAI/pythia-160m)
describes Pythia as a research model not fine-tuned for instruction-following use.
The single-pass supplied-evidence RARR-inspired prompt is an explicitly limited
adaptation, not the original RARR retrieval/agreement/revision system.
Full Week2 language comparisons remain NOT_RUN; this 11-input diagnostic was run.

An input-contract review found fault-condition names in one trace case's source
paths. That first attempt is preserved in `language_attempt01_source_provenance/`.
The four tainted outputs were excluded, not hidden or replaced with another case.
Only source paths were removed for the same case; observation IDs/facts/times,
action model, initial text and all generation settings stayed fixed. Forty other
byte-identical valid-input outputs were reused, and only four calls were repeated.
There were 48 diagnostic generation calls plus one backend qualification call in
total, with all CPU/artifacts counted. Independent checks verify exact reuse, all
raw JSON classifications and unchanged model-file hashes. Raw outputs and input/
source/config hashes are retained; no cap or prompt was tuned to obtain a success.

"""
    )
    text = text.replace(
        "## Independent structured factual-error / retention tradeoff",
        language_text + "## Independent structured factual-error / retention tradeoff",
    )
    text += "\nTask-stratified key controls (full variant/method rows remain in `independent_claim_metrics.json`):\n\n"
    text += table(
        [
            "Task",
            "Method",
            "Unsupported / factual assertions",
            "Supported original facts retained",
            "Informative / inputs",
        ],
        [
            [
                task,
                method,
                f"{v['unsupported_assertions']}/{v['emitted_unique_claims']}",
                f"{v['original_supported_retained']}/{v['original_supported_unique']}",
                f"{v['informative_outputs']}/{v['inputs']}",
            ]
            for (task, method), v in sorted(per_task.items())
            if method
            in ["proposed", "delete", "regenerate", "no_temporal", "no_action_model"]
        ],
    )
    text += f"""
The proposed editor matches deletion's supported-fact retention; regeneration also
retains those facts and has stronger coverage when the original explanation is
wholly unsupported or unparseable. Improvements over generic fallback do not
establish a new method advantage over these stronger equal-information controls.
Temporal ablation errors concern the explicitly different historical/current
intervals. Removing the action model loses valid declared-model deductions; this is
conditional applicability reasoning, not a unique cause or guaranteed recovery.

All {len(sensitivity)} sensitivity comparisons at loss weights 0/1/3/10 gave
{sum(not s["same_as_frozen_default"] for s in sensitivity)} operation changes.
The preservation penalty did no observed selection work in these independent menus;
its contribution is not established. No weights were tuned on evaluation outcomes.
All seven deterministic methods together took {runtime["total_seconds_all_methods"]:.4f}
seconds across {runtime["bundles"]} structured bundles, excluding serialization/I/O,
source checks and audit. `runtime.json` contains each measurement. This aggregate
is not a measured per-method speedup or a language-model inference comparison.

## Five worked cases and comparator outputs

These are authored examples, separate from the raw-trace evaluation and natural
public explanations. Unknown does not mean failed; a command does not prove an
effect. Model deductions and observations carry separate proof bases/IDs.

"""
    text += table(
        ["Authored case", "Actual proposed text", "Unresolved items"],
        [
            [
                c["id"],
                c["outputs"]["proposed"]["text"],
                "; ".join(c["outputs"]["proposed"]["unresolved"]) or "none",
            ]
            for c in worked
        ],
    )
    partial = next(c for c in worked if c["id"] == "selective-replacement")
    text += "\nActual baseline outputs on the same partially incorrect input:\n\n"
    text += table(
        ["Method", "Output"], [[m, partial["outputs"][m]["text"]] for m in methods]
    )
    text += """
All 5,250 public method outputs, original labels and unparsed text are retained in
`public_outputs.jsonl` / `public_inputs.jsonl`; these are outputs, not certified gold
repairs. `repair_examples.json` gives actual source-linked simulator repairs,
support identifiers, unresolved items and their reused selected-action outcomes.

## Fixed-selector downstream demonstration

All conditions get the complete same projection, history, model, selector and exact
70-control candidate actions. The selector prioritizes the current shared sensor
slot. In this prototype it is fully determined without using explanation content.
Thus no explanation effect is identifiable: this is an interface/outcome-link
control, not evidence that repair improves recovery. Direct evidence and full
evidence/no-explanation controls are included; no sensor is hidden to create a gain.

"""
    text += table(
        [
            "Task",
            "Condition",
            "Cells",
            "Chosen recover",
            "Selected successes",
            "Continue successes",
            "Harm / benefit vs continue",
        ],
        [
            [
                r["task"],
                r["condition"],
                r["cells"],
                r["selected_recover"],
                r["selected_success"],
                r["continue_success"],
                f"{r['harm_vs_continue']}/{r['benefit_vs_continue']}",
            ]
            for r in recovery
            if r["method"] == "proposed" and r["variant"] == "unedited_template"
        ],
    )
    text += """
Proposed minus original/generic/deletion/regeneration/full-evidence/direct-evidence
success difference is exactly zero on every reused cell; there are no action
disagreements. This follows from the observation-dominant rule, not a confirmation
equivalence test. Any selected-vs-continue benefit belongs to the same existing
selector/action library for every condition. It cannot be credited to explanation
repair. No abstention occurred on these fully observed selected cells; separate
tests cover absent, conflicting and non-Boolean sensor values. Executed library
cost is 70 controls / 3.5 simulated seconds, not time to completion or new wall-time
physics execution. See `paired_recovery_comparisons.json` for the exact comparisons.

## Independent verification, corrections and limits

"""
    text += f"The separate raw-state/contact/time/outcome interpreter passed {audit['raw_cells']} cells, {audit['actual_reference_continuations_checked']} actual old continuations, {audit['trace_input_variants']} structured variants, {audit['result_rows']} result rows and {audit['unique_emitted_assertions_evaluated']} unique emitted factual assertions. It checked {audit['historical_text_time_qualifiers_checked']} historical text qualifiers and {audit['historical_source_members_verified']} sealed historical members. Proposed soundness violations observed: {len(audit['proposed_soundness_violations'])}. It does not call the editor's support checker to label assertions. This is independent numerical software, not an independent human annotation study or unrestricted causal truth.\n\n"
    text += """Development01's structured numerical checks passed, but readable historical
statements initially lacked time qualifiers. That defect and its source snapshot
are preserved. Later refinements mark persistence-based inference explicitly,
retain conflict support IDs, separate qualified causal hypotheses from factual
error denominators, and abstain on non-Boolean sensor slots. All earlier attempts
remain local. `development_refinements.json` records them. No projection value,
seed, objective, precondition, action tape, selector choice or physical outcome was
changed to obtain a favorable result. The public grammar was tightened to reject
false positives, reducing coverage to zero; it was not broadened to manufacture a
linguistic success. An additional regression covers those parser failures.

Validation summaries (complete stdout/stderr remain in local `validation.json`
and bounded-worker logs):

"""
    for check in validation["checks"]:
        summaries = [
            line
            for line in check["stdout"].splitlines()
            if "passed" in line or "formatted" in line
        ]
        summary = "; ".join(summaries) or f"exit {check['exit_status']}"
        text += "- `" + " ".join(check["command"]) + "`: " + summary + ".\n\n"
    text += f"""The four maintained optional physics tests are skipped in the main environment;
no physics code changed in this session. Tests are not scientific sample counts.
Historical evidence, `.gitignore`, `uv.lock`, and the initial unrelated documentation
moves are preserved. Large raw inputs, repeated outputs and logs remain excluded
locally and are not committed.

## Evidence, resource accounting and reproduction

Evidence root: `{root}`. Final development: `{target}`. The exact source/config
freeze is `frozen_specification.json`; upstream pin/hashes, historical inputs,
independent metrics, paired choices, sensitivity and all job logs are retained.
`commands.jsonl` meters substantive jobs using the existing bounded worker.
`resources.json` and `completion_manifest.json` provide final wall/CPU/bytes/peak
RAM, commit, source hashes, preservation and zero-worker accounting after closing.
Unmetered interactive inspection/tool overhead is disclosed with a conservative
600 CPU-second allowance; remote tool/host reasoning CPU is not locally measured.
No model weights were downloaded. The public JSON/code and small isolated language
runtime dependencies were downloaded and are counted in the artifact footprint;
web/package transfer bytes are not individually metered. There was no GPU training
or inference and no paid language call. The four-hour / six CPU-hour / two GB
ceilings are enforced; no unused ceiling is treated as a reason to continue.

Actual development commands, run before sealing:

```bash
UV_CACHE_DIR=/tmp/dual-rec-uv-cache PYTHONDONTWRITEBYTECODE=1 \\
uv run --no-sync python scripts/reboot_overnight_worker.py --root {root} \\
 --name final-development-comparison05 --timeout 600 -- uv run --no-sync python \\
 scripts/explanation_repair_run.py --root {root} --attempt {target.name}
uv run --no-sync python scripts/explanation_repair_audit.py --root {root}
uv run --no-sync python scripts/explanation_repair_language_audit.py --root {root}
```

The language generation/resume commands are recorded exactly in `commands.jsonl`.
They use `scripts/explanation_repair_language.py`, `--offline --no-project`, the
qualified supplementary Transformers4.57.6/tokenizers0.22.2/Hub0.36.2 runtime,
unchanged project CPU Torch, and `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1`.
`language/frozen_language_inputs.json` pins the cases, instructions, one-shot format
example, cap and runner/config hashes; `language/backend.json` pins model assets
and every supplementary dependency version. Reuse is verified in
`language/independent_audit.json`; source-path correction is in
`language_input_correction.json`. `post_batch_source_amendments.json` preserves the
original structured protocol and runner: only an appended language scope and an
incorrect output-manifest availability statement changed, with exact replacements
verified. Structured editor/selector logic and results did not change.

Sealed evidence refuses mutation. Repeating a batch requires a separately authorized
fresh unsealed root/clock and the pinned inputs; it must not overwrite an attempt.
The core CLI can read a saved worked bundle and write to a new temporary output:

```bash
UV_CACHE_DIR=/tmp/dual-rec-uv-cache PYTHONDONTWRITEBYTECODE=1 \\
uv run --no-sync python scripts/explanation_repair_run.py \\
 --input {target}/worked_inputs/selective-replacement.json \\
 --output /tmp/explanation-repair-example-new.json
UV_CACHE_DIR=/tmp/dual-rec-uv-cache PYTHONDONTWRITEBYTECODE=1 \\
uv run --no-sync python scripts/explanation_repair_finish.py --root {root} --stage verify
```

The fixed question remains unresolved as a substantive research contribution.
Parser/gold-repair limitations, unsuccessful bounded language outputs, missing full
language comparisons, and the uninformative
downstream contrast prevent a complete claim. [RARR](https://aclanthology.org/2023.acl-long.910/)
already edits for attribution while preserving content; the parent and HEXAR
overlap limits are recorded in the protocol. There is no proven literature gap.
The full Weeks 2–4 campaign, fresh independent seeds, held-out confirmation and
model-misspecification experiments were not authorized for this first session and
were not run; the bounded language diagnostic above was part of this first session. No new
topic, simulator, controller, architecture, detector or manuscript was substituted.
The supervisor retains continuation and publication decisions; simulation-only
evaluation is the target and no real robot is imposed as a later requirement.
"""
    Path("EXPLANATION_REPAIR_RESULTS.md").write_text(text)
    save(
        root / "research_disposition.json",
        {
            "authorized_session": "COMPLETE_FIRST_SESSION_ONLY",
            "method_advantage": "NOT_ESTABLISHED_OVER_DELETE_OR_EVIDENCE_ONLY_REGENERATION",
            "end_to_end_language_evaluation": "INCOMPLETE_LOW_PARSER_COVERAGE_AND_NO_GOLD_REPAIRS",
            "language_baselines": "BOUNDED_11_INPUT_DIAGNOSTIC_COMPLETED_ZERO_COMPLETE_JSON; FULL_COMPARISON_NOT_RUN",
            "downstream_repair_effect": "NOT_IDENTIFIABLE_WITH_OBSERVATION_DOMINANT_SELECTOR",
            "held_out_confirmation": "NOT_RUN_NOT_AUTHORIZED_FIRST_SESSION",
            "new_physics": 0,
            "manuscript": False,
        },
    )
    print(
        {
            "report": "EXPLANATION_REPAIR_RESULTS.md",
            "attempt": target.name,
            "public_rows": public["rows"],
            "proposed_totals": dict(totals["proposed"]),
        }
    )


def seal(root):
    started_cpu = time.process_time()
    with Path("/tmp/reboot-overnight-ieeeral.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        target = Path(read(root / "latest_development.json")["path"])
        assert read(target / "independent_audit.json")["status"] == "PASS"
        assert read(root / "language/independent_audit.json")["status"] == "PASS"
        assert read(root / "validation.json")["status"] == "PASS"
        save(root / "preservation.json", preserve(root))
        commands = [
            json.loads(line)
            for line in (root / "commands.jsonl").read_text().splitlines()
        ]
        resolutions = (
            read(root / "resolved_worker_failures.json")
            if (root / "resolved_worker_failures.json").exists()
            else {}
        )
        assert all(
            c["exit_status"] == 0 or c["name"] in resolutions for c in commands
        ), "Preserve and explain a failing job before closing"
        workers = []
        for process in psutil.process_iter(["pid", "cmdline"]):
            cmd = process.info["cmdline"] or []
            if str(root) in cmd and any(
                Path(a).name
                in [
                    "reboot_overnight_worker.py",
                    "explanation_repair_run.py",
                    "explanation_repair_audit.py",
                ]
                for a in cmd
            ):
                workers.append(process.info)
        assert not workers, workers
        inventory = {
            str(p.relative_to(root)): sha(p)
            for p in root.rglob("*")
            if p.is_file() and not p.is_symlink()
        }
        initial = read(root / "initial.json")
        resources = {
            "session_wall_seconds": time.time() - initial["started_epoch"],
            "wall_scope": initial["start_scope"],
            "measured_worker_and_seal_cpu_seconds": sum(
                c["cpu_seconds"] for c in commands
            )
            + time.process_time()
            - started_cpu,
            "interactive_cpu_allowance_seconds": 600,
            "overhead_scope": "Interactive discovery, inspection, short lint checks, data materialization and read-only final verification covered conservatively; remote tool/host reasoning CPU not locally measured",
            "peak_job_rss_kib": max(c["max_rss_kib"] for c in commands),
            "new_logical_bytes_before_small_seal": sum(
                p.stat().st_size
                for p in root.rglob("*")
                if p.is_file() and not p.is_symlink()
            ),
            "maintained_change_allowance_bytes": 1000000,
            "gpu_training_seconds": 0,
            "gpu_inference_seconds": 0,
            **language_resources(root),
            "paid_research_language_calls": 0,
            "preserved_nonzero_jobs": [
                c["name"] for c in commands if c["exit_status"] != 0
            ],
            "neural_training_fits": 0,
            "new_physical_rollouts": 0,
            "unique_reused_reference_continuations": 170,
            "unique_task_parent_seeds": 45,
            "reused_condition_cells": 85,
            "computational_attempts": len(list(root.glob("development[0-9][0-9]"))),
            "research_workers_remaining": 0,
            "worker_check": "No matching foreground research worker; exclusive shared lock held during seal; no agents or detached jobs launched",
            "branch": subprocess.check_output(
                ["git", "branch", "--show-current"], text=True
            ).strip(),
            "commit": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], text=True
            ).strip(),
            "push_attempted": False,
            "upstream_file_bytes": sum(
                f["bytes"] for f in read(root / "upstream_manifest.json")["files"]
            ),
            "public_web_transfer": "Not byte-metered remote primary-source reading; no downloaded model weights",
        }
        assert resources["session_wall_seconds"] < initial["limits"]["wall_seconds"]
        assert (
            resources["measured_worker_and_seal_cpu_seconds"] + 600
            < initial["limits"]["cpu_seconds"]
        )
        assert (
            resources["new_logical_bytes_before_small_seal"] + 1000000
            < initial["limits"]["new_bytes"]
        )
        save(root / "resources.json", resources)
        inventory["resources.json"] = sha(root / "resources.json")
        save(
            root / "completion_manifest.json",
            {
                "status": "COMPLETE_AUTHORIZED_FIRST_SESSION",
                "disposition": read(root / "research_disposition.json"),
                "resources": resources,
                "sha256": inventory,
                "source_sha256": {str(p): sha(p) for p in maintained()},
            },
        )
        print(json.dumps(resources, indent=2))
        print("seal_sha256", sha(root / "completion_manifest.json"))


def verify(root):
    manifest = read(root / "completion_manifest.json")
    for name, expected in manifest["sha256"].items():
        assert sha(root / name) == expected, name
    for name, expected in manifest["source_sha256"].items():
        assert sha(Path(name)) == expected, name
    assert preserve(root)["status"] == "PASS"
    print(
        {
            "status": "PASS",
            "sealed_files": len(manifest["sha256"]),
            "seal_sha256": sha(root / "completion_manifest.json"),
        }
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument(
        "--stage", choices=["validate", "report", "seal", "verify"], required=True
    )
    args = parser.parse_args()
    if args.stage != "verify" and (args.root / "completion_manifest.json").exists():
        raise SystemExit("Evidence sealed")
    {"validate": validate, "report": report, "seal": seal, "verify": verify}[
        args.stage
    ](args.root)
