# Robot recovery research

This repository preserves the DSRE and RPD research programs, including unfavorable
results, source-qualification failures and equivalent baselines. The current RPD
Stage 1 artifact is a frozen methodology-first review candidate; H1/H2 are not
experimentally confirmed and RSS acceptance is not asserted.

## Current checkpoints

- [Frozen RPD V4.5 source, PDF and build](research/rpd_stage1_final_handoff_20261121/paper_freeze/V45_FROZEN/README.md).
- [Scientific preflight and remaining risks](research/rpd_stage1_final_handoff_20261121/reviews/SCIENTIFIC_PREFLIGHT.md).
- [Separate failed nominal-source investigation](research/rpd_v45_source_development_20261121/SOURCE_REPORT.md).
- [Earlier assembly source qualification](research/rpd_assembly_preliminary_20261120/SCIENTIFIC_REPORT.md).
- [Repository synchronization and publication scope](rss2027/SYNC_STATUS.md).

The canonical frozen paper is unchanged after its freeze commit. Later simulator
results remain separate. No confirmation campaign or conference submission is
started by repository synchronization.

## Development and reproduction

Python 3.12 and the locked `uv` environment are defined in `pyproject.toml` and
`uv.lock`. With dependencies and registered local data already available:

```bash
PYTHONPATH=src:scripts uv run --offline --no-sync pytest -q tests
```

The complete maintained suite includes recorded-data checks. It requires the
pinned LOGIV cache and original sealed experiment inputs; a clean clone without
those inputs cannot run every test. The source restoration instructions and
individual research reproduction receipts distinguish missing inputs from failed
scientific outcomes. No simulator rollout is needed for these offline checks.

Research code is under `src/`, commands under `scripts/`, tests under `tests/`, and
protocols/reports under `docs/`. Earlier project documentation was moved into
`docs/` without changing its contents. See [local setup](docs/LOCAL_CODEX_HANDOFF.md)
and the [original qualification protocol](docs/RESEARCH_PROTOCOL.md) for historical
commands and their scientific scope.

## Data and history

Full local history, user changes and bulk evidence are preserved. GitHub publication
must respect its file-size limit; a publication projection, when used, records
excluded bulk files with hashes and their original source commit instead of
pretending those archives are present. Source, manuscripts, figures and evidence
seals are not recomputed or rewritten to obtain favorable results. The published
and full local trees can therefore differ by the explicitly inventoried bulk data.

The 2026-11-24 publication is a compact snapshot of full local source commit
`4d86a19fc024160814cebb16fdd862e13fde80fc`. Its
[retained-local archive manifest](rss2027/LOCAL_ARCHIVE_MANIFEST_20261124.json)
identifies 86 bulk files (773,799,343 bytes) preserved locally, with Git object IDs
and SHA256 checksums. Full local history is on
`integration/full-history-20261124`; the original public histories remain in
GitHub `main`. No original branch was removed.
