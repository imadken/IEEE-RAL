# Separate post-freeze source investigation

Verdict: **NOT_QUALIFIED — NOMINAL_COMPLIANT_INSERTION_GATE_FAILED**.
This does not prove no controller can work. It documents the inspected fixed
source control and stops before a postfailure hold pair or new qualification.

Paper freeze:e644addb5848545e8c114974a62e52eb7a080682.
Prospective development protocol/source/jobs:
e65133d73454bcb42ff820bba52e43a4883df3a1, committed before either attempt.
One new development parent, geometry seed702360274, two fresh-process repeats.
Zero injected initial alignment fault; all native simulation settings, controller,
goal and sampled constraints remain fixed. The inherited postfailure screen was
also measured aseligible, but this development control is not a qualification
parent, independently sampled population or H1/H2 label. No favorable seed search.

Both complete episodes ran550physics samples/110commands. Both failed stable
insertion and whole-postroot compliance. Traces are byte-identical and root
controller/drive/clock state matches exactly. No timeout, missing result or native
crash occurred. Native source replay is reproducible at this control; that is not
source qualification or a general stability claim.

The independent verifier checks1100samples and220commands, stable goal dwell,
pose/slip/constraint flags, force from native contact impulses divided by.01s,
whitelisted online features, cubic command targets and absolute clock. In each
run, peg-fixture force first exceeded its20.444332N envelope at absolute substep187
(.37s after the checkpoint); rotation slip at193, TCP residual at196 and
translation slip at201. Peaks:53.757840N,35.673070mm TCP residual,
133.680758mm translation slip and.411594rad rotation slip. Joint limits, joint
speed and nonfinger-contact checks never violated. These observations localize
failure; they do not establish a unique cause or justify relaxed constraints.
The final peg-head coordinate was(-.09742136,.00731093,-.13308104)m in the hole
frame, failing the actual goal rather than a missing/imputed result.

Two failed runs at one technical parent do not estimate population risk. The
nominal a1 branch, neutral-hold recovery pair, both probe comparisons,12NEW-root
qualification and24-parent exploration were not run. Their outcomes and recovery
sets are UNKNOWN, not empty or failed. No full-erasure observation or diagnostic
information finding is inferred from this control.1024confirmation parents are
untouched. The paper remains unchanged; no candidate addendum is supported.

Source worker time24.807748505s in total(.006891041h), artifact size recorded in
resource_ledger.json, below the600s/100MiB bounded development gate. The1–3day
optional budget is a ceiling, not a reason to keep running after a reproduced
nominal source blocker. No physics-source upgrades, gain/deadline/envelope
relaxations or replacement seeds were made. The source baseline's49/49violations
and first-failure census are retained separately, not pooled with this regime.

Exact next engineering action: inspect the measured grasp/drive/contact evolution
around substeps187–201, and identify a source/controller explanation before any
new source version. Demonstrate compliant nominal insertion, then postfailure
hold recovery, then preregister12new qualification roots with>=8eligible and
>=6hold-recoverable. No confirmation campaign is authorized by this handoff.

Offline audit from repository root (no new physics):
```
UV_CACHE_DIR=/tmp/rss-rpd-uv uv run --offline --no-sync python research/rpd_stage1_final_handoff_20261121/reproduce/audit_development.py --evidence research/rpd_stage1_final_handoff_20261121/experiments/development --output /tmp/rpd-dev-audit-new.json
```
Native source commands are the sealed nominal_worker.py --job repeat0/job.json
and repeat1/job.json commands under this branch/worktree's locked Python3.12
environment. They replay physics and are NOT part of offline reproduction.
