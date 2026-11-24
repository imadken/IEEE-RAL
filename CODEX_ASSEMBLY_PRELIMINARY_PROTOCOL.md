# Codex execution contract: RPD assembly qualification and optional small exploratory pilot

## Purpose
Produce a small, source-qualified physical check relevant to the existing RPD Stage 1 methodology. Do not search for positive seeds, change the recovery method, or declare H1/H2 established from a small exploratory run. Preserve all prior local evidence and current paper worktree.

Repository: /home/imad/Desktop/IEEE-RAL
Existing paper workspace: papers/rss2027_rpd_stage1/
Latest reported paper commit: 3465dd56c7b14e6aaa3e28a596ed6d4f1164e2d7
Source of truth: papers/rss2027_rpd_stage1/reviews/STAGE2_VALIDATION_SPEC.md and PROPOSED_PROTOCOL_AND_NUMERICS.json.

### Stage A, mandatory, before any new physics

1. Confirm all latest LOCAL user changes and commit HEAD; do not reset or overwrite newer history. Preserve the official template and original V2. Use a separate scoped work branch, e.g., research/rpd-assembly-preliminary-20261120. Do not push or submit.
2. Import the revised editorial bundle only by a reviewed copy into the editable manuscript workspace, never into immutable original_v2. Rebuild and visually inspect pages; verify that body and bibliography are identical except for the documented editorial edits.
3. Audit the proposed native ManiSkill/SAPIEN source configuration, gripper and fixture geometry, checkpoint dynamics, native 20Hz controller, stable insertion event, two probes, equal-duration hold, two frozen feedback recovery macros and absent privileged sensing. Check that the original geometry and source constraints are implementable. Source adjustments that alter the registered task require written methodological review BEFORE outcomes.

### Stage B, qualification pilot, maximum three physics worker-hours

Use the 12 **pre-existing frozen `qual` root IDs** in the proposal, in ascending index order and without replacement. Execute the fixed source screening and specified seven terminal branches, including equal-duration hold, preload, dither and both recovery actions, and the required two-parent parity repeats. Retain all outcomes, including no-checkpoint, source failure, constraint violations and missing. A root cannot be selected or discarded based on downstream success or erasure.

Pass only if at least eight technically eligible roots exist, all reported branches have finite, source-consistent execution, and native clock, controller state, command/force channels, exact goal flag and replay tolerances meet the original qualification criteria. This pilot is not a performance-selection gate and must not require a positive erasure effect. Stop on native crash, source provenance mismatch or invalid branch reconstruction. Investigate only the exact engineering failure within bounded time; do not search different tasks or fault severities.

Report measured median and p95 per physical branch, source qualification, controller/goal fidelity, and whether the full 512-parent protocol is feasible under declared resources. If not, state exact blocker and a proposed **pre-outcome** resource amendment requiring author approval.

### Stage C, OPTIONAL after B passes: frozen 24-parent independent exploratory sample

Create a complete immutable ID list under the NEW namespace `RPD-assembly-prelim-v1/index/geometry` and `.../fault` using the same SHA256 and NumPy PCG64 construction as the registered root generator. Indices are 0..23; source generator and all observable features fixed before any exploratory physics. Verify nonoverlap with ALL `qual`, 64 `discovery` and 512 `confirmation` IDs. Save and hash list and exact controller/method configuration before opening any exploratory labels.

For each eligible exploratory parent, execute exactly the same three alternatives (hold, preload, dither) followed by both original recovery macros. Evaluate all six terminal branches from matched, independently regenerated checkpoints and same remaining deadline; include matched-hold path compliance. Record Z and native physical contact measurements only in the isolated evaluator. For technically ineligible parents, retain the original ID and disposition; no replacements. No cherry-picked severity, source-mode or parameter search.

If the frozen source has not yet fitted a learned grasp estimator, use *one fixed, explicitly labeled nominal-source exploratory version* for all arms with parameters shared across branches; do not pretend it is the final learned RPD. A learned model cannot be fitted using the exploratory/test labels. The effect study is a technical/physical feasibility diagnostic; its sample size is inadequate to establish the preregistered H1/H2 population margins. Do not use any of the original 512 confirmation labels or treat evaluator-only pairs as online information.

### Stage D: reporting, independent audit and exit

Report complete raw denominators: attempted, eligible, unknown eligibility, missing, successful hold/recovery, successful probe/recovery, individual-option losses, full-repertoire erasures, option creations, compliance and unexpected contacts. For signal, report valid predecision features and actual Y, without inventing force sensors. If illustrative cases exist, provide their trace IDs and all matched branches; report how they were selected from the full fixed sample, not just pictures.

Produce method/source fingerprints, independent replay audit, costs and reproducible compact archive. Validate all maintained tests and exact source hashes; commit locally without touching protected evidence or pre-existing user changes. Do not push or submit. If source does not qualify, end with a truthful source-blocker report, not a replaced or repurposed pilot.

The final summary must say precisely: (a) which RPD scientific hypothesis this preliminary study does or does not address, (b) source/engineering qualification, (c) any observed physical effect with complete denominator, and (d) what remains for Stage 2. The user decides whether the result belongs in the Stage 1 paper.
