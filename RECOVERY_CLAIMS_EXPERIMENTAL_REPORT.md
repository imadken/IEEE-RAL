# RecoveryClaim experimental research report

This is a measured research handoff, not a manuscript. All registered confirmation cells completed. The method-advancement verdict is **NO DISTINCT NET METHOD BENEFIT ESTABLISHED over strict qualification plus qualified-prefix completion**. Decision-relative certification does separate some harmless replay mismatches from decision-changing ones, but equal-affordance completion removes the observed admission advantage and this eager campaign does not demonstrate net computational savings.

The paired physical effects below belong to existing scripted simulator interventions. They are not improvements caused by the certifier and are not real-robot recovery evidence. No new detector, policy architecture, annotation, task, fault severity, or dataset was introduced.

## Frozen scope and inference

Reviewed base: b29d9e5f8873b7fa4c59ffa93ed72cc7379ed6a0. Frozen implementation/protocol commit: 6c4f819082c172fc56025df57e1b97f1b610b96b. Branch: research/recovery-claims-validated-results. Final local HEAD is recorded in resources.json/completion_manifest.json after the scoped commit.

The immutable hash rule selected 20 development and then 210 confirmation seeds/task. The initial target 100 is retained as the first confirmation block. The extension was frozen before confirmation because alpha=.05/10 and per-action discordance tolerance .025 require 210 zero-disagreement parents. It was not selected from confirmation outcomes. Conditions/actions share parents. Invalid controls with swapped parents use registered parent-pair clusters. Effect intervals are per-cell, not simultaneously valid across all displayed contrasts. The finite seed distribution, fixed action tapes, software/model construction, and measurement channels are explicit assumptions; no policy-general or safety guarantee follows.

The supervisor increased the downstream reserve to 90 minutes. Physics finished at 01:07:50 UTC, before the early admission cutoff 01:31:55 UTC and hard cutoff 01:46:55 UTC. The original 12-hour ceiling is 03:16:55 UTC. Original scientific protocol/configs and raw outcomes are preserved. Two post-collection reporting fixes (NumPy JSON conversion and optional CLI stdout witness access) have exact source replacements and original copies in source_amendments.json; neither changes numerical/scientific logic.

## Table A: actual confirmation inventory

PickCube offset002 is a scripted grasp-target x offset .02 m; PushCube misaligned is the existing lateral scripted-path offset .07 m. Lift is the nominal full-adapter control. All use original 70-step actions. Failed means the original event trigger plus initial nonsuccess; unfinished clean prefixes are not automatically failures. First-hit counts below exclude already-successful starts.

| Task | Condition | Attempted | Qualified | Initial nonsuccess | Triggered failed | New continue first-hit | New recover first-hit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Lift | nominal | 210 | 210 | 0 | 0 | 0 | 0 |
| PickCube-v1 | nominal | 210 | 210 | 1 | 0 | 1 | 0 |
| PickCube-v1 | offset002 | 210 | 210 | 144 | 113 | 2 | 120 |
| PushCube-v1 | misaligned | 210 | 210 | 210 | 210 | 0 | 207 |
| PushCube-v1 | nominal | 210 | 210 | 210 | 0 | 205 | 206 |

There are 630 task-parent seeds and 1,050 confirmation condition cells, with 14,700 completed continuations. Development has 20 seeds/task; only the five finalized instrumentation cells have complete reference-controller telemetry. Earlier development outcomes remain preserved and unqualified rather than backfilled. Five original repeat-cell records are retained separately and never counted as independent confirmation.

## Table B: native-route fidelity and uncertainty

F1 input/controller/history checks pass for these confirmation candidates. F2 includes both checkpoint and continuation; post-only is shown separately. The ten primary one-sided bounds use alpha=.005 each. Seven action/domain cells meet .025; three PickCube cells do not. The union bound implies a contrast tolerance at most .05 only when both action bounds qualify in that domain. Other route bounds are diagnostic.

| Task | Condition | Action | n | Strict F2 passes | Post-only passes | Y disagreements | Upper discordance | F3 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Lift | nominal | continue | 210 | 0 | 210 | 0 | 2.491% | PASS |
| Lift | nominal | recover | 210 | 0 | 210 | 0 | 2.491% | PASS |
| PickCube-v1 | nominal | continue | 210 | 0 | 0 | 0 | 2.491% | PASS |
| PickCube-v1 | nominal | recover | 210 | 0 | 0 | 8 | 8.626% | INSUFFICIENT |
| PickCube-v1 | offset002 | continue | 210 | 0 | 0 | 3 | 5.129% | INSUFFICIENT |
| PickCube-v1 | offset002 | recover | 210 | 0 | 0 | 5 | 6.593% | INSUFFICIENT |
| PushCube-v1 | misaligned | continue | 210 | 0 | 0 | 0 | 2.491% | PASS |
| PushCube-v1 | misaligned | recover | 210 | 0 | 0 | 0 | 2.491% | PASS |
| PushCube-v1 | nominal | continue | 210 | 0 | 0 | 0 | 2.491% | PASS |
| PushCube-v1 | nominal | recover | 210 | 0 | 0 | 0 | 2.491% | PASS |

All native full-checkpoint F2 gates fail under the frozen channels. For Lift, post-step traces and terminal outcomes match, but immediate recorded body position/contact differs despite identical qpos, velocity, observation and time. A representative offset is 0.2884 mm. This is consistent with a derived-readout phase issue; its cause was not independently established. P2 strict checkpoint parity is **not met**. Do not interpret that readout difference as proven physical dynamics divergence or use it to claim dominance over a canonicalized state checker. No tolerance or phase convention was changed after results. Fresh-prefix P1 qualified all 1,050 confirmation cells.

Native intervention-contrast diagnostics, independently recomputed from raw-verified bundles:

| Task | Condition | Parents | Native contrast disagreements | Ranking changes | Native minus reference effect pp | Paired 95% pp |
| --- | --- | --- | --- | --- | --- | --- |
| Lift | nominal | 210 | 0 | 0 | 0.00 | [0.00, 0.00] |
| PickCube-v1 | nominal | 210 | 8 | 8 | -3.81 | [-6.67, -1.43] |
| PickCube-v1 | offset002 | 210 | 6 | 6 | -0.95 | [-3.33, 1.43] |
| PushCube-v1 | misaligned | 210 | 0 | 0 | 0.00 | [0.00, 0.00] |
| PushCube-v1 | nominal | 210 | 0 | 0 | 0.00 | [0.00, 0.00] |

These are descriptive paired diagnostics; the registered simultaneous F3 decision uses both action-specific bounds. The qualification and contrast summaries use the same fixed confirmation cohort, rather than a separate prospective deployment test.

## Table C: controlled admission matrix

Entries are SUPPORTED/REFUTED/INSUFFICIENT. SUPPORTED means scoped evidence support, not that the task succeeded. Valid-input native cases can still lack F3; M may explicitly replace them with an executed qualified prefix. Missing manifests are separated from contradicted contracts. B2/B3/B4 are adapted component proxies, not official prior-system reproductions.

| Task | Method | Valid-input cases P/F/U | Invalid-contract cases P/F/U | Incomplete-manifest cases P/F/U |
| --- | --- | --- | --- | --- |
| Lift | B0 | 840/0/0 | 2100/0/0 | 210/0/0 |
| Lift | B1 | 420/0/420 | 0/2100/0 | 0/0/210 |
| Lift | B2 | 420/0/420 | 0/2100/0 | 0/0/210 |
| Lift | B3 | 840/0/0 | 0/2100/0 | 210/0/0 |
| Lift | B4 | 840/0/0 | 0/2100/0 | 0/0/210 |
| Lift | M | 840/0/0 | 0/2100/0 | 0/0/210 |
| Lift | no_F3 | 840/0/0 | 0/2100/0 | 0/0/210 |
| Lift | no_completion | 840/0/0 | 0/2100/0 | 0/0/210 |
| Lift | no_memory | 840/0/0 | 420/1680/0 | 0/0/210 |
| Lift | no_unknown | 840/0/0 | 0/2100/0 | 210/0/0 |
| PickCube-v1 | B0 | 1680/0/0 | 4200/0/0 | 420/0/0 |
| PickCube-v1 | B1 | 840/0/840 | 0/4200/0 | 0/0/420 |
| PickCube-v1 | B2 | 840/0/840 | 0/4200/0 | 0/0/420 |
| PickCube-v1 | B3 | 1680/0/0 | 0/4200/0 | 420/0/0 |
| PickCube-v1 | B4 | 1680/0/0 | 0/4200/0 | 0/0/420 |
| PickCube-v1 | M | 1680/0/0 | 0/4200/0 | 0/0/420 |
| PickCube-v1 | no_F3 | 1680/0/0 | 0/4200/0 | 0/0/420 |
| PickCube-v1 | no_completion | 1050/0/630 | 0/4200/0 | 0/0/420 |
| PickCube-v1 | no_memory | 1680/0/0 | 840/3360/0 | 0/0/420 |
| PickCube-v1 | no_unknown | 1680/0/0 | 0/4200/0 | 420/0/0 |
| PushCube-v1 | B0 | 1680/0/0 | 4200/0/0 | 420/0/0 |
| PushCube-v1 | B1 | 840/0/840 | 0/4200/0 | 0/0/420 |
| PushCube-v1 | B2 | 840/0/840 | 0/4200/0 | 0/0/420 |
| PushCube-v1 | B3 | 1680/0/0 | 0/4200/0 | 420/0/0 |
| PushCube-v1 | B4 | 1680/0/0 | 0/4200/0 | 0/0/420 |
| PushCube-v1 | M | 1680/0/0 | 0/4200/0 | 0/0/420 |
| PushCube-v1 | no_F3 | 1680/0/0 | 0/4200/0 | 0/0/420 |
| PushCube-v1 | no_completion | 1680/0/0 | 0/4200/0 | 0/0/420 |
| PushCube-v1 | no_memory | 1680/0/0 | 840/3360/0 | 0/0/420 |
| PushCube-v1 | no_unknown | 1680/0/0 | 0/4200/0 | 420/0/0 |

Across the fixed valid-input mixture, M withheld 0/4,200 cases; B1 and B2 withheld 2,100/4,200, all as INSUFFICIENT rather than contradicted contracts. B4 and strict-plus-prefix also withheld 0/4,200. These records share 630 task-parent seeds and are not 4,200 independent trials. Conditional native-route coverage and actual prefix replacement are separated below.

## Table D: strongest-baseline comparison and computational cost

The registered paired admission comparison is M minus baseline, using parent means across condition/action variants. Constant bootstrap intervals describe these observed gate outcomes; they do not prove population equivalence.

| Task | Comparator | Parents | Valid admission difference pp | Paired bootstrap 95% pp |
| --- | --- | --- | --- | --- |
| PickCube-v1 | B1 | 210 | 50.00 | [50.00, 50.00] |
| PickCube-v1 | B2 | 210 | 50.00 | [50.00, 50.00] |
| PickCube-v1 | B4 | 210 | 0.00 | [0.00, 0.00] |
| PickCube-v1 | no_F3 | 210 | 0.00 | [0.00, 0.00] |
| PushCube-v1 | B1 | 210 | 50.00 | [50.00, 50.00] |
| PushCube-v1 | B2 | 210 | 50.00 | [50.00, 50.00] |
| PushCube-v1 | B4 | 210 | 0.00 | [0.00, 0.00] |
| PushCube-v1 | no_F3 | 210 | 0.00 | [0.00, 0.00] |
| Lift | B1 | 210 | 50.00 | [50.00, 50.00] |
| Lift | B2 | 210 | 50.00 | [50.00, 50.00] |
| Lift | B4 | 210 | 0.00 | [0.00, 0.00] |
| Lift | no_F3 | 210 | 0.00 | [0.00, 0.00] |

M accepted 0 invalid cases: PickCube-v1: 0/4200 records, 0/105 linked-parent clusters, upper 3.824%; PushCube-v1: 0/4200 records, 0/105 linked-parent clusters, upper 3.824%; Lift: 0/2100 records, 0/105 linked-parent clusters, upper 3.824%. Bounds are simultaneous across the three tasks per method at alpha=.05/3, not a proof of zero future error. Strict-plus-prefix and B4 have the same observed invalid-control admission.

Native candidate endpoint fields were checked separately against raw-verified bundles:

| Task | Method | Native records | Admitted | Withheld | Admitted selected-Y disagreements | Prefix replacements |
| --- | --- | --- | --- | --- | --- | --- |
| Lift | B1 | 420 | 0 | 420 | 0 | 0 |
| Lift | B4 | 420 | 420 | 0 | 0 | 0 |
| Lift | M | 420 | 420 | 0 | 0 | 0 |
| Lift | no_F3 | 420 | 420 | 0 | 0 | 420 |
| Lift | no_completion | 420 | 420 | 0 | 0 | 0 |
| PickCube-v1 | B1 | 840 | 0 | 840 | 0 | 0 |
| PickCube-v1 | B4 | 840 | 840 | 0 | 16 | 0 |
| PickCube-v1 | M | 840 | 840 | 0 | 0 | 630 |
| PickCube-v1 | no_F3 | 840 | 840 | 0 | 0 | 840 |
| PickCube-v1 | no_completion | 840 | 210 | 630 | 0 | 0 |
| PushCube-v1 | B1 | 840 | 0 | 840 | 0 | 0 |
| PushCube-v1 | B4 | 840 | 840 | 0 | 0 | 0 |
| PushCube-v1 | M | 840 | 840 | 0 | 0 | 0 |
| PushCube-v1 | no_F3 | 840 | 840 | 0 | 0 | 840 |
| PushCube-v1 | no_completion | 840 | 840 | 0 | 0 | 0 |

The 16 PickCube native endpoint disagreements are avoided by M's qualified-prefix replacement. The no_F3 strict-plus-prefix workflow achieves the same zero selected-endpoint disagreements and full admission. M selects 630 prefix replacements versus 2,100 for that workflow, conditional on the already-collected qualification cohort. These are **selection counts, not observed saved executions**: all reference/candidate/control continuations were eagerly executed for every method. No prospective net speedup or amortization benefit is established.

Actual route creation/restoration, prefix and continuation timing follows; reference acquisition and the remaining negative controls are additional campaign costs.

| Task | Route | Recorded continuations | Measured wall s | Median route s | Prefix controls |
| --- | --- | --- | --- | --- | --- |
| Lift | native_snapshot | 420 | 616.722 | 1.447 | 0 |
| Lift | fresh_prefix | 420 | 1202.584 | 2.824 | 27300 |
| PickCube-v1 | native_snapshot | 840 | 712.865 | 0.828 | 0 |
| PickCube-v1 | fresh_prefix | 840 | 1660.491 | 1.973 | 71084 |
| PushCube-v1 | native_snapshot | 840 | 539.017 | 0.629 | 0 |
| PushCube-v1 | fresh_prefix | 840 | 1124.076 | 1.314 | 44520 |

## Table E: matched physical effects

Differences and intervals are percentage points, recovery minus continue, on qualified fresh-prefix starts. Bootstrap is the registered 2,000 parent draws. The supplementary conservative paired-binary interval uses separate Bonferroni Clopper-Pearson gain/loss bounds and avoids treating degenerate bootstrap intervals as certainty. Zero-denominator contrasts are N/A.

| Task | Condition | Population | n | Continue Y | Recover Y | Difference pp | Bootstrap95% pp | Conservative95% pp |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Lift | nominal | all | 210 | 210 | 210 | 0.00 | [0.00, 0.00] | [-2.07, 2.07] |
| Lift | nominal | failed | 0 | 0 | 0 | N/A | N/A | N/A |
| Lift | nominal | clean_success | 210 | 210 | 210 | 0.00 | [0.00, 0.00] | [-2.07, 2.07] |
| PickCube-v1 | nominal | all | 210 | 210 | 155 | -26.19 | [-32.38, -20.48] | [-33.62, -17.57] |
| PickCube-v1 | nominal | failed | 0 | 0 | 0 | N/A | N/A | N/A |
| PickCube-v1 | nominal | clean_success | 209 | 209 | 155 | -25.84 | [-32.06, -20.10] | [-33.26, -17.22] |
| PickCube-v1 | offset002 | all | 210 | 67 | 169 | 48.57 | [40.00, 57.14] | [35.27, 60.07] |
| PickCube-v1 | offset002 | failed | 113 | 0 | 91 | 80.53 | [73.45, 87.61] | [66.98, 88.19] |
| PickCube-v1 | offset002 | clean_success | 66 | 65 | 49 | -24.24 | [-36.36, -13.64] | [-38.08, -7.01] |
| PushCube-v1 | misaligned | all | 210 | 0 | 207 | 98.57 | [96.67, 100.00] | [93.37, 99.77] |
| PushCube-v1 | misaligned | failed | 210 | 0 | 207 | 98.57 | [96.67, 100.00] | [93.37, 99.77] |
| PushCube-v1 | misaligned | clean_success | 0 | 0 | 0 | N/A | N/A | N/A |
| PushCube-v1 | nominal | all | 210 | 205 | 206 | 0.48 | [-1.43, 2.38] | [-3.59, 4.48] |
| PushCube-v1 | nominal | failed | 0 | 0 | 0 | N/A | N/A | N/A |
| PushCube-v1 | nominal | clean_success | 0 | 0 | 0 | N/A | N/A | N/A |

P3 genuine triggered-failure recovery is 91/113 versus 0/113 for PickCube. PushCube has 207/210 versus 0/210 in its fixed misalignment family. Clean already-successful PickCube states show harm (155/209 versus 209/209). Lift has no qualified failed starts and cannot support general C4 recovery-improvement claims. All actions execute 70 controls at 20 Hz, so elapsed simulation cost is 3.5 s/action and paired cost difference is 0 by design. This is not a time-to-completion or robot-efficiency result. No method ranking was selected using these outcomes.

## Table F: robustness and witnessed controls

Native is a candidate restoration, not automatically an invalid contract. Controller-memory replacement, physically read-back friction changes, reversed actual controls, midrollout injection, swapped actual parent records and removed claim provenance retain their original outcomes. Parent/provenance mutations are mechanical evidence controls, not additional simulator rollouts. N7 removes model identity from the claim while the original counterpart is retained for audit.

| Task | Route/control | M P/F/U |
| --- | --- | --- |
| Lift | action_order | 0/420/0 |
| Lift | controller_memory | 0/420/0 |
| Lift | fresh_prefix | 420/0/0 |
| Lift | midrollout_injection | 0/420/0 |
| Lift | missing_provenance | 0/0/210 |
| Lift | native_snapshot | 420/0/0 |
| Lift | parent_rng | 0/420/0 |
| Lift | physics | 0/420/0 |
| PickCube-v1 | action_order | 0/840/0 |
| PickCube-v1 | controller_memory | 0/840/0 |
| PickCube-v1 | fresh_prefix | 840/0/0 |
| PickCube-v1 | midrollout_injection | 0/840/0 |
| PickCube-v1 | missing_provenance | 0/0/420 |
| PickCube-v1 | native_snapshot | 840/0/0 |
| PickCube-v1 | parent_rng | 0/840/0 |
| PickCube-v1 | physics | 0/840/0 |
| PushCube-v1 | action_order | 0/840/0 |
| PushCube-v1 | controller_memory | 0/840/0 |
| PushCube-v1 | fresh_prefix | 840/0/0 |
| PushCube-v1 | midrollout_injection | 0/840/0 |
| PushCube-v1 | missing_provenance | 0/0/420 |
| PushCube-v1 | native_snapshot | 840/0/0 |
| PushCube-v1 | parent_rng | 0/840/0 |
| PushCube-v1 | physics | 0/840/0 |

Budget/timing declaration-corruption checks are in mechanical_control_checks.json: actual unchanged controls/outcomes are paired with corrupt declarations. They are software checks, not additional physical timing experiments. Actual midrollout injection also produces a recorded clock inconsistency. The emitted first-observed witnesses were independently recomputed; no minimum-unsatisfiable-core claim is made.

## Ablations and paired uncertainty

These reuse the registered Table D weighting/bootstrap. Invalid comparisons use fixed parent-pair clusters; other comparisons use parents. Nonzero entries below are M minus ablation admissions in percentage points. Zero/constant bootstrap intervals are descriptive for this fixed mixture of control types. All entries, including zero contrasts, remain in ablation_paired_comparisons.json.

| Task | Ablation | Population | Clusters | M minus ablation pp | Paired 95% pp |
| --- | --- | --- | --- | --- | --- |
| PickCube-v1 | no_memory | invalid | 105 | -20.00 | [-20.00, -20.00] |
| PickCube-v1 | no_unknown | incomplete | 210 | -100.00 | [-100.00, -100.00] |
| PickCube-v1 | no_completion | valid | 210 | 37.50 | [37.50, 37.50] |
| PushCube-v1 | no_memory | invalid | 105 | -20.00 | [-20.00, -20.00] |
| PushCube-v1 | no_unknown | incomplete | 210 | -100.00 | [-100.00, -100.00] |
| Lift | no_memory | invalid | 105 | -20.00 | [-20.00, -20.00] |
| Lift | no_unknown | incomplete | 210 | -100.00 | [-100.00, -100.00] |

Removing F3 leaves full admission but requires prefix replacement on every native branch. Removing memory obligations admits contradicted memory-reset controls; removing UNKNOWN handling admits incomplete model manifests. Removing completion withholds 630 PickCube native claims that M supports only after real prefix replacement. These are component diagnostics, not deployable variants.

## Secondary adapters, independent verification and tests

No models were retrained. The prior 100-record FailTime Long cross-fit retains 57 failures, 43 successes and the one censored onset; source/task separation and calibration/continuous alarms are checked. Its previously zero timely-alarm result is not promoted into an online detector success. REBOOT reuses 55 annotated recoveries and 62 expert-source references. All 55 reset witnesses are recomputed on unchanged scores; known aliases remain invalid unless explicitly collapsed, and missing cross-object temporal evidence remains UNKNOWN. An annotation convention is not a physically established onset. These previously-used records support adapter portability, not untouched confirmation or physical recovery effects.

The independent physical software audit passed 13,800 traces, 4,220 full prefix pairs, 16,100 primary continuations, 1,713,686 recorded control steps, 172,500 certificates, 1,150 matched input bundles and all 30 effect cells. The separate legacy/evaluator audit passed 100 + 117 score streams, 55 reset witnesses, 330 historical member hashes and 23 fresh-process mixed cases. There was no independent human study. The package answer key is separate. Selected endpoint fields are additionally checked in selected_outcome_audit.json.

Final maintained tests: 349 passed and 4 optional-stack skips (final-maintained-tests.log). All four optional old-stack physics tests passed separately in their unchanged Python3.10/MuJoCo2.3.2 environment; see final-pinned-physics-tests.log. Maintained Ruff scope is src/scripts/tests. Whole-tree findings in historical ad hoc scripts and bare-pytest vendored collection failures are preserved; they were not relabelled as passing tests. Engineering failures and same-parent retries are retained in resolved_worker_failures.json and parent_attempt_failure_resolutions.json. No confirmation attempt failed or seed was replaced.

## Provenance, resources and exact reproduction

Evidence root: `results/recovery-claims/20261112T152155Z`. Source/engine identities: confirmation_freeze.json, source_amendments.json, engine_fingerprints.json (1256 installed simulator files), worker_runtime_versions.json, secondary_source_hashes.json and the final completion_manifest.json. The current measured completed-job CPU total before report/packaging is 10.4858 core-hours; final authoritative usage, local branch/HEAD, archive hash and workers=0 are recorded by resources.json/completion_manifest.json after closing. They include the 600 CPU-second allowance for interactive work. GPU 0; new dataset/weight downloads 0; public primary-source tool traffic is not byte-metered and has a 20 MB conservative allowance. The original 12-hour/20CPUh/6GB limits remain in force.

```bash
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
