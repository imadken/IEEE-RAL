# DSRE: recovered-runtime physical qualification

Evidence root: `results/dsre-operational/20261116T130334Z-runtime-recovery` (R).
The process-only ICD correction is described in
[the native diagnosis](DSRE_SAPIEN_NATIVE_CRASH_DIAGNOSIS.md).

`R/qualification_registration.json` preselects previously inspected parents
13000000, 13000001 and 13000002 from the November 15 v1.2 pilot. Each uses all
five original approach offsets and both original 70-control actions. These
historical parents include nonempty contacts and both terminal classes. Parent
13000000 additionally has two full fresh-process repeats in distinct preserved
namespaces; they add no independent calibration or test support.

Independent comparison uses `scripts/dsre_runtime_parity.py`, which imports only
the earlier pure raw-source auditor. It never imports the production selector
or simulator. It checks full prefix and continuation time series at the original
tolerances, action ordering/equations, qpos/qvel, object/TCP/goal observations,
time, exact contact lists, model provenance/readbacks, canonical controller and
interpolation/drive memory, saved simulator/batched RNG aliases and Torch RNG,
and terminal success. No native snapshot is substituted for full reset/prefix
reconstruction. A first disagreement is saved and blocks collection.

Historical packets contain the saved simulator/batched and Torch RNG channels.
They do not separately store global Python/NumPy RNG snapshots; the original
deterministic seed setup is unchanged. This scope is explicit and no missing
historical field is manufactured. Full physical trajectory agreement must also
hold; final-success agreement alone is insufficient.

Per-parent reports separate model, contacts, controller, saved RNG, observations,
trajectory and terminal-success verdicts. The final authority is
`R/qualification_audit.json`, written only after all three parents and both
additional repetitions pass. `R/source_qualification_seal.json` then binds
that audit, the process configuration, source freeze and old failure seal.

Qualification **passes**. All three distinct inspected parents and both
additional fresh-process repetitions match: 25 checkpoints, 50 continuations
and 3,500 future states, including exact nonempty-contact and both terminal
classes. Each model/contact/controller/saved-RNG/observation/trajectory/terminal
category passes independently. The process/source seal was written before any
fresh cohort outcome. This authorizes the original calibration, not a risk claim.

A second independent endpoint checker recomputes the unchanged task predicate
from saved float32 cube/goal positions and the seven arm-joint velocities:
distance at most 0.025 m and maximum absolute arm velocity at most 0.2 rad/s.
Finger velocity is excluded, as in the original task. All 25 initial flags and
50 qualification terminals agree (38 successful and 12 unsuccessful terminals).
The checker, its boundary tests and installed predicate definitions were hashed
before test collection. This corroborates the recorded labels without importing
the simulator or changing the outcome definition; it does not add experimental
parents.
