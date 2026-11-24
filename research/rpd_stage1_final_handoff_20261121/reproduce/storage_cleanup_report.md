# Disk cleanup — 21 November 2026

Reclaimed approximately **1.22 GiB** across the project and its stale `/tmp` verification copies, after accounting for compressed archives and audit records.

- Removed 73,471 stale scratch files. 73,203 were byte-verified against canonical repository files; 268 unique files were retained in a verified 4.8 MB lossless archive.
- Removed disposable project caches and 22 reproducible PDF page-preview images. Runtime environments, offline TeX dependencies and literature source downloads were preserved.
- Compacted Git from 632.8 to 524.9MiB. All 3,722 object IDs, branches, commits and refs remain; no unreachable objects were discarded, no reset/push occurred, and HEAD is unchanged.
- Deduplicated 31 immutable historical data files with identical bytes, modes, owners and timestamps using shared storage. Every original path remains readable. These sealed files must remain immutable; create a separate copy for future edits.

All 2,604 protected content paths, 1,936 earlier protected paths and 185,513 historical size/mtime records verified. User changes are unchanged. Existing RPD evidence/template/manuscript seals passed. A fresh offline paper build remains six pages and is byte-identical to the review PDF. No science, simulator source or manuscript was changed. The large historical HDF5/gzip evidence was already compressed and remains in place for existing auditors.

The 268 retained unique scratch files were restored to a fresh directory and checked byte-for-byte with original modes and nanosecond timestamps. The verified temporary test copy was then removed. Unique files can be recovered, without overwriting existing files, using:

```bash
UV_CACHE_DIR=/tmp/rss-rpd-uv uv run --offline --no-sync python results/storage-cleanup/20261121/cleanup.py restore /tmp/rpd-storage-restored
```

`verified_scratch_inventory.json.xz` records every original path/hash and its canonical duplicate or archive member. `retained_unique_scratch.tar.zst` contains the unique files. `plan.json.xz`, `execution.json`, `preservation_after.json`, `restore_test.txt`, `paper_clean_build_after_cleanup.json` and `summary.json` record exact actions/results. Cache deletion does not require evidence restoration. The maintenance records are local ignored results; scientific Git history is unchanged.
