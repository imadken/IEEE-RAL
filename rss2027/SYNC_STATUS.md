# DSRE research synchronization (2026-11-15)

The recovery-evidence branch merges workstation history through `9f42bb8df9d0e9a695ae1c7eda3bb00c8af72de3` and public editorial history through `6670fa5`. Both histories are preserved. The complete local Stage 1 build and research implementation take precedence over the partial public source snapshot; its scientific introduction is incorporated, while exact negative results, baseline equivalences and limitations remain.

The original public snapshot and local manuscript are archived unchanged under `results/dsre-operational/20261115T082827Z-recovery-evidence/{public_snapshot,starting_files}` on the workstation. Raw logs and bulk results remain local. Subsequent calibrated evidence and compact review records are documented in the recovery-evidence report.

This named public repository reveals authorship. The blind PDF must contain no identifying repository link. No conference submission is authorized or performed. The Stage 2/full-paper master remains unchanged.

## Repository reconciliation — 2026-11-24

GitHub initially had 22 branches, no `main`, no open PRs and no historical PRs;
its default branch was `dual-rec/day4`. The three independent public tips were
merged without deleting any original branch. GitHub `main` was created at
`c98ef13187ddbee85c82c9e252b1debe16604f9f`, preserving every existing public
branch as an ancestor. This commit is the public integration base, not necessarily
the final publication tip.

Full local `main` additionally merges all original local research branches,
including the isolated RPD source-development history. The exact pre-integration
working state is preserved at `backup/uncommitted-20261124`, commit
`ddc9e6057d8f8f99926c097ff1d1e2faf697992e`: 27 byte-identical document moves plus
all 36 formerly untracked files. The original dirty checkout was preserved during
integration. A verified all-refs Git bundle, binary patches, untracked-file tar
and before/after inventories are under `results/repository-sync/20261124/` locally.

One add/add conflict was only a terminal-newline difference in
`DSRE_RSS2027_FINAL_SUPERVISOR_DECISION_20261118.md`; the original local bytes were
retained. Source modules, controller execution, outcomes and the immutable
`V45_FROZEN` tree were not changed. The user explicitly authorized public
publication of the manuscript branches in this session.

The local history contains a 225,070,164-byte archive,
`research/dsre_final_science/final_science_evidence_20261118.tar.gz`, exceeding
GitHub's 100 MiB regular-file limit. Full original history is retained locally;
publication cannot be represented as an unchanged full-history Git push. Any
source/compact-evidence publication projection must list each retained-local
bulk file and its hashes, preserve the original public branches, and identify its
full local source commit. It must not claim missing archives were uploaded or
that a data-free clone can reproduce all recorded-data tests.

The isolated full local integration initially lacked ignored experiment inputs
and the pinned LOGIV cache: 18 failures and 16 setup errors were data-availability
errors. After attaching existing local inputs, all 34 affected tests passed;
the full maintained suite then passed **799 tests, 6 skipped**. No new physics,
scientific retuning or manuscript revision was performed. Detailed test and
preservation receipts remain in the local reconciliation directory.

### Final compact publication

The user approved public manuscript publication and a compact snapshot while
retaining bulk evidence locally. The snapshot derives from full local source
commit `4d86a19fc024160814cebb16fdd862e13fde80fc`, with the complete public
integration as its parent. The [archive manifest](LOCAL_ARCHIVE_MANIFEST_20261124.json)
lists all 86 retained-local bulk files, totaling 773,799,343 bytes. Only the
225,070,164-byte archive exceeds GitHub's 100 MiB individual-file limit; the other
omissions follow the approved compact-publication policy. All manuscript sources,
figures, compact evidence seals and the canonical `V45_FROZEN` directory are in
the public tree. The full-history branch remains local as
`integration/full-history-20261124`; `main` is the compact publication branch.

All original branch heads and the pre-integration working-state snapshot are
retained. Existing full local archives remain at their original paths. The
reconciliation receipt under `results/repository-sync/20261124/` records final
commit IDs, preservation checks and test results. No pull request existed to
merge at the initial inspection. The connector cannot change repository default
branch settings; the existing default remains `dual-rec/day4` unless changed
separately by an administrator.
