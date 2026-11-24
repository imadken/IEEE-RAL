# RPD fixed physical feasibility pilot: actual outcomes

19 November 2026. **Verdict: SOURCE_NOT_QUALIFIED.** Both native workers
terminated with exit139 (SIGSEGV convention) on the39th planned branch of
parent0. Each returned38 complete native traces; neither reached a neutral
hold. The source-failure stop rule was applied to both families. The original
ten-parent lists remain unchanged; these are incomplete pilots, not smaller
completed cohorts. No source repair, resumed physics or seed replacement followed.

## Exact attempted, returned and missing counts

| Task | Registered parents | Attempted parents | Complete qualified parents | Planned episodes | Started | Returned complete | Interrupted, outcome unknown | Unattempted | Missing terminal labels |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| PickCube-v1 |10|1|0|540|39|38|1|501|502|
| PushCube-v1 |10|1|0|540|39|38|1|501|502|

Across tasks:78 started episodes,76 returned complete traces,2 interrupted
unknown outcomes,1,002 unattempted episodes. All1,004 missing terminal labels
remain missing. Independent parent exposure is one per family, not38; zero
complete qualified parents and zero eligible matched-hold contrasts exist.

The authoritative ledger is `final_audit/summary.json` and its complete
1,080-row `all_registered_rows.jsonl`. The frozen preliminary trace auditor
counts only38 returned files/task and has no worker finalizer after SIGSEGV.
Its `attempted=38`, `failed=0`, `worker_wall_seconds=0` fields are NOT the
campaign counts or resource measurements. The journal-based forensic audit
explicitly supersedes those fields; there was one interrupted attempt/task.
All76 returned complete paths passed the separate sampled geometric allowed-set
checks at all11,400 recorded boundaries. This supplies no contact-force or
continuous-time safety guarantee and does not establish option preservation.

## PickCube-v1: all ten fixed parent slots

| Index | Seed | Parent ID prefix | Started | Complete | Interrupted unknown | Unattempted | Source disposition |
|---:|---:|---|---:|---:|---:|---:|---|
|0|2004000000|`36afc2ba23e79ed6`|39|38|1|15|Native worker failure; parent incomplete|
|1|2004000001|`a8188a7f5e693f92`|0|0|0|54|Not attempted after family source guard|
|2|2004000002|`521ee858718c3d25`|0|0|0|54|Not attempted after family source guard|
|3|2004000003|`c27c4986e4ee0bbf`|0|0|0|54|Not attempted after family source guard|
|4|2004000004|`d897164a529e1561`|0|0|0|54|Not attempted after family source guard|
|5|2004000005|`f1bed2b0ff79b23a`|0|0|0|54|Not attempted after family source guard|
|6|2004000006|`9ce46ba745c18a4b`|0|0|0|54|Not attempted after family source guard|
|7|2004000007|`0a4a00dc6554c484`|0|0|0|54|Not attempted after family source guard|
|8|2004000008|`0f45c5e6e3f66e78`|0|0|0|54|Not attempted after family source guard|
|9|2004000009|`86d805338256bf59`|0|0|0|54|Not attempted after family source guard|

The manifest and canonical row ledger retain the full parent IDs. Returned
prefix, native clock, controller memory and full repeated paths passed for 19 pairs.
This validates those returned traces; it does not qualify the unfinished family.

### Actual terminal outcomes of exposed parent0

Each cell is actual macro-end/common-deadline success for repeat0. Its
paired repeat1 agrees on every returned path. STOP has no macro endpoint.
MISSING means no returned outcome; it does not mean task failure.

| History | Continue @70/@90 | Recover @70/@90 | STOP @90 |
|---|---|---|---|
|empty|1/1|1/1|0|
|micro_lift|1/1|1/1|0|
|release_settle|0/0|1/1|0|
|micro_lift → micro_lift|1/1|1/1|0|
|micro_lift → release_settle|0/0|1/1|0|
|release_settle → micro_lift|0/0|1/1|0|
|release_settle → release_settle|0/0|MISSING|MISSING|
|neutral10|MISSING|MISSING|MISSING|
|neutral20|MISSING|MISSING|MISSING|

@70 denotes70 macro controls after history; absolute post-checkpoint time is
history_delay+70. @90 is the common post-checkpoint deadline. All returned
macro success labels happened to agree at both endpoints; no absorbing
success assumption or early success stop was used.

### Native contact, motion and allowed observations

These are actual evaluator measurements from the continue/repeat0 branch
of the sole exposed parent. They are descriptive and are not matched-time
causal effects or independent population samples. Contact counts refer to
native robot/object manifold points at20Hz; object motion is evaluator-only.
The stricter active-contact audit separately requires native nonpositive point
separation or nonzero solver impulse. Positive-gap zero-impulse manifolds are
proximity-only, despite the legacy robot_object_contact boolean being true.

| History | Manifold ticks | Active-contact ticks | Root active contact | Object displacement (mm) | TCP displacement (mm) | Sampled probe path allowed |
|---|---:|---:|---|---:|---:|---|
|micro_lift|10/10|10/10|True|7.820435|7.822770|True|
|release_settle|10/10|0/10|True|45.322056|5.924698|True|
|micro_lift → micro_lift|20/20|20/20|True|9.875657|9.877804|True|
|micro_lift → release_settle|20/20|10/20|True|44.143674|7.726069|True|
|release_settle → micro_lift|20/20|0/20|True|45.322055|9.405542|True|
|release_settle → release_settle|20/20|0/20|True|45.322055|5.924698|True|

Active contact occurs in some recorded histories; the source-review table
distinguishes active contact, release of existing contact and proximity-only
motion. A nonzero command or object displacement alone does not establish
a diagnostic contact mechanism. No-contact/zero-impulse cases remain visible.
They are neither synthetic truth labels nor a purely analytical example.
However, their difference from neutral waiting is UNKNOWN. All sampled
geometry, including full prefix/suffix and adverse-frame lists, is available
in `independent_trace_audit/case_checks.json`. There is no force/damage,
hardware or continuous-time safety guarantee.

### Option preservation, erasure, creation and sensor information

**K_hold=UNKNOWN; matched K_probe/K_hold contrasts=0 eligible.** Erasure,
creation, loss/preservation of one successful macro, and their frequencies
relative to equal-duration waiting are **NOT ESTIMABLE**, not zero.
Immediate no-probe completion is not a valid substitute for neutral10/20.
All60 planned parent/history matched contrasts per family remain unqualified.

Actual native arm qpos/qvel, FK TCP response and clock were recorded for
every returned probe tick. Their frozen response bins are stored per raw
trace and independently reproduced. Only one root parent was exposed, so
variation of the evaluator-only hidden pose label at fixed root observations
cannot be assessed across parents. No decoder, held-out predictive gain,
information ranking or Shannon-information claim was fitted to this pilot.

## PushCube-v1: all ten fixed parent slots

| Index | Seed | Parent ID prefix | Started | Complete | Interrupted unknown | Unattempted | Source disposition |
|---:|---:|---|---:|---:|---:|---:|---|
|0|2004100000|`1abfd02f49137f01`|39|38|1|15|Native worker failure; parent incomplete|
|1|2004100001|`4d7f99450c95ceef`|0|0|0|54|Not attempted after family source guard|
|2|2004100002|`8d2e778aa469588f`|0|0|0|54|Not attempted after family source guard|
|3|2004100003|`0999ae8192a4c811`|0|0|0|54|Not attempted after family source guard|
|4|2004100004|`27930c1f28d76828`|0|0|0|54|Not attempted after family source guard|
|5|2004100005|`7a1c8a734031e906`|0|0|0|54|Not attempted after family source guard|
|6|2004100006|`3eba92e9aa7ad7df`|0|0|0|54|Not attempted after family source guard|
|7|2004100007|`9cbd3a8f304bf35e`|0|0|0|54|Not attempted after family source guard|
|8|2004100008|`b974a294588a2ef6`|0|0|0|54|Not attempted after family source guard|
|9|2004100009|`07c95462ebf2e897`|0|0|0|54|Not attempted after family source guard|

The manifest and canonical row ledger retain the full parent IDs. Returned
prefix, native clock, controller memory and full repeated paths passed for 19 pairs.
This validates those returned traces; it does not qualify the unfinished family.

### Actual terminal outcomes of exposed parent0

Each cell is actual macro-end/common-deadline success for repeat0. Its
paired repeat1 agrees on every returned path. STOP has no macro endpoint.
MISSING means no returned outcome; it does not mean task failure.

| History | Continue @70/@90 | Recover @70/@90 | STOP @90 |
|---|---|---|---|
|empty|1/1|1/1|0|
|forward_tap|1/1|1/1|0|
|lateral_sweep|1/1|1/1|0|
|forward_tap → forward_tap|1/1|1/1|0|
|forward_tap → lateral_sweep|1/1|1/1|0|
|lateral_sweep → forward_tap|1/1|1/1|0|
|lateral_sweep → lateral_sweep|1/1|MISSING|MISSING|
|neutral10|MISSING|MISSING|MISSING|
|neutral20|MISSING|MISSING|MISSING|

@70 denotes70 macro controls after history; absolute post-checkpoint time is
history_delay+70. @90 is the common post-checkpoint deadline. All returned
macro success labels happened to agree at both endpoints; no absorbing
success assumption or early success stop was used.

### Native contact, motion and allowed observations

These are actual evaluator measurements from the continue/repeat0 branch
of the sole exposed parent. They are descriptive and are not matched-time
causal effects or independent population samples. Contact counts refer to
native robot/object manifold points at20Hz; object motion is evaluator-only.
The stricter active-contact audit separately requires native nonpositive point
separation or nonzero solver impulse. Positive-gap zero-impulse manifolds are
proximity-only, despite the legacy robot_object_contact boolean being true.

| History | Manifold ticks | Active-contact ticks | Root active contact | Object displacement (mm) | TCP displacement (mm) | Sampled probe path allowed |
|---|---:|---:|---|---:|---:|---|
|forward_tap|10/10|3/10|True|8.251737|8.211689|True|
|lateral_sweep|10/10|0/10|True|3.529297|7.703895|True|
|forward_tap → forward_tap|20/20|7/20|True|16.000218|15.956235|True|
|forward_tap → lateral_sweep|20/20|12/20|True|8.287009|11.090407|True|
|lateral_sweep → forward_tap|20/20|3/20|True|8.393367|11.250972|True|
|lateral_sweep → lateral_sweep|20/20|0/20|True|3.529281|15.523314|True|

Active contact occurs in some recorded histories; the source-review table
distinguishes active contact, release of existing contact and proximity-only
motion. A nonzero command or object displacement alone does not establish
a diagnostic contact mechanism. No-contact/zero-impulse cases remain visible.
They are neither synthetic truth labels nor a purely analytical example.
However, their difference from neutral waiting is UNKNOWN. All sampled
geometry, including full prefix/suffix and adverse-frame lists, is available
in `independent_trace_audit/case_checks.json`. There is no force/damage,
hardware or continuous-time safety guarantee.

### Option preservation, erasure, creation and sensor information

**K_hold=UNKNOWN; matched K_probe/K_hold contrasts=0 eligible.** Erasure,
creation, loss/preservation of one successful macro, and their frequencies
relative to equal-duration waiting are **NOT ESTIMABLE**, not zero.
Immediate no-probe completion is not a valid substitute for neutral10/20.
All60 planned parent/history matched contrasts per family remain unqualified.

Actual native arm qpos/qvel, FK TCP response and clock were recorded for
every returned probe tick. Their frozen response bins are stored per raw
trace and independently reproduced. Only one root parent was exposed, so
variation of the evaluator-only hidden pose label at fixed root observations
cannot be assessed across parents. No decoder, held-out predictive gain,
information ranking or Shannon-information claim was fitted to this pilot.

## Unfavorable and unresolved findings

PickCube's release-containing histories can fail fixed continue while the
observed recover branch succeeds. This is an actual *history-conditional*
terminal distinction for one parent, not full option erasure; the uncollected
matched holds prevent attributing it to contact beyond elapsed time. PushCube
returned continue/recover branches succeed for the same exposed parent.
Repeated release/lateral-sweep recover and STOP, all neutral controls, and
all nine later parents per task are unobserved. Missing labels are not filled.

Both native processes failed after38 complete episodes on their39th start.
No final trace, native backtrace or exact intra-episode stage was returned.
The failed planned row is recover/repeat0 after two release_settle probes
(Pick) or two lateral_sweep probes (Push). It is not known whether its
checkpoint, probes or macro were reached. The repeated episode/environment
lifetime topology is a possible engineering contributor, not an established
root cause. The raw worker callsgc.collect only after a full parent; no
process-isolation repair or extra diagnostic physics was authorized by the
sealed failure path and none was run.

## Resource accounting

| Task | Returned native controls | Sum measured completed episode wall(s) | Conservative whole-worker upper bound(s) | Raw/journal bytes |
|---|---:|---:|---:|---:|
|PickCube-v1|5890|95.007588|471.917064|7517324|
|PushCube-v1|5434|63.194694|438.917064|5617937|

The hard cap was10,800worker seconds/task and3GiB compressed/task. Bounds
start at the console's filesystem birth before worker launch and end at a
post-exit observation; they conservatively include time after process death.
They are NOT precise runtime measurements. Native finalizers did not run,
so exact total worker CPU/wall time and peak memory are unavailable. The
completed-episode wall sums are measured. The unreturned39th episode has
unknown native control count between0 and155(Pick)/143(Push). Source failure,
rather than a budget ceiling, stopped collection. No full Stage2 parent was
collected; every original discovery/calibration/test reservation is untouched.

## Reproduction and evidence

The SHA-256 raw/canonical manifests, original prephysics source/seed seal,
both native-exit receipts, all1,080 canonical planned rows, source review,
test receipts and compact archive are in `research/rpd_physical_pilot_20261119/`.
Reproduction is offline only; do not restart a native worker after this guard.

```bash
export UV_CACHE_DIR=/tmp/dsre-evidence-uv PYTHONPATH=src:scripts:.
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
uv run --no-sync python scripts/rpd_pilot_reproduce.py --verify
uv run --no-sync python scripts/rpd_pilot_reproduce.py --audit --output /tmp/rpd-pilot-review
uv run --no-sync pytest -q tests
```

Use a fresh audit directory. The local Git commit anchors the package.
No manuscript, historical seal, native source or user change is modified.
