# RSS 2027 Stage 1 paper-readiness receipt

Checked 20 November 2026. This is an anonymous **author-review artifact**, not an
OpenReview upload or an acceptance assessment. No new physics ran. The original
V2 and historical source/evidence are preserved.

## Deliverables and format

| Requirement | Result / reproducible evidence |
|---|---|
| Isolated local workspace and branch | `papers/rss2027_rpd_stage1/`; `paper/rpd-rss2027-stage1-preparation-20261120`, descended from `b9f4496867a670fbf829609efbf6b13299209969` |
| Immutable V2 copy | Nine byte-exact read-only files, including original figure generator; `original_v2_hashes.json`; `make verify-originals` |
| Official template | Downloaded directly from the RSS URL; original archive and all four upstream files preserved; `template/verification.json` and `template/SHA256SUMS.txt` |
| Archive SHA256 | `ffc8b8053bd218ba9be4c93a569de4c2f36c7f70ae8d2245c747611bed697271` |
| Official class unchanged | SHA256 `d63d4bf27f29603a733d06e27ba5fbb40488acf9d1d696354a88b886758f70a7`; byte-identical to V2 class |
| Layout | Official IEEEtran conference 10pt, US Letter; all 13 measured class dimensions/font settings equal a minimal official-template probe, `layout_comparison.json` |
| Bibliography style | Official kit's natbib/plainnat; no custom font, margins, line spacing or class edits |
| Page budget | Exactly five content pages and one references page; no critical method deferred to a supplement |
| Fonts | All 18 PDF font resources embedded/subset Type 1C; no Type 3/TrueType figure fonts |
| Anonymity | No author identity, active PDF Info/XMP metadata, public repository URL, external link annotation, or page number; generic anonymous-author line only |
| Citations and cross-references | Twelve resolved references, no undefined citation/reference or overfull TeX box; primary-source metadata audit in `CITATION_AUDIT.md` |
| Clean reproduction | Fresh directory yields identical PDF bytes, extracted text and page count; `clean_build_receipt.json` |
| Editable figure | `manuscript/figures/figure1.svg`, real SVG text and shapes; generator `tools/figure1.py`; PDF/PNG provided |
| Visual review | All six final pages inspected at page scale, including equations/column breaks and balanced references; no clipping/overlap observed. Figure labels are at least 7.5pt at official column width; conceptual/analytical scope is explicit |
| Review-ready artifacts | `submission/rpd_stage1_anonymous.pdf` and `submission/rpd_stage1_source.zip`; private audits/originals are not inside the anonymous source ZIP |

The class supplied by the conference is IEEEtran v1.7a, rather than a custom class
whose filename contains “2027.” The official current RSS archive is the authority.
Template dimensions were measured, not guessed from generic IEEE margins.

## Scientific corrections and scope

The main paper now specifies the checkpoint mixture and coordinate transforms,
native initialization/control, measured contact eligibility, two physical probes,
equal-duration equilibrium hold, two feedback recovery macros, online/evaluator
information boundary, sampled constraints, stable mid-depth goal, clocks, shared
model, policy controls, statistics, attrition and resource stop rules. Numerical
design choices without experimental qualification are explicitly proposed for
author review. The adapter and proposed assembly study have **not** been run or
qualified by this task.

H1 retains its 10% margin, but distinguishes two population properties from
same-checkpoint informative erasure. Weighted full-parent score diagnostics assess
average co-occurrence separately. Loss of one macro is distinct from loss of the
entire declared repertoire. H2 retains its five-percentage-point completion margin,
matched constraints and paired independent-parent inference. The paper discloses
asymptotic profile coverage, conservative exact sensitivity, missing-outcome bounds,
unknown-eligibility limits and potential score-test underpower.

Recovery parameters are root-frozen across physical branches. Goal-based and
constraint-compliant recovery sets are separate. Existing contingent/reach-avoid
planning can represent the objective. Shared-model Bayesian coverage and exact
same-objective planning remain equivalent; no novel POMDP solver is claimed.

The former cube table is a short preliminary note: **14 valid fresh-process
episodes at one parent per task**, not 14 independent parents; no full repertoire
erasure; earlier 38 completed branches per task followed by crashes, with original
lost labels still missing. Assembly confirmation count is **zero**. Constructed
worlds and numerical count examples are analytical, never reported as robot data.

A material V2 citation error was corrected in the new copy: the bioRxiv DOI
attributed to terminal controllability actually identifies a different paper.
Verified IEEE journal metadata and author-linked archived source establish the
correct relevant article. Publisher full-PDF access remained unavailable; this
limit is recorded, and no inaccessible full text is claimed as inspected.

## Independent adversarial assessments

Three separate computational reviewers assessed robotics significance,
methodology, and causal/statistical validity. Original objections and follow-up
assessments are retained in `REVIEW_ROBOTICS.md`, `REVIEW_METHODOLOGY.md`, and
`REVIEW_STATISTICS.md`. `V2_RISK_REGISTER.md` maps corrections and ranks the twelve
remaining risks. These are independent computational assessments, not human RSS
reviews or a prediction of acceptance. The disclosed robotics-review overread
precludes portraying that exercise as a perfectly controlled blind study.

Corrected issues include controller-state/recovery-estimator confounding, native
time-limit truncation, bootstrap/model dependency, endpoint/dwell ambiguity,
undefined abstention, invalid outcome-dependent missingness handling and omitted
direct-recovery discovery cost. Later wording specifies eligible retained parity
IDs, the common-action quantifier, and exact geometric/path-monitor metrics.

## Verification and preservation

- Workspace regression tests: **11 passed**.
- Maintained repository tests (`tests/`): **789 passed, 6 skipped**, 48.27 seconds;
  preserved output `maintained_tests.txt`. Skips are not counted as executed checks.
- Offline exhaustive nominal transition/response/action/path masks: **1,024**,
  solver versus independently coded policy-tree oracle, `nominal_oracle_recheck.json`.
- Ruff lint and formatting: pass for all four new workspace tools.
- Old V2 seal: **56 integrity files verified**.
- Prior source-isolation seal: **153 integrity files and 155 archive members verified**.
- Preservation: **1,933 baseline path checks**, including **27 protected absences**;
  **185,513 historical size/mtime records** unchanged; **59 pre-existing Git-status
  entries** untouched. Full content hashes cover the inventoried source/manuscript/
  user paths and separately verified seals; the large metadata inventory alone is
  not represented as a full byte hash of all historical files.

The first formatting check detected one new unformatted assertion; it was fixed.
All relevant checks pass after correction. No failed physical result was deleted,
replaced or changed. `integrity_manifest.json` records the final new-workspace
artifact hashes; `handoff_receipt.json` records actual resource/scope information.

## Reproduction commands

From repository root:

```bash
make -C papers/rss2027_rpd_stage1 check
make -C papers/rss2027_rpd_stage1 reproduce
make -C papers/rss2027_rpd_stage1 verify-originals verify-preservation
make -C papers/rss2027_rpd_stage1 verify-seal
make -C papers/rss2027_rpd_stage1 tests
UV_CACHE_DIR=/tmp/rss-rpd-uv uv run --offline --no-sync ruff check papers/rss2027_rpd_stage1/tools
UV_CACHE_DIR=/tmp/rss-rpd-uv uv run --offline --no-sync ruff format --check papers/rss2027_rpd_stage1/tools
PYTHONPATH=src:scripts UV_CACHE_DIR=/tmp/rss-rpd-uv uv run --offline --no-sync pytest -q tests
PYTHONPATH=src:scripts UV_CACHE_DIR=/tmp/rss-rpd-uv uv run --offline --no-sync python scripts/rpd_paper_v2_receipt.py --verify
PYTHONPATH=src:scripts UV_CACHE_DIR=/tmp/rss-rpd-uv uv run --offline --no-sync python scripts/rpd_isolation_reproduce.py --verify
```

`make figure` regenerates the editable figure with existing dependencies;
`make numerics` writes proposed inputs and offline calculations to a new build
output. Compilation needs the existing cached Tectonic setup or a standard TeX
installation; it installs no dependency or physics source.

## Author decision and unresolved evidence

**Build/format/integrity: PASS. Scientific manuscript: ready for author review as
a methodology and prospective-validation paper. Assembly qualification/H1/H2:
UNTESTED.** Neither empirical significance nor acceptance is established.

The exact missing evidence is a source-qualified assembly checkpoint population,
repeatable matched branches, diagnostically informative responses, material
compliant whole-repertoire erasure, and paired completion/constraint outcomes.
The fixed simulation-only next protocol is in `STAGE2_VALIDATION_SPEC.md`: twelve
qualification candidates/three worker-hours first, then disjoint 64 discovery and
512 confirmation candidates under a 28-worker-hour proposal, no replacement or
outcome-driven retuning. It has 4,096 base terminal comparisons and up to 4,798
total base source episodes, not an achieved sample. Runtime and attrition may
prevent completion. A qualified null, model equivalence or vacuous interval must
be reported honestly. No new physics, public push or submission is authorized or
performed by this handoff.
