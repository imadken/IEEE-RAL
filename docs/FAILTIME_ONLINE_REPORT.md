# FailTime causal online-trigger study

2026-11-12. Exploratory internally held-out pilot on the fixed principal-researcher plan. This report records the completed scientific calculations and passing audits; final branch/commit, archive hash and closing resource accounting are bound by the completion manifest. It does not itself certify that finalization has finished.

## Result and scientific gates

```json
{
  "G0": "DATA_GO",
  "G1": "DEVELOPMENT_CONTRAST_RECORDED_CONTEXT_SPECIFICITY_INCONCLUSIVE",
  "G1_reason": "Development contrasts and early-prefix role controls are quantified; without independently time-matched counterfactual histories they do not establish event specificity beyond normal progress.",
  "G2": "METHOD_NO_GO",
  "G2_details": {
    "timely_route_point": false,
    "timely_ci_favorable": false,
    "burden_route_point": false,
    "burden_ci_favorable": false,
    "reference": "B2 global same-modality sequential baseline"
  },
  "G3": "NOT_ESTIMABLE_NO_HELDOUT_SO101",
  "G3_reason": "Fixed task hash yields2ALOHAevaluationtasks only; no cross-platform held-out result.",
  "disposition": "Exploratory screening only; no physical recovery or publication-readiness claim"
}
```

Gates are screening criteria, not acceptance or novelty decisions. The fixed comparisons, negative controls and perturbations were completed independently of gate direction. The principal researcher decides subsequent claims.

The evaluated causal scores yield zero timely detections in 405/405 fixed main comparison cells. These are repeated operating points on the same eight held-out recordings, not 405 independent studies. No cell is selected as a favorable result. The primary method disposition is `METHOD_NO_GO`; this is a result for these fixed scores, calibration and split, not an information-theoretic limit on proprioception.

## Qualified cohort, split and annotation boundary

Evidence root: `results/failtime-online/20261112T101800Z`. Source Git revision `63dafa9b703be0347d80f63d049304269f8d000f`; HF revision `07aea9142616cf1f8047512bd53a4d9fcd5e7cee`. All 100 declared Long signals are retained: 57 failures and 43 success references across 13 task groups. 56 failures have released onsets within observed history and support DATA_GO. Whole original HDF5 objects were hashed against pinned HF identities; only numerical signals/indexing and camera schemas were inspected, with no video decoding.

The unchanged `handover_episode_10` onset is 45.233333s while its last observed timestamp is 45.20000076293945s. Its history and denominator are retained, its target window is unobservable, and no label is repaired. This is an observability discrepancy, not physical adjudication.

FailTime-Long supplies only an official test annotation file. The internal SHA256(robot/task) modulo-five rule was frozen before model/performance comparisons; all episodes of a robot/task stay together. Qualification metadata and three fixed fixture signals had already been inspected. Consequently held-out fitting/calibration separation is meaningful, but these data are not untouched confirmation or an official Long leaderboard training split.

| Split | Robot | Task | Failures | Successes |
| --- | --- | --- | --- | --- |
| calibration | aloha | balls_to_egg_carton | 3 | 1 |
| calibration | so101 | handover | 8 | 6 |
| evaluation | aloha | pour_ball_transfer_cup | 3 | 1 |
| evaluation | aloha | stabilize_and_insert_block | 2 | 2 |
| train | aloha | bottle_to_bowl_and_cover | 2 | 1 |
| train | aloha | empty_bowl_insert_block | 3 | 1 |
| train | aloha | stack_cup_pyramid | 3 | 1 |
| train | aloha | uncap_marker_draw_recap | 3 | 1 |
| train | aloha | yellow_red_blocks_to_bowls | 2 | 1 |
| train | so101 | balls_to_rack | 12 | 7 |
| train | so101 | block_assembly | 6 | 7 |
| train | so101 | blocks_to_bowls | 2 | 3 |
| train | so101 | cube_stack | 8 | 11 |

The fixed split has 74 training, 18 calibration and eight evaluation recordings. Evaluation contains five failures and three successes from two ALOHA tasks; no SO-101 episode is held out for evaluation. Do not reroll the split or claim platform transfer. A one-record change can move timely sensitivity by 20 points or clean-alarm rate by 33.3 points.

Task/recording grouping and numerical signal deduplication were checked, but released task/episode identifiers do not certify independent collection sessions or operators. Session/operator identities and their dependence are not independently established. Task grouping is therefore not proof of collection-level independence.

Official Short annotations were preserved separately. Its calibration file has 50 episodes, all overlapping its 1,084-episode train file; future Short training would have to remove those IDs. The original raw source is public, rather than absent or globally DATA_BLOCKED. Three fixed annotation IDs were matched by metadata; no Short HDF5 was downloaded. Their complete task folders exceed this run's full transfer cap, so a complete official Short comparison was not qualified. No partial favorable comparison, alternative conversion, official Short confirmation or REBOOT-label transfer was performed.

Original Short raw repository `sii-rhos-ai/ViFailback-Dataset`, revision `21df46c2585c52e5a62df5f4b946bae6cbc6fed7`; bounded path/size evidence in short_access.json:

| Official split | Matched sample | Object bytes | Complete task bytes | Raw downloaded |
| --- | --- | --- | --- | --- |
| train | drag_basket_place_cube_ep1_episode_12 | 90915490 | 11153786360 | False |
| calibration | drag_basket_place_cube_ep1_episode_150 | 23986888 | 11153786360 | False |
| test | pick_object_place_left_box_ep1_episode_33 | 102954680 | 15602888330 | False |

## Runtime inputs, frozen methods and actual fits

All monitors receive the same 10Hz causal sample-and-hold EEF16 stream plus backward differences on the decision grid, and a robot stratum known before execution. These increments divided by .1s are not certified native physical velocities. No onset, verdict, reason, future command, task-completion result, episode identity or eventual duration enters the monitor. Static task XML does not supply time-aligned phase labels. Runtime state starts only at recording start and never resets at the released onset.

B0_time is elapsed time and B0_prior is training failure prevalence. B1 preserves pinned modal-Hamming Sign-CPD costs, penalty and pruning, using available-prefix processing, a training-success motion floor and arrival-time cut-count decisions. It is an explicit causal adaptation of a retrospective component. B2 is the global nominal CUSUM; B3 is the fixed one-second logistic comparator; B4 is the GRU32 probability ensemble. MCSFA uses the same derivative evidence/CUSUM with 36 mechanically defined gripper/motion modes. Insufficient mode support backs off to the robot-global nominal distribution; unknown robot coverage abstains. No-mode is exactly B2. No-accumulation uses the instantaneous evidence increment.

| Checkpoint | Kind | Training records | Seed | Epochs | Converged |
| --- | --- | --- | --- | --- | --- |
| nominal | nominal_velocity | 33 | None | None | None |
| B3 | logistic | 74 | None | None | True |
| B4_seed11 | gru32 | 74 | 11 | 30 | None |
| B4_seed23 | gru32 | 74 | 23 | 30 | None |
| B4_seed37 | gru32 | 74 | 37 | 30 | None |
| source_role | logistic | 73 | None | None | True |

Actual per-fit hashes and optimizer metadata are in report_fits.json and models_index.json. No architecture/hyperparameter search or favorable seed selection was performed. The GRU has one 32-unit causal recurrent layer; its three declared seeds train for 30 epochs each. The nominal fit and early-prefix classifier are separate lightweight fits, not additional neural architectures.

Nominal training coverage:

| Robot | Success recordings | Frames | Supported modes / 36 |
| --- | --- | --- | --- |
| aloha | 5 | 3605 | 14 |
| so101 | 28 | 14169 | 10 |

report_nominal_coverage.json retains per-evaluation recording fallback counts. Mode support requires 50 frames from two success recordings. Scaling, evidence drift and motion floors use development successes only. No released phase boundaries are invented.

## Matched calibration and primary first alarms

Each method receives one constant threshold: the maximum of separately fitted calibration-success and strictly pre-onset failure-prefix thresholds. The conservative order statistic permits floor(alpha*n_valid) empirical alarms and uses nextafter above tied scores. Invalid prefixes are explicit and excluded from that population's valid-capacity denominator, never fabricated. Alpha .10 and persistence .1s are primary. The seal binds input arrays, weights, score source, calibration streams and thresholds before evaluation performance scoring. No hindsight threshold is deployed.

| Method | Threshold | Success valid/invalid; allowed; realized | Prefix valid/invalid; allowed; realized |
| --- | --- | --- | --- |
| B0_time | 78.400000 | 7/0; 0; 0 | 11/0; 1; 0 |
| B0_prior | 0.554054 | 7/0; 0; 0 | 11/0; 1; 0 |
| B1 | 14.000000 | 7/0; 0; 0 | 11/0; 1; 0 |
| B2 | 133.860975 | 7/0; 0; 0 | 11/0; 1; 0 |
| B3 | 0.962977 | 7/0; 0; 0 | 11/0; 1; 1 |
| B4 | 0.827576 | 7/0; 0; 0 | 11/0; 1; 0 |
| MCSFA | 201.504167 | 7/0; 0; 0 | 11/0; 1; 1 |
| MCSFA_no_mode | 133.860975 | 7/0; 0; 0 | 11/0; 1; 0 |
| MCSFA_no_accum | 27.818658 | 7/0; 0; 0 | 11/0; 1; 1 |

Calibration is empirical with small task-dependent populations; it is not a conformal or physical-safety guarantee. Success episodes are reference recordings, not certified physically fault-free executions. Pre-annotation periods are permitted background labels, not proof of physical normality.

At the primary operating point, the seven calibration successes permit zero empirical alarms, and the eleven failure prefixes permit one. These coarse integer constraints and cross-task distribution shifts do not guarantee a 10% held-out alarm rate. Realized calibration counts and all invalid-prefix counts are shown above rather than replacing uncertainty with a safety claim.

Timely means onset ≤ first persistent alarm ≤ onset+1s; premature alarms remain false stops and cannot later become timely detections. Late and no-alarm failures remain in denominators. Clean alarms are any first alarm on a success reference. All methods use the same last 10Hz decision time as exposure.

| Method | Timely / fail | Premature / fail | Late | Missed | Clean / success | Clean alarms/hour | Median timely delay s | Abstentions |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B0_time | 0/5 | 0/5 | 0 | 5 | 0/3 | 0.000 | not estimable | 0 |
| B0_prior | 0/5 | 0/5 | 0 | 5 | 0/3 | 0.000 | not estimable | 0 |
| B1 | 0/5 | 0/5 | 0 | 5 | 0/3 | 0.000 | not estimable | 0 |
| B2 | 0/5 | 0/5 | 2 | 3 | 1/3 | 25.770 | not estimable | 0 |
| B3 | 0/5 | 0/5 | 4 | 1 | 0/3 | 0.000 | not estimable | 0 |
| B4 | 0/5 | 0/5 | 1 | 4 | 0/3 | 0.000 | not estimable | 0 |
| MCSFA | 0/5 | 0/5 | 2 | 3 | 1/3 | 25.770 | not estimable | 0 |
| MCSFA_no_mode | 0/5 | 0/5 | 2 | 3 | 1/3 | 25.770 | not estimable | 0 |
| MCSFA_no_accum | 0/5 | 0/5 | 0 | 5 | 0/3 | 0.000 | not estimable | 0 |

Primary clean exposure is 139.700000s per method, with 5 fully observable failure target windows. Conditional delays are shown alongside all misses. A no-alarm policy cannot establish useful recognition merely by eliminating both alarm populations.

## Paired comparison and method disposition

MCSFA minus each fixed alternative; differences are percentage points with 2,000 task-cluster bootstrap intervals:

| Baseline | Timely pp [95%] | Premature pp [95%] | Clean pp [95%] | Burden pp [95%] |
| --- | --- | --- | --- | --- |
| B2 | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] |
| B3 | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | 33.3 [0.0, 50.0] | 12.5 [0.0, 25.0] |
| B4 | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | 33.3 [0.0, 50.0] | 12.5 [0.0, 25.0] |
| MCSFA_no_accum | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | 33.3 [0.0, 50.0] | 12.5 [0.0, 25.0] |

paired_effects.json includes valid resample counts and the exact seed/unit. With only two evaluation tasks, uncertainty is coarse and role-absent draws are invalid rather than silently imputed. Identical indicators yielding [0,0] do not imply population equivalence. Descriptive task-cluster intervals do not remove shared source, annotation, operator or embodiment limitations. G2 uses actual alarm rates and directional intervals; no score or task condition was changed after seeing outcomes.

All three GRU seeds are reported descriptively without selection. Each seed has its own matched threshold fitted from the same two calibration populations. seed_sensitivity.json retains 135 fixed seed/alpha/persistence/stress cells; the primary seed counts are:

| Seed comparator | Timely/fail | Premature/fail | Late | Missed | Clean/success |
| --- | --- | --- | --- | --- | --- |
| B4_seed11 | 0/5 | 0/5 | 2 | 3 | 0/3 |
| B4_seed23 | 0/5 | 0/5 | 0 | 5 | 0/3 |
| B4_seed37 | 0/5 | 0/5 | 2 | 3 | 0/3 |

Primary held-out task/platform cells:

| Stratum type | Stratum | Method | Timely/fail | Premature/fail | Clean/success |
| --- | --- | --- | --- | --- | --- |
| task_id | pour_ball_transfer_cup | B0_time | 0/3 | 0/3 | 0/1 |
| task_id | stabilize_and_insert_block | B0_time | 0/2 | 0/2 | 0/2 |
| robot | aloha | B0_time | 0/5 | 0/5 | 0/3 |
| task_id | pour_ball_transfer_cup | B0_prior | 0/3 | 0/3 | 0/1 |
| task_id | stabilize_and_insert_block | B0_prior | 0/2 | 0/2 | 0/2 |
| robot | aloha | B0_prior | 0/5 | 0/5 | 0/3 |
| task_id | pour_ball_transfer_cup | B1 | 0/3 | 0/3 | 0/1 |
| task_id | stabilize_and_insert_block | B1 | 0/2 | 0/2 | 0/2 |
| robot | aloha | B1 | 0/5 | 0/5 | 0/3 |
| task_id | pour_ball_transfer_cup | B2 | 0/3 | 0/3 | 0/1 |
| task_id | stabilize_and_insert_block | B2 | 0/2 | 0/2 | 1/2 |
| robot | aloha | B2 | 0/5 | 0/5 | 1/3 |
| task_id | pour_ball_transfer_cup | B3 | 0/3 | 0/3 | 0/1 |
| task_id | stabilize_and_insert_block | B3 | 0/2 | 0/2 | 0/2 |
| robot | aloha | B3 | 0/5 | 0/5 | 0/3 |
| task_id | pour_ball_transfer_cup | B4 | 0/3 | 0/3 | 0/1 |
| task_id | stabilize_and_insert_block | B4 | 0/2 | 0/2 | 0/2 |
| robot | aloha | B4 | 0/5 | 0/5 | 0/3 |
| task_id | pour_ball_transfer_cup | MCSFA | 0/3 | 0/3 | 0/1 |
| task_id | stabilize_and_insert_block | MCSFA | 0/2 | 0/2 | 1/2 |
| robot | aloha | MCSFA | 0/5 | 0/5 | 1/3 |
| task_id | pour_ball_transfer_cup | MCSFA_no_mode | 0/3 | 0/3 | 0/1 |
| task_id | stabilize_and_insert_block | MCSFA_no_mode | 0/2 | 0/2 | 1/2 |
| robot | aloha | MCSFA_no_mode | 0/5 | 0/5 | 1/3 |
| task_id | pour_ball_transfer_cup | MCSFA_no_accum | 0/3 | 0/3 | 0/1 |
| task_id | stabilize_and_insert_block | MCSFA_no_accum | 0/2 | 0/2 | 0/2 |
| robot | aloha | MCSFA_no_accum | 0/5 | 0/5 | 0/3 |

## Development controls and robustness

Development-only equal-length pre/early-target contrasts, including the clock, are retained in development_contrasts.json and the G1 assessment. These annotation-delimited windows are diagnostics, not online success rates. A rising clock or eventual-verdict classifier can explain context/progress trends without identifying an event-specific alarm.

| Method | Included development failures | Positive mean changes | Median mean change |
| --- | --- | --- | --- |
| B0_time | 40 | 40 | 1.000000 |
| B0_prior | 40 | 0 | 0.000000 |
| B1 | 40 | 25 | 0.300000 |
| B2 | 40 | 16 | 0.000000 |
| B3 | 40 | 31 | 0.046839 |
| B4 | 40 | 15 | -0.006831 |
| MCSFA | 40 | 8 | -0.004057 |
| MCSFA_no_mode | 40 | 16 | 0.000000 |
| MCSFA_no_accum | 40 | 29 | 0.075853 |

The early-prefix source-role control actually targets the eventual failure/success verdict, not an independently annotated collection source. It uses only the first complete second and excludes failures with onset≤1s from this diagnostic only. Fixed .5 decisions and train-only scaling are used; no failure denominator is removed. Results:

The training row is resubstitution on the fitted recordings, not an out-of-fold or held-out score. Its high AUROC cannot establish generalization; calibration and eight-record evaluation rows are the separate held-out diagnostics. Neither the near-chance held-out scores nor their small sample sizes establish absence of a context shortcut.

| Split | Records | Failures | Successes | Excluded | AUROC | Balanced accuracy |
| --- | --- | --- | --- | --- | --- | --- |
| train | 73 | 40 | 33 | 1 | 0.955 | 0.882 |
| calibration | 18 | 11 | 7 | 0 | 0.545 | 0.487 |
| evaluation | 8 | 5 | 3 | 0 | 0.467 | 0.500 |

Strong early-prefix classification does not establish fraud, annotation error, causal confounding, or absence of later event signal. Small or one-class subsets cannot support an AUROC, which remains not estimable rather than fabricated.

Fixed alpha sensitivities .05/.20 and persistence 0/.2s are fully tabulated in tables/all_comparisons.csv and summary.json. Primary-persistence clean alpha sensitivity counts (timely/premature/clean):

| Method | alpha .05 | alpha .10 | alpha .20 | persistence 0s | persistence .2s |
| --- | --- | --- | --- | --- | --- |
| B0_time | 0/0/0 | 0/0/0 | 0/0/1 | 0/0/0 | 0/0/0 |
| B0_prior | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| B1 | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| B2 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 |
| B3 | 0/0/0 | 0/0/0 | 0/0/1 | 0/0/1 | 0/0/0 |
| B4 | 0/0/0 | 0/0/0 | 0/4/3 | 0/0/0 | 0/0/0 |
| MCSFA | 0/0/1 | 0/0/1 | 0/2/3 | 0/0/1 | 0/0/1 |
| MCSFA_no_mode | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 |
| MCSFA_no_accum | 0/0/0 | 0/0/0 | 0/4/2 | 0/2/3 | 0/0/0 |

Frozen primary operating points under sensor stress, timely/premature/clean counts:

| Method | clean | drop0.1 | drop0.3 | delay0.2 | delay0.5 |
| --- | --- | --- | --- | --- | --- |
| B0_time | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| B0_prior | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| B1 | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| B2 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 |
| B3 | 0/0/0 | 0/0/0 | 0/0/1 | 0/0/0 | 0/0/0 |
| B4 | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| MCSFA | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 |
| MCSFA_no_mode | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 |
| MCSFA_no_accum | 0/0/0 | 0/0/0 | 0/0/1 | 0/0/0 | 0/0/0 |

Native-packet dropout uses deterministic sample-derived draws; delayed streams expose only observations already available. Holding and missing initial packets are causal. Thresholds are unchanged across perturbations and persistence sensitivities. A delay that moves a premature alarm into the label window is not improved sensing. Multiple perturbations are repeated analyses of the same recordings, not new independent samples.

## Streaming, examples and independent audit

streaming_parity.json records the actual deterministic replay checks. Runtime sees only current/past packets, learned weights and static robot context; annotation overlays in figures/examples are offline review aids. Model-level mode, fallback, risk, source time and threshold traces explain computation, not physical root causes.

All 7 streaming comparisons passed with exact first-alarm agreement and maximum batch/stream risk discrepancy 5.96e-08. The replay evidence additionally retains 1 unchanged uncertain-annotation example(s).

| Category | Available | Method | Recording | Split |
| --- | --- | --- | --- | --- |
| timely | False | — | — | — |
| premature | False | — | — | — |
| late | True | MCSFA | stabilize_and_insert_block_episode_9 | evaluation |
| missed | True | MCSFA | pour_ball_transfer_cup_episode_19 | evaluation |
| clean_alarm | True | MCSFA | stabilize_and_insert_block_episode_7 | evaluation |
| annotation_observability_uncertain | True | MCSFA | handover_episode_10 | calibration |

Unavailable categories remain explicit. The uncertain example retains its raw released bounds/provenance and is not relabeled. report_examples.json and local risk streams reproduce the figure selection. A successful offline alarm is not evidence a recovery action would have succeeded.

Independent audit status:

| Artifact | Status | SHA-256 |
| --- | --- | --- |
| independent_data_audit.json | PASS | ab41f0d10106b0621ff4087f03ebe53243a90309c147d55b4bc6f6f2bdae3284 |
| independent_numerical_audit.json | PASS | b8cc193d3ae572691817a3e801f3665e2f7a76aa356c141256bad3725da91333 |
| streaming_parity.json | PASS | 70498b2231b530836815c1c5adbcc8c79230f30e8acfd00ce2b43b855bdc2201 |

The data auditor independently checks pinned raw hashes, aliases, schemas, timestamps, onset observability and split identities. The numerical auditor imports neither model nor primary scorer and reconstructs first alarms, calibration masks/IDs, both alarm populations, outcomes, source-role predictions and paired inference from saved values. Exact counts, tolerances and hashes remain in those audit JSON files.

The numerical audit records 100 native-array hashes, 27 main calibration cells and 3240 main outcome rows. Separate packet and fixed-seed audit details, including all checked risk histories and seed operating points, remain in the same audit artifact rather than being inferred from test counts.

Completed verification commands (failed earlier attempts remain visible rather than being erased):

| Command record | Exit | Result |
| --- | --- | --- |
| causal-and-data-contract-tests | 0 | 29 passed in 3.26s |
| complete-causal-contract-tests | 0 | 38 passed in 3.00s |
| independent-complete-data-audit | 0 | {"status": "PASS", "G0": "DATA_GO", "verified_independent_raw_failures": 56, "verified_independent_raw_successes": 43, "verified_raw_task_groups": 13} |
| independent-risk-calibration-and-outcome-audit | 0 | {"status": "PASS", "risk_files_checked": 58, "threshold_cells": 27, "outcome_rows": 3240} |
| environment-reproduction-snapshot | 0 | hon3", "packages": {"torch": "2.5.1+cpu", "numpy": "1.26.4", "scipy": "1.17.1", "h5py": "3.16.0", "pydantic": "2.12.3", "matplotlib": "3.11.2", "psutil": "7.2.2", "pytest": "8.3.5", "ruff": "0.17.4"}, "workflow": "uv run --no-sync; reused existing CPU environment, no package installation or lockfile change", "borrowed_path": "results/reboot-phase/20261111T204459Z/env/lib/python3.12/site-packages"} |
| maintained-failtime-and-reboot-regressions | 0 | 100 passed in 3.75s |
| independent-complete-numerical-and-seed-audit | 0 | {"status": "PASS", "risk_files_checked": 99, "threshold_cells": 27, "outcome_rows": 3240} |
| maintained-ruff-final | 0 | All checks passed! |
| maintained-format-final | 0 | 149 files already formatted |

## Positioning and limits

[ProTracer v2](https://arxiv.org/html/2609.21369v2) is a retrospective full-rollout diagnosis framework. Its runtime comparison already includes an onset-supervised GRU on visual features; our proprioception-only GRU is a separate baseline. First-alarm deployment agreement cannot be ranked directly against its retrospective MAE. [FAIL-Detect](https://www.roboticsproceedings.org/rss21/p073.html) already establishes nominal sequential failure monitoring/calibration, and [ProTAS](https://openaccess.thecvf.com/content/CVPR2024/html/Shen_Progress-Aware_Online_Action_Segmentation_for_Egocentric_Procedural_Task_Videos_CVPR_2024_paper.html) already combines causal segmentation, progress and task graphs. Generic mode conditioning, CUSUM and threshold calibration are not new formal guarantees.

The historical [REBOOT report](docs/REBOOT_PHASE_REPORT.md) remains unchanged: primary Q-only phase-filter benefit failed; matched calibration improved Q/B2 to 14/55 while leaving 41 misses; early source-role AUROC was .982. Those exposed records are development history, not fresh confirmation. The bounded upstream source review and exact source hazards are retained at provenance/upstream_review.md.

This pilot cannot establish cross-platform generality, independent physical onset precision, causal attribution, actual recovery improvement or IROS/RA-L readiness. Neither a negative MCSFA comparison nor a small positive cell authorizes another architecture, grammar, dataset or threshold search. All scientific conclusions remain limited to the fixed internal split, released annotation agreement and measured operating points.

## Resource and local review handoff

Before report/archive/seal: conservative wall 2449.482s; completed bounded-worker CPU 894.476s. The final resources.json adds closing costs, actual GPU, downloads and artifact bytes, with accounting scope. No GPU or paid inference was needed for the fixed CPU pipeline. Upper limits are eight wall hours, ten measured CPU core-hours, 8GB downloads and 10GB new artifacts; no hours are consumed artificially.

Compact review archive: `results/failtime-online/20261112T101800Z/supervisor_review.tar.gz`; archive.json stores its exact size and SHA-256. completion_manifest.json binds the final local branch/commit, resource accounting, preservation check and every artifact. Detailed logs, original HDF5, extracted arrays, environments and detector checkpoints stay local/untracked. The archive contains compact risk predictions and decisive examples, not the 6.1GB raw cohort. Local publication remains manual.

`.gitignore`, uv.lock and sealed historical scientific evidence are preserved. One initial untracked duplicate, root `supervisor_review.tar.gz`, disappeared during this session without a campaign write to that path. Its recorded initial SHA-256 matches the intact authoritative onset archive under `results/reboot-onset-specificity/20261112T090003Z/supervisor_review.tar.gz`. The root duplicate is not recreated because that would reverse concurrent user/external state. The exact exception is recorded in concurrent_worktree_observation.json and the final preservation manifest; a blanket unchanged-user-state claim is not made.

This report does not certify that finalization workers have already stopped. The final completion seal is written only after all foreground workers have returned and the worker lock is free. No push, credentials, author contact, paid inference or physical robot intervention is authorized.

![first_alarm_tradeoffs](results/failtime-online/20261112T101800Z/figures/first_alarm_tradeoffs.png)

![task_strata](results/failtime-online/20261112T101800Z/figures/task_strata.png)

![example_timelines](results/failtime-online/20261112T101800Z/figures/example_timelines.png)
