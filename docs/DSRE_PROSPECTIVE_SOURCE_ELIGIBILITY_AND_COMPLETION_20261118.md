# DSRE: Source eligibility ruling and frozen prospective-study completion

Scientific-supervisor decision: 2026-11-18.
Status: CONDITIONAL_SOURCE_AMENDMENT, NOT NEW SCIENTIFIC RESULT.
Approved research question and method remain those in DSRE_EVIDENCE_SPEC_V2.md. This document is an amendment to execution and source eligibility only; not permission to optimize the method, change its risk targets, alter tasks, or tune on results.

Current latest local implementation HEAD according to Codex: 6525dc6bf79a96e798d2d94c6778eae81d7b8304, with substantial UNCOMMITTED continuation changes on research/dsre-evidence-aware-prospective.
GitHub scientific design remains research/dsre-evidence-aware-design-20261117. Do NOT reset local history to this remote design branch. Import this file without overwriting local changes.
Submission is not yet scientifically endorsed.

## A. Required initial action: save current work with no new physics

Before investigating or restarting the experiment:
1. Inspect current Git status, source SHA, previous 1,075 tracked-file preservation checks, exact frozen manifests and seal roots. Preserve all user modifications, previous experiments, raw traces, manuscripts and archives.
2. Reproduce the existing outcome counts, source/evaluator separation and the 628-pass test run. Complete the compact archive and extract/verify it in a clean temporary directory. Check immutable manifest/source hashes, report any preexisting incomplete seal honestly, and preserve failed development attempts.
3. Commit the current continuation code/reports/seals in a scoped LOCAL commit on the existing work branch. Do not push. Provide the new commit SHA, archive hash and a 100%-restorable reproduction recipe. Never stage unrelated changes.
4. Only after a durable commit is verified should source diagnosis and additional physics begin.

## B. Source-eligibility rule: exact authorized interpretation

Source failure: insertion parent seed 180937078, calibration prefix-screen index 259. The existing source screw planner returned -1 BEFORE any prefix control was executed. There was no recovery decision checkpoint and no observed intervention outcome. All previously screened 259 seeds had usable prefixes; no calibration action outcomes have yet been collected.

The correct experimental target is the distribution of checkpoints that the UNMODIFIED SOURCE PLANNER reaches, conditioned on the predecision checkpoint eligibility event. Because a recovery decision does not exist if that checkpoint is never reached, an ex-ante, outcome-blind source failure is not an action failure. This is a narrower conditional population than all raw seeds.

Conditionally authorize a deterministic source status:
  NO_DECISION_CHECKPOINT_SOURCE_PLANNER_FAILURE

Use it ONLY if each of the following pass:
1. Independently replay that same frozen seed in two fresh isolated processes, without changing source, environment, controller, simulator build, observed inputs, fault setting, physics, horizon or RNG. The planner must produce the same -1 before ANY prefix controls in each repetition. Preserve full commands, fingerprints, logs and last attempted planning stage.
2. Confirm the action-assignment randomizer and prospective selector have NOT seen the eventual intervention outcome, nor affected whether the predecision checkpoint exists. Check the exact stage of source planner failure from the raw trace, not by name alone.
3. Independently verify there is no model/source mismatch, memory corruption, parity failure, misapplied fault, nonfinite physics, controller exception, or missing environment import. Any such occurrence is a HARD QUALIFICATION FAILURE and must halt that arm.
4. The same predefined eligibility logic must be applied uniformly to every remaining frozen seed, without seeing future outcomes. A source checkpoint that reaches terminal success before the registered decision (e.g., navigation) is classified NO_DECISION_CHECKPOINT_PREFIX_COMPLETED, with the observed prefix success stored separately, not as a DSRE intervention result. A normal upstream planning failure after controls or a failed state reconstruction requires independent review; do not automatically skip it.
5. Freeze and hash an eligibility-amendment document BEFORE collecting any new action outcome, clearly stating that the amendment followed one inspected source failure at index 259. Its justification is the absence of an action-decision state, not a desired numerical result.

If ANY condition fails, DO NOT bypass the source guard, do not replace the seed or weaken assertions. Preserve the blocker and finish all safe reporting.

## C. Population, denominators and missingness

Retain exactly the original per-domain target: 128 discovery, 1024 calibration, 256 untouched test seed parents. No new or replacement seed IDs; no new controller or condition variant. The original insertion discovery is complete (128/128), but its 1024 calibration action outcomes and 256 test decisions remain unobserved.

For each originally registered raw seed, count exactly one of:
- eligible decision checkpoint (usable training/calibration/test action and a qualified terminal observation);
- deterministic predecision planning failure (no checkpoint, no action outcome);
- prefix completes task before the decision point (no action selection; separately record source completion);
- failed qualification/parity/endpoint check (hard source guard and separately reported);
- pending/unattempted.

Keep BOTH denominators visible: originally registered seed parents and actually checkpoint-eligible independent parents. Under iid independent seed sampling conditioned on eligibility and outcome-blind action assignment, all risk and gain guarantees are CONDITIONAL ON ELIGIBILITY AND ON DECLARED ROUTING REGIONS. Never present them as all-seed end-to-end bounds.

Report the eligibility rate with grouped uncertainty, stratified by task; for full seed-population completion give conservative best/worst-case bounds for missing terminal outcomes, not made-up zeros. For test cohorts, do not claim 256 DSRE decisions if an eligible decision was never reached. Source failures are not DSRE abstentions. The 11 navigation calibration parents and one navigation test parent that finish during prefix must remain in original denominators but not intervention-at-risk or action-regret counts.

Repeated replay of the same seed for source diagnosis or outcome evaluation does not create an independent parent. If the 259 earlier screens recorded only prefix outcomes, physically executing their already registered randomized actions is allowed; this is NOT rerunning a previously measured assigned outcome. Audit that each original assigned action outcome is collected at most once.

## D. Freeze and complete G3; no cherry-picking

Original scientific estimands and settings are immutable: source-aware joint-outcome ambiguity, minimum scoped obligation certificates, intervention harm <=0.10, expected useful gain >=0.05, per-tail simultaneous allocation as registered, K<=4 frozen candidate leaves, behavior propensity 0.5, and matched baselines with identical observations and evidence.

After G1 qualification, execute the original remaining insertion source-screen and action continuation work in registered seed order, in bounded atomic batches with full physical/provenance guards. Keep source/evaluator files separated. Finish independent calibration before opening the original 256 untouched test outcomes. Actual policy execution must be separate from evaluator counterfactual reconstruction.

Current completed G3:
- Navigation: 128/128 discovery, 1013 valid randomized calibration logs / 1024 registered parents, 256 original test outcomes, with one no-decision prefix-success test parent. No recover-only success and no qualified selected recovery.
- PickCube: 128/128 discovery, 1024/1024 valid randomized calibration logs, 256/256 test outcomes. Frozen DSRE recovers 84 genuinely required states out of 256 test checkpoints; ordinary rules/CART/direct bounds take the same actions.
- Insertion: 128/128 discovery, ZERO assigned-action calibration observations, ZERO untouched test interventions. Of 260 initial prefix screens, 259 are technically usable and one fails before any control; 1020 screens were never attempted. Report exact additional screen counts and do not treat a technically usable screen as a calibration observation.

All five available single-action acquisition strategies tie at the primary 512-unit budget on PickCube. Navigation's 508/512 eligible candidates remain a documented shortfall, with no replacement. This outcome is already seen and cannot be reoptimized.

## E. One-time bounded resource amendment

Original cumulative new-physics ceiling: 18 worker-hours. Used: 9.73 worker-hours. Originally remaining: 8.27 worker-hours. The source-qualified insertion continuation is estimated at 11.32 worker-hours BEFORE acquisition and source requalification. The original ceiling cannot complete the frozen target.

Authorize a ONE-TIME extension to a maximum cumulative **28 worker-hours** measured from the start of the prospective continuation. Thus additional physics allowance is at most 18.27 worker-hours from the current 9.73 debit. This is an engineering capacity amendment to finish THE SAME preregistered insertion cohort, not to collect more favorable data or add a fourth task.

Priority of new physics: (1) exact source-eligibility qualification; (2) original insertion randomized calibration and untouched test; (3) registered insertion evidence-acquisition comparison at nested budgets 64/128/256/512 ONLY if feasible with enough reserved budget for auditing. No new model training or task discovery. Maintain original 5 GiB compressed artifact cap, lossless archiving/preservation and 2 worker-hour buffer for safe sealing and scientific audit. At the soft physics limit, end at an atomic parent boundary and seal incomplete results honestly; no new authorization of further resources in this contract.

This extension MUST be registered before opening any new outcome and never applied to retrospective claims as if it had been part of the first preregistration. The independent 256 test parent set and all statistical thresholds remain unchanged.

## F. G4 witness acquisition and valid statistical inference

Historical and prospective PickCube acquisition curves are complete; the primary 512-budget result is an equality among five strategies. Do not search more strategies or rerun until one wins. Navigation's candidate limitation is an observed feasibility boundary.

On insertion, use only fixed outcome-blind acquisition schedules and budgets, with equal actual action-execution costs. The selection of training observations must not bias calibration inference. A PAC population risk claim requires independent qualification samples from fixed decision regions; no naive Clopper-Pearson guarantee on an outcome-adaptively selected subgroup. All single-arm randomized logs and post-selection paired acquisitions must be separately counted.

If the fixed intervention/outcome support is insufficient to make any qualified recovery or the remaining budget cannot collect enough evidence, report INSUFFICIENT_SUPPORT without changing the risk target, sample partitions, predicate vocabulary or registered task. Negative results are part of G4.

## G. Scientific gates and end products

G1: technical source status independently justified and uniformly applied, or exact hard blocker.
G2: frozen 4,224 parent IDs and all cohorts unchanged, with the eligibility and resource amendments sealed before further physics.
G3: three-domain data complete to the extent checkpoint-eligible, with independent source/evaluator verification and honest attrition.
G4: source-grounded acquisition comparison complete, or explicitly budget-limited; no witness advantage unless a fixed-budget gain is real and independently reproduced.
G5: independently audited science report with identical-scope comparisons. Separate binary non-degradation, usefulness, harm, and raw completion; no inference of safety from zero observed harm. Never present identical ordinary-rule decisions as algorithm superiority.
G6: **science gate NOT YET PASSED**. A meaningful additional non-grasp recovery result and/or a demonstration that source-specific certificates cause genuinely better evidence decisions is necessary for a stronger RSS significance claim. If insertion proves homogeneous or source-blocked, report SCIENTIFIC_ADVANCE_NOT_ESTABLISHED. Do not quietly substitute another task.

Mandatory outputs: local commits for current work and follow-up; full results and resource ledger; independent audit, source-qualification log, grouped denominators, uncertainty and missingness sensitivity, exact reproduction, verifiable plots/tables, final sealed compact archive tested after extraction, G1-G6 status, and explicit remaining work. Keep manuscripts unchanged until supervisor authorizes G6. No force-push and no RSS submission.

## H. Immediate Codex instruction

Execute this document in order, beginning with packaging and committing currently UNCOMMITTED work. Do not start physics before the commit, source diagnosis, and sealed amendment. Continue only after the explicit source conditions pass. No intermediate user approval is required for outcomes within this bounded contract; stop with a precise report if a scientific guard fails. Do not claim that completing the task count guarantees RSS acceptance.
