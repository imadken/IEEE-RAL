# DSRE RSS 2027 Stage 1: scientific synthesis and artifact audit

Scientific assessment **BOUNDED_STAGE1_SCIENCE**; artifact disposition **READY_FOR_SUPERVISOR_REVIEW**, without submission or public-release authorization. The six-page paper is an integrated research narrative, not this internal audit. Its novelty and external-validity objections remain in the companion adversarial review.

Scientific starting commit: `e63848e2487ca59e7c66bdd4430614748ae1ece0`. Local branch: `research/dsre-rss2027-stage1-scientific-synthesis`. Session evidence: `results/dsre-operational/20261116T082328Z-stage1-synthesis` (abbreviated S below). Scientific inputs remain read-only in `results/dsre-operational/20261115T195007Z-science-v12` (V). Exact final commit and hashes are in S/completion_manifest.json and the final handoff; a tracked document does not embed its own commit hash.

## Preservation and authorized scope

Before editing, all 4,907 V root members and 66 maintained-deliverable hashes were verified against its seal. The previous Stage 1 PDF/source, bibliography, all existing figures and the two prior audit/review documents were copied to S/original-stage1 with hashes in initial.json. All 55 initial user-status entries remain preserved. The Stage 1 bibliography is now a separate `stage1_synthesis_references.bib`: the shared `operational_references.bib`, full-length source/PDF and all its figures remain byte-identical. `.gitignore`, `uv.lock`, fixed DSRE source, frozen models, thresholds and historical evidence are unchanged. No simulator, controller, architecture or training campaign is initiated. No push, credential request or conference submission occurs.

The external synthesis instruction was read completely and retained as S/execution_contract.md. The new local branch begins at the stated scientific commit. Old prose and source remain recoverable both from their original commits and the dated archive.

## Independent scientific consolidation

The untouched compact archive was extracted into S/review-extracted. Its standalone verifier reproduced 880,906 routes, 11,451,778 raw-label count fields, 492 minimum-certificate cases and 22,904 grouped bootstrap intervals across 2,442 compact rows. This is separate from the new manuscript recount.

`scripts/dsre_stage1_synthesis.py` independently recounts all 201,600 confirmation decision-label records, confirms exactly seeds 14000064–14000191 and all five conditions per parent, verifies action/evidence identities to B7, intersects adequate-action sets independently, and recomputes the principal grouped intervals from the paired labels. Its output is S/scientific_consolidation.json. `dsre_stage1_synthesis_audit.py` separately checks selected-action compositions, required versus preventive states, noisy errors and literal totals, historical reference sizes, original calibration support, bibliography bindings, final PDF and preservation. These are internal independent implementations, not external peer review.

| Paper claim/location | Definition and verified primary evidence |
|---|---|
| Abstract, IV, Table I: 128 parents, 640 states, five arms; 69/239/284/48; 238 required R | Compact paired rows, filtered `population=new_confirmation`; original prospective_rows.jsonl.gz. Each seed retains every arm. S/scientific_consolidation.json `parents/checkpoints/classes/per_arm_classes/per_arm_required/required`. |
| IV: 64 characterization, 192 total parents, 960 pairs/1920 continuations; five pilot parents/arm; 70 controls/3.5 s | V/study_plan.json, pilot_qualification_seal.json, prospective_physics_audit.json, cohort_ordering_audit.json. Recommendations sealed before every primary future; no reruns here. |
| III, IV: fixed C/R, six/seven/twelve predicates and exact thresholds | Frozen source/input hashes in V/science_freeze.json; features.py, repair_selection.py, measurement.py, operational.py; fixed skills in overnight_pick.py and overnight_replay.py. |
| III-A: minimum three-fact R certificate, five matched parents, removal witness | S/scientific_consolidation.json `minimum_certificate_example`; independent integer-mask Oracle, qualified reference and historical raw source. Removing left-of-goal admits PickCube-v1/102892/offset002, a both-fail row. |
| Fig. 1, III-B: Push D/E same twelve bits 011110100010, opposite actions, both initially failed; Pick F neither succeeds | `historical_conflict_examples` traces to PushCube-v1/103984/nominal and /105544/nominal; raw before-state/70-step outcomes/source hashes checked. New F is PickCube-v1/14000066/offset003. All displayed geometry is predecision or labeled terminal; figures never pool these cohorts. |
| III-C: actual true/observed x differences −21.55/−13.96 mm; enclosing [−23.96,−3.96] mm | `measurement_example`, from V/constructive_measurement_examples.json first lexicographic historical illustration. Coordinate errors are explicitly checked <=5 mm; false point literal, UNKNOWN invariant result and unchanged paired success are verified. |
| V-A, Fig. 2: action mass592; six/seven/twelve masses206/256/365; gap336; neither48 | Independent per-signature set intersection on the same 640 rows. Full-pose singleton and source checks retained in V/prospective_full_pose_audit.json. Hindsight descriptors do not bound cross-reference proposals. |
| V-A: prior Push417/422 physically feasible, all menu masses0 | Compact development_reference rows, frozen old paired labels and V/mechanism_results.json; independent reference total and action recount in manuscript audit. Old data are exploratory. |
| V-A: new-grid seven-fact conflict is preventive; no failed-start C-only/R-only pair shares all seven facts | Exhaustive cross-class pair comparison on the confirmation rows, `confirmation_failed_start_conflict_pairs_exist=false`. This limits interpretation rather than changing the registered study. |
| V-A: raw fixedC353 and fixedR523/117,69 harms; +26.56 pp [18.91,33.59] | Paired terminal labels, parent-group resampling. `intervals.fixed_r_minus_c`, clean fixed-action tables. These are skill effects, not DSRE/controller improvement. |
| Table II, V-B: strict351/2/287; risk401/2/237; CART388/1/251; 48/238 vs35/238 | All proposal adequacy/error/STOP/required fields independently recounted from actual labels. B7 matches action and evidence exactly across every main scenario, not only totals. Full selected control rows have source ledger entries. |
| V-B: required recall20.17% [13.42,27.48], CART14.71% [8.26,22.09], contrast+2.03 pp [0.94,3.28] with one extra bad action | Independent ratios/differences of grouped parent totals, 4000 PCG64 draws, seed2026111504. `intervals.required_recall/cart_required_recall/adequate_dsre_minus_cart`. |
| V-B: R selections48 necessary+1 maintenance+1 neither; 190 required STOP; risk/strict extra50 all maintenance | Separate raw selected-action composition and initially-successful status recount in synthesis audit. No prevention or maintenance is relabeled failed-start recovery. |
| V-B: selected explanations1.49 vs2.00 asserted literals | Main clean DSRE/CART `literals/(adequate+inadequate)`; generated macros. CART descriptions are not minimized conjunctions; no algorithmic/human-usability advantage inferred. |
| V-C/Table II: strict280/1/359 versus margin148/0/492 at5mm; risk368/5/267,R15; CART256/0/384,R14 | Same bound/interface, original fixed proposal records. Margin is matched to strict purity. All robust asserted literals valid. No source/noise population qualification. |
| V-C: robust required recall6.30% [2.10,11.42]; five bad C, four initially failed | Independent parent-group ratios and exact row/outcome/error composition. `intervals.rho5_required_recall`. |
| Abstract/V-C: point123/1953 false facts vsrobust0/1507, three5mm replicates; robust bad4 each,R14/22/16 | Sum each replicate's literal numerator/denominator separately from paired parent counts. S/manuscript_audit.json corrupted_literal_counts. Not384 parents or1507 independent trials. |
| V-C:250ms delayed point-risk bad16; invariantSTOP640 | Separate secondary_decisions.jsonl.gz read and count, actual recorded prefix packets; no invented motion bound. |
| III-D/VI: original112 assigned/0 errors =>6.239%;69 zero-error parents needed atdelta.05/68 | Previous calibration_decision.json `new_assigned_parents/new_error_parents/new_upper`, independently checked with exact zero-error binomial expression. No transfer or new fit. Support minimum is not a power guarantee. |

All paper macros and table rows are generated from audited fields by the synthesis script, rather than manually adjusted to improve a comparison. Exact macro-to-field mappings are in S/claim_source_ledger.json; the numeric TeX input is `stage1_synthesis_numbers.tex`. The physical and statistical definitions remain explicit in the paper.

## Formal obligations

The three elementary properties and short proofs are in Section III. Fixed-repertoire impossibility follows from unchanged U(s,a). Same-table partition refinement preserves each parent's common action by set inclusion and cannot exceed action feasibility; it does not generalize to differently trained policies or wildcard-query semantics. Invariant literal soundness follows from joint-frame signed-difference and triangle enclosures, while reference and true-state action outcomes have different quantifiers. Conservative UNKNOWN does not imply an actual truth flip; the separate recorded corruption does.

An exhaustive 256-table two-action/four-state regression checks the finite properties, in addition to the proof. Original adapter tests cover zero radius, nested UNKNOWN, both-operand bounds, strict boundaries, missing/stale evidence and risk nontransfer. The oracle verifies the minimum certificate and each literal-removal counterexample. The unchanged B7 equivalence is stated structurally and checked throughout the decision ledgers.

## Sources, figures and layout

S/citation_verification.json records ten reopened primary sources, bibliographic title/year/venue/status and the eight required closest-work contrasts. The main paper cites only these relevant works. The manuscript audit checks bibliography keys, protected-title punctuation and years against that record. The old shared bibliography is untouched. All figures are original plots of owned recorded data, with no copied literature illustrations.

`scripts/dsre_stage1_synthesis_figures.py` draws two source-grounded figures. S/figure_source_ledger.json gives each input field, source SHA256 and PDF/PNG hashes. The compiled paper uses PNG to retain only the official TeX Type1 fonts in the final PDF; vector figure originals are also supplied. Figure 1 uses actual predecision/terminal geometry and full task outcome labels, not outcome inference from a 2-D projection. Figure 2 separates same-table diagnostic masses from differently referenced proposal scores, with no misleading shared ceiling.

The live RSS2027 CFP and FAQ were checked on November16,2026. S/official-author-kit.tar.gz is the freshly retrieved official kit; its IEEEtran.cls and the repository class share SHA256 `d63d4bf27f29603a733d06e27ba5fbb40488acf9d1d696354a88b886758f70a7`. The final artifact has five content pages and exactly one references page, no supplementary dependency, no external URLs or identifying metadata, and only embedded Type1 fonts. No font-size/margin/line-spacing changes were introduced. Machine results and word counts are in manuscript_audit.json; final six-page visual review is in visual_review.json.

Compilation attempt1 exposed a missing cached cmr8 Type1 font; attempt2 used an incompatible pre-existing format cache. Both failures remain recorded. The successful build uses an isolated copy of the original cache plus the already available unmodified font, without changing the class or global caches. The legacy class emits TU-font tuning warnings before the document's T1/Times packages; final PDF fonts are verified Type1 Times/Computer Modern. No unresolved citations/references or overfull boxes remain. Minor underfull-line warnings are retained. A figure-label overlap and a long equation were corrected before the final build. Two audit false positives (class-load font wording and BibTeX case-protection punctuation) were fixed; the punctuation behavior has a regression test.

## Validation and reproduction

Maintained suite: **543 passed,4 skipped**; new synthesis/adapter subset **12 passed**. Ruff passes and all309 maintained Python files meet formatting. Test/lint logs remain local in S; no logs, caches, raw physics or old data are added to Git. No research workers remain at final closure. Resources and exact deliverable/source hashes are recorded in completion_manifest.json/release_receipt.json.

Run from the repository root; do not write into historical evidence:

```bash
S=results/dsre-operational/20261116T082328Z-stage1-synthesis
# The original archive is untouched. Extract only into a new scratch root.
A=$(mktemp -d /tmp/dsre-synthesis-reproduction.XXXXXX)
mkdir "$A/review-extracted"
tar -xzf docs/dsre_science_v12_review.tar.gz -C "$A/review-extracted"
UV_CACHE_DIR=/tmp/dual-rec-uv-cache OPENBLAS_NUM_THREADS=1 \
  uv run --no-sync python "$A/review-extracted/verify_compact.py" "$A/review-extracted"
UV_CACHE_DIR=/tmp/dual-rec-uv-cache PYTHONPATH=src:scripts OPENBLAS_NUM_THREADS=1 \
  uv run --no-sync python scripts/dsre_stage1_synthesis.py "$A"
# Regeneration writes the current Stage1 numeric inputs/figures; run in a clean checkout.
UV_CACHE_DIR=/tmp/dual-rec-uv-cache PYTHONPATH=src:scripts MPLCONFIGDIR=/tmp/dsre-synthesis-mpl \
  uv run --no-sync python scripts/dsre_stage1_synthesis_figures.py "$A"
B=$(mktemp -d /tmp/dsre-synthesis-paper.XXXXXX)
tectonic --untrusted --keep-logs --outdir "$B" rss2027/dsre_stage1.tex
cp "$S/citation_verification.json" "$A/"
cp "$S/initial.json" "$A/"
cp -a "$S/official-author-kit" "$A/"
UV_CACHE_DIR=/tmp/dual-rec-uv-cache PYTHONPATH=src:scripts OPENBLAS_NUM_THREADS=1 \
  uv run --no-sync python scripts/dsre_stage1_synthesis_audit.py "$A" "$B"
UV_CACHE_DIR=/tmp/dual-rec-uv-cache PYTHONPATH=src:scripts uv run --no-sync pytest -q tests
UV_CACHE_DIR=/tmp/dual-rec-uv-cache uv run --no-sync ruff check src scripts tests
UV_CACHE_DIR=/tmp/dual-rec-uv-cache uv run --no-sync ruff format --check src scripts tests
```

This workstation used `/tmp/tectonic-rss2027-bin/tectonic --only-cached` with `XDG_CACHE_HOME=/tmp/dsre-synthesis-tex-cache-v2`. A normal Tectonic installation can obtain the same standard bundle resources automatically. The local anonymous source archive contains only the paper, dedicated bibliography, numeric/table inputs, official class and required figures; internal audit documents and identifying workstation paths are excluded. Its extracted build is checked independently at closure.

The full-length paper is unchanged and no conference submission or public push occurs. The named public repository's prior disclosure cannot be erased by anonymizing a new artifact; release risk remains a supervisor decision. No new experiment is indispensable for the bounded argument; proposed extensions and their limitations are recorded in the adversarial review without authorizing collection.
