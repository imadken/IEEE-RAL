# V45_FROZEN — immutable review candidate

Frozen21 November2026 after numerical/scientific/format preflight. This is a
methodology-first anonymous Stage1 candidate, not a claim of RSS acceptance.
Do not edit this tree. Subsequent simulator evidence belongs in a separate
report/addendum and cannot silently alter this paper.

The supplied V4.4 PDF is the authoritative content source; original LaTeX and
figure masters were unavailable. This complete editable reconstruction preserves
its question and mathematical obligations, integrates V4.5, and uses newly
reconstructed conceptual SVG/PDF diagrams. SOURCE_ORIGIN.json records the input
hash. The original paper/workspace and historical evidence remain preserved.

Open scientific risks: assembly source qualification and actualH1/H2 effects are
unestablished; same-objective planning may equalRPD. The explicit prospective cost
menu11,136base/11,520with deadline sensitivity corrects the incomplete public
10,112total. Supervisor review must assess transcription and this accounting.

Build from this directory with an existing Tectonic or standard latexmk install:

```bash
make BUILD=../V45_BUILD
sha256sum -c SHA256SUMS.txt
```

Use PYTHON=python3 or another existingPython3. The build is outside this tree.
Tectonic uses only an existing cache (setTECTONIC/XDG_CACHE_HOME when needed);
no packages are automatically installed. A normal latexmk/TeX distribution is the
alternative. No absolute workstation source path is required. Type1C fonts and
layout are checked with Poppler. Figure regeneration needs the recorded existing
Matplotlib environment; `make figures` writes outside the freeze too. All figure
text remains editable inSVG; PDF glyphs are outlines to avoid noncompliant fonts.

The clean sourceZIP contains everything needed to rebuild, subject to a compiler
and its font/package cache; it is not a bundled TeX distribution. The exact local
freeze commit/tree is recorded OUTSIDE the immutable tree in FREEZE_RECEIPT.json
and the final ZIP's LOCAL_COMMITS.json, avoiding a self-referential commit hash.
