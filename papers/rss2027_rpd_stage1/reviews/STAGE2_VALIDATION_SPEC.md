# Fixed simulation-only validation specification

Status: **author-review proposal, not executed or experimentally qualified**.
The main manuscript contains the critical scientific mechanics. This operational
receipt does not defer any required Stage 1 method to a supplement. The canonical
parameter/seed receipt is `PROPOSED_PROTOCOL_AND_NUMERICS.json`; no output in it is
a robot observation. No physics is authorized by this paper-preparation task.

## Prerequisite and ordering

Use the pinned ManiSkill/SAPIEN/NumPy/Torch versions and native assets, never an
in-place source upgrade. Use one CPU worker in fresh processes. Source hashes and
all 588 proposed IDs are recorded in the protocol receipt. Hash uniqueness is
checked; statistical independence and stationarity remain declared sampling
assumptions, not proven by seed uniqueness.

1. Implement only the specified initialization/monitoring adapter around native
   `pd_ee_pose`. No blocked motion-planner prefix, welded peg, new sensor or trained
   robot controller is required. It is not implemented or qualified in this run.
2. Screen all 12 fixed `qual` IDs without replacement. Use nominal peg-in-TCP
   transform for both qualification-only routines, and `a0` as direct control.
   Evaluate six probe/hold/recovery branches plus direct; repeat all seven for the
   first two eligible IDs. At most 12 screening +98 terminal source episodes,
   three worker-hours, 60 seconds per episode including initialization. A branch
   source failure is not a failed goal; constraint violation is a measured outcome.
3. Source qualification needs at least eight eligible roots, complete finite
   records, genuine predecision contact, correct whitelisted observations, native
   commands/clock, no implicit reset and declared replay tolerances. It does not
   require any erasure, predictor accuracy, success rate or policy advantage.
4. Screen 64 fixed `discovery` IDs. Fit only the root grasp estimator from those
   observed root features and evaluator-labeled grasp transforms. Freeze it before
   recovery outcomes. Compute and store each parent's estimate once from its
   screened root X; inject this same recorded calibration value after each matched
   fresh-prefix regeneration. Do not recompute it from a probe response.
5. Collect all eight terminal branches for each eligible discovery parent: two
   macros after hold/preload/dither and both macros directly at the full deadline.
   These fixed-policy labels also contain probe responses. No separate 192-episode
   response-collection pass is needed after the root-frozen estimator correction.
   Fit the shared finite observation/outcome model and freeze all policy code,
   decoders, normalization, codebooks, risk gate and ties. No calibration of physical
   recovery probabilities is asserted from this discovery fit.
6. Repeat all eight final-policy branches for the first two eligible discovery
   IDs (16 additional episodes); compare root/trajectory fingerprints and flags.
   Source validity is required, not positive goal/erasure or relative performance.
7. Screen the complete fixed 512-ID `confirmation` list before opening any terminal
   comparison. Disposition is KNOWN_ELIGIBLE, KNOWN_INELIGIBLE, or ELIGIBILITY_UNKNOWN.
   UNKNOWN cannot be silently excluded from an unconditional eligible-population
   claim. Report descriptive/source-evaluable results if full target identification
   remains unresolved; do not relabel a new population as the registered one.
8. Run the fixed confirmation order: ascending ID; hold/preload/dither; `a0,a1`;
   then the frozen shared direct policy. Every regeneration is checked against its
   screened root. A source-invalid branch is missing, never a synthesized success
   or failure. Continue logging goals and violations after the first goal through
   the declared deadline; STOP is scored at its actual prefix.

Native time limits must be 200 control ticks in both wrappers. Setup is 30 ticks,
primary remainder 80, doubled remainder160, so complete episodes use110/190 ticks.
Do not reset the elapsed counter at the checkpoint. Every 20 Hz command is applied
for five 100 Hz physics substeps. Monitor each substep; 26 consecutive inclusive
samples span the required .25-second dwell. Dither's last command is literally the
stored equilibrium. Per-parent feedback parameters and native memory remain fixed.

## Physical defaults and information boundary

See manuscript Section IV for exact world/hole/TCP transforms, native geometry,
fault mixture, initialization joint vector, pose interpolation and targets. The
3 mm square per-side clearance is a source fact; perturbation scales, 4/8-second
budgets, force/velocity/slip limits and strengthened stable goal are proposed design
choices, not validated robot tolerances. Native force/impulse and true peg/grasp
geometry are evaluator-only. Online fields are the stated 28-dimensional X and
230-dimensional response, not native state_dict wholesale. Public CAD/fixture
calibration does not include the actual unknown grasp transform.

The primary goal is held stable **mid-depth** insertion, not released assembly.
The source stock head-only flag remains a secondary metric. Record both goal-only
K and goal-and-recovery-compliant K^C; the primary joint event checks probe/hold
compliance and must not be renamed a general safe-recoverability guarantee.

The parent fingerprint includes body/joint poses and velocities, robot drives,
commanded equilibrium, root X and stored estimator, RNG/source configuration,
absolute simulation/controller counters, task flag and dwell history. Prefix
regeneration must not be replaced by unqualified get/set-state calls. Root
positions/angular differences must be below1e-5 m/1e-4 rad; source command/clock
records match exactly. Changed eligibility predicates or missing controller fields
make a branch invalid. Small tolerances are a source assumption/guard, not a proof
that every possible physical outcome is invariant under perturbation.

## Falsifiable questions and analyses

| Question | Fixed design / statistic | What an adverse or null result means |
|---|---|---|
| H1 material erasure | q_IG>=.10 under probe-only frozen IG; J=goal-set loss times probe/hold compliance | Narrow upper bound below.10 limits prevalence in this distribution; it does not establish all diagnosis harmless |
| H1 population signal | Positive D0 and DH means using discovery-frozen predictors | Uninformative probing does not establish diagnosis-induced useful sensing merely because it damages recovery |
| Same-case average signal, secondary | Full-parent J*D0 and J*DH; no refit or erased-only denominator | Broad/negative intervals leave co-occurrence unresolved even when H1's two properties hold |
| H2 completion | Paired RPD-minus-IG improvement>=.05 plus violation increase<.02 | No margin means no asserted benefit; H2 is evaluated even if H1 fails |
| Strong task-aware control | Shared-model Bayesian coverage and full-objective response-wise enumeration | Equality is expected; no unique optimizer claim |
| Information value | Response-blind versus response-aware action selection on the same fixed macros | Separates catalogue-choice benefit from the probe's physical effect |
| Deadline dependence | Same six branches at8 s on64 pre-hash-selected confirmation IDs | Recovery after extra time narrows claim to original budget |
| Repertoire dependence | One pre-existing extra skill on the same three branches, only if qualified before confirmation | Currently unavailable; do not invent a controller after failures or claim robustness without it |

H1 returns abstention when no probe passes its modeled pre-recovery risk gate.
J and score contributions then equal zero by the policy estimand, not by terminal
label imputation; all eligible parents remain included. H2's distinct deployment
wrapper can choose direct recovery at common-action roots. Report both execution
and abstention rates; H1 is not the executed H2 wrapper's unconditional erasure rate.

Each primary hypothesis has alpha .025; its component conditions form a conjunction.
CP binary and empirical Bernstein score claims require independently sampled
eligible parents conditional on the frozen discovery model. Profile-based paired
H2 coverage is asymptotic, including its rare-discordance switching rule; exact CP
differences remain a sensitivity for all complete samples, and primary fallback
when fewer than30 pairs disagree or labels are missing. Weighted secondary score
bounds use .0125 each; no exact joint guarantee over all reported exploratory
strata is claimed. For n<2 the score/H1 decision is UNRESOLVED.

Known-eligible missing outcomes remain in the full registered denominator. Use the
paper's worst-case CP difference and bounded-variance score envelopes. Never call
an outcome-dependent completed prefix an independent fixed sample. UNKNOWN root
eligibility is a distinct source-identification limit, not binary outcome missingness.

## Cost and stopping

| Source work, assuming all candidates eligible | Episodes / terminal branches |
|---|---:|
| Qualification screening |12 source-only |
| Qualification branches and repeats |up to98 terminal |
| Discovery + confirmation screening |576 source-only |
| Discovery terminal labels, 64 x8 |512 terminal |
| Confirmation matched labels, 512 x6 |3,072 terminal |
| Confirmation shared direct control |up to512 terminal |
| Final-estimator parity before confirmation |16 terminal |
| Base terminal comparisons (512+3072+512) |4,096 |
| Maximum base source episodes including all above |4,798 |
| Doubled deadline on64 fixed candidates |up to384 additional terminal |
| Extra pre-existing skill, conditional/unavailable |up to192 additional terminal |
| Maximum if both sensitivities qualified |5,374 source episodes |

STOP may require no new terminal rollout because the prefix completion flag is
already recorded. The values are prospective upper accounting, not measured cost.
The28-worker-hour proposal allocates3 to qualification,20 to primary and5 to
sensitivities. Primary full work (4,096+576+16=4,688 episodes) requires about15.36
worker-seconds per episode on average within20 hours. This is a feasibility
requirement to assess from source timings, not an estimate established by cubes.
There is no promise of full completion within the ceiling. Finish/mark missing an
atomic parent and retain all unfinished fixed IDs. A failed runtime qualification
or vacuous worst-case interval is a legitimate unresolved outcome, not permission
to lower margins, replace seeds, or broaden tasks. No current physics is authorized.

Keep newly generated source evidence below2 GiB by recording fixed scalar/vector
telemetry and compact lossless traces, not duplicate rendered videos or meshes.
If the resource cap prevents the fixed experiment, the author must report actual
counts and missingness rather than claim the proposed sample was achieved.
