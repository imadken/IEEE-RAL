# DSRE v1.2: primary-source novelty challenge

This is a bounded, source-grounded assessment, not a first-ever claim or a
prediction of acceptance. Primary records were checked on2026-11-15. The matrix
below is the one-page comparison; publication year/venue are taken from the
linked author, proceedings or publisher records.

| Prior work / primary source | Established mechanism and evidence | Precise overlap and remaining DSRE distinction |
|---|---|---|
| Khan, Poupart & Black, ICAPS2009, [Minimal Sufficient Explanations for Factored MDPs](https://cs.uwaterloo.ca/~ppoupart/publications/explaining-mdps/ICAPS09OKhan.pdf) | Minimal collections of explanation templates justify factored-MDP policy decisions using the specified decision model. | Minimal sufficient decision explanations are established. DSRE uses minimum observable literals over an empirical paired-action table, with explicit missing-observation, repertoire and reference witnesses; this is a different evidence contract, not the invention of minimal explanations. |
| Wu et al., ICML2024, [DISCRET](https://arxiv.org/abs/2406.00611) ([author paper](https://www.seas.upenn.edu/~mkeoliya/assets/pdf/icml_2024_paper.pdf)) | Faithful rules serve as database queries for individual treatment-effect estimation; reinforcement learning searches rule space. | Outcome-aware explanations/rules are established. DSRE's binary terminal adequacy and finite-reference universal support are narrower than ITE estimation, and equivalent ordinary rules must retain equal credit. |
| Peddi & Bezzo, IROS2023, [Decision Tree-based Monitoring and Recovery](https://ieeexplore.ieee.org/abstract/document/10342207) ([author preprint](https://arxiv.org/abs/2308.00944)) | Decision trees assess failure uncertainty and support MPC corrective controls, with simulated and physical UGV evidence. | Interpretable uncertainty-aware recovery predates DSRE and has stronger hardware breadth. DSRE keeps skills fixed and asks which observed literals justify their measured adequacy; no new recovery controller is claimed. |
| Wang et al.,2026 preprint, [DA-GRD](https://arxiv.org/html/2609.29065v1) | Tactile probes update pose hypotheses until a sufficiently supported executable grasp agrees across remaining uncertainty; simulation and hardware grasps. | Sensing for action agreement is established. DSRE's finite-table minimum certificate, typed insufficiency and separate assigned-parent risk scopes are the proposed combination, not decision-aware sensing itself. |
| Ahmedt-Aristizabal et al.,2026 preprint, [RESCUE](https://arxiv.org/html/2610.13516v1) | Matched simulator/policy branches evaluate action-conditioned recoverability and intervention cost, including unnecessary/harmful intervention. | Paired recovery evaluation and the difference between detection and intervention value are established. DSRE adds an observable explanation contract rather than a new branching protocol; its deterministic two-skill evidence is much smaller. |
| Jiang et al., Artificial Intelligence336(2024), [Interval Abstractions for Robust Counterfactual Explanations](https://doi.org/10.1016/j.artint.2024.104218) ([author version](https://arxiv.org/abs/2404.13736)) | Interval abstractions and verification establish explanation validity across sets of model-parameter changes. | Interval robustness machinery is established. Here elementary input-telemetry enclosures expose invariant literals before an unchanged finite solver. Input error differs from their model-parameter uncertainty; neither distinction supports a new interval-optimization claim. |
| Additional close challenge: Ceder, Freitag & Åkesson,2026 preprint, [Teaching a Tree to Recover](https://arxiv.org/abs/2610.39775) | Online tree distillation uses counterfactual labels for needed, unnecessary and harmful recovery; it matches expert rules/LLM supervision in navigation simulations. | Counterfactual-labeled interpretable recovery and ties with ordinary rules are already present. DSRE studies observable sufficiency/witness scopes with a frozen skill repertoire, rather than online supervisor distillation. |

The possible contribution is the **testable evidence contract** linking minimum
observable justification of fixed physical actions to typed insufficiency,
measurement-invariant assertions and explicitly separate population qualification.
No individual component—minimality, hitting sets, outcome-aware rules, decision
trees, interval analysis, paired replay or binomial calibration—is new.
Exact B7 and strict-first ordinary-rule risk wrappers are mathematical identities,
including the robust UNKNOWN interface. This extension cannot support an optimizer
win against them. A positive comparison against an all-input margin rule would
isolate the value of using a sufficient subset, not a novel robustness algorithm.

Within the inspected primary descriptions, no single paper establishes this exact
combination of fixed binary action adequacy, minimum literal certificates, three
counterexample types, declared input-error invariance and disjoint parent-action
risk qualification. That is an inference about these inspected sources, not an
exhaustive absence theorem. DA-GRD, RESCUE and the recovery-tree work substantially
limit broad novelty claims. A remaining scientific case must rest on correct,
discriminating mechanism evidence and explicit scopes, not rebranding established
machinery or an unsupported controller advantage.

The [official RSS2027 author FAQ](https://roboticsconference.org/information/author-faq/)
asks for testable scientific hypotheses and experiments that distinguish reasons
for failure; an unfavorable score alone is insufficient. The sprint therefore
separates action infeasibility, observation aliasing, unstable factual assertions,
reference support and population-risk coverage. Its results/gate documents assess
these mechanisms after independent verification. Neither manuscript is revised.
