# DSRE evidence-aware implementation and experiment contract

Date: 17 November 2026. Authoritative implementation target: `DSRE_EVIDENCE_SPEC_V2.md`. Codex implements the supervisor's definitions; it does not choose another contribution, tune to confirmation outcomes, or change the statistical target.

## 1. Repository and local history

Repository `/home/imad/Desktop/IEEE-RAL`. Saved design branch `research/dsre-evidence-aware-design-20261117` is based on the last remotely available scientific history. It DOES NOT contain the user's newer unpublished local synthesis commit `5547450d66e7561d701afcddd29f0e29156fc55c` or necessarily all dual-obligation work. Start from the verified latest LOCAL history in a new branch `research/dsre-evidence-aware-implementation`; import the design documents as ordinary files. Do not reset/cherry-pick a large old branch over newer code. Preserve both manuscripts, every old seal, `.gitignore`, `uv.lock`, and unrelated user modifications. Git authentication must never halt scientific work.

Read the design specification, retained approved plan, and `supervisor_reference.py`. Run its audit as a fixed expected-result check, then implement production code independently. Never claim that importing the same solver twice constitutes an independent audit.

No manuscript writing, Stage 2 draft, large language model, learned controller or new theory chosen by Codex is authorized. No real robot is required. No promised favorable result is a completion criterion.

## 2. Implementation order and API

Implement `src/dual_rec/evidence_aware/` or an equivalently narrow package:

- `schema.py`: immutable action/observation scope, evidence type, one-action record, paired record, frozen leaf partition, certificate and witness. Store propensities and whether any counterpart was exposed.
- `bounds.py`: four-probability LP, analytic logged-data checks, CP intervals, simultaneous confidence ledger. Fail closed for empty/inconsistent Q, absent overlap or unsupported causal assumptions.
- `partition.py`: exact depth-two Boolean partition fitting from observed-arm labels only, up to four leaves, min eight discovered examples per arm/leaf. Enumerate all six-predicate binary assignments to verify candidate certificates select entire leaves.
- `certificate.py`: minimum conjunction over whole qualified leaves, deterministic tie-breaking, exact bound/witness references; no hidden exclusions.
- `diagnosis.py`: the distinction between marginal identification barrier, current two-world ambiguity, sample-limited-at-plugin, benefit unsupported, no overlap and scope mismatch.
- `views.py`: separate learner and evaluator files/processes. One random arm per parent for L. Never send hidden counterfactuals to partition fitting, threshold selection, calibration or acquisition policy.
- `baselines.py`: same-region bound solver with no compression, ordinary rules, CART with matched evidence gate, empirical utility policy, naive independence negative control, fixed continue/recover, no-harm constrained finite-cell policy adaptation. Document which named literature methods are actual reproductions versus scoped adaptations.
- `acquisition.py`: frozen diagnostic-guided allocation, all-logs, all-pairs, uniform mix and decision-aware uncertainty, with execution-cost ledger and final independent calibration.
- `cli.py`: deterministic run commands and resumable experiments from immutable manifests.

Primary obligation: harm <=.10 and mean gain >=.05. Secondary absolute completion, harm-only, and fixed tolls are not replacements when the primary fails. Primary deployed fallback is continue; STOP is a separately reported composition. The same regions and confidence constraints can feed multiple policies, but no policy may split a calibrated region using finer hidden information. Missingness-dependent routing requires its own predeclared observation partition; otherwise it is an unqualified robustness diagnostic.

## 3. Data program, executed in a bounded first session

A. Deduplicate previous PickCube paired data across archives using full physical/checkpoint identity. Keep all old results unchanged. Select one condition per parent by the SHA-256 namespace `dsre-evidence-v2:condition:<task>:<parent>` before reading outcomes. Use deterministic discovery/calibration/evaluation *development* partitions 40/30/30 by parent hash. Every historic dataset was previously inspected, so these are exploratory results only.

B. Create paired and randomized-arm views from the exact same parents. Arm assignment derives from a separate SHA-256 namespace. In L files serialize only assigned outcome; hide names implying the true fault/outcome. Require a leak audit that fails if any unassigned outcome is accessed. Compare equal-parent and equal-executed-action budgets. Report the implied independence/overlap assumptions.

C. Run small exact finite controls: same marginals but harm 0 versus .4, naive-independent false qualification, routed-subregion failure, missing overlap, both-actions-fail, all-regions-certified empty explanation, unknown query, and inconsistent evidence.

D. Run the two new task pilots exactly below. Qualified physics must precede any learning comparison. No failure may be deleted to make qualification, heterogeneity or performance appear better. Initial task readiness, low-level planner errors and replay failures are separate statuses.

E. If a task passes technical qualification, immediately implement its genuinely single-action log collector and execute up to 64 development parents for an end-to-end demonstration. Also run a separate evaluator counterpart for paired assessment, with isolated files and no learner access. These are development demonstrations, not final qualification.

F. Produce the research results and ready-to-execute full prospective manifest. The full plan is fixed at 128 discovery / 1024 calibration / 256 test new parents per qualified domain. Do not launch that large cohort in the first session. Provide a measured runtime and per-leaf-assignment forecast. This is an engineering feasibility check, not an opportunity to change the question or to promise statistically significant gains.

## 4. Task A: existing grasping

Use the already qualified PickCube macros, terminal horizon and renderer-free CPU path, including worker-local Lavapipe selection when needed. No dependency upgrade in this environment. Retain the original observation dictionary, with at most six selected semantic predicates for the primary partition; selection is documented on discovery only and shared by all comparators. Future success, injected offset ID and seed cannot be features.

Old simulation labels support exploratory masked-log experiments. True prospective one-arm collection uses new parents with one condition assigned independently from the existing five-condition mixture. Its statistical unit is one parent checkpoint, not all five siblings treated as independent. Report this new estimand explicitly; do not borrow parent-any-condition calibration from earlier experiments.

## 5. Task B: PegInsertionSide-v1 assembly

Canonical source: `mani-skill/ManiSkill`, `mani_skill/examples/motionplanning/panda/solutions/peg_insertion_side.py`, last source-file commit checked `e1996f2234965dc75e6a6234509837ad9a76da95`, blob `d92eaa1fec9641e4f79b950ec4200527d39f5ac1`. Prefer the installed compatible source; record its exact diff against this pin. Do not upgrade frozen PickCube dependencies or pretend different source versions are identical.

The published solution grasps, moves to pre-insertion, performs three alignment-refinement iterations, then inserts. Define the checkpoint after pre-insertion and before refinement. The two fixed macros are:

- Continue: execute the cached insertion pose using the released motion-planning primitive, then hold.
- Recover: run the released three-step pose refinement and insert using a target recomputed from current peg/hole geometry, then hold. Record this task-adapter change explicitly; it is not an unmodified upstream policy or the research algorithm.

Both use the same robot state, motion-planning parameters, gripper state, horizon and available pose-estimate interface. These are scripted action alternatives, not trained policies. Goal/peg poses supplied by the simulator are idealized estimates; neither high-level method gets hidden fault labels. Low-level controller information is declared separately from the evidence selected for explanations.

A fixed plan-offset family provides context without outcome search: target transverse offsets `{0,+0.003,-0.003,+0.006,-0.006}` metres in the hole's local y direction, assigned before source prefix generation. Apply the stale offset to the cached target and its pre-insertion approach; recovery uses the existing current-pose correction. No mid-rollout teleport, object edits, force changes or success-threshold changes. The standard task card specifies 3-mm clearance; these values are a controlled sensitivity family, not real sensor-noise statistics.

For the ten-parent pilot, use two fixed parents per offset. Source reset failures, planning errors or inability to reach a well-defined checkpoint remain recorded. Freeze a 400-control postcheckpoint horizon and the task's existing terminal-success predicate. If the source's standard TimeLimit prevents completing the recorded prefix, create an explicitly labeled wrapper before collecting outcomes, preserving task dynamics and horizon semantics. No reactive horizon enlargement after observing failures.

Predecision predicates, measured in hole coordinates with existing pose estimates: transverse error <=3 mm; angular peg/hole-axis error <=5 degrees; insertion-depth progress >=1 mm over last five recorded controls; tip within 2 cm of the hole entrance; finger aperture <= declared gripper threshold copied from the installed source; TCP tracking error <=5 mm. Missing fields are unknown, not invented. Record exact frame conventions and units. Condition IDs are evaluator-only.

Pilot passes technical qualification only with reproducible complete prefix/state/controller/action parity on the cases that reach a checkpoint, and at least eight of ten usable decision checkpoints. Nontrivial outcome variation is reported separately, not a criterion to secretly change offsets. If outcomes are homogeneous, keep the domain as a boundary and do not claim a difficult recovery benchmark. A severe prerequisite/physics failure blocks this task arm, not the whole research.

## 6. Task C: PointMaze navigation

Use the official Gymnasium-Robotics `PointMaze_UMaze-v3` goal-reaching environment in an isolated pinned environment. It is a force-controlled 2-DoF point agent, not a realistic mobile robot. The official observations include position/velocity and goal. Keep the official fixed U-maze layout. No invented dynamic walls or task replacement.

Implement a fixed grid A* route planner and a deterministic waypoint tracker. Both action macros use the same force controller `clip(2*(waypoint-position)-0.8*velocity,-1,1)` with 0.20-map-unit waypoint advancement threshold. Lock map-coordinate conversions against the environment source. This is a basic evaluation-harness controller, not a method contribution.

At reset, compute an initial route from an estimated localization offset `{(0,0),(+0.35,0),(-0.35,0),(0,+0.35),(0,-0.35)}` in map coordinates, independently assigned before outcomes. Snap the estimated start to the nearest free cell by fixed lexical tie-breaking if needed. Run the first 20 tracker controls with the actual declared current localization feedback, keeping the cached route/index. The checkpoint occurs after that prefix, unless the episode already terminated, which is a logged already-solved or failed-prefix case, not a new recovery.

- Continue: follow the remaining cached route.
- Recover: replace it with an A* route from current observed position to the same goal.

Use 200 postcheckpoint controls and the environment's declared episodic goal-success semantics; termination is an absorbing outcome for evaluation. Do not add a fictional replan delay to make recovery harmful. Record actual planning latency and action effort. This task may exhibit only helpful or redundant replanning; that is an informative domain property, not grounds to alter the environment.

Pilot: ten fixed parents, two per initial offset. Predicate vocabulary: goal distance <=1; speed <=.2; next-waypoint straight segment traversable in known static map; path-progress over last five controls >=.1; current distance to remaining route <=.35; route-current-goal consistency. These predicates are task-level abstractions, not proof of physical sensing. No future success or branch outcomes.

Same qualification thresholds as insertion: at least eight usable predecision states; exact reset/prefix/control state replay within source-justified numerical tolerances; all attempts preserved. If the environment API differs, fix an interface mapping without changing problem semantics, otherwise block this arm with a precise reason. No more than 90 minutes of dependency/debug setup per new task before completing independent remaining work.

## 7. Pilot seed and provenance policy

Use namespace-based SHA-256 seeds (`dsre-evidence-v2:<task>:<phase>:<index>`, first 31 bits), check collisions against every historic seed/parent identity, and freeze manifests before outcomes. A deterministic collision resolution is allowed for genuinely duplicate IDs before running; outcome failure never triggers replacement.

Each branch reconstructs the exact physical prefix in a fresh process. Capture source/runtime fingerprints, relevant controller and planner memory, full controls, state/contact checks, endpoint success and costs. The history includes plan offsets, but offsets remain out of the high-level observation vector unless physically inferred from legitimate measurements. Use no native snapshot shortcut known to fail parity.

## 8. Required first-session outputs and resources

End-to-end deliverables:

1. Production bound solver and certificate implementation; independent supervisor-oracle agreement and leakage tests.
2. Exploratory paired/logged evidence comparison with counts, support, raw outcomes, four-class composition, risk/gain intervals and witness examples.
3. Fixed-baseline equivalence matrix and closest-work table distinguishing genuine implementation from adaptation.
4. Source-qualified insertion and navigation pilot outcomes or exact blockers, with all ten attempts and source hashes.
5. At least one complete development-only one-action ingestion -> certificate -> one-action execution trace where prerequisites permit; never present an abstaining or failing run as a successful recovery.
6. A frozen prospective manifest and actual throughput/assignment feasibility for the already specified full study.
7. Code, tests, research-only results, compact archive, source seals, exact commands, resource ledger and scoped local commit.

Maximum first session: 12 hours total wall, 6 hours new physics wall, 12 CPU core-hours, 2 GB artifacts and 1 GB new dependencies/downloads. No paid APIs, foundation-model training, whole-environment upgrades or detached workers. GPU use is unnecessary for the inference; do not change the qualified CPU physics merely to use it. Existing episodes are read-only.

If a task blocks, finish the other independent components. Do not return only a preflight document. Do not switch topics or announce publication readiness. Do not edit manuscripts. Commit locally; user publication policy remains in force. No force push, manuscript upload or submission.

Final response: what executed, actual source types seen by each learner, mathematical tests, qualified parents per domain, single-action data counts, certificates versus abstentions, harm/gain/coverage and baseline equality, unresolved identification, pilot failures, remaining fixed work, audit, resources, branch, SHA and zero remaining workers. The supervisor decides the next scientific gate.
