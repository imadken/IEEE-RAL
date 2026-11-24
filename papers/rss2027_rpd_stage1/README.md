# RSS 2027 RPD Stage 1 paper workspace

This workspace prepares a separate, anonymous revision of **When Does Physical
Diagnosis Compromise Robot Recovery?** The scientific hypotheses remain
prospective. No assembly or other physics is launched by any target here.

Starting local commit: `b9f4496867a670fbf829609efbf6b13299209969`.
Paper branch: `paper/rpd-rss2027-stage1-preparation-20261120`.

V2.1 continuation: branch `research/rpd-assembly-preliminary-20261120`, from
`3465dd56c7b14e6aaa3e28a596ed6d4f1164e2d7`. The supplied editorial PDF's abstract,
introduction and caption are integrated into editable LaTeX; method sections and
bibliography are unchanged. All previous workspace files and seals are preserved
in `research/rpd_assembly_preliminary_20261120/inputs/pre_v21_workspace.tar.xz`.
Versioned build/check receipts are under `reviews/v21_preliminary/`; older review
receipts describe the preceding revision. The assembly execution and its scientific
scope are reported separately under `research/rpd_assembly_preliminary_20261120/`.

- `original_v2/`: byte-exact, read-only baseline, with the original figure generator.
  Its hashes are in `reviews/original_v2_hashes.json`. Never edit this directory.
- `template/`: freshly downloaded official RSS archive, its checksums, an untouched
  extraction, and a class/style comparison receipt.
- `manuscript/`: editable `main.tex`, `body.tex`, bibliography and vector figure.
  Both TeX files contribute to the main PDF; there is no scientific supplement.
- `reviews/`: independent assessments, dispositions, submission and citation audits,
  proposed protocol/numerical checks, provenance and preservation receipts.
- `build/`: ignored generated files, compiler logs and fresh-build checks.
- `submission/rpd_stage1_anonymous.pdf`: checked six-page review artifact.
- `submission/rpd_stage1_source.zip`: anonymous editable source, not a submission
  supplement. Nothing is uploaded or submitted automatically.

## Build and reproduce

From this directory:

```bash
make all
make check
make verify-originals
make verify-preservation
make verify-seal
make verify-prior-seal
make reproduce
make tests
make numerics
```

`make all` uses the unmodified official class and an existing Tectonic compiler,
or standard `latexmk -pdf`. Set `TECTONIC=/path/to/tectonic` when needed. Locally,
the existing `/tmp/tectonic-stage1-bin/tectonic` and its previously populated TeX
cache are detected. Cached-only compilation never downloads packages. A complete
standard TeX installation can compile `main.tex` with natbib/plainnat as usual.
No project or simulator dependency is installed or upgraded. `make clean` removes
only this workspace's ignored build files, retaining `.gitkeep` and every source.

The build copies editable inputs into `build/`, checks the class, compiles, removes
the generated PDF information dictionary through a validated incremental update,
then checks content, fonts, anonymity and layout before copying into `submission/`.
The update changes neither text nor font objects; regression tests verify this.
`SOURCE_DATE_EPOCH` is fixed. Fresh-directory reproduction compares PDF text and
page count and records whether bytes also match. All pages must be visually
inspected after a substantive revision; automated checks cannot assess scientific
clarity or all figure legibility.

`make tests` and `make numerics` use existing locked Python through `uv`, for
offline statistics/protocol verification only. The numerics target requires a
fresh output file; remove only its generated `build/` output before repeating.
The canonical author-review design is `reviews/PROPOSED_PROTOCOL_AND_NUMERICS.json`;
the proposed candidate seeds are inputs, not observed episodes or measured labels.

## Figure editing

`manuscript/figures/figure1.svg` retains editable SVG text and shapes for PowerPoint
or another vector editor. `tools/figure1.py` reproduces SVG, PDF and preview PNG:

```bash
make figure
make all
```

The PDF version outlines figure text so the paper contains no embedded TrueType
or Type 3 figure fonts. The scene and three-world option sets are explicitly
conceptual/constructed; they are not rendered simulator results. A PPTX is not
claimed or supplied. Review scene/labels after any redraw and keep the analytical
scope warning.

## Scientific status

The manuscript supplies concrete author-review defaults for checkpoint generation,
native control, probes, equal-duration equilibrium hold, two fixed feedback
recoveries, online features, evaluator constraints, a stable insertion goal,
shared empirical model, selectors, statistical decisions and bounded validation.
Source facts, proposed choices and untested physical effects are distinct.

Material corrections are documented in `reviews/V2_RISK_REGISTER.md`: H1's two
population properties versus same-case informativeness; fixed recovery estimates
across physical branches; no-safe-probe abstention; native episode-limit coverage;
unknown eligibility and missingness; direct-recovery discovery cost; and a verified
replacement for V2's mismatched terminal-controllability DOI.

H1/H2 have **zero assembly confirmation parents**. The known planner equivalence
is retained. Existing cube source cases remain narrowly described, including no
complete erasure, one inspected parent per task, and original lost rows. Stage 2
qualification can fail; a running paper build establishes no physical feasibility
or novelty. The exact bounded validation and unresolved risks are in
`reviews/STAGE2_VALIDATION_SPEC.md` and the risk register. Submission remains the
author's decision, with no promise of invitation or acceptance.
