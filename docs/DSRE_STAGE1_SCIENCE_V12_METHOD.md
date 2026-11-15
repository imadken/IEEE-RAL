# DSRE v1.2: measurement-robust observable evidence

This research extension answers the original question: what is the smallest
observable evidence sufficient to justify a fixed recovery intervention relative
to measured alternative-action outcomes? It adds an uncertainty adapter around
the unchanged finite-reference DSRE solver. It introduces no controller,
feature threshold, optimizer, learned perception model or population-risk theorem.
The six-page and full-length manuscripts are preserved byte-for-byte.

## Registration and scope

Scientific base: `ae63512bade0a10c43514a81743243f157d287a0`.
Supervisor protocol: `docs/DSRE_RSS2027_SCIENCE_FIRST_SPRINT_20261115.md` at
`fe60f6172625b9b47579995c8ddf3652dada2717`.
Machine-readable preregistration: `config/dsre_science_v12.json`.
Local evidence root: `results/dsre-operational/20261115T195007Z-science-v12`.
Its `study_plan.json` hash is
`7ff595f7d2a8206a7c2deda28fa50b09cca0e42366d235ee9f2719998fe073e2`;
`science_freeze.json` hash is
`afa53462eea29ad4410324c23bf3121c0ebf89772fef4a0425380cc2cce5ba1a`.
Both are written before new physics and freeze all execution inputs/source.

The registered new source varies the existing scripted **approach-target x
offset**, not object position: `0,+.01,+.02,+.03,-.02 m`. The original
`PickFault.offset_x` is used without changing its semantics, prefix timing,
event trigger, two skills or 70-control/3.5-second continuation horizons.
The complete five-condition population is explicitly OOD; old clean bounds do
not transfer even to a marginal condition that was seen historically.

Pilot seeds `13000000..13000004` are shared across the five arms; there are five
independent parents per arm, not 25 independent parents. Each pilot branch is
executed twice to qualify future trajectory/contact/controller parity. Registered
primary seeds `14000000..14000191` have first64 development/characterization
parents and next128 untouched confirmation parents. Every condition of a seed
stays grouped. All192 parents' recommendations are sealed before any primary
continuation; no new fitting or risk calibration is planned. Historical seed
manifests, attempted execution identifiers and previous seals are checked before
collection. Failed qualification arms are retained and unavailable, never replaced.

## Bounded observation set and algebraic soundness

For each supporting first/current frame and each object, hand and goal position,
every coordinate can independently differ from its measured value by at most
`rho`. This is an absolute coordinate-wise box, not a Gaussian standard
deviation or an Euclidean-radius ball. Independence here defines the product
uncertainty set, not a stochastic independence assumption. Shared calibration
errors across objects/frames form subsets and are conservatively covered.
Finger encoder values are assumed exact; this assumption is part of every
reported scope and is not a camera-noise guarantee.

If measured scalar coordinates are `a_hat,b_hat`, then
`a-b in [a_hat-b_hat-2*rho, a_hat-b_hat+2*rho]`. Both operands contribute; using
only `rho` would be unsound. If measured vectors have distance `d_hat`, each
vector error has norm at most `sqrt(3)*rho`, so the triangle and reverse-triangle
inequalities give
`d in [max(0,d_hat-2*sqrt(3)*rho), d_hat+2*sqrt(3)*rho]`.
The same bound applies to cross-frame object displacement because both frames
are bounded jointly. Goal progress is old goal distance minus current goal
distance, enclosed by `[old_lower-current_upper, old_upper-current_lower]`.
This deliberately loses correlations and can return UNKNOWN unnecessarily;
it cannot falsely assert an invariant literal within the declared set.

The existing inequalities are retained exactly:
goal-near `<=.03`, hand/object-near `<=.04`, progress `>=.005`, displacement
`>=.005`, summed absolute finger positions `<=.04`, hand-above `>.03`, and six
signed optional differences `<-.02`/`>.02`. An interval establishes TRUE only
when every enclosed value satisfies the exact strict/non-strict inequality;
FALSE only when every enclosed value violates it. Otherwise it establishes
UNKNOWN. Missing operands also yield UNKNOWN, never FALSE.

For fixed fresh telemetry, these enclosures are nested as `rho` increases.
Once a threshold straddles an enclosure it cannot become invariant at a larger
radius. At `rho=0`, each enclosure collapses to the original arithmetic, so
original Boolean facts and every frozen routing decision are recovered. The
independent oracle uses coordinate-box norm extrema, explicit corners and
sampled joint-frame errors to check the implementation. Sampling is regression
evidence, not the proof of invariance.

Delay has no declared motion envelope. A current-state pose from an earlier
timestamp therefore establishes no current-state-dependent predicate, including
the gripper predicate. The descriptive five-control/250-ms stress uses the actual
recorded prefix packet, only when its time difference is exactly0.25s. These
are two names for one stress, not two independent experiments. No extrapolated
pose or bounded-motion assumption is invented.

## Certificates, witnesses and comparators

Only invariant literals enter the original `ParentIndex` minimum-cardinality
search, with the original two-parent support, reference table and tie breaking.
Every asserted literal is stable under the declared measurement set; the
certificate remains a finite-table claim about measured paired outcomes.
An interval crossing a threshold is an observation-instability witness. Existing
reference-support, conflicting-action and both-actions-fail witnesses remain
available and may overlap. Removing an invariant literal still exposes the
solver's original necessity counterexample when a minimum certificate exists.

Outputs include measured/invariant facts, interval bounds, undecidable facts,
source timestamps, the reference identity, minimum certificate, typed reasons
for abstention, measurement scope and risk-scope eligibility. Eligibility for a
clean source is not a method/action guarantee: the separately sealed original
calibration must also enable that exact policy/action. Altered sensor or OOD
regimes are never marked statistically qualified.

All17 frozen policies are retained. DSRE and robust B7 see identical
invariant/UNKNOWN inputs and remain exactly equivalent, as do their strict-first
risk wrappers. B1 one/two-literal and B5 rules use the same facts. Robust CART1/2
enumerates every Boolean completion of unknown primary inputs and returns an
action only if all completions of the frozen point policy agree on that
nonempty action. This includes every physically reachable completion, potentially
also impossible correlated completions, so conservatism is explicit. Completion
bits are never asserted as measured literals. Its reported known-fact evidence
is a sufficient, generally nonminimum description of the invariant interface;
explanation-length differences are not an optimizer-superiority claim.

The simple margin comparator requires all six/registered-seven inputs invariant,
then uses original point DSRE strict; robust DSRE can instead use any sufficient
invariant subset. Fixed actions use no observation advantage. The12-fact
full-signature method is explicitly an extra-information control, not a matched
seven-fact baseline. Original CART/DSRE results with missing inputs are reported
separately from the completion-aware robust interface. No method inherits a
different method's bound.

## Mechanism and statistical analysis

On each named paired table, action feasibility is the fraction with at least one
successful action. Observation sufficiency is the mass of exact feature-signature
classes with a common successful action. Policy coverage reports adequate,
inadequate and STOP separately. Compute6/7/12-fact and robust ternary signature
versions; exact full-pose signatures are an unattainable-information diagnostic
whose singletons can overfit the hindsight table. Exact ternary-pattern ceilings
describe that interface partition, not validity over overlapping measurement sets
or a deployed certificate. Reference-query compatibility remains conservative
inside the actual unchanged solver.

Repertoire failures and signature ambiguity can occur in the same class; preserve
their overlap. All ceilings are hindsight descriptors on a declared table, not
test guarantees or an additive generalization-error decomposition across tables.

Bounded radii are `0,1,5 mm`; uniform-in-box corruptions have three fixed
replicates per nonzero radius. Every method receives the identical corruptions.
Raw physical pairs are reused for sensor-only experiments. Required recoveries
exclude initially successful preventive opportunities. Parent-group bootstrap
uses4000 draws/seed2026111504, preserving every condition and corruption per
parent; empty denominators are unavailable. CIs are descriptive, without a
multiple-comparison superiority claim. Fixed stopping/resource rules precede all
new outcomes:10 simulation hours,16 session hours,4GiB artifacts, at least one
hour analysis reserve, <=12 parents/15 minutes per checkpoint.
