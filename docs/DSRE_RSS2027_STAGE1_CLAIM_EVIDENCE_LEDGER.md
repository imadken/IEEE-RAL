# Stage 1 numerical and methodological claim ledger

The paper is `rss2027/dsre_stage1.tex`, with generated figures/tables in `rss2027/stage1_evidence/`. Scientific input is local commit `d917a69d47f3102123030eaf565f4623dad86525`; no experiment or fit was added. Supervisor documents were imported byte-exactly from `036a5849763453a46523624542f8281e5436de4f`; Git blob checks are in `research/dsre_stage1_manuscript/supervisor_import.json`.

Primary audit output: `research/dsre_stage1_manuscript/independent_numbers.json`. It contains every input SHA256, exact calibration intervals, independent CP/LP discrepancies, every matched policy's parent-level actions, outcome classes, support, certificates and boundary/acquisition reconstructions. `main_results.csv` is the complete numerical table, including controls not repeated in the paper. Counts below are reconstructed from native outcomes, not copied from supervisor prose or report totals. `scripts/dsre_stage1_verify_numbers.py` imports no production inference or simulator module: it independently reads gzip/XZ traces, verifies sealed hashes, recomputes native endpoint geometry, inverts binomial CDFs and solves four-cell LPs.

For compact source names below:

- `G = results/dsre-evidence-aware/20261117-prospective/prospective/PickCube-v1`
- `GP = results/dsre-evidence-aware/20261117-prospective/physics/PickCube-v1`
- `P = results/dsre-evidence-aware/20261118-final-science`
- `N = results/dsre-evidence-aware/20261117-prospective/prospective/PointMaze_UMaze-v3`

## Main test claims — abstract, Table I and V-B

Each domain has 256 distinct independent registered test parents, one condition per parent. Every comparison uses the same physical macro alternatives and recorded paired test endpoints. The original primary policy was physically executed first; alternatives were evaluator-only and all other frozen policies are scored on those common labels. These are not separate independent deployments for every comparator.

| Domain / policy | R | Necessary rescues (01 among R) | Harm (10 among R) | Futile (00 among R) | Redundant (11 among R) | Completion | Default C |
|---|---:|---:|---:|---:|---:|---:|---:|
| Grasp DSRE / B7 / direct ID / matched CART | 111 | 84 | 0 | 27 | 0 | 227/256 | 145 |
| Grasp ridge regression, retrospective | 111 | 84 | 0 | 27 | 0 | 227/256 | 145 |
| Grasp always C | 0 | 0 | 0 | 0 | 0 | 143/256 | 256 |
| Grasp always R | 256 | 86 | 32 | 27 | 111 | 197/256 | 0 |
| Push DSRE / B7 / direct ID / matched CART / ridge | 128 | 126 | 0 | 2 | 0 | 253/256 | 128 |
| Push always C | 0 | 0 | 0 | 0 | 0 | 127/256 | 256 |
| Push always R | 256 | 127 | 2 | 2 | 125 | 252/256 | 0 |

Exact sources: `G/test/*.json`, `G/evaluator/*.json`, `G/evaluations/logged.json` (actions only, totals independently recomputed), `GP/test/*/{selected_policy,evaluator_counterpart}.json.gz`; `P/records/test/*.json`, `P/physics/test/*/{selected,evaluator}.json.gz`. All 512 selected/alternative timing inequalities and prefix/controller parity checks pass. Compressed P traces are lossless `.xz` representations with original-gzip SHA sidecars; the reader checks both encoded and decoded digests against the unchanged seal. Original gzip byte reconstruction was separately established by the science closure.

Grasp four cells: 00=27,01=86,10=32,11=111; hindsight ceiling 229/256, two unselected rescues. Push four cells: 00=2,01=127,10=2,11=125; hindsight ceiling 254/256, one unselected rescue. The push 253-versus-252 contrast is descriptive and establishes no meaningful superiority. No outcome gain over equivalent learned methods is claimed. B7/direct-ID equality is structural under identical cells/thresholds; CART and ridge equality is verified parent by parent (256/256 in each domain). Grasp regression is a previously frozen retrospective reanalysis at `P/legacy_regression/{model_frozen,evaluation}.json`, not new independent confirmation. Pushing regression was prospectively frozen before its test.

Observed conditional harm intervals are **two-sided exact descriptive 95% test intervals**, computed with tail .025: 0/111 gives [0,.03268699402394771], 0/128 gives [0,.02840805344354391]. These do not replace the calibration event. The paper deliberately omits completion/gain bootstrap intervals rather than silently substitute the later standardized bootstrap for the original registered grasp bootstrap. Both old versions remain unchanged in historical evidence.

## Calibration, confidence, minimum facts — Table II, Fig. 2, IV and V-C

`G/calibration/*.json/record` and `P/records/calibration/*.json/record` provide exactly one primary learner outcome per parent. Independent binomial CDF inversion agrees with saved production endpoints to less than 1e-10 (actual task discrepancies in the audit JSON); independent HiGHS extrema agree with the rectangular formulas. Full precision is in the JSON; paper values below are rounded display only.

| Cell | n C | n R | Harm upper | Gain lower | Gain upper | Primary |
|---|---:|---:|---:|---:|---:|---|
| G0 | 147 | 167 | .0430035201231355 | .6617422103889946 | .8887069465451968 | pass |
| G1 | 88 | 82 | .0707948862688430 | .5643538489725929 | .9053437615980222 | pass |
| G2 | 158 | 136 | .4594616918595944 | -.4594616918595944 | -.1778331629827461 | fail |
| G3 | 121 | 125 | .3942668804839017 | -.3942668804839017 | -.1054663969662646 | fail |
| P0 | 251 | 261 | .0227192984661949 | .9335751700248749 | .9989038756354168 | pass |
| P1 | 241 | 271 | .0358331842698125 | -.0346457693718708 | .0469677038044895 | fail |

Primary constants alpha=.10, eta=.05 are frozen. A whole-cell primary pass needs both H_U<=alpha and G_L>=eta, using unrounded values. A .025 logged-family budget allocates `.025/(4K)` to each endpoint tail of two arm marginals over K leaves: K4 grasp tail .0015625; K2 push tail .003125. A separate .025 remains reserved for paired refinement. Logged-only containment is at least .975; the combined specified family at least .95. This is per task/fixed method/allocation/one look, not joint confidence across tasks, methods or budgets, and assumes independent/stationary/binomial regional sampling.

Sources: `G/models/logged.json`, `G/discovery_freeze.json`, `P/model_frozen.json`, `P/discovery_freeze.json`, source `src/dual_rec/evidence_aware/{partition,bounds,certificate}.py`. Partition construction is depth<=2, K<=4, within-arm SSE, at least8 discovery samples/arm in split leaves, canonical ties/unsplit fallback. No estimator was fitted in this writing run. Regression lambda1/unpenalized intercept/clipped predictions/two whole prediction regions/minimum8 support/collapse behavior is in `scripts/dsre_last_model.py`; it receives its own same-standard confidence family.

Minimum grasp evidence is `goal_near_03=False`, exactly whole G0+G1, worst-cell H_U=.0707948863 and G_L=.564353849. Minimum push evidence is `hand_object_near_04=False`, whole P0, H_U=.0227192985/G_L=.933575170. Independent subset enumeration over all64 Boolean assignments verifies all111+128 selected certificates, including empty-set rejection and admitted unqualified cells when the sole literal is deleted. Broader E never inherits a narrow leaf bound. P1 gain upper .0469677038<.05 supplies the reported useful-recovery obstruction, while both P leaves separately pass harm-only and absolute-success requests; therefore those weaker requests permit the empty conjunction. The earlier science auditor independently verifies all64x3 obligation queries in `P/source_obligation_witnesses.json`.

Nominal push measured signature contains128 parents with q11 count125,q10 count2,q01 count1,q00 count0. The independently reconstructed `signature_diagnostics` records the opposing finite-reference outcomes. This refutes a common successful action on that finite signature, not its regional average harm-only obligation. Point-estimate full-signature paired-only counts at n>=10 are zero for both main tasks. No physical confidence-qualified necessity of pairing is established. These inspected-test signature diagnostics are exploratory descriptions, not new calibration regions.

## Sampling, access, execution cost and physical definitions — V-A

Original manifests: `results/dsre-evidence-aware/20261117-first-session/{prospective_manifest,prospective_ready_manifest}.json` have identical original cohorts; every G spec is checked against them. P specs match `P/registration.json`. D/C/T128/1024/256 per task are disjoint and unique. Grasp arm/condition and deterministic seed hashing are verified against recorded spec/parent data; pushing arm assignment is the first MSB of SHA256 of the registered namespace, propensity .5. Independence/randomization interpretations for deterministic simulator draws are explicit assumptions, not inferred from lack of seed collisions.

The logged G model has no exposed pair parents; its whitelist and successful reads contain no test/evaluator/counterpart path. Later separately budgeted grasp acquisition counterparts exist in the physical archive: their existence does not mean exposure to the primary learner. P D/C contain only the assigned raw outcome. P frozen model reads only D/C and the discovery freeze. The new audit verifies input-file digests and saved access whitelists. Saved instrumentation audits trusted fitting code, not an adversarial operating-system sandbox.

Equal learner budget is128+1024=1152 observed outcomes per method/task, not two observations per parent. Each selected test execution is one70-control macro, 3.5s at .05s/control. Shared evaluator cost is an additional256 outcomes/task. Prefix replay, source qualification, separate acquisition studies and process startup are not claimed free or included in this learner-information count; native traces/resource ledgers retain them. A pair costs two observed action outcomes; acquisition cost is already-exposed first labels plus extra counterpart labels, not double-counted pairs.

Six original telemetry predicates are fixed in `src/dual_rec/dsre/features.py`: distances .03/.04m, progress/displacement .005m, summed finger magnitude .04m, height .03m; strictness is retained. Grasp native task success uses <=.025m Euclidean cube-goal distance and max absolute arm velocity <=.2, verified against installed task/agent source and independently recomputed native endpoints. It is not the .03m observation threshold. Grasp cached approach offsets [0,.01,.02,.03,-.02]m are checked against original registration. The grasp source runs a90-control script, permitting a stop from70 for missed lift (three ungrasped frames, cube height<initial+.03m and hand>initial+.06m) or drop (peak>initial+.06m, fall>.03m, ungrasped). Successful prefixes do not trigger; otherwise it stops at90. The native grasp flag defines this simulator source boundary, not learner facts. P prefix53 controls, cached initial+goal y offset .07m in half the parents, neither physical object nor goal shifted; a0 goal-directed hand feedback, a1 lift/reapproach then pushing. Terminal P success is XY distance<.1m and cube z<.025m, not a grasp metric. Sources: `scripts/{dsre_evidence_grasp,overnight_pick,overnight_replay,dsre_last_push}.py`, native raw spec/controller memories, source-qualified locked ManiSkill3.0.1/SAPIEN3.0.3 environment.

## Acquisition and boundary claims — V-C and VI

The independent audit re-scores every saved primary512 acquisition decision against G paired native outcomes, not summary policy counts. Sources: `G/{models,evaluations}/{all_logs,all_pairs,uniform_mix,witness,decision_uncertainty}_512.json`. Every strategy costs512 base+512 additional outcomes and chooses the same111 R/84 rescues/0 harm/27 futile/227 completions. No efficiency advantage follows. First labels and counterpart labels are counted once each. Smaller-budget exploratory curves remain historical and are not selected for a favorable headline.

Navigation: N/test has256 registered parents,255 COMPLETE checkpoints and1 ALREADY_SOLVED_PREFIX with actual success and UNKNOWN facts. Only255 eligible evaluator pairs enter the recovery signature analysis; their four cells have no01 successes. Absorbed successes are neither failed recoveries nor fabricated checkpoints. Main paper makes no positive navigation recovery claim.

Insertion: P/records/insertion_pilot has48 registered valid checkpoints, no missing endpoints, q00=22/q01=25/q10=0/q11=1. P/insertion_extension_decision.json is false; zero continue-only fails the preset>=2 each opposing unique-success requirement despite>=32 valid checkpoints. P/records/insertion_confirmation does not exist: 0/96 conditional parents activated. The index38 observed post-checkpoint stopped endpoint is retained, not imputed failure or precheckpoint attrition. The older interrupted insertion C0/1024,T0/256 cohort remains historical and is not presented as the 48-parent pilot or completed task.

## Formal and diagram claims — III/IV, Fig. 1

| Claim | Basis | Exact scope / limitation |
|---|---|---|
| Marginals identify gain but need not identify binary task harm | Four-cell algebra; Kallus primary source; two explicitly analytical couplings | Requires valid causal marginals. No observational-confounding repair or individual counterfactual label. |
| Sharp harm bounds max(0,p0-p1) through min(p0,1-p1) | Classical Fréchet nonnegativity derivation, cited Kallus | Established mathematics, not DSRE novelty. |
| Same p0=.4,p1=.6,g=.2 can yield h0 or.4 | q=(.4,.2,0,.4), (0,.6,.4,0), independent numerical assertions | Constructed worlds only. Neither is a claimed measured robot region. |
| Finite rectangle H_U=min(U0,1-L1),G_L=L1-U0 | Independent four-variable LP and binomial CDF endpoints | Exact for the rectangular marginal ambiguity set; not pointwise safety. |
| Calibrated whole-cell regional soundness | Proposition1, simultaneous containment and mixture proof | Retains within-cell distribution and cell-constant actual selection. No arbitrary subcells, shift or missingness sub-selection. |
| Minimum E and deletion witnesses | Exhaustive cardinality search over known-literal subsets; complete-cube oracle | Finite fixed grammar only; not global human explanation, optimal sensing or new algorithm. |
| Scope counterexample harm .08 overall/.80 in10%-mass subgroup | Constructed mixture, .1*.8+.9*0=.08 | Illustrates invalid subcell inference, not measured task harm. |
| Additional valid paired constraints improve extrema | Set intersection over the same target/source population | Changing sensor/controller/conditioning region is not automatically a valid set intersection. |
| No-source/no-overlap/missing-label refusal | Source semantics and production schema/access/solver tests | No outcome imputation. Continue is measured fallback, not a certified successful action. |

Figure 1 is an original schematic drawn by `scripts/dsre_stage1_manuscript_figures.py`; no generated robot photograph or copied figure. Its analytical tables are labeled, paired data remain offline, and the online path has one action. Figure2 green region is the exact-marginal primary criterion; its rectangles come only from independent audited calibration intervals. Editable SVG, embedded-font PDF and450dpi PNG are delivered. PNG is included in the manuscript so the main PDF retains the official template's Type1 fonts; this does not change font sizes or page geometry. The scientific data and drawing source are included separately.

## Citation, artifact and preservation checks

`research/dsre_stage1_manuscript/citation_audit.json` verifies every bibliography entry against primary publisher/author records and records preprint status. The official author-kit SHA256 is `ffc8b8053bd218ba9be4c93a569de4c2f36c7f70ae8d2245c747611bed697271`; the unchanged IEEEtran class matches byte for byte. The paper has no author identity, acknowledgments, external links, internal gate names or source paths. Anonymity is an artifact inspection, not a claim that prior public repository disclosures can be erased.

`preservation_before.json` protects480 existing files: full master and all its existing RSS dependencies, original bibliography/figures, .gitignore, uv.lock and historical seals. The old Stage1 source/PDF remain recoverable at the scientific base commit. Unrelated user document deletions/moves remain unstaged. No new physics, model fit, policy threshold, source change or manuscript outside Stage1 occurred. Tests and PDF/page checks are recorded in the submission audit.
