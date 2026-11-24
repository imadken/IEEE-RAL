# RPD physical feasibility pilot: frozen method and neutral-hold amendment

19 November 2026. This document is written before new physics and is frozen by
`research/rpd_physical_pilot_20261119/prephysics_seal.json`. The two verbatim user
attachments in that directory's `supervisor/` are the source instructions. The
user authorizes these two technical pilots only, superseding the old protocol's
inactive status for its ten technical parents per family. The original Stage 2
protocol, reservation, source, evidence and manuscripts remain untouched.

## Scope and fixed source

Use local parent commit `b00c441ffa88924c157dda51b8e4deff3934566b`, branch
`research/rpd-minimal-physical-pilot-20261119`. There are exactly ten reserved
nominal independent parents per task; no replacement, fault edits, new controllers,
seed selection or simulator-mode shopping. Source/version hashes are recorded in
`source_preflight.json`; all code, seed manifests, both attachments and this method
are SHA-256 sealed before any new environment construction. The seed audit checks
retained historical metadata and path identities, excluding only the original RPD
reservation as evidence of previous collection. No terminal label is used to choose
parents. Discovery/calibration/test reservations remain inactive.

Pinned source: ManiSkill3.0.1, SAPIEN3.0.3, Torch2.5.1+cpu, NumPy1.26.4,
Pydantic2.14.3. Native Panda CPU `state_dict`, render backend none,
`pd_ee_delta_pos`, 20Hz control boundaries, wrapper horizon200. The controller
uses normalized delta position with native feedback at each tick; zero delta
holds measured-current EE position without freezing physics. The original fixed
macros internally use native object/goal state and are simulation-only; this
privilege is disclosed and identical in all branches.

| Task | Registered checkpoint | Frozen probe1 | Frozen probe2 |
|---|---|---|---|
| PickCube-v1 | nominal native transport prefix65:20 approach,25 descend,15 close,5 transport | micro_lift:4*(0,0,.025,-1),6*(0,0,0,-1) | release_settle:10*(0,0,0,+1) |
| PushCube-v1 | nominal prefix53:20 approach,25 descend,8 push | forward_tap:4*(.05,0,0,-1),6*(0,0,0,-1) | lateral_sweep:4*(0,.05,0,-1),6*(0,0,0,-1) |

Checkpoint requires registered clock, previously reached native robot/object
contact, finite telemetry, and native success false. Already-complete prefixes
are recorded as ineligible, without a failed terminal label or replacement.
A failed source, prefix, repeat, controller or clock guard stops that family;
unattempted parents remain missing, not a smaller completed cohort. No insertion
flow is involved.

## Registered addition: matched time control

Add neutral10 and neutral20 histories at the *same original checkpoint*, with
exactly10 or20 repeated `(0,0,0,-1)` actuator vectors. Both registered prefixes end
with closed-gripper command-1. Native arm/gripper feedback, gravity, contact and
elapsed control clock continue. This control removes neither contact nor physical
state evolution; it isolates the extra effect of the registered probe commands
from equal-duration waiting. It does not isolate contact mediation from all other
probe mechanics. No equal-effort control or alternative menu is added.

For every parent: original seven histories (empty, two length1, four length2),
plus neutral10 and neutral20; each followed independently by continue, recover,
STOP, twice. Total54 branches/parent,540/task,1080maximum. These branches share
parents and are correlated. Every branch is a new evaluator-only native episode
with original seed reset then complete original prefix. First branch supplies
the canonical prefix tape; later branches replay that tape and check all frames,
full controller memory and native task/configuration. No within-history reset,
restore, teleport, state injection or return to an earlier probe state occurs.
The counterfactual alternatives never enter a deployed diagnostic policy.

## Timetable and outcome semantics

At checkpoint control0, execute0/10/20 history controls. Start the original
`dsre_paper_physics.action_for` macro from the actual post-history state and TCP,
using j=0..69. Record native task success immediately at history_delay+70, then
pad with zero Cartesian delta and the last actual gripper command until common
control90. Thus pad20/10/0 controls. STOP has no recovery macro and holds from
history completion to90; its actual terminal outcome is measured. Maximum native
absolute endpoints155(Pick) and143(Push), below wrapper200. Native success is
not absorbing: record both actual endpoints and all intermediate task flags.

The first registered empty/continue/repeat0 branch measures native startup and
runtime, remains in the planned540, and is not an extra throughput experiment.
Hard cap10800worker seconds/task, including failed episodes; compressed artifact
cap3GiB/task. Before later parents reserve54 times the largest measured episode
wall cost with20%margin plus10seconds. Stop at parent boundaries if forecast
cannot fit. A surprising hard cap takes precedence over finishing a parent;
partial traces and exact incomplete counts remain. Sealed per-row and per-parent
files permit clean resume without silently repeating interrupted attempts.

## Native measurements and source qualification

Record all20Hz control commands and boundary states from reset through prefix,
probe, macro and padding. Allowed diagnostic packets contain ONLY seven arm qpos,
seven arm qvel, FK TCP xyz and native clock. Frozen response encoding is5mm TCP
bins, .01rad arm-motion bins and .1rad/s peak arm-speed bins. Native object poses,
contacts/contact points, object motion, gripper joints, task flags and future
success are evaluator-only. Contact point impulses are native solver diagnostics,
not a force sensor or a force/damage safety guarantee.

Repeat tolerances: object position<=1e-5m, orientation/qpos<=1e-4rad,
velocity/observation<=1e-4, time<=1e-9s; exact contacts/task flags, exact canonical
controller memory. Compare full prefix, repeated full histories and physical
configuration. Missing or nonfinite observations are source failures, not false
predicates. No old DSRE success calibration transfers.

At each recorded boundary, separately evaluate arm URDF limits with1e-6rad
allowance; TCPabs(x/y)<=.60m,z in[.015,.50]; objectabs(x/y)<=.45m,z in
[cube_half_size-.002,.50]. Report full-path and post-checkpoint compliance and
violations. Post-probe violations are adverse outcomes, never discarded as
attrition. These checks establish sampled geometric allowance only.

## Fixed estimands and verdict

For a source-qualified parent/history, K consists of continue/recover macros with
actual native success at common90. Both repeats and the paired complete outcomes
must agree. Any missing/unstable source row gives UNKNOWN, never the empty set.
Compare each10/20-control probe history with neutral10/neutral20 respectively.
Erasure=K_hold nonempty and K_probe empty; creation is the converse. Also report
lost/gained individual macro membership and no-probe K, both endpoints, STOP,
contact and physical movement vs hold. Native actuator commands alone do not
establish a contact mechanism. Describe no-contact and no-measured-effect strata.
A mechanistic contact response requires actual native contact points during the
probe and either object divergence from matched hold>1e-5m or a changed native
contact trace. No favorable recovery effect is required for source eligibility.

PHYSICAL_MECHANISM_OBSERVED requires a qualified, reproducible, contact-associated
option erasure beyond matched waiting with sampled allowance through probe and
both probe/hold macro paths. Otherwise qualified complete/contact-acting pilots
may give QUALIFIED_NO_ERASURE_IN_PILOT; no acting contact mechanism gives
PROBE_NOT_MECHANISTIC; any source guard failure/incomplete qualification is
SOURCE_NOT_QUALIFIED. All observed adverse examples remain visible regardless.

Information analysis is descriptive response distinctness and evaluator-only
root pose-cell variation within frozen root proprioceptive signatures. Do not
train a decoder on these ten parents, claim held-out information gain, rank probes
after outcomes, infer population prevalence or claim algorithm novelty. Fixed
strong/POMDP and consensus equivalence from the original audit remains intact.

The independent auditor reads canonical native traces without constructing a
simulator, independently reconstructs command schedules, terminal endpoints,
geometry, response bins, replay checks, option sets and matched erasure contrasts.
Offline maintained tests and archive/hash verification follow collection.
The separate outcomes/gate documents will report all actual counts and the
feasible paired-parent future study, not launch the superseded Stage 2 campaign.
