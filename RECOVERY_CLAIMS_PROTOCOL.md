# Fixed physical experiment protocol

Authoritative config: config/recovery_claims.json. Reviewed base b29d9e5f8873b7fa4c59ffa93ed72cc7379ed6a0.
No manuscript work. Preserve historical roots and user documentation moves.

PickCube uses frozen x-offset .02m and clean control, original event-triggered prefix
and nominal/regrasp actions, 70-step fixed continuation. PushCube uses original .07m
alignment and clean control, fixed transport prefix and nominal/recontact alternatives.
Lift uses existing nominal BASIC OSC controller and 65-step prefix, nominal/conservative
alternative. All reuse existing source hashes and CPU simulator environments. Actual
versions are captured before confirmation; no physics/controller search is permitted.

For each task, hash-sort seeds 100000..109999 with recoveryclaim-v1|task|seed;
first20 development, next100 confirmation. Exact lists are frozen in config.
Both conditions share a parent seed and must remain clustered, not counted independently.
P1 repeats identical prefix and action tape from fresh reset. P2 uses full existing
MuJoCo adapter. P3 measures genuine initially unsuccessful PickCube recoveries; P4 retains
clean starts and possible recovery harm. Initially successful starts never count as new recovery.

N1 native ManiSkill snapshot is a candidate with incomplete hidden provenance, not an
automatic decision-error label. N2 resets controller/gripper memory to fresh-reset values.
N3 physically changes friction after restoring checkpoint. N4 reverses action tape.
N5 reinjects start snapshot after first control. N6 mechanically pairs another parent's
record (no fabricated outcome); N7 removes provenance and must abstain. Negative
control mutations apply only to continuation branches, with real readback/step logs.
Missing channels are explicit. Do not manufacture a decision-disagreement example.

F1 input/provenance and matched budget/predicate/history precede F2/F3. F2 uses original
Tolerances (position1e-5m, angle/qpos1e-4, velocity/observation1e-4, time1e-9s, contacts).
F3 epsilonY=.05 for contrast, costs fixed elapsed simulation seconds, epsilonC=.10s
(two20Hz control periods; fixed independently of confirmation outcomes). One-sided alpha .05,
Bonferroni10 action/domain claims, per-action discordance tolerance .025. Zero-error
required n=ceil(log(.005)/log(.975))=210, exceeding target100. Report actual exact achieved
precision and INSUFFICIENT_EVIDENCE rather than relaxing the tolerance. Seed bootstrap
2000 draws seed20261112 clusters conditions/actions/variants by parent. No iid claim
about multiple conditions from one seed. Finite-seed simulator inference is conditional
on the hash-sampled scene distribution, not policy-general or physical-robot safety.

B0 accepts flags; B1 strict trajectory and input fidelity; B2 finite-horizon continuation
parity and input fidelity; B3 interface conformance only (adapted proxy); B4 all observable
input/admission gates (adapted proxy); M F1 then F2 or precise F3, otherwise qualified
prefix completion where available. Ablations remove decision test, controller-memory
gate, unknown handling, completion separately. Primary comparison: M minus B1/B2 valid
claim admission and invalid admission, paired parent bootstrap. All share identical
physically executed evidence; report the cost of obtaining reference data separately
from cheap-route use and fallback. Population decision support and local executable
support are distinct certificate fields. Unresolved effect sign remains unresolved.

Execute20 development then100 confirmation seeds/task, checkpoint per parent, no seed
replacement. If setup unqualified continue other engines. If fewer30 qualified failed
starts, C4 generality/power is unmet, but finish all F1/F2/F3 controls. Strong-baseline
parity is a negative result, not a reason to invent another method. Max12h wall/20CPUh,
zeroGPU,1GB new downloads,6GB artifacts; one bounded foreground worker, reserve30min.
