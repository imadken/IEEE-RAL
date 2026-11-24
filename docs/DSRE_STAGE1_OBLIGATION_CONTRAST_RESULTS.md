# Obligation comparison: fixed facts, actions and calibration

Scientific authority: the complete user-supplied closure contract (18 November 2026). Start commit `f551a6e546a55f59dc059747af6dfe8a3899c478`; branch `research/dsre-rss2027-experimental-closure`. All results are read-only audits or explicitly retrospective analyses. Zero new physics/controllers; no manuscript or final-figure edit. Final source artifacts: `research/dsre_experimental_closure/final`.

The original 128 discovery / 1024 one-action calibration / 256 test parents are separate in each task. O1 requires H_U<=.10; O2 requires L1>=.90; O3 requires H_U<=.10 and G_L>=.05. The C-only process freezes all rules before this offline oracle scoring. All three obligations were already specified in the scientific contract; the completed secondary policy comparison is a **post hoc obligation contrast**, not a new prospective trial. Each secondary action is scored on an actually executed native branch from the same qualified checkpoint. It is not an additional deployment or an imputed counterfactual.

| Task | Obligation | R | Rescue | Harm | Futile | Redundant | Completion | Minimum support on selected parents |
|---|---|---|---|---|---|---|---|---|
| PickCube-v1 | O1 harm-only | 111 | 84 | 0 | 27 | 0 | 227/256 | 1 literals: 111 parents |
| PickCube-v1 | O2 absolute success | 0 | 0 | 0 | 0 | 0 | 143/256 | none qualified |
| PickCube-v1 | O3 useful recovery | 111 | 84 | 0 | 27 | 0 | 227/256 | 1 literals: 111 parents |
| PushCube-v1 | O1 harm-only | 256 | 127 | 2 | 2 | 125 | 252/256 | 0 literals: 256 parents |
| PushCube-v1 | O2 absolute success | 256 | 127 | 2 | 2 | 125 | 252/256 | 0 literals: 256 parents |
| PushCube-v1 | O3 useful recovery | 128 | 126 | 0 | 2 | 0 | 253/256 | 1 literals: 128 parents |

| Task | Obligation | Minimum E | Whole-cell S |
|---|---|---|---|
| PickCube-v1 | O1 harm-only | [["goal_near_03", false]] | [0, 1] |
| PickCube-v1 | O2 absolute success | NO CERTIFICATE (not an empty conjunction) | none |
| PickCube-v1 | O3 useful recovery | [["goal_near_03", false]] | [0, 1] |
| PushCube-v1 | O1 harm-only | [] | [0, 1] |
| PushCube-v1 | O2 absolute success | [] | [0, 1] |
| PushCube-v1 | O3 useful recovery | [["hand_object_near_04", false]] | [0] |

## Exact regional support

| Task | Leaf | n0 | n1 | L0 | U0 | L1 | U1 | H_U | G_L | O1 | O2 | O3 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PickCube-v1 | 0 | 147 | 167 | 0.000000000000 | 0.043003520123 | 0.704745730512 | 0.888706946545 | 0.043003520123 | 0.661742210389 | pass | withhold | pass |
| PickCube-v1 | 1 | 88 | 82 | 0.000000000000 | 0.070794886269 | 0.635148735241 | 0.905343761598 | 0.070794886269 | 0.564353848973 | pass | withhold | pass |
| PickCube-v1 | 2 | 158 | 136 | 0.959929563847 | 1.000000000000 | 0.540538308140 | 0.782096400864 | 0.459461691860 | -0.459461691860 | withhold | withhold | withhold |
| PickCube-v1 | 3 | 121 | 125 | 0.948000202195 | 1.000000000000 | 0.605733119516 | 0.842533805229 | 0.394266880484 | -0.394266880484 | withhold | withhold | withhold |
| PushCube-v1 | 0 | 251 | 261 | 0.000000000000 | 0.022719298466 | 0.956294468491 | 0.998903875635 | 0.022719298466 | 0.933575170025 | pass | pass | pass |
| PushCube-v1 | 1 | 241 | 271 | 0.952732085592 | 0.998812585102 | 0.964166815730 | 0.999699789396 | 0.035833184270 | -0.034645769372 | pass | pass | withhold |

Full precision, all five four-cell extrema and parent support lists: `research/dsre_experimental_closure/final/E1/calibration_freeze.json`. The independent CDF inversion and four-variable LP agree with the original production bounds; no sample/threshold or discovery tree changes. Pick uses K=4 (tail .0015625); Push K=2 (tail .003125). Each tail is .025/(4K); the separate paired reserve remains .025. All three obligations are deterministic functions of the SAME simultaneous interval event, so they do not consume that family budget three times. No joint95 claim across tasks/methods/source budgets follows.

## Interpretation and nontriviality

Pick absolute success has **no qualified recovery**, not a zero-literal success certificate: the default continue macro is measured and is not certified successful. Harm-only and useful recovery require the same one literal under this grammar. Push O1/O2 permit the empty conjunction over both cells. Useful recovery needs `hand_object_near_04=False`, excluding cell 1 whose gain upper bound is below .05. The broader weak-obligation policy has recorded harms and redundant interventions; zero-literal support is not universal individual safety.

Deleting each retained grasp literal admits cells 2/3, whose harm/gain constraints fail; deleting the useful push literal admits cell 1. Per-case removal records include the exact admitted cells, parent support, bounds and feasible model witnesses at `research/dsre_experimental_closure/final/E3/full_certificate_audit.json`. Splitting any calibrated leaf is disallowed. UNKNOWN is never false.

Minimum means minimum **within the frozen, all-compatible-leaves-qualified grammar**. Whole-leaf componentwise qualification is sufficient, not universally necessary for an average obligation on a fixed-weight union. The checked analytical two-cell example has gains 1 and 0; its half-and-half union has gain .5 and harm 0 although one cell fails useful recovery. Thus the reported one-literal requirement is not a universal theorem that every valid pooled-region analysis needs that observation. No controller/optimizer novelty follows from the contrast.

All instrumented B7/direct-ID/obligation-gated trees have identical outputs. The original CART additionally vetoes discovery cells lacking empirical gain; this is retained as a distinct, stronger preference in the policy JSON. In particular a harm-only objective and a harm-plus-gain proposal filter need not recommend the same intervention. No comparison advantage is manufactured by hiding this distinction.
