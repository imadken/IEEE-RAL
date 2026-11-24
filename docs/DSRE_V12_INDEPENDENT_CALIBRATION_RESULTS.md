# DSRE v1.2 independent source-risk calibration: execution and results

Scientific state: **PHYSICS_OR_DATA_BLOCKED**. The new-source experiment is
incomplete. The frozen old-seed qualification failed during native scene
construction, before any saved state or continuation. No calibration or test
parent started. This is a runtime qualification failure, not an observed negative
effect of DSRE, nor evidence that the historical simulator results are false.

Evidence root: `results/dsre-operational/20261116T102110Z-source-calibration`
(denoted R below). The immutable design is
[DSRE_V12_SOURCE_RISK_PREREGISTRATION.md](DSRE_V12_SOURCE_RISK_PREREGISTRATION.md)
and `config/dsre_source_risk.json`. It was committed at
`629f1676881c910cc6ffec990bdeacd0bffcb72a` before qualification. The source freeze
was written at 10:46:02 UTC, November 16, 2026; the failed attempt followed it.
Scientific parent `e375fe4ac68ea223d5e7bd94ce0bc6ff0a195731` and published ancestor
`e63848e2487ca59e7c66bdd4430614748ae1ece0` remain in this branch's ancestry.

## Actual denominators and risk decisions

| Cohort | Planned independent parents | Started | Complete | Saved checkpoints / continuations |
|---|---:|---:|---:|---:|
| Previously inspected qualification | 1 | 1 | 0 | 0 / 0 |
| New independent calibration | 256 | 0 | 0 | 0 / 0 |
| Disjoint held-out test | 128 | 0 | 0 | 0 / 0 |

Calibration would contain 1,280 checkpoints and 2,560 continuations; testing
would contain 640 checkpoints and 1,280 continuations. Every condition is
missing in the new cohorts. There are no completed new physical pairs, failed
new interventions, exclusions, replacement seeds, or outcome-dependent stops.
The qualification failure occurred in the first nominal condition of inspected
seed 13000000; it does not count as an intervention failure.

All 17 registered methods have **zero assigned calibration parents** for each
action, zero observed error parents, undefined point risk, and uninformative
upper bound 1 under the n=0 convention. All **34 method/action claims** are
`NOT_QUALIFIED_INCOMPLETE_COHORT`; both continue and recover remain disabled in
the proposed certified operational policy. These are missing-data decisions,
not measured zero error, 100% error, or zero empirical coverage. No operational
gate or calibration seal was issued.

The registered 10% target and delta=0.05/68 were preserved. Independent exact
binomial inversion agrees with the production Clopper–Pearson routine; zero
errors require at least 69 independent assigned parents. Five correlated
conditions never count as five independent risk observations. Completing the
entire 256-parent calibration cohort is mandatory even when an action has
enough assignments. Old v1.2 labels cannot provide missing independent support.

DSRE strict/B7, DSRE risk/B7 risk, CART2 risk, B5 and the registered ordinary
rules, and fixed always-continue/recover therefore have no new empirical
comparison. There is no paired effect estimate or confidence interval. C-only,
R-only, both-success, neither-success, initially unsuccessful counts, selected
adequacy, STOP, completion with STOP=0 credit, conditional success, necessary
recovery recall, intervention harms and maintenance are all **not estimable**.
Likewise no new 1/5-mm paired diagnostic exists, and no noisy-input policy is
risk-qualified. Mathematical B7 identities remain true; an empty dataset is not
an empirical tie between methods.

## Physical source qualification and independent failure audit

The bounded collector used the unchanged CPU simulator/backend, original full
canonical action-prefix reconstruction, fixed controllers and 70-control
terminal-success endpoint. Its child exited with signal 11 (`returncode=-11`)
after 7.194434 seconds, before recording a prefix. The failed attempt, empty
child log, chunk accounting and permanent halt are preserved in R. The existing
shared PhysX lock was respected; no parallel physics worker was launched.

An imports-only probe succeeded. An independent direct invocation of the
unchanged historical prefix, without importing the policy scorer, also
segfaulted (shell status 139, 5.782059 seconds). Python's fault trace identifies
`mani_skill/utils/building/actors/common.py:87`, creation of SAPIEN
`RenderMaterial` in `build_cube`, called during PickCube scene initialization.
This identifies the observed fault site; its underlying native cause remains
unknown. Serialization, prefix comparison and intervention execution were never
reached. The contract allows engineering serialization repair, not changing
the renderer/backend, environment packages, controller or task semantics to
get through a source failure. No such change was attempted.

The recorded environment is Python 3.12.12, ManiSkill 3.0.1, SAPIEN 3.0.3,
Torch 2.5.1+cpu, NumPy 1.26.4, Pydantic 2.12.3 and SciPy 1.17.1. The previously
qualified package/build hashes and all 35 frozen source files plus 11 inputs
still match. The numerical/physical auditor correctly refused qualification
because no complete five-condition, ten-continuation parent exists. It did not
silently accept imports or source hashes as physical parity.

`R/independent_failure_audit.json` verifies the failure boundary independently
of the production scorer: registration before the attempt, no fresh parent
attempts/labels, no gate/test seal, exact source hashes and protected files,
disabled claims and undefined rates. Its integrity pass is **not** a passed
physical replay audit. Raw traces are retained locally, including
`R/metered/inspected_prefix_diagnostic.log` and the intentionally failed raw-audit
attempt. No new physics labels exist to audit for success, contacts or timing.

## Preserved scientific evidence, with its original scope

The older v1.2 evidence is independently reproduced and never pooled into this
study. Its 128 confirmation parents contain 640 checkpoints:

| Old clean proposal method | Adequate | Inadequate | STOP | Necessary recoveries selected / eligible |
|---|---:|---:|---:|---:|
| DSRE risk / exact B7 risk rule | 401 | 2 | 237 | 48 / 238 |
| Frozen CART2 risk | 388 | 1 | 251 | 35 / 238 |

These are earlier unqualified proposals, not independently certified source-risk
decisions. Physical action feasibility covers 592/640 old checkpoints, whereas
the seven-fact common-action signature mass is 256/640. This supports the
distinction between unavailable adequate skills and inadequate observation
support. Robust 5-mm facts had no observed false assertions within the declared
synthetic scope, while their risk proposals still made five inadequate actions
and lost recovery coverage. Factual robustness does not establish action risk.

The earlier compact verifier reproduced 880,906 routes, 11,451,778 raw
label-count fields, 492 minimum-certificate cases, 22,904 original bootstrap
intervals and 2,442 compact rows exactly. Existing intervals were verified, not
re-estimated to improve the paper. The v1.2 4,907-member and synthesis
283-member seals remain intact. This positive control establishes historical
reproducibility; it cannot substitute for new source qualification.

## Figures, verification and reproduction

The ready-to-insert [cohort table](figures/dsre_source_risk_table.tex) and
[risk–coverage figure](figures/dsre_source_risk_coverage.pdf) show the actual
incompleteness. The left panel has no empirical points; the right is explicitly
an analytic, zero-error **design-only** support curve. Its 69-parent marker is
not an observed result. The PNG was visually checked for labels and clipping.
The source data are `R/figure_source_data.json`.

The targeted statistical/source tests pass (19 tests), including independent
CP inversion, zero assignments, mixed assignments, correlated conditions,
incomplete calibration and test-seal guards. The maintained suite passes
550 tests with four skips. The blocked-report test explicitly prevents n=0
being displayed as zero measured risk. Maintained Ruff and formatting checks,
archive verification and final accounting are recorded under R. Required failed
checks are the native qualification, direct old-prefix probe and resulting
complete-parent physical audit; none is reported as passing.

From the repository root, without altering the locked environment:

```bash
export UV_CACHE_DIR=/tmp/dual-rec-uv-cache
export PYTHONPATH=src:scripts:/home/imad/Desktop/IEEE-RAL/results/reboot-phase/20261111T204459Z/env/lib/python3.12/site-packages
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1
export MPLCONFIGDIR=/tmp/dsre-source-risk-mpl
uv run --no-sync python scripts/dsre_source_risk_review.py audit results/dsre-operational/20261116T102110Z-source-calibration
uv run --no-sync pytest -q tests
uv run --no-sync ruff check src scripts tests
uv run --no-sync ruff format --check src scripts tests
```

Extract `docs/dsre_source_risk_review.tar.gz` into an empty temporary directory
and run `uv run --no-sync python scripts/dsre_source_risk_review.py verify
<extracted-directory>` for the portable numerical/hash review. The full private
raw archive is `R/source_risk_raw_evidence.tar.gz`; no raw logs are committed.
`R/completion_manifest.json` records exact hashes, resources and the final local
commit. The compact archive contains no manuscript or raw fault logs. It is a
research review packet and is not prepared for public anonymous submission.

## Exact remaining work and resource boundary

All seeds 15000000–15000255 and 16000000–16000127 remain never-started. The
halted root must not be unsealed, its halt deleted, or the failed old-parent
attempt overwritten. A continuation first needs independently demonstrated
fidelity of the unchanged source on previously inspected seeds, recorded in a
new immutable qualification-attempt namespace. Any required source/environment
change must be disclosed before collection and assessed against the fixed
scientific contract. None is authorized by a successful import alone.

Only then could the frozen 256-parent calibration, its complete physical and
decision audits, sealed eligibility, all-test recommendation seal and 128-parent
paired test proceed. No new hypothesis, enrichment, replacement, threshold,
controller or experiment is proposed here. The present stop is the source
qualification boundary, not a resource-limit stop. The ledger counts both native
construction attempts as physics time (12.976493 seconds total), measured child
CPU separately from a conservative 600-second unmetered setup debit, and all
new artifacts against the original 14-hour/12-hour/20-core-hour/6-GB limits.
The independent source-risk hypothesis remains untested.
