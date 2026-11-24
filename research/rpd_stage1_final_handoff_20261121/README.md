# Final RPD Stage1 handoff

The immutable candidate is `paper_freeze/V45_FROZEN/`; the returnZIP maps its
contents to`paper_frozen/`. The editable reconstruction is`manuscript_working/`,
based on the user-suppliedV4.4PDF, not an overwrittenV2.1. Both conceptual SVG/PDF
figures, an official-class portable build, input provenance and29claim groups
are included. Scientific preflight and exact statistical certificates are under
`reviews/`; reproduction scripts/results are under`reproduce/`.

Paper verdict: REVIEW_READY_WITH_EXPLICIT_SOURCE_FEASIBILITY_RISK. The original
LaTeX/masters were not supplied; reconstruction and cost correction are explicit
supervisor review items. EmpiricalH1/H2 remain prospective. PhaseB development
runs only after the freeze commit and is reported separately under`experiments/`.
No confirmation collection or outcome inspection is authorized here.

```bash
python3 reproduce/build_paper.py --source paper_freeze/V45_FROZEN --output /tmp/rpd-v45-rebuild-new
UV_CACHE_DIR=/tmp/rss-rpd-uv uv run --offline --no-sync python reproduce/statistical_preflight.py --output /tmp/rpd-v45-statistical-new/result.json
UV_CACHE_DIR=/tmp/rss-rpd-uv uv run --offline --no-sync python reproduce/verify_finite.py --output /tmp/rpd-v45-finite-new.json
```

Run these from this directory in the repository's existing locked environment;
standaloneTeX build only needsPython, a compiler/cache andPoppler. The finalZIP
adds the full historicalV2.1+failed source evidence under`reproduce/historical_v21/`
for offline audits. ReadSTART_HERE.md in the ZIP first. Commits and final ZIP SHA
are external receipts; no hash is falsely embedded in its own commit.
