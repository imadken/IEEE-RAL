# Final DSRE experimental audit and reproduction

## Verified scope

The independent final auditor passed, with maximum numerical discrepancy 9.99e-16. Its counts are `{'source_hashes': 394, 'native_continuity_hashes': 27, 'preserved_tracked_files': 1146, 'preserved_historical_seals': 435, 'preserved_historical_raw_files': 37132, 'historical_regression_CP_endpoints': 8, 'historical_regression_LP_extrema': 10, 'CP_endpoints': 16, 'LP_extrema': 20, 'whitelisted_model_reads': 8, 'all_cube_obligation_minimum_queries': 192, 'physical_branches': 1824, 'prefix_controls': 103680, 'future_controls': 155600, 'native_repeat_future_states': 560, 'minimum_scope_certificates': 128}`. Independent here means separately implemented LP/binomial/physical-equation and scope checks in isolated read-only analysis processes, not a claimed external-laboratory replication. The audit process imports no production inference module or simulator. A separate historical paired audit checks 133 checkpoints/266 outcome macros; fresh full Pick and navigation audits reproduce all original counts, scored models and source-access logs. Native binary/controller continuity is rehashed against the immutable pre-campaign source proof.

The supervisor 41x41 LP grid and production vertex grid match to 1.11e-16. The old 1280-row diagnostic reproduces 10/15/52 signatures and zero empirical paired-only groups at n>=10. Per-cell actual C arm counts, all CP endpoints, LP extrema and optimizer feasibility are independently checked. Every selected minimum conjunction is compared with the supervisor's independent exhaustive grammar oracle, including whole-cell scope. Every completed one-arm D/C directory contains only its assigned outcome trace; no counterpart was physically collected. Model reads are restricted to their whitelisted discovery/calibration inputs; the deployed worker reads only its frozen model after receiving measured X. Test alternatives start after the selected native outcome completes.

## Preservation and protocol boundaries

The local branch descends directly from `e8efd0fddf70a5405b5e9bda07e206655aa05d8b`; no remote reset or history replacement occurred. Every initially tracked file, initial user deletion, manuscript and prior seal is compared to its initial hash/absence. Every 37132-entry historical prospective raw seal member still verifies, with lossless archived-byte resolution where required. The 27 root-document deletions and corresponding untracked document moves were pre-existing user changes and remain unstaged. New scientific documents/code/evidence alone are committed.

The required supervisor mathematics and original-table check ran before new physics. Extended historical full-domain read-only audits and retrospective baseline scoring ran alongside frozen discovery/calibration, before opening the new test; they did not alter collection, model definitions, thresholds or partitions. The supervisor decision import adds one final LF; removing exactly that LF reproduces its remote Git blob. The supervisor oracle is byte-for-byte exact. No scientific content was changed by import.

Registration records deterministic first-MSB hash convention, complete seed/condition manifests, all inference/controller/CI source hashes, source eligibility, renderer ICD, package versions, targets, baselines and resources before new outcomes. Push is fixed 53-control prefix plus 70-control macro. Peg is the existing source-v2 worker, prefix cap 2000 and future 400, with ANY native predecision screw-planner abort retained as no checkpoint. A post-eligible abort is an observed stopped endpoint when readable, otherwise missing. No replacement seed, aperture imputation, compensating control, test tuning or hidden controller repair occurs. Source failures stop the affected task. The scientific hard deadline is November 21, 2026.

Individual fixed-method families use delta_L=.025 and a separate reserved delta_P=.025; each marginal endpoint tail is `.025/(4K)`. No joint95 guarantee across tasks/methods/budgets or optional insertion pilot is claimed. Parent-level test CP/bootstrap intervals are descriptive and distinct from calibration guarantees. Fixed alternating conditions and simulator seed semantics retain their declared stationary/binomial population assumptions. Historical five-condition data are never treated as 1280 independent parents.

## Validation and resources

The supported scoped repository suite `uv run --no-sync pytest -q tests` passed **635 tests**, with **6 skips**. Relevant focused tests passed 28/28. Ruff checks/formatting passed for the new campaign files. An initial unscoped `pytest -q` attempt descended into archived vendored upstream test trees and failed collection on their command-line parsers/imports; this was not a successful project-suite run and did not justify editing archived sources. The reproducible supported command explicitly targets `tests`.

Actual new physics: 13099.530186s = 3.638758 worker-hours, 1824 isolated processes. This count includes native startup, all qualification repetitions, prefixes, selected macros and evaluator macros. Offline numerical/audit/report work is not presented as physics. The prior campaign's cumulative 9.987875 worker-hours remains a separate historical ledger; this new campaign also remains below the older 28-hour cumulative ceiling. Artifact storage and exact gzip reconstruction savings are recorded in the closure receipt. No claimed peak-RAM measurement was made.

## Exact reproduction commands

From the local repository, using the already locked environment:

```bash
export UV_CACHE_DIR=/tmp/dsre-evidence-uv
export PYTHONPATH=src:scripts:.
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
uv run --no-sync python scripts/dsre_last_existing.py --output /tmp/dsre-final-existing-recheck.json
uv run --no-sync python scripts/dsre_last_audit.py --output /tmp/dsre-final-independent-recheck.json
uv run --no-sync pytest -q tests
uv run --no-sync python scripts/dsre_last_verify.py
```

The verifier extracts the committed compact archive into a fresh `/tmp` directory, checks every manifest member and every new raw seal member, reconstructs every original new gzip byte string with matching SHA256, and reruns the independent complete-new-physics/CP/LP/minimum/access audit plus original mathematical/historical checks. It shares the installed locked environment only; it executes **zero new physics**. Its `--compact` audit deliberately does not pretend to repeat the full older 37132-file local raw preservation check from a compact bundle omitting those old traces. The full local audit above performs that separate preservation check. Extraction retains registered freeze timestamps for sequence verification. See `research/dsre_final_science/closure_receipt.json` for exact archive hash, verified counts and independent reproduction result.

For a literal clean-room re-execution of the already completed registered experiment, first extract code/data separately and move the completed `results/dsre-evidence-aware/20261118-final-science` directory outside that isolated working copy; retain the immutable historical inputs required by the collision check and full local preservation check. Restore the recorded locked native environment, run `dsre_last_existing.py`, then `dsre_last_prepare.py` from the recorded base commit, followed in order by:

```bash
uv run --no-sync python scripts/dsre_last_collect.py native_pilot
uv run --no-sync python scripts/dsre_last_collect.py discovery
uv run --no-sync python scripts/dsre_last_model.py discovery
uv run --no-sync python scripts/dsre_last_collect.py calibration
uv run --no-sync python scripts/dsre_last_model.py calibration
uv run --no-sync python scripts/dsre_last_collect.py test
uv run --no-sync python scripts/dsre_last_collect.py insertion_pilot
# Only if insertion_extension_decision.json says extend=true:
uv run --no-sync python scripts/dsre_last_collect.py insertion_confirmation
```

These are provenance commands, not authorization for another campaign or new seeds after the science lock. Existing source-stop records forbid retrying a failed source; existing completed records are immutable/idempotent. No attempt is restarted merely to obtain a favorable outcome. The current final archive contains every new raw trace needed for read-only reproduction without this physical re-execution.

The local scoped commit contains the four reports, imported decision/oracle, campaign scripts/tests, scientific figures/CSV, evidence archive and closure receipt. Its exact hash is reported with the delivery and is available from `git log -1 --format=%H`; it is not inserted into its own hashed archive. Neither manuscript, `.gitignore`, `uv.lock`, historical evidence nor unrelated user edits are staged. No force-push or RSS submission occurs.
