"""Render the measured research handoff and audit selected endpoint fields."""

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from recovery_claims_analyze import boot

from dual_rec.replay import jsonable


def read(path):
    return json.loads(path.read_text())


def save(path, value):
    path.write_text(json.dumps(jsonable(value), indent=2) + "\n")


def table(headers, rows):
    def cell(value):
        return "N/A" if value is None else str(value).replace("|", "/")

    return (
        "\n".join(
            [
                "| " + " | ".join(headers) + " |",
                "| " + " | ".join(["---"] * len(headers)) + " |",
            ]
            + ["| " + " | ".join(cell(v) for v in row) + " |" for row in rows]
        )
        + "\n"
    )


def interval(values):
    return (
        "N/A"
        if values is None
        else "[" + ", ".join(f"{100 * v:.2f}" for v in values) + "]"
    )


def run(root):
    assert read(root / "independent_audit.json")["status"] == "PASS"
    assert read(root / "external_evaluator_smoke.json")["status"] == "PASS"
    A, B, C, D, E = [
        read(root / (name + ".json"))
        for name in [
            "A_inventory",
            "B_fidelity",
            "C_acceptance",
            "D_baselines",
            "E_effects",
        ]
    ]
    certificates = read(root / "all_certificates.json")
    cs = [c for c in certificates if c["split"] == "confirmation"]
    fresh = {}
    native = {}
    for c in cs:
        if c["method"] == "M" and c["route"] in ["fresh_prefix", "native_snapshot"]:
            payload = read(root / c["bundle"])
            key = (c["task"], c["parent"], c["condition"], c["action"])
            if c["route"] == "fresh_prefix":
                fresh[key] = payload["success"][-1]
                assert c["terminal_success"] == fresh[key]
            else:
                native[key] = payload
    endpoints = defaultdict(
        lambda: {
            "records": 0,
            "supported": 0,
            "withheld": 0,
            "selected_endpoint_disagreements": 0,
            "prefix_completed": 0,
        }
    )
    for c in cs:
        if c["route"] != "native_snapshot":
            continue
        key = (c["task"], c["parent"], c["condition"], c["action"])
        payload = native[key]
        assert c["candidate_terminal_success"] == payload["success"][-1]
        chosen = (
            payload["completion_success"]
            if c["completed_with_prefix"]
            else payload["success"]
        )
        assert c["terminal_success"] == chosen[-1]
        out = endpoints[(c["task"], c["method"])]
        out["records"] += 1
        out["supported"] += c["status"] == "SUPPORTED"
        out["withheld"] += c["status"] != "SUPPORTED"
        out["selected_endpoint_disagreements"] += (
            c["status"] == "SUPPORTED" and c["terminal_success"] != fresh[key]
        )
        out["prefix_completed"] += c["completed_with_prefix"]
    endpoint_rows = [
        {"task": t, "method": m, **v} for (t, m), v in sorted(endpoints.items())
    ]
    save(
        root / "selected_outcome_audit.json",
        {
            "status": "PASS",
            "native_certificate_fields_checked": sum(
                v["records"] for v in endpoints.values()
            ),
            "prerequisite": "Full raw-to-bundle independent audit PASS",
            "scope": "Separate selected/candidate endpoint checks against the already raw-verified input bundles; no new simulator outcomes",
            "rows": endpoint_rows,
        },
    )
    # Same registered parent bootstrap and class weighting as frozen Table D.
    groups = defaultdict(lambda: defaultdict(list))
    for c in cs:
        groups[(c["task"], c["method"], c["control_status"])][c["parent"]].append(
            c["status"] == "SUPPORTED"
        )
    ablations = []
    cfg = read(root / "registration.json")
    for task in cfg["tasks"]:
        for ablation in ["no_F3", "no_memory", "no_unknown", "no_completion"]:
            for kind in ["valid", "invalid", "incomplete"]:
                left, right = groups[(task, "M", kind)], groups[(task, ablation, kind)]
                delta = {
                    p: float(np.mean(v) - np.mean(right[p]))
                    for p, v in left.items()
                    if p in right
                }
                values = list(delta.values())
                if kind == "invalid":
                    ids = sorted(cfg["seeds"][task]["confirmation"])
                    values = [
                        float(np.mean([delta[str(p)] for p in pair if str(p) in delta]))
                        for pair in zip(ids[::2], ids[1::2], strict=True)
                        if any(str(p) in delta for p in pair)
                    ]
                row = {
                    "task": task,
                    "ablation": ablation,
                    "population": kind,
                    "parents": len(delta),
                    "clusters": len(values),
                    "admission_difference": float(np.mean(values)) if values else None,
                    "ci95": boot(values),
                }
                if ablation == "no_F3":
                    original = next(
                        d
                        for d in D
                        if d["split"] == "confirmation"
                        and d["task"] == task
                        and d["baseline"] == ablation
                        and d["population"] == kind
                    )
                    assert (
                        row["admission_difference"] == original["admission_difference"]
                        and row["ci95"] == original["ci95"]
                    )
                if values and np.ptp(values) == 0:
                    assert np.allclose(row["ci95"], [values[0], values[0]])
                ablations.append(row)
    save(root / "ablation_paired_comparisons.json", ablations)
    contrast_rows = []
    recorded_contrasts = read(root / "decision_contrasts.json")
    domains = sorted({(k[0], k[2]) for k in native})
    for task, condition in domains:
        parents = sorted({k[1] for k in native if k[0] == task and k[2] == condition})
        values = []
        for parent in parents:
            keys = [(task, parent, condition, a) for a in ["continue", "recover"]]
            reference = int(fresh[keys[1]]) - int(fresh[keys[0]])
            candidate = int(native[keys[1]]["success"][-1]) - int(
                native[keys[0]]["success"][-1]
            )
            values.append((reference, candidate))
        observed = next(
            r
            for r in recorded_contrasts
            if r["split"] == "confirmation"
            and r["task"] == task
            and r["condition"] == condition
            and r["route"] == "native_snapshot"
        )
        ranking_changes = sum(np.sign(a) != np.sign(b) for a, b in values)
        disagreements = sum(a != b for a, b in values)
        differences = [b - a for a, b in values]
        assert ranking_changes == observed["ranking_changes"]
        assert disagreements == observed["contrast_disagreements"]
        assert np.isclose(
            abs(np.mean(differences)), observed["absolute_mean_difference"]
        )
        contrast_rows.append(
            {
                "task": task,
                "condition": condition,
                "parents": len(values),
                "ranking_changes": ranking_changes,
                "contrast_disagreements": disagreements,
                "candidate_minus_reference": float(np.mean(differences)),
                "paired_ci95": boot(differences),
            }
        )
    save(
        root / "independent_native_contrasts.json",
        {"status": "PASS", "rows": contrast_rows},
    )
    primary = [
        b for b in B if b["split"] == "confirmation" and b["route"] == "native_snapshot"
    ]
    b_rows = []
    for b in primary:
        payloads = [
            v
            for k, v in native.items()
            if k[0] == b["task"] and k[2] == b["condition"] and k[3] == b["action"]
        ]
        b_rows.append(
            [
                b["task"],
                b["condition"],
                b["action"],
                b["qualified"],
                b["trajectory_pass"],
                sum(max(v["state_errors"]) <= 1 for v in payloads),
                b["discordances"],
                f"{100 * b['upper']:.3f}%",
                "PASS" if b["upper"] <= 0.025 else "INSUFFICIENT",
            ]
        )
    matrix = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    for c in C:
        if c["split"] == "confirmation":
            for status in ["SUPPORTED", "REFUTED_CONTRACT", "INSUFFICIENT_EVIDENCE"]:
                matrix[(c["task"], c["method"])][c["control_status"]][status] += c[
                    status
                ]

    def triple(counts):
        return "/".join(
            str(counts[s])
            for s in ["SUPPORTED", "REFUTED_CONTRACT", "INSUFFICIENT_EVIDENCE"]
        )

    routes = defaultdict(lambda: defaultdict(int))
    for c in cs:
        if c["method"] == "M":
            routes[(c["task"], c["route"])][c["status"]] += 1
    a_rows = [
        [
            a[k]
            for k in [
                "task",
                "condition",
                "attempted",
                "qualified",
                "initial_nonsuccess",
                "triggered_failed",
                "new_continue",
                "new_recover",
            ]
        ]
        for a in A
        if a["split"] == "confirmation"
    ]
    e_rows = [
        [
            e["task"],
            e["condition"],
            e["population"],
            e["n"],
            e["continue_success"],
            e["recover_success"],
            None if e["difference"] is None else f"{100 * e['difference']:.2f}",
            interval(e["ci95"]),
            interval(e["conservative_exact_difference_ci95"]),
        ]
        for e in E
        if e["split"] == "confirmation"
    ]
    bounds = [
        b
        for b in read(root / "invalid_acceptance_bounds.json")
        if b["split"] == "confirmation" and b["method"] == "M"
    ]
    commands = [
        json.loads(s) for s in (root / "commands.jsonl").read_text().splitlines()
    ]
    tests = next(c for c in commands if c["name"] == "final-maintained-tests")
    assert tests["exit_status"] == 0
    text = """# RecoveryClaim experimental research report

This is a measured research handoff, not a manuscript. All registered confirmation cells completed. The method-advancement verdict is **NO DISTINCT NET METHOD BENEFIT ESTABLISHED over strict qualification plus qualified-prefix completion**. Decision-relative certification does separate some harmless replay mismatches from decision-changing ones, but equal-affordance completion removes the observed admission advantage and this eager campaign does not demonstrate net computational savings.

The paired physical effects below belong to existing scripted simulator interventions. They are not improvements caused by the certifier and are not real-robot recovery evidence. No new detector, policy architecture, annotation, task, fault severity, or dataset was introduced.

## Frozen scope and inference

Reviewed base: b29d9e5f8873b7fa4c59ffa93ed72cc7379ed6a0. Frozen implementation/protocol commit: 6c4f819082c172fc56025df57e1b97f1b610b96b. Branch: research/recovery-claims-validated-results. Final local HEAD is recorded in resources.json/completion_manifest.json after the scoped commit.

The immutable hash rule selected 20 development and then 210 confirmation seeds/task. The initial target 100 is retained as the first confirmation block. The extension was frozen before confirmation because alpha=.05/10 and per-action discordance tolerance .025 require 210 zero-disagreement parents. It was not selected from confirmation outcomes. Conditions/actions share parents. Invalid controls with swapped parents use registered parent-pair clusters. Effect intervals are per-cell, not simultaneously valid across all displayed contrasts. The finite seed distribution, fixed action tapes, software/model construction, and measurement channels are explicit assumptions; no policy-general or safety guarantee follows.

The supervisor increased the downstream reserve to 90 minutes. Physics finished at 01:07:50 UTC, before the early admission cutoff 01:31:55 UTC and hard cutoff 01:46:55 UTC. The original 12-hour ceiling is 03:16:55 UTC. Original scientific protocol/configs and raw outcomes are preserved. Two post-collection reporting fixes (NumPy JSON conversion and optional CLI stdout witness access) have exact source replacements and original copies in source_amendments.json; neither changes numerical/scientific logic.

## Table A: actual confirmation inventory

PickCube offset002 is a scripted grasp-target x offset .02 m; PushCube misaligned is the existing lateral scripted-path offset .07 m. Lift is the nominal full-adapter control. All use original 70-step actions. Failed means the original event trigger plus initial nonsuccess; unfinished clean prefixes are not automatically failures. First-hit counts below exclude already-successful starts.

"""
    text += table(
        [
            "Task",
            "Condition",
            "Attempted",
            "Qualified",
            "Initial nonsuccess",
            "Triggered failed",
            "New continue first-hit",
            "New recover first-hit",
        ],
        a_rows,
    )
    text += "\nThere are 630 task-parent seeds and 1,050 confirmation condition cells, with 14,700 completed continuations. Development has 20 seeds/task; only the five finalized instrumentation cells have complete reference-controller telemetry. Earlier development outcomes remain preserved and unqualified rather than backfilled. Five original repeat-cell records are retained separately and never counted as independent confirmation.\n\n## Table B: native-route fidelity and uncertainty\n\nF1 input/controller/history checks pass for these confirmation candidates. F2 includes both checkpoint and continuation; post-only is shown separately. The ten primary one-sided bounds use alpha=.005 each. Seven action/domain cells meet .025; three PickCube cells do not. The union bound implies a contrast tolerance at most .05 only when both action bounds qualify in that domain. Other route bounds are diagnostic.\n\n"
    text += table(
        [
            "Task",
            "Condition",
            "Action",
            "n",
            "Strict F2 passes",
            "Post-only passes",
            "Y disagreements",
            "Upper discordance",
            "F3",
        ],
        b_rows,
    )
    text += "\nAll native full-checkpoint F2 gates fail under the frozen channels. For Lift, post-step traces and terminal outcomes match, but immediate recorded body position/contact differs despite identical qpos, velocity, observation and time. A representative offset is 0.2884 mm. This is consistent with a derived-readout phase issue; its cause was not independently established. P2 strict checkpoint parity is **not met**. Do not interpret that readout difference as proven physical dynamics divergence or use it to claim dominance over a canonicalized state checker. No tolerance or phase convention was changed after results. Fresh-prefix P1 qualified all 1,050 confirmation cells.\n\n## Table C: controlled admission matrix\n\nEntries are SUPPORTED/REFUTED/INSUFFICIENT. SUPPORTED means scoped evidence support, not that the task succeeded. Valid-input native cases can still lack F3; M may explicitly replace them with an executed qualified prefix. Missing manifests are separated from contradicted contracts. B2/B3/B4 are adapted component proxies, not official prior-system reproductions.\n\n"
    contrast_table = table(
        [
            "Task",
            "Condition",
            "Parents",
            "Native contrast disagreements",
            "Ranking changes",
            "Native minus reference effect pp",
            "Paired 95% pp",
        ],
        [
            [
                r["task"],
                r["condition"],
                r["parents"],
                r["contrast_disagreements"],
                r["ranking_changes"],
                f"{100 * r['candidate_minus_reference']:.2f}",
                interval(r["paired_ci95"]),
            ]
            for r in contrast_rows
        ],
    )
    marker = "## Table C: controlled admission matrix"
    text = text.replace(
        marker,
        "Native intervention-contrast diagnostics, independently recomputed from raw-verified bundles:\n\n"
        + contrast_table
        + "\nThese are descriptive paired diagnostics; the registered simultaneous F3 decision uses both action-specific bounds. The qualification and contrast summaries use the same fixed confirmation cohort, rather than a separate prospective deployment test.\n\n"
        + marker,
    )
    text += table(
        [
            "Task",
            "Method",
            "Valid-input cases P/F/U",
            "Invalid-contract cases P/F/U",
            "Incomplete-manifest cases P/F/U",
        ],
        [
            [t, m, triple(v["valid"]), triple(v["invalid"]), triple(v["incomplete"])]
            for (t, m), v in sorted(matrix.items())
        ],
    )
    text += "\nAcross the fixed valid-input mixture, M withheld 0/4,200 cases; B1 and B2 withheld 2,100/4,200, all as INSUFFICIENT rather than contradicted contracts. B4 and strict-plus-prefix also withheld 0/4,200. These records share 630 task-parent seeds and are not 4,200 independent trials. Conditional native-route coverage and actual prefix replacement are separated below.\n"
    text += "\n## Table D: strongest-baseline comparison and computational cost\n\nThe registered paired admission comparison is M minus baseline, using parent means across condition/action variants. Constant bootstrap intervals describe these observed gate outcomes; they do not prove population equivalence.\n\n"
    text += table(
        [
            "Task",
            "Comparator",
            "Parents",
            "Valid admission difference pp",
            "Paired bootstrap 95% pp",
        ],
        [
            [
                d["task"],
                d["baseline"],
                d["parents"],
                f"{100 * d['admission_difference']:.2f}",
                interval(d["ci95"]),
            ]
            for d in D
            if d["split"] == "confirmation" and d["population"] == "valid"
        ],
    )
    text += (
        "\nM accepted 0 invalid cases: "
        + "; ".join(
            f"{b['task']}: 0/{b['invalid_records']} records, 0/{b['parent_pair_clusters']} linked-parent clusters, upper {100 * b['upper']:.3f}%"
            for b in bounds
        )
        + ". Bounds are simultaneous across the three tasks per method at alpha=.05/3, not a proof of zero future error. Strict-plus-prefix and B4 have the same observed invalid-control admission.\n\nNative candidate endpoint fields were checked separately against raw-verified bundles:\n\n"
    )
    text += table(
        [
            "Task",
            "Method",
            "Native records",
            "Admitted",
            "Withheld",
            "Admitted selected-Y disagreements",
            "Prefix replacements",
        ],
        [
            [
                r[k]
                for k in [
                    "task",
                    "method",
                    "records",
                    "supported",
                    "withheld",
                    "selected_endpoint_disagreements",
                    "prefix_completed",
                ]
            ]
            for r in endpoint_rows
            if r["method"] in ["B1", "B4", "M", "no_F3", "no_completion"]
        ],
    )
    text += "\nThe 16 PickCube native endpoint disagreements are avoided by M's qualified-prefix replacement. The no_F3 strict-plus-prefix workflow achieves the same zero selected-endpoint disagreements and full admission. M selects 630 prefix replacements versus 2,100 for that workflow, conditional on the already-collected qualification cohort. These are **selection counts, not observed saved executions**: all reference/candidate/control continuations were eagerly executed for every method. No prospective net speedup or amortization benefit is established.\n\nActual route creation/restoration, prefix and continuation timing follows; reference acquisition and the remaining negative controls are additional campaign costs.\n\n"
    text += table(
        [
            "Task",
            "Route",
            "Recorded continuations",
            "Measured wall s",
            "Median route s",
            "Prefix controls",
        ],
        [
            [
                x["task"],
                x["route"],
                x["continuations"],
                round(x["wall_seconds_sum"], 3),
                round(x["wall_seconds_median"], 3)
                if x["wall_seconds_median"] is not None
                else None,
                x["prefix_controls"],
            ]
            for x in read(root / "qualification_costs.json")
            if x["split"] == "confirmation"
            and x["route"] in ["native_snapshot", "fresh_prefix"]
        ],
    )
    text += "\n## Table E: matched physical effects\n\nDifferences and intervals are percentage points, recovery minus continue, on qualified fresh-prefix starts. Bootstrap is the registered 2,000 parent draws. The supplementary conservative paired-binary interval uses separate Bonferroni Clopper-Pearson gain/loss bounds and avoids treating degenerate bootstrap intervals as certainty. Zero-denominator contrasts are N/A.\n\n"
    text += table(
        [
            "Task",
            "Condition",
            "Population",
            "n",
            "Continue Y",
            "Recover Y",
            "Difference pp",
            "Bootstrap95% pp",
            "Conservative95% pp",
        ],
        e_rows,
    )
    text += "\nP3 genuine triggered-failure recovery is 91/113 versus 0/113 for PickCube. PushCube has 207/210 versus 0/210 in its fixed misalignment family. Clean already-successful PickCube states show harm (155/209 versus 209/209). Lift has no qualified failed starts and cannot support general C4 recovery-improvement claims. All actions execute 70 controls at 20 Hz, so elapsed simulation cost is 3.5 s/action and paired cost difference is 0 by design. This is not a time-to-completion or robot-efficiency result. No method ranking was selected using these outcomes.\n\n## Table F: robustness and witnessed controls\n\nNative is a candidate restoration, not automatically an invalid contract. Controller-memory replacement, physically read-back friction changes, reversed actual controls, midrollout injection, swapped actual parent records and removed claim provenance retain their original outcomes. Parent/provenance mutations are mechanical evidence controls, not additional simulator rollouts. N7 removes model identity from the claim while the original counterpart is retained for audit.\n\n"
    text += table(
        ["Task", "Route/control", "M P/F/U"],
        [[t, route, triple(v)] for (t, route), v in sorted(routes.items())],
    )
    text += "\nBudget/timing declaration-corruption checks are in mechanical_control_checks.json: actual unchanged controls/outcomes are paired with corrupt declarations. They are software checks, not additional physical timing experiments. Actual midrollout injection also produces a recorded clock inconsistency. The emitted first-observed witnesses were independently recomputed; no minimum-unsatisfiable-core claim is made.\n\n## Ablations and paired uncertainty\n\nThese reuse the registered Table D weighting/bootstrap. Invalid comparisons use fixed parent-pair clusters; other comparisons use parents. Nonzero entries below are M minus ablation admissions in percentage points. Zero/constant bootstrap intervals are descriptive for this fixed mixture of control types. All entries, including zero contrasts, remain in ablation_paired_comparisons.json.\n\n"
    text += table(
        [
            "Task",
            "Ablation",
            "Population",
            "Clusters",
            "M minus ablation pp",
            "Paired 95% pp",
        ],
        [
            [
                a["task"],
                a["ablation"],
                a["population"],
                a["clusters"],
                f"{100 * a['admission_difference']:.2f}",
                interval(a["ci95"]),
            ]
            for a in ablations
            if a["admission_difference"] not in [None, 0]
        ],
    )
    text += "\nRemoving F3 leaves full admission but requires prefix replacement on every native branch. Removing memory obligations admits contradicted memory-reset controls; removing UNKNOWN handling admits incomplete model manifests. Removing completion withholds 630 PickCube native claims that M supports only after real prefix replacement. These are component diagnostics, not deployable variants.\n\n## Secondary adapters, independent verification and tests\n\nNo models were retrained. The prior 100-record FailTime Long cross-fit retains 57 failures, 43 successes and the one censored onset; source/task separation and calibration/continuous alarms are checked. Its previously zero timely-alarm result is not promoted into an online detector success. REBOOT reuses 55 annotated recoveries and 62 expert-source references. All 55 reset witnesses are recomputed on unchanged scores; known aliases remain invalid unless explicitly collapsed, and missing cross-object temporal evidence remains UNKNOWN. An annotation convention is not a physically established onset. These previously-used records support adapter portability, not untouched confirmation or physical recovery effects.\n\nThe independent physical software audit passed 13,800 traces, 4,220 full prefix pairs, 16,100 primary continuations, 1,713,686 recorded control steps, 172,500 certificates, 1,150 matched input bundles and all 30 effect cells. The separate legacy/evaluator audit passed 100 + 117 score streams, 55 reset witnesses, 330 historical member hashes and 23 fresh-process mixed cases. There was no independent human study. The package answer key is separate. Selected endpoint fields are additionally checked in selected_outcome_audit.json.\n\nFinal maintained tests: 349 passed and 4 optional-stack skips (final-maintained-tests.log). All four optional old-stack physics tests passed separately in their unchanged Python3.10/MuJoCo2.3.2 environment; see final-pinned-physics-tests.log. Maintained Ruff scope is src/scripts/tests. Whole-tree findings in historical ad hoc scripts and bare-pytest vendored collection failures are preserved; they were not relabelled as passing tests. Engineering failures and same-parent retries are retained in resolved_worker_failures.json and parent_attempt_failure_resolutions.json. No confirmation attempt failed or seed was replaced.\n\n## Provenance, resources and exact reproduction\n\n"
    text += f"Evidence root: `{root}`. Source/engine identities: confirmation_freeze.json, source_amendments.json, engine_fingerprints.json (1256 installed simulator files), worker_runtime_versions.json, secondary_source_hashes.json and the final completion_manifest.json. The current measured completed-job CPU total before report/packaging is {sum(c['cpu_seconds'] for c in commands) / 3600:.4f} core-hours; final authoritative usage, local branch/HEAD, archive hash and workers=0 are recorded by resources.json/completion_manifest.json after closing. They include the 600 CPU-second allowance for interactive work. GPU 0; new dataset/weight downloads 0; public primary-source tool traffic is not byte-metered and has a 20 MB conservative allowance. The original 12-hour/20CPUh/6GB limits remain in force.\n\n"
    text += """```bash
# On an unsealed registered run, using the unchanged bounded worker environment:
uv run --no-sync python scripts/reboot_overnight_worker.py --root RUN --name UNIQUE --timeout 3600 -- uv run --no-sync python scripts/recovery_claims_analyze.py --root RUN
uv run --no-sync python scripts/reboot_overnight_worker.py --root RUN --name REVIEW_UNIQUE --timeout 300 -- uv run --no-sync python scripts/recovery_claims_review.py --root RUN
uv run --no-sync python scripts/reboot_overnight_worker.py --root RUN --name AUDIT_UNIQUE --timeout 1800 -- uv run --no-sync python scripts/recovery_claims_audit.py --root RUN
# Frozen portable representative verification, no simulator or trained weights:
uv run --no-sync python RUN/external_evaluator/run.py
# Read-only final checksum/preservation verification:
uv run --no-sync python scripts/recovery_claims_finalize.py --root RUN --stage verify
```

Full reproduction needs the preserved original inputs, engine versions and registered seed lists. Sealed evidence refuses mutation; a later authorized campaign needs a fresh unsealed root/clock. remaining_registered_cells.json is empty: there is no unfinished frozen physics cohort. Complete raw records are under parents/; the compact supervisor_review.tar.gz contains review tables, sources, audits and selected replay records rather than the entire raw cohort. No logs, raw trajectories or archive are committed to Git. User documentation moves, .gitignore, uv.lock and historical evidence are preserved. Publication remains manual; no push was attempted.

## Novelty and scientific boundary

[RESCUE](https://arxiv.org/html/2610.13516) already supplies robot-policy branching and trunk replay prerequisites. [ROEP](https://www.mdpi.com/1424-8220/26/15/4757) already supplies claim admission and runtime-integrity gates. [EvalSpec](https://doi.org/10.1109/TASE.2026.3745671) primary full text was inaccessible; B3 is explicitly a limited proxy. No absence-of-prior-work or whole-system dominance claim is established. The six-source inspection and exact overlap limits are in RECOVERY_CLAIMS_NOVELTY_LEDGER.md.

The defensible result is scoped, uncertainty-aware physical replay/evidence characterization with working certificates and witnessed failures. Net advantage over the strongest completion workflow, full native checkpoint fidelity, broad recovery-policy generalization, real-robot intervention effects and direct novelty clearance remain unestablished. Minimum further work requires supervisor review: resolve the checkpoint-readout phase issue, assess full EvalSpec overlap, test prospective net qualification cost under the same methods, and obtain independent human/real-robot evidence before making corresponding claims. No new experiment, topic or manuscript is started by this report.
"""
    Path("RECOVERY_CLAIMS_EXPERIMENTAL_REPORT.md").write_text(text)
    disposition = {
        "method_advancement": "NO_DISTINCT_NET_METHOD_BENEFIT_ESTABLISHED",
        "full_frozen_confirmation_cells": 1050,
        "qualified_confirmation_cells": 1050,
        "qualified_failed_pick_starts": 113,
        "qualified_failed_push_starts": 210,
        "failed_lift_starts": 0,
        "native_decision_domains_qualified": 7,
        "native_decision_domains_total": 10,
        "strict_native_checkpoint_gate": "NOT_MET",
        "matched_simulator_effects": "SUPPORTED_CONDITIONAL_ON_FROZEN_CONSTRUCTION",
        "novelty": "UNRESOLVED_CLOSEST_PRIMARY_EVALSPEC_INACCESSIBLE",
        "independent_human_evaluation": False,
        "real_robot_intervention_effects": False,
        "manuscript_created": False,
        "publication_readiness_claimed": False,
    }
    save(root / "scientific_disposition.json", disposition)
    Path(
        "RECOVERY_CLAIMS_SUPERVISOR_GATE.md"
    ).write_text("""# Research-only supervisor gate

Disposition: **NO DISTINCT NET METHOD BENEFIT ESTABLISHED over the strongest strict-plus-qualified-prefix workflow.** The fixed implementation/physical campaign is complete; no manuscript or publication-readiness decision follows.

| Requirement | Disposition and evidence |
|---|---|
| Real physical simulator continuations and full fixed cohorts | Met: 210 parents/task, 1,050 qualified confirmation cells, 14,700 confirmation continuations |
| Input/contract controls | Scoped support: 0 invalid M admissions; per-task linked-parent upper bound 3.824%, not zero-error proof |
| Positive reconstruction controls | Fresh-prefix P1 met. Lift post-step parity met; strict native checkpoint P2 not met. Preserve pose/contact readout-phase uncertainty |
| Claim-relative outcome fidelity | 7/10 native action/domain bounds meet .025; three PickCube domains fail. No universal or policy-general replay guarantee |
| Genuine differential recovery | Simulator support: PickCube failed 113, 91 recovered versus 0; PushCube failed 210, 207 versus0. Clean PickCube harm retained. Lift failed-state C4 power unmet |
| Strongest applicable baseline | Admission/selected outcome parity with strict-plus-prefix; apparent gains over candidate-only strict checks require executed completion. Net compute savings unmeasured |
| Ablations, failure witnesses, uncertainty | Completed on same evidence; memory/UNKNOWN removals unsafe, completion essential for 630 PickCube native claims |
| Independent numerical verification | Separate raw-trajectory/status/effect/bound/hash/witness software paths passed; portable 23-case process verifier passed; no independent human evaluator |
| Closest-work novelty | Unresolved: RESCUE/ROEP overlap strong, EvalSpec primary inaccessible. Component proxies do not establish whole-method superiority |
| Real-robot recovery and publication readiness | Not established; offline REBOOT/FailTime adapter checks do not supply physical recovery outcomes |

The exact tables, paired bootstrap and conservative intervals, both first-hit and terminal populations, negative evidence, source hashes, tests and reproduction commands are in RECOVERY_CLAIMS_EXPERIMENTAL_REPORT.md and the linked evidence root. Final local SHA/resources/archive integrity and campaign-worker shutdown are attested by completion_manifest.json after closing.

Stop for scientific supervisor review. Minimum additional evidence for stronger claims: checkpoint-readout-phase qualification, full closest-source review, prospective net qualification-cost measurement with the same methods, and independent human/real-robot validation where claimed. This does not authorize a new method, dataset, architecture, experiment or manuscript.
""")
    print(
        {
            "report": "RECOVERY_CLAIMS_EXPERIMENTAL_REPORT.md",
            "gate": "RECOVERY_CLAIMS_SUPERVISOR_GATE.md",
            "endpoint_checks": sum(v["records"] for v in endpoints.values()),
            "ablation_contrasts": len(ablations),
        }
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    a = p.parse_args()
    assert not (a.root / "completion_manifest.json").exists(), "Evidence sealed"
    run(a.root)
