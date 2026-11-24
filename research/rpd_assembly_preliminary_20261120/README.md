# RPD assembly preliminary execution

Authority: `inputs/CODEX_ASSEMBLY_PRELIMINARY_PROTOCOL.md` and the user's explicit
continuation request. Starting history: `3465dd56c7b14e6aaa3e28a596ed6d4f1164e2d7`.
Branch: `research/rpd-assembly-preliminary-20261120`. No confirmation execution is
implemented. The old workspace is preserved byte-for-byte in
`inputs/pre_v21_workspace.tar.xz`, including every old seal and manuscript.

Completed disposition: **qualification failed, seven eligible of twelve fixed
candidates, below the eight-root guard**. All 49 distinct terminal branches and 14
parity repeats were completed at the seven eligible technical parents. Neither
nominal macro achieved a stable goal; no physical opportunity erasure was observed.
The 24-parent exploratory sample and 512-parent confirmation remain unattempted.
Two pre-prefix logging/serialization failures and their sealed repairs are retained.
See `SCIENTIFIC_REPORT.md` for the complete negative results, constraints, source
limits, measurements and exact next action. These outcomes do not validate H1/H2.

The supplied editorial artifact is a PDF, not editable LaTeX. Only its abstract,
introduction/contribution/hypothesis presentation and Figure 1 caption were
transcribed into the editable source. Sections II onward and the bibliography
remain byte-identical to the preceding LaTeX. The source diff and Unicode/line-wrap
normalized PDF text comparison are in `audit/editorial_integration.json` and
`audit/editorial_source.diff`. The official class and original V2 are untouched.
Current build receipts are versioned under the paper's `reviews/v21_preliminary/`.

## Pre-outcome source review and frozen engineering interpretation

The six proposal-pinned native files are checked against the original SHA256s
before registration and every worker. Extra source files, executables, native
libraries, robot assets, package versions, all new scripts and input documents
are fingerprinted in `registration.json`. No installed source is modified.

The native square peg dimensions, 3 mm per-side clearance, generated hole offset,
robot base, 60 mm grasp displacement, PD gains/limits, CPU100 Hz/20 Hz and absolute
base-frame XYZ Euler actions agree with the inspected pinned implementation.
The fixture pose compensates its native offset; the peg perturbation is about its
centre. Native100-tick truncation is overridden to200 through `gym.make`; every
remaining active time-limit wrapper is checked. The registered30-tick setup and
80-tick remainder are retained, without resetting the absolute clock.

One controller initialization occurs before stepping the fixed prefix. Thereafter
only native `set_action` updates run. No checkpoint restore, drive recentering,
weld, teleport or hidden pose correction occurs. Each matched branch starts in a
fresh process and regenerates the exact parent. Root state, native drives, custom
controller memory, command, dwell and clock are compared to screening. Two-parent
qualification repeats compare full traces, not only success. Pose tolerances are
1e-5 m/1e-4 rad; other numerical state uses conservative absolute1e-5, clocks and
flags exact. A failure stops qualification and cannot become a failed task label.

The monitor attaches a read-only after-physics-substep callback, preserving the
native hook. It logs100 Hz state/contact impulses and26-sample stable-goal dwell.
The source contact guard means all six inclusive samples spanning the final.05 s
must meet.5 N. All finger links, including native pads, are excluded from
“non-finger robot contact.” Actual force directions and opening directions are
retained to independently check the native two-finger grasp criterion. Goal-only
K and probe/hold path compliance are distinct. True object/fixture/contact/Z data
are evaluator-only; online X has28 entries and each of ten Y samples has23.

No discovery model exists. Both feedback macros therefore share exactly one
nominal peg-in-TCP transform, fixed before all branches. Their trajectories still
differ: direct insertion versus withdraw/realign/insert. This is the contract's
**NOMINAL_SOURCE_EXPLORATORY_NOT_LEARNED_RPD** version, not final learned RPD.
Qualification and exploratory labels cannot be used to fit or tune it.

The12 pre-existing qualification IDs are copied from the original proposal.
The24 independent exploratory IDs use the new requested namespace; all612 native
geometry seeds across qualification/discovery/confirmation/exploration are checked
for uniqueness before physics. Their complete list is registered before any new
outcome, which is stricter than waiting until qualification passes. Qualification
screens all12 in order, runs seven branches for every eligible parent and repeats
all seven for the first two eligible parents. It passes only with at least eight
eligible roots and all source/parity checks. The exploratory path asserts that
gate before launching its24 screens/six-branch comparisons. There is no seed
replacement or downstream-success eligibility filter.

Three qualification worker-hours,60 seconds per source episode including process
startup, and2 GiB total new artifacts are enforced. The24-parent optional study
is additionally bounded by168 episodes and10,080 worker-seconds (24 screens plus
144 terminal branches, each at most60 s), within the previously declared primary
resource allowance. Timings establish feasibility requirements only; no timing
or physical success is assumed before execution. Timeout/crash/invalid trace is
retained as source missingness and closes the gate.

## Reproduction

From repository root, using existing locked dependencies:

```bash
make -C papers/rss2027_rpd_stage1 check reproduce
PYTHONPATH=src:scripts UV_CACHE_DIR=/tmp/rss-rpd-uv uv run --offline --no-sync pytest -q tests
PYTHONPATH=src:scripts UV_CACHE_DIR=/tmp/rss-rpd-uv uv run --offline --no-sync python scripts/rpd_assembly_audit.py --output /tmp/rpd-assembly-independent-audit.json
```

Actual run commands (physics; **do not automatically repeat them**):

```bash
PYTHONPATH=src:scripts UV_CACHE_DIR=/tmp/rss-rpd-uv uv run --offline --no-sync python scripts/rpd_assembly_run.py qual
# Only after the recorded qualification gate passes:
PYTHONPATH=src:scripts UV_CACHE_DIR=/tmp/rss-rpd-uv uv run --offline --no-sync python scripts/rpd_assembly_run.py exploratory
```

Per-row inputs are written before each subprocess. `episodes/` retains console,
process exits, streaming physical traces and compact result metadata. The final
report must distinguish known ineligibility, unknown eligibility, branch missingness
and unattempted registered IDs. Physical loss or creation is reported with its
entire matched branch set. These small technical/exploratory data cannot validate
H1/H2 or justify opening the512-parent confirmation cohort.
