# RPD V2 Stage 1 manuscript and verification

## Deliverable and authority

The separate anonymous manuscript is
`research/rpd_stage1_v2/paper/paper.pdf`, with LaTeX, bibliography, unmodified RSS
class and vector Figure 1 alongside it. It has five content pages and one
references page. This is a methodology-first prospective paper, not an empirical
claim that diagnosis-induced complete recovery erasure has been observed.

The user explicitly authorized the V2 package after clarifying the relationship
between its writing assignment and the pasted paper-facing core. The package
SHA-256 is `25fd623d585458a5a2a825ea8f6387ef0e2321cc2e0d1fd0a7d59855bce1ea1f`.
Its four files and the supplied pasted lock are preserved byte-for-byte under
`research/rpd_stage1_v2/supervisor/`. Starting local commit:
`d97c13a686c23963af0c1c3d6145a51d79cfcac0`. Working branch:
`research/rpd-stage1-v2-manuscript-20261119`. No historical manuscript was edited.
DSRE V5 remains available for the author's decision.

The separately named Universal Top Paper Playbook v7 could not be located in the
repository, user document/download directories or supplied attachments. The V2
package's explicit scientific story, page order and figure requirements were
followed; an absent playbook is not represented as read.

## Scientific disposition

**Nominal formulation: supported, known formulation.** The recovery catalogue,
remaining time, memory-augmented physical state, trajectory-dependent observation,
common executable correction and explicit STOP are defined. The one-probe
criterion is necessary and sufficient only in the complete deterministic model,
with admissible paths. It is standard contingent planning. The paper neither
claims new AND/OR or POMDP mechanics nor an advantage over the same-objective
planner. The physical kernel extension is stated without transferring nominal
guarantees through model mismatch.

**Population H1/H2: untested.** The 10% erasure and five-point completion margins
are prospective supervisor choices. No new simulation, training, physical
episode, sensor or controller was introduced. Assembly confirmation has zero
parents. The matched hold continues physical feedback/contact/time; it is not an
implicit reset or frozen state. It is also not silently equated with the old cube
neutral commands, which maintained the source's measured-pose command semantics.

**Source feasibility: limited.** The assembly geometry and native interfaces are
verified statically, but a complete source-qualified assembly adapter is not
established. The manuscript can describe a falsifiable proposed study and the
precise dependencies; it cannot describe that study as runnable or completed.
This is a significant empirical feasibility risk for author judgment, not a
reason to manufacture settings or rewrite historical evidence.

**Method originality: recovery-specific measurement proposal within known
planning.** Closest work already covers active estimation under constraints,
contact-aware task disambiguation, reversibility and downstream controllability.
The proposed evidence is the post-failure, equal-time, catalogue-relative loss
estimand and its decision consequences. Their physical materiality is open.
Implementation success is not evidence of methodological novelty or RSS acceptance.

## Analytical and statistical verification

`scripts/rpd_paper_v2_checks.py` constructs a new, explicitly analytical,
equal-duration three-world model; the historical examples are untouched. Fine
diagnosis returns A/B/C but leaves C without any declared correction, and removes
only a0 in B. Coarse diagnosis returns AB/C and permits a0/a1 respectively. All
paths obey the constructed allowed-state constraint. Fine information is
1.0986122886681098 nats with maximum completion 2/3; coarse information is
0.6365141682948128 nats with completion 1. Task-consensus and the full-objective
planner also obtain 1. These are mathematical worlds, not robot episodes.

The existing production planner and independently coded complete policy-tree
enumerator agree with the one-probe criterion on 1,024 exhaustive small models:
16 recovery masks, four transition maps, four response maps and four path masks.
The check includes aliased observations, physically allowed but irrecoverable
states and no common recovery despite per-state viability. The new focused tests
also compare the proposed paired likelihood decision against independent scalar
numerical likelihood optimization. No calibration claim is attached to the
analytical truth table.

Independent numerical design calculations reproduce the supervisor JSON:

| Quantity | Recomputed value | Scope |
|---|---:|---|
| H1 binomial rejection count, n=512, one-sided .025, q0=.10 | 66 | Exact independent binary parents |
| Size at q=.10 | .020318522616838825 | Binomial component only |
| Power at q=.15 | .9212959594666066 | Not power for full H1 conjunction |
| Zero-event 97.5% upper bound | .007178950026259456 | Requires qualified source/denominator |
| H2 normal 95% half-width, discordance .20 and difference .10 | .037756341973792434 | Approximation, not observed precision |
| H2 profile test power at p+=.15, p-=.05 | .7472681942802396 | Asymptotic LR decision; analytical multinomial enumeration |
| Conservative exact difference-bound power at the same alternative | .3076074862622259 | Exact CP marginal bounds; dependence allowed |

The paired profile test has asymptotic coverage, with an exact conservative
fallback below 30 discordances. Exact CP-difference sensitivity is reported for
all counts in the proposed study. Zero discordances must not yield a degenerate
equality claim. The violation noninferiority margin is +.02. H1 additionally
requires positive bounded log-score contrasts against both X-only and hold
responses. The score bound is the rescaled empirical Bernstein inequality with
range 2b and b=-log(.001), not an estimate of mutual information and not evidence
that every erasure case was informative. The probability floor, decoder family,
label definition and feature encoding must be frozen before confirmation.

Each primary hypothesis is a conjunction tested one-sided at .025; the
two-hypothesis family interpretation is asymptotic where the profile likelihood
is used. The paper does not claim an exact finite-sample simultaneous H2 or
family guarantee. Information/constraint conjunctions can reduce power far below
the binomial illustration. This remains a design limitation.

## Source-grounded physical evidence

The original 28 source-isolation episodes were independently re-audited from
compressed native traces, without a simulator. Their complete audit summary
reproduces the original summary. The retrospective matched view was rebuilt from
the original/new trace combination and all referenced hashes were checked.

| Domain | Valid isolation episodes | Inspected parents | Matched histories | Partial-option loss histories | Full-catalogue erasure histories |
|---|---:|---:|---:|---:|---:|
| PickCube-v1 | 14 | 1 | 6 | 4 | 0 |
| PushCube-v1 | 14 | 1 | 6 | 0 | 0 |
| Proposed assembly | 0 | 0 | 0 | unmeasured | unmeasured |

The six histories include technical two-probe histories, not six independent
parents and not the proposed one-probe H1 population. Pick release-containing
histories remove successful continuation while recovery remains. Push retains
both options. Original pilot branch 39 failed natively in each task after 38
completed branches. Those original missing outcomes and failures remain intact.
The isolated cases succeeded under GDB/fresh-process topology; this establishes
limited replay/execution capability, not a crash cause or global stability.
These observations do not support an assembly prevalence estimate, a zero-erasure
population claim or an H2 completion advantage. DSRE's separate historical
completion results and unfavorable baseline equalities were not repurposed.

Relevant source outputs:

- `research/rpd_stage1_v2/final_verification/preliminary_recount.json`
- `research/rpd_stage1_v2/raw_source_reaudit/summary.json`
- original `research/rpd_source_isolation_20261119/technical_matches.json`
- original `research/rpd_source_isolation_20261119/final_audit/summary.json`

## Exact remaining assembly bindings

Pinned source: ManiSkill 3.0.1, SAPIEN 3.0.3, Torch 2.5.1+cpu, NumPy 1.26.4.
The task file SHA and exact path are in
`final_verification/assembly_source_review.json`. It uses panda_wristcam, a square
peg/hole, 3 mm per-side clearance, hole-local +x insertion, half-length
85--125 mm and half-width 15--25 mm. Calling the clearance circular/radial would
be incorrect. Available declared online channels are arm qpos/qvel, FK TCP and
history. True peg/hole geometry and latent modes remain evaluator-only.

| Binding | Present evidence | Required before confirmation |
|---|---|---|
| Failed-approach checkpoint | Prior insertion prefix was blocked | New qualified grasped contact checkpoint, complete controller state/clock replay; no use of blocked prefix as if qualified |
| Source population | Native geometry ranges only | Fixed lateral/angular ranges, optional friction strata, predecision eligibility, independent parent seeds/IDs and attrition log |
| Pose/grasp estimate | FK TCP available; exact object geometry privileged | Declare an available estimate/grasp-transform channel and test that Z is not leaked into X |
| Diagnostic target/decoder | Proposed alignment/contact Z | Development-frozen classes, feature encoding, decoder capacity and probability smoothing; identical fit budget for probe and hold |
| Probe operations | Axial preload and one transverse dither proposed | Native servo mode, gains, amplitudes in clearance units, endpoints and equal durations; no new sensor/controller |
| Physical hold | Commanded-equilibrium definition fixed | Implement/replay same equilibrium and feedback without per-step recentering |
| Recoveries | Current-alignment and withdraw--realign--insert defined conceptually | Bind and source-qualify fixed feedback macros and action/state interfaces, with common tau-d clock |
| Constraints/contact | Native evaluator contact and state records possible | Actual sampled channels, limits, sampling rate and permitted contact events; no force sensor inferred from contact records |
| Task success | Stock head-position event | Validate adequacy for intended assembly; any stronger predicate fixed before new data. No historical relabeling |
| Time | Proposed d=.5 s, tau=4 s, sensitivity 8 s | Technical feasibility and source-rate bindings; these are not executed settings |
| Third skill | No pre-existing qualified third assembly macro bound | Optional catalogue sensitivity unavailable unless one is predeclared and qualified; do not invent a skill after failures |
| Runtime | Cube source times do not identify assembly cost | Bounded technical pilot cost and clean-boundary stop rule before population campaign |

The head predicate checks x>=-15 mm and y/z within opening half-width. It is not
a force, stable-full-insertion or hardware safety guarantee. One success/failure
rollout is not a calibrated noisy recovery-success predicate. No source upgrade,
new prefix repair, physics or engineering tuning was attempted here.

## Prospective resource accounting

64 discovery parents, 512 disjoint untouched confirmation parents; all six
matched branches remain one parent. Freeze all policies before evaluator access.
No test-driven generator changes, informative/safe-parent filtering, destructive
best-probe search, or replacement seeds.

| Planned evaluation | Terminal branches |
|---|---:|
| Discovery: (two probes + hold) x two macros x 64 | 384 |
| Confirmation: same coverage x 512 | 3,072 |
| Frozen direct policy at full root deadline x 512 | 512 |
| Base total, excluding qualification/parity | 3,968 |
| 2tau one-factor sensitivity on fixed 64-parent subset | +384 |
| Pre-existing extra skill at original deadline on same three branches | +192, conditional |
| Total if both sensitivities qualify | 4,544 |

Post-hold outcomes cannot stand in for direct recovery at the full deadline; this
corrected an initially incomplete cost accounting in the draft. The direct rule
selects its action from legitimate X, not evaluator outcomes. Additional
discovery direct-policy or parity executions, if required for qualification,
must be added to the future resource registration rather than hidden in 3,968.
Worker-hour estimates remain unbound until the assembly source costs are
measured. No physics budget was consumed by this assignment.

## Skeptical review and supported corrections

These are three separate adversarial self-review passes, not external referee
endorsements. Ranked unresolved risks and corrections are retained.

| Rank / review | Objection | Evidence-based response and manuscript correction |
|---|---|---|
| 1 / robotics significance | There is no demonstrated informative complete erasure in assembly | Explicit in abstract, Sections IV--V and source table. H1/H2 remain prospective; technical partial loss is not full erasure. |
| 2 / formal methodology | This is known contingent/POMDP planning, not a new solver | Criterion proof uses standard quantifier argument; full same-objective planner is an equivalence control. Originality claim is restricted to the proposed measurement/investigation. |
| 3 / source feasibility | Proposed adapter is not executable as specified | Exact unbound checkpoint/sensor/controller/constraint/goal details disclosed; native geometry and event are distinguished from qualification. No fabricated numeric gains or fault ranges. |
| 4 / causal/statistical | Destructive motion might be uninformative or merely time-consuming | Joint compliant event, physical equal-duration hold, frozen IG selector, two held-out predictive contrasts and fixed parent denominator. |
| 5 / causal/statistical | Six branches and repeated histories inflate n | One independent parent for each old domain; new 512 refers to independently drawn parents. Repeats cluster; no H1 estimate from old data. |
| 6 / formal methodology | Every state can be recoverable without a shared action | Common-action intersection and response-dependent criterion explicit; no evaluator action oracle. |
| 7 / causal/statistical | H1 power implies H2 or joint-information power | Exact binomial component, asymptotic paired interval, rare-discordance fallback and conservative power limits separated. |
| 8 / robotics significance | Ordinary task-aware methods already solve the example | Task-consensus and same-objective planning equality reported; DA-GRD contact disturbance and terminal-controllability work credited. |
| 9 / formal/source | Pose/force privileges trivialize the information comparison | Exact peg/hole poses and native contact evaluator-only; no invented force/aperture sensor. Declare pose-estimation interface and leakage test before confirmation. |
| 10 / source | Replay success hides historical crashes | Original two lost rows and 38-before-39 context disclosed, with GDB topology and no stability/cause inference. |
| 11 / causal/statistical | Selecting only safe/erased cases biases the effect | Joint event over the fixed eligible cohort; H2 unconditional on H1/erasure, missingness bounded, no replacement parents. |
| 12 / resources | Full-deadline direct control and sensitivity costs are missing | Added 512 root direct evaluations; 384 deadline +192 conditional extra-skill branches; runtime remains explicitly unknown. |

The same-duration illustration is labeled constructed in the figure, caption,
text and numerical ledger. Its entire-catalogue and partial losses look different.
Arrow/text overlap was corrected and labels enlarged. A compact source table
reports actual episode/parent/history counts. Balanced references use the
official template's multicol package without font/margin compression.

## Verification, preservation, and reproduction

The canonical offline outputs are in `final_verification/`; earlier `audit/` and
`verification/` directories are retained as development receipts, not separate
physical studies. `claims_to_sources.json` maps paper quantities to exact paths
and hashes. `citation_audit.json` records verified primary metadata, method text,
access limitations and conservative venue attribution. Public literature is not
reproduced as an empirical baseline implementation.

The final focused suite passed 74 tests. The final maintained suite passed 789 with six
skipped. A broad unscoped `pytest -q` mistakenly reached archived upstream vendor
trees and aborted during collection with an argparse SystemExit (56 collection
errors, exit 3); its log is retained. This is not concealed or called a maintained
suite pass. The correct broad repository command scopes collection to `tests`.
Ruff checks/formatting cover the new code only; no unrelated old code was changed.
The PDF is checked for six pages, references only on page 6, embedded Type 1C
fonts, no unresolved references, no external URLs or identifying author metadata.
All pages and the figure were rendered and visually inspected. Clean-directory
analysis and anonymous source compilation must match the canonical JSON, PDF
text and page count; binary PDF dates may differ.

Commands from the repository root (new output directories must not exist):

```bash
PYTHONPATH=src:scripts UV_CACHE_DIR=/tmp/rpd-v2-uv-cache uv run --offline --no-sync python scripts/rpd_paper_v2_checks.py --output /tmp/rpd-v2-independent-checks
PYTHONPATH=src:scripts UV_CACHE_DIR=/tmp/rpd-v2-uv-cache uv run --offline --no-sync pytest -q tests
UV_CACHE_DIR=/tmp/rpd-v2-uv-cache uv run --offline --no-sync ruff check scripts/rpd_paper_v2_checks.py scripts/rpd_paper_v2_figure.py scripts/rpd_paper_v2_receipt.py tests/test_rpd_paper_v2.py
MPLCONFIGDIR=/tmp/rpd-v2-mpl UV_CACHE_DIR=/tmp/rpd-v2-uv-cache uv run --offline --no-sync python scripts/rpd_paper_v2_figure.py --output /tmp/rpd-v2-independent-figure
PYTHONPATH=src:scripts UV_CACHE_DIR=/tmp/rpd-v2-uv-cache uv run --offline --no-sync python scripts/rpd_paper_v2_receipt.py --verify
PYTHONPATH=src:scripts UV_CACHE_DIR=/tmp/rpd-v2-uv-cache uv run --offline --no-sync python scripts/rpd_paper_v2_receipt.py --clean /tmp/rpd-v2-independent-clean
```

For the PDF, in the paper directory use a full standard TeX installation with
natbib/plainnat or the existing compiler:

```bash
XDG_CACHE_HOME=/tmp/dsre-stage1-tex-cache /tmp/tectonic-stage1-bin/tectonic --only-cached --untrusted --keep-logs paper.tex
```

The existing compiler retrieved two missing standard TeX font assets (cmsy5 and
cmr5); no Python/project dependency, simulator version or controller changed.
The anonymous bundle includes only paper source, bibliography, class, figure and
PDF; internal provenance, user paths and supervisor documents are excluded.

The preservation inventory records 1,849 protected file hashes and 27 protected
pre-existing absences, metadata for 185,513 historical files, and all 59
pre-existing dirty-status entries. An initial verifier incorrectly treated the
27 already-deleted paths as new missing files; the original snapshot records
them as null and the verifier was corrected and regression-tested. No original
file had changed. Its compact
archive and the final preservation receipt establish that original manuscripts,
source fingerprints, historical seals and unrelated user changes remain intact.
Only this paper namespace, new offline utilities/tests and this report are in the
scoped local commit. No workers are left running, and nothing is pushed or submitted.
The commit is obtained with `git log -1 --format=%H`; the final user handoff names it.
