# ERR sealed robot context/capability witnesses

This process reads ONLY original discovery/calibration learner files, models,
record metadata and assigned native branches. No selected-policy test,
evaluator, acquisition counterpart or future alternative label is read.
The CPython audit-hook whitelist and every successful protected read are in
`research/err_method_challenge/final/robot/robot_context_witnesses.json`. Each task retains 128 D and 1024 C
independent original parents; selecting examples does not create a new cohort.

## Actual recorded predecision anchors

| Task | Original phase | Parent ID | Six facts | Object-goal m | Hand-object m | Actual assigned macro |
|---|---|---|---|---|---|---|
| PickCube-v1 | calibration | ad552a48fa35584b62fda307bae5bd3d4b8c6327c7be971ac2a6c9380e0fe076 | [False, True, True, True, True, False] | 0.038523869393 | 0.038650063621 | c |
| PickCube-v1 | calibration | 450b48bf2683238ea3b9c843cb57d5a54c6aee2906218792df3c38e9eb9285c0 | [True, True, True, True, True, False] | 0.022074505666 | 0.021815351460 | c |
| PushCube-v1 | calibration | 686fc364a9f55bb6e80073f698591a7186a562e8ecfc129cb9829b17a0153ad4 | [False, False, False, False, True, False] | 0.200901060890 | 0.075163084592 | c |
| PushCube-v1 | discovery | 3e4b6a86522fc5161c04d83c2126def7e098051ab6b2bdcbda608feb5e45b21a | [False, True, True, True, True, False] | 0.147088153395 | 0.028836730296 | c |


The four records are actual native traces. Facts are independently recomputed
from first/current recorded pose packets and match their declared six-predicate
source. Goal-near is distance<=.03m; hand-object-near is distance<=.04m. These
are ideal simulator observations, not validated real-robot vision. The native
grasp trigger remains source-only and excluded from the planner's observations.

### PickCube-v1

Original shortest scoped explanation: `[['goal_near_03', False]]`; whole leaf set
`[0, 1]`; harm upper 0.070794886269, gain lower
0.564353848973. It is the unchanged original one-arm certificate,
additionally accepted by the conservative ERR boundary. This is an offline
query on an old D/C checkpoint, not a newly executed policy or independent test.

Retrospectively hide the registered split fact in the stored packet. Current
DSRE and B7 both withhold the recovery certificate. The declared context plan
returns `['reveal_goal_near_03']`
at logical recorded-fact lookup cost 1. Restoring the original packet allows the
same scoped certificate. Revealing the other value can refute the regional
obligation. It does not guarantee an individual's success or show a sensor
measurement was acquired online.

Context provenance: `['ACTUALLY_RECORDED_PREDECISION_CONTEXT', 'ACTUALLY_RECORDED_PREDECISION_CONTEXT']`.
The complete processor output, original source scope, true versus logical
context mapping, native source hashes and literal-deletion countermodels are
retained in the machine artifact. B7+identical planner is fully equivalent;
direct-ID receives the same explicit source menu and processor. The greedy
control gives `(Fraction(1, 1), ('reveal_goal_near_03',))`. Source-scoped Boolean certificate
comparisons: 192.
### PushCube-v1

Original shortest scoped explanation: `[['hand_object_near_04', False]]`; whole leaf set
`[0]`; harm upper 0.022719298466, gain lower
0.933575170025. It is the unchanged original one-arm certificate,
additionally accepted by the conservative ERR boundary. This is an offline
query on an old D/C checkpoint, not a newly executed policy or independent test.

Retrospectively hide the registered split fact in the stored packet. Current
DSRE and B7 both withhold the recovery certificate. The declared context plan
returns `['reveal_hand_object_near_04']`
at logical recorded-fact lookup cost 1. Restoring the original packet allows the
same scoped certificate. Revealing the other value can refute the regional
obligation. It does not guarantee an individual's success or show a sensor
measurement was acquired online.

Context provenance: `['ACTUALLY_RECORDED_PREDECISION_CONTEXT', 'LOGICAL_BOOLEAN_COMPLETION_NOT_A_ROBOT_EPISODE']`.
The complete processor output, original source scope, true versus logical
context mapping, native source hashes and literal-deletion countermodels are
retained in the machine artifact. B7+identical planner is fully equivalent;
direct-ID receives the same explicit source menu and processor. The greedy
control gives `(Fraction(1, 1), ('reveal_hand_object_near_04',))`. Source-scoped Boolean certificate
comparisons: 192.


## Constructive literal-deletion check

Removing the retained literal admits the entire original partition: Pick
leaves0/1/2/3 and Push leaves0/1. The following saved four-cell distributions
are compatible with the disallowed leaf's original logged marginal rectangle
and strictly violate useful recovery. They are ANALYTICAL countermodels, not
observed robot endpoints. Plain simplex/marginal arithmetic is checked again
when generating this report; numerical feasibility tolerance is1e-12, while
the displayed obligation violations are far from the thresholds. Independent
LP checks and exhaustive scope enumeration are in the pinned reproduction.

| Task | Removed literal | Admitted disallowed leaf | q00,q01,q10,q11 | Harm / gain | Violating bound |
|---|---|---|---|---|---|
| PickCube-v1 | ['goal_near_03', False] | 2 | [0.0, -0.0, 0.4594616918595942, 0.5405383081404058] | h=0.459461691860, g=-0.459461691860 | harm_upper |
| PickCube-v1 | ['goal_near_03', False] | 3 | [0.0, -0.0, 0.39426688048390157, 0.6057331195160984] | h=0.394266880484, g=-0.394266880484 | harm_upper |
| PushCube-v1 | ['hand_object_near_04', False] | 1 | [0.0011874148979417187, -0.0, 0.034645769371870805, 0.9641668157301875] | h=0.034645769372, g=-0.034645769372 | gain_lower |


This verifies literal-deletion necessity in the registered whole-leaf grammar.
It does not assert universal necessity under a different pooled-population
guarantee. Global minimum explanation cardinality also comes from the complete
Boolean/subset checks, not deletion alone.

## Physical versus logical versus causal distinctions

The two Pick anchors share all five other measured facts. Both branches of its
one-bit context ambiguity have actual source evidence. This is the required
physical-origin recorded-observation witness. It is NOT a paired demonstration
that these two parents require opposite unique-success actions.

The Push positive anchor is actual. Its alternative completion with the SAME
five visible facts is explicitly LOGICAL, not an observed robot episode. A
separate actual negative-region anchor is provided, with its different facts
fully visible. No unobserved state or terminal label is invented. The frozen
partition's full Boolean scope and independent regional bounds justify the
logical deletion argument; empirical absence of a Boolean row is not used to
shrink a calibrated leaf.

The context catalogue's binary predicate is the ORIGINAL whole-region
qualification/refutation status, not an observed individual causal joint Q.
All nonqualifying cells used in these cases are refuted by gain upper<.05 or
harm lower>.10 on the original confidence event. Fact refinement changes the
conditioning context; it does not identify the old aggregate population law.
The minimum is within the declared original grammar/menu and known source
protocol, not universal minimum sensing or individual safety. A new measurement
or missingness protocol needs independent calibration; merely restoring a
retrospectively hidden bit does not supply such a transfer result.

The counterfactual-harm source case is kept ANALYTICAL in the finite-model
artifact: equal p0=.4,p1=.6, harms0/.4; one-arm-only menu impossible, paired
type capable. No physically qualified paired-only region is asserted. Current
D/C one-arm evidence does not expose both terminal alternatives for a native
repertoire-failure witness. The typed offline repertoire output is tested with
explicit analytical fixtures, not fabricated physical endpoints.

## Trace hashes, regional supports and countermodels

| Task | Parent | Original native path | Original gzip SHA256 | Storage link |
|---|---|---|---|---|
| PickCube-v1 | ad552a48fa35584b62fda307bae5bd3d4b8c6327c7be971ac2a6c9380e0fe076 | results/dsre-evidence-aware/20261117-prospective/physics/PickCube-v1/calibration/56/randomized_assigned.json.gz | 8c44fcec93f5a805e216413d11b5626735689cf11af1181c30e4c78c6fc8ceb3 | original gzip exists |
| PickCube-v1 | 450b48bf2683238ea3b9c843cb57d5a54c6aee2906218792df3c38e9eb9285c0 | results/dsre-evidence-aware/20261117-prospective/physics/PickCube-v1/calibration/881/randomized_assigned.json.gz | 28f385c2f9e4e751cdd92a2835a16b2ece77801e01014b255ff6b1d76b3e9100 | original gzip exists |
| PushCube-v1 | 686fc364a9f55bb6e80073f698591a7186a562e8ecfc129cb9829b17a0153ad4 | results/dsre-evidence-aware/20261118-final-science/physics/calibration/475/assigned.json.gz | bbcf9bd253c33000ddaed0d6c07ed5de6f163fcf7d0241ab5c9093c2eed7e2bb | exact original gzip linked through .xz/.archive.json reconstruction |
| PushCube-v1 | 3e4b6a86522fc5161c04d83c2126def7e098051ab6b2bdcbda608feb5e45b21a | results/dsre-evidence-aware/20261118-final-science/physics/discovery/38/assigned.json.gz | d416e895acb15c5981e8bdd6fab329d00507b3583bcce96d3f38727d3ffbaf7a | exact original gzip linked through .xz/.archive.json reconstruction |


Every original-gzip hash is verified directly or through exact archive
reconstruction and was already covered by the original sealed-source audit.
The new raw-source bundle contains the consumed source records and these native
branches with byte hashes. It does not replace the complete original physics
archive. Literal-removal countermodels are source-confidence-compatible
ANALYTICAL distributions, not new native rollouts. Whole-cell calibration
support, every bound and source/controller/population scope remain attached.

The independent numerical/source revalidation of the old evidence still gives
Pick 227/256 with 84 rescues and Push 253/256 with 126, equal to the strong matched
policies. Those are historical outcomes, not the performance of the new ERR
planner. The old insertion failures and acquisition equivalences remain intact.
