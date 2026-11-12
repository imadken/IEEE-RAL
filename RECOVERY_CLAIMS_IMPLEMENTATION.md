# RecoveryClaim implementation and reproduction

The common API is src/dual_rec/contracts/claims.py, extending the existing contracts
package. Claim, MatchedEvidence and AlarmEvidence validate finite execution, matched
alternative and online-protocol records respectively. certify, matched_effect and
certify_alarm expose their distinct obligations. The latter reuses the previous
causal/annotation/calibration checker; it does not claim detector performance.

A certificate records SUPPORTED, REFUTED_CONTRACT or INSUFFICIENT_EVIDENCE, the first
observed violated obligation, F1/F2/F3, achieved discordance precision, missing fields
and whether a qualified prefix replaced the candidate. Candidate and selected
terminal outcomes remain separate. Missing model/history cannot be repaired merely
by observing equal successes. Known unobserved solver caches are retained as F2 scope limitations; missing model/controller/reference-controller provenance remains UNKNOWN. Exact controller/RNG hashes are compared before F3.
F3 is statistical and conditional on the registered parent distribution; it does not
identify physical-robot safety or general policy behavior. A supported local executable
claim is distinct from a supported population replay equivalence or positive effect sign.

Run a bundle and verify it in a separate process:

```bash
PYTHONPATH=src uv run --no-sync python -m dual_rec.contracts.claims \
  --bundle BUNDLE.json --output CERTIFICATE.json
PYTHONPATH=src uv run --no-sync python -m dual_rec.contracts.claims \
  --bundle BUNDLE.json --output CERTIFICATE.json --verify
```

Verification checks the bundle hash, recomputed certificate, raw trace hash, action
array, observed success/time sequence and any selected completion outcome sequence.
Raw paths must remain inside the evidence root. No minimum-unsatisfiable-core or
universal truth claim is made. Hashes preserve provenance, not authenticity of an
arbitrary untrusted simulator. Source control, recording code and model construction
are explicit trusted assumptions. The independent numerical auditor uses separate
code and SciPy confidence bounds, and reads physical trajectories without importing
the compared certificate/scoring implementation.

scripts/recovery_claims_physics.py reuses World, the existing replay adapters, PickCube
initial controller/event trigger, nominal/regrasp actions and fixed Lift/Push alternatives.
It creates new real continuations and saves state, contacts, integration snapshots,
exposed controls, checkpoint controller memory, executed actions, outcomes and timing.
Unexposed PhysX caches remain unexposed. The recording adapters make no policy decisions
from evaluation labels. Simulator control uses the original privileged scripted
engineering controllers, not a new learned/deployable recovery policy.

scripts/recovery_claims_batch.py executes registered seeds sequentially in fresh
processes; completed checkpoints resume by their exact IDs. A simulator segmentation
fault in a long-lived development process motivated per-parent/condition isolation.
Failures, retries and original outputs are retained. No seed is replaced.

```bash
PYTHONDONTWRITEBYTECODE=1 UV_CACHE_DIR=/tmp/dual-rec-uv-cache \
uv run --no-sync python scripts/reboot_overnight_worker.py --root RUN \
 --name UNIQUE_JOB --timeout 32000 -- uv run --no-sync python \
 scripts/recovery_claims_batch.py --root RUN --split confirmation
```

RUN must be unsealed with its original registration and fresh/resumable accounting.
Do not edit sealed historical evidence. The outer worker enforces shared locking,
wall/CPU/artifact limits and CPU-only execution. Parent attempts have a 300s timeout
and one exact-seed retry; a repeatedly blocked parent remains an explicit missing cell.
Do not reuse an initial wall clock for a later separately authorized campaign.

After physics completes, recovery_claims_analyze.py emits tables A–F, ablations,
per-execution bundles/certificates, source hashes and parent-bootstrap effects.
recovery_claims_audit.py independently checks physical outcomes, state gates, paired
counts/effects, precision and certificate statuses. The evaluator package contains
frozen mixed bundles and raw evidence; its answer key is separate. No independent
human evaluation is claimed. No manuscript or publication files are generated.

Maintained checks use `uv run --no-sync pytest -q tests` and Ruff over `src scripts tests`. Bare repository discovery includes vendored historical environments and is not a passing maintained-suite command. Whole-tree Ruff also includes preserved historical ad hoc scripts; those findings are retained without altering sealed evidence.
