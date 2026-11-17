# DSRE evidence-aware research handoff

This branch saves research design, a numerical reference oracle and an execution contract. It does not replace newer unpublished local code, create robot results, or claim RSS acceptance readiness.

## Read in this order

1. `docs/DSRE_EVIDENCE_AWARE_RESEARCH_PLAN_20261117.md`: the approved plan, saved byte-for-byte in commit `125199a9a773c764425d0007575a01db2e54105d`. SHA-256: `1067909f6dda63f3162c75805eb3411f602458a2f14920b782ed8d57ca91288a`.
2. `docs/DSRE_EVIDENCE_SPEC_V2.md`: authoritative mathematical choices, inferential scope, confidence allocation, minimum evidence grammar, matched baselines and end-to-end evidence program.
3. `docs/DSRE_TASK_AND_EXECUTION_CONTRACT.md`: explicit Codex work packages, frozen task interfaces, source pins, pilot settings, run budgets, milestones and failure handling.
4. `research/dsre_evidence_design/supervisor_reference.py` and `supervisor_validation.json`: executed supervisor numerical checks, not production code or simulator results.

## Scientific thesis

A recovery certificate must state both the observable facts and the type of intervention evidence supporting its obligation. More single-action logs can reduce sampling uncertainty but cannot always resolve counterfactual-harm ambiguity. DSRE should identify which evidence is missing, preserve the scope of its statistical statement, and test whether that diagnosis improves evidence acquisition.

## Already checked by the supervisor

- 441 exact marginal-probability pairs agree with the four-cell LP to maximum absolute error 1.11e-16.
- 256 random interval rectangles agree with closed-form harm and gain bounds.
- 256 valid paired-refinement intersections never weaken the same-scope bound.
- 64 finite certificate cases agree with exhaustive minimum conjunction search.
- Constructive counterexamples expose naive independence and unqualified subgroup routing.

Run:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python research/dsre_evidence_design/supervisor_reference.py --output /tmp/dsre_supervisor_validation.json
```

The reported results were produced with Python, NumPy 2.3.5 and SciPy 1.17.0. Exact package upgrades are not required if the existing compatible environment reproduces the checks. The oracle uses ordinary numerical optimization and exact binomial intervals, not a new statistical theorem.

## Implementation handoff

Use the latest local DSRE branch. Import these design files without resetting or overwriting local history. Run the fixed oracle, implement the independent production solver, compare paired and single-action development views, qualify the two specified new tasks, and produce the bounded development demonstrations. No manuscript edits or large confirmation campaign in the first session. Preserve failures and equivalent-rule results. The supervisor chooses scientific revisions; Codex executes the registered design.

## Primary sources used in the design

- Kallus, NeurIPS 2022: https://proceedings.neurips.cc/paper_files/paper/2022/hash/666cccc6376058e251315b4de7e085b9-Abstract-Conference.html . Sharp harm bounds and identification assumptions were inspected in the primary methodological text.
- Li et al., ICML 2023: https://proceedings.mlr.press/v202/li23ay.html . Counterfactual no-harm policy learning is established prior work.
- Wu et al., ICML 2024: https://proceedings.mlr.press/v235/wu24n.html . Faithful treatment-effect rules are established prior work.
- Conformal Risk Control: https://arxiv.org/html/2208.02814 . Expected-risk control is not the same guarantee as a high-probability conditional-region bound and does not identify missing counterfactual labels.
- ManiSkill insertion task: https://maniskill.readthedocs.io/en/latest/tasks/table_top_gripper/index.html . Source adapter pin and semantics are in the execution contract.
- PointMaze: https://robotics.farama.org/envs/maze/point_maze/ . A 2-DoF navigation abstraction, not a real mobile robot experiment.

PDF screenshot retrieval for the Kallus and Li papers failed during this session; primary parsed methodological text was available. No unseen figure or table was used as evidence. The new insertion/navigation adapters have not been executed in the supervisor environment and are explicitly subject to qualification.
