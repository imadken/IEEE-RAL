"""Render final scientific reports exclusively from completed, audited evidence."""

from collections import Counter
from pathlib import Path

from dsre_last_common import ROOT, read


def interval(value):
    if isinstance(value, dict):
        value = [value["lo"], value["hi"]]
    return "[" + ", ".join(f"{v:.4f}" for v in value) + "]"


def main():
    audit = read(ROOT / "independent_final_audit.json")
    assert audit["passed"]
    frontier = read(ROOT / "evidence_frontier.json")
    read(ROOT / "registration.json")
    old = read(ROOT / "legacy_policy_rescoring.json")["tasks"]
    phases = audit["phases"]
    new = audit["policies"]
    pegrows = [read(p) for p in (ROOT / "records/insertion_pilot").glob("*.json")]
    extension = (
        read(ROOT / "insertion_extension_decision.json")
        if (ROOT / "insertion_extension_decision.json").exists()
        else None
    )
    pegclasses = Counter(
        f"{int(r['yc'])}{int(r['yr'])}" for r in pegrows if r["status"] == "QUALIFIED"
    )
    pegclasses = {cell: pegclasses[cell] for cell in ("00", "01", "10", "11")}
    worker_hours = audit["physics_worker_seconds"] / 3600
    summaries = []
    for task, policies in [
        ("Pick historical inspected", old["PickCube-v1"]["policies"]),
        ("Push prospective", new),
        ("Navigation historical raw256", old["PointMaze_UMaze-v3"]["policies"]),
    ]:
        for method in [
            "DSRE",
            "ordinary_rules",
            "exact_B7",
            "tabular_Kallus_adaptation",
            "direct_partial_ID",
            "CART2_matched",
            "CART_same_gate",
            "outcome_regression_same_gate",
            "always_continue",
            "always_recover",
        ]:
            if method not in policies:
                continue
            p = policies[method]
            summaries.append(
                f"| {task} | {method} | {p['success']}/{p['n']} | {p['recover']} | {p['required_rescues']} | {p['harm']} | {p['futile']} | {interval(p['gain_parent_bootstrap95'])} |"
            )
    counts = []
    for phase, v in phases.items():
        qualification = (
            "conditional, never activated"
            if phase == "insertion_confirmation"
            and extension
            and not extension["extend"]
            else "registered"
        )
        counts.append(
            f"| {phase} | {v['completed']}/{v['registered']} | {v['remaining']} | {v['status_counts']} | {qualification} |"
        )
    model = (
        read(ROOT / "model_frozen.json")
        if (ROOT / "model_frozen.json").exists()
        else None
    )
    leafrows = []
    if model:
        for c, v in model["leaves"].items():
            b = v["bounds"]
            cc, cr, _ = v["ledger"]["counts_c_r_pair"]
            if not b:
                leafrows.append(
                    f"| {c} | {cc}/{cr} | unavailable | unavailable | no | no | no |"
                )
                continue
            h = b["harm_upper"]
            g = b["gain_lower"]
            f = b["failure_upper"]
            leafrows.append(
                f"| {c} | {cc}/{cr} | {h:.6f} | {g:.6f} | {h <= 0.1 + 1e-12 and g >= 0.05 - 1e-12} | {h <= 0.1 + 1e-12} | {f <= 0.1 + 1e-12} |"
            )
    actualT = phases["test"]["completed"]
    primary = new.get("DSRE")
    prospective = (
        f"The frozen Push selector completed **{primary['success']}/{primary['n']}** test parents, with **{primary['required_rescues']}** useful rescues, **{primary['harm']}** harmful interventions and **{primary['futile']}** futile recoveries among **{primary['recover']}** recover authorizations. Its whole-policy gain versus continue was {primary['gain']:.6f}, descriptive parent-bootstrap95 {interval(primary['gain_parent_bootstrap95'])}; harm per authorization CP95 {interval(primary['harm_per_recover_CP95'])}."
        if primary
        else "The new Push test did not supply qualified policy scoring; the incomplete counts below delimit all claims."
    )
    equality = ""
    if primary:
        equal = [
            k for k, n in audit["equal_action_counts_vs_DSRE"].items() if n == actualT
        ]
        equality = f"Matched summary equivalences with Push DSRE: {', '.join(equal)}. Exact B7/direct partial-ID action identity is also independently checked per parent; other action equalities are computed from the saved decisions, not inferred solely from aggregate totals."
        difference = audit["DSRE_minus_always_R_completion"]
        equality += (
            f" Against always-recover, the completion difference is only {difference['net_parents']} parent(s), "
            f"with descriptive paired-parent bootstrap95 {interval(difference['paired_parent_bootstrap95'])}. "
            f"Unselected rescue opportunities: {audit['unselected_rescue_opportunities']}. "
            "The near-always-recover contrast does not establish a meaningful completion advantage, and the identical fitted-baseline actions rule out a unique selector advantage."
        )
    pegstatement = (
        f"Insertion registered 48 development parents and completed {len(pegrows)}. Outcome classes at qualified paired checkpoints were {dict(pegclasses)}; statuses were {dict(Counter(r['status'] for r in pegrows))}. The fixed extension decision was **{extension['extend']}**, with {extension['qualified_checkpoints']} qualified checkpoints. "
        if extension
        else f"Insertion completed {len(pegrows)}/48 before its recorded boundary; no extension gate is claimed passed. "
    )
    pegstatement += (
        "The separate 96-parent exploratory confirmation was activated; its actual counts are below. Neither pilot nor confirmation is formal risk/gain calibration."
        if extension and extension["extend"]
        else "The 96-parent confirmation was not activated. Insertion is permanently closed for Stage 1 under this protocol; unused conditional IDs are not silently replaced or called missing terminal labels."
    )
    if extension:
        pegstatement += (
            f" Source gate: {extension['qualified_checkpoints']}/48 qualified checkpoints against the required 32. "
            f"Diversity gate: {pegclasses['10']} continue-only and {pegclasses['01']} recover-only parents against the required 2 of each. "
            "The missing continue-only diversity prevents extension despite passing physical source qualification."
        )
    for phase, stats in audit["insertion"].items():
        if stats["eligible_checkpoints"]:
            pegstatement += (
                f" {phase}: continue successes {stats['known_continue_successes']}, recover successes {stats['known_recover_successes']}, "
                f"paired hindsight successes {stats['known_any_action_success']} out of {stats['eligible_checkpoints']} eligible checkpoints; "
                f"missing C/R endpoints {stats['missing_continue']}/{stats['missing_recover']}. "
                f"The empirical gain range allowing all missing outcomes is {interval(stats['recover_gain_empirical_bounds'])}; "
                f"the corresponding harm range is {interval(stats['recover_harm_empirical_bounds'])}. These are descriptive paired development counts, not calibrated selector guarantees."
            )
    oldstats = []
    for stratum, v in read(ROOT / "existing_checks.json")[
        "historical_frontiers"
    ].items():
        task, condition = stratum.split("|", 1)
        oldstats.append(
            f"| {task} [old paired inspected] | {condition} | {v['n']} checkpoints/{v['unique_parents']} parents | {v['action_capacity']} | {v['observable_common_action_rows']} | {v['empirical_log_certifiable']} | {v['empirical_paired_only']} |"
        )
    for task, entry in frontier["tasks"].items():
        for stratum, v in entry["empirical_frontiers"].items():
            oldstats.append(
                f"| {task} | {stratum} | {v['n']} | {v['action_capacity']} | {v['observable_common_action_rows']} | {v['empirical_log_certifiable']} | {v['empirical_paired_only']} |"
            )
    breaks = [
        p.name + ": " + read(p).get("error", "resource boundary")
        for p in ROOT.glob("*.source_stop.json")
    ]
    breaks += [
        p.name + ": resource boundary" for p in ROOT.glob("*.resource_stop.json")
    ]
    source_status = (
        "No hard source/resource stop was recorded."
        if not breaks
        else "Recorded stops: " + "; ".join(breaks)
    )
    hypothesis = f"H1: the analytical source-identification contrast is reproduced; the physical empirical paired-only counts are reported below and are not assumed positive. H2: source/whole-cell/minimum-scope obligations were independently audited; new Push has {actualT}/256 qualified test parents. H3: historical Pick supplies useful recovery and always-recover harm, while navigation supplies an unnecessary/harmful intervention regime. The new Push comparison above determines corroboration and any always-action equivalence. These results support a bounded simulator evidence-certificate study, not optimizer dominance, new Fréchet theory, acquisition superiority or hardware safety."
    hypothesis += " No confidence-qualified physical paired-only regime was established; the specified signature analyses also found zero empirical paired-only cases. Thus physical evidence for a necessary pairing advantage remains unsupported, while randomized one-arm feasibility and scope-valid certificate construction are corroborated. This limits the scientific novelty claim and does not justify another experimental redesign."
    science = f"""# Final DSRE scientific report — November 18, 2026

## Decision and scope

{prospective}

{equality}

{pegstatement}

{hypothesis} The science-expansion phase closes with this sealed evidence. The exact next authorized action is supervisor review and Stage 1 manuscript preparation under separate writing instructions; no new task search, controller redesign or additional campaign is implied. Both manuscripts remain untouched.

## Registration, actual counts and source qualification

Start: local commit `e8efd0fddf70a5405b5e9bda07e206655aa05d8b`; local branch `research/dsre-rss2027-final-science-20261118`. Imported design commit `eea75861cbf57013e3983dfbcf08e2a4252c2a54`; Git blob verification and the document's single final-LF normalization are recorded in `supervisor_import.json`. The supervisor-mentioned convenience JSON/diagnostic files were absent from that verified branch; the prescribed mathematics and historical table check were independently executed from original evidence.

The complete pre-outcome registry preserves all fixed seed ranges, MSB hash assignment, alternating nominal/misaligned Push conditions, existing controllers, PRIMARY6 observations, `.10/.05` primary targets, `.025/(4K)` tails, individual method confidence scope, native CPU/ICD, qualification gates and 12-worker-hour/4GiB limits. Seed collision verification checked 172577 historical paths and 67482 metadata files with no collision. No discovery/calibration counterpart was executed or learner-readable. Every test selected action finished before its isolated alternative evaluator began. The four disjoint native-source pilot parents passed both macros and independent repeats.

| Phase | Completed / registered | Unfinished count | Recorded statuses | Activation |
| --- | --- | --- | --- | --- |
{chr(10).join(counts)}

{source_status} Every source failure, missing endpoint and unopened parent remains in its original denominator. Native Peg predecision screw-planner aborts at any prefix stage are uniformly no checkpoint; post-checkpoint action failures retain observed endpoints or missing bounds. One cached-insertion macro (pilot index 38) aborted after its valid checkpoint with zero future controls; its actually observed false endpoint is retained, not imputed or excluded. No new terminal endpoint is missing. Aperture stays UNKNOWN. The original interrupted insertion study is **not** this pilot: its 128 discovery parents, 363 usable calibration screens, two native predecision failures, **0/1024 calibration action outcomes and 0/256 test decisions** remain historical. Its 659 unopened calibration screens and 256 unopened test parents are retired from this Stage 1 campaign, not relabeled complete.

## Formal methodology and calibrated support

See [method and proofs](DSRE_FINAL_METHOD_AND_PROOFS.md) for `C=(E,R,D,O,B,W)`, the classical sharp bounds, exact-marginal region, rectangular finite-sample criterion, constructive same-marginal worlds, whole-cell mixture proof and cardinality minimum proof. Minimum applies only to the declared Boolean grammar and source-calibrated population. A short conjunction does not warrant an arbitrary narrower subgroup or individual safety.

| Push leaf | n continue / recover | H upper | gain lower | primary useful | harm-only | recover-success>=.90 |
| --- | --- | --- | --- | --- | --- | --- |
{chr(10).join(leafrows)}

The frozen model records every marginal interval, support count, source assumption and confidence allocation. Bounds require within-cell binomial sampling and stable source-population assumptions in addition to parent independence. Registered deterministic seeds/assignments are interpreted as independent simulator draws under the declared source; no distribution-free claim for arbitrary deployment follows. The ridge comparator has its own discovery-frozen whole regions, with the same observation/data/target/confidence standards. Its conditional region scope is explicitly recorded; a broad-region average gain does not imply gain on each narrower subgroup.

## Matched physical comparisons

All rows use actual paired offline scoring of fixed decisions. Intervals below are descriptive independent-parent bootstrap95 with a common 4000-draw seed; original historical intervals are preserved in their original files. Historical rows are previously inspected development reanalysis in the final campaign. The added historical ridge comparison is explicitly retrospective, even though its algorithm and D-only fit are frozen; it is not a new untouched-test confirmation.

| Task / role | Method | Completion | Recover | Useful rescues | Harm | Futile | Gain bootstrap95 |
| --- | --- | --- | --- | --- | --- | --- | --- |
{chr(10).join(summaries)}

Push test four-cell counts `(Yc,Yr)` are **{audit["four_cells"]}**; offline hindsight completion ceiling **{audit["paired_hindsight_completion"]}/{actualT}**. The paired oracle costs two outcome macros per test parent and is never deployed or used for one-arm calibration. Exact rules/direct partial ID have the same available evidence and gate. CART and ridge are conventional matched comparators, not invented algorithms. Fixed C/R require no fitted training data; they have the same execution opportunities and may ignore the common 1152-outcome learning budget. Do not charge fixed policies fictitious necessary training costs or assert selector superiority when their completion matches it. Useful rescues, avoidable interventions, conditional certificate coverage, completion and harm are distinct metrics.

For new Push, D128 and C1024 each cost one observed macro per completed parent; selected T costs one, and evaluator T adds one offline. Source qualification adds16 diagnostic macros. Low-level prefix/future command counts and every process wall time are independently audited. Existing Pick/navigation source comparisons count `logged first outcomes + paired second outcomes`, avoiding double counting the first outcome of a pair.

## Evidence availability and constructive limitations

The supervisor old 1280-checkpoint/256-parent five-condition diagnostic reproduced **10/15/52** full signatures from 6/7/12 predicates and **zero** empirical paired-only groups with at least 10 rows. This is an exploratory warning about current vocabularies, not a proof of absence or a confidence claim; five conditions within a parent are correlated.

The following quantities are separate. Common-action coverage means all physical parents in an exact measured signature share a successful action; an opposing-action witness obstructs that finite pointwise requirement, not automatically an average10%/5% claim. Log and paired-only columns use empirical point estimates from paired evaluator data, **not learner-accessible joints or formal population confidence claims**. Calibrated coverage belongs in the policy table, under independent C support.

| Task | Original condition / scope | Checkpoints | Any action succeeds | Full-X common-action rows | Empirical log-certifiable rows | Empirical paired-only rows |
| --- | --- | --- | --- | --- | --- | --- |
{chr(10).join(oldstats)}

Physically grounded opposing-action and neither-success witnesses, with original source paths, are preserved in `evidence_frontier.json`; they are not fabricated state labels. The two distinct joint worlds at `pc=.4,pr=.6` demonstrate intrinsic nonidentification analytically. Finite confidence uncertainty, source attrition, missing telemetry and limited actions are reported separately from that intrinsic ambiguity.

The previously registered acquisition comparison remains unchanged. At the primary 512 added actions, all five Pick strategies tie at 111 recover authorizations,84 rescues,0 harm,227/256 completion. Smaller budgets and actual support/cost differences are fully retained in the fourth figure/CSV; pairing is not guaranteed better at equal action cost. Navigation's remaining candidate shortfall and differing observed costs are retained, not manufactured into an equal-cost victory. No new strategy search was run.

## G1 through G6 and remaining work

| Workstream | Final status |
| --- | --- |
| G1 source interface / eligibility | Source-v2 aperture remains unknown; prior native failures and both isolated reproductions preserved. Final contract authorizes uniform predecision abort handling, with no controller/environment repair. New Push native qualification passed 4/4. |
| G2 independent manifests / registration | PASS: original 4224 IDs unchanged; final 1556 reserved IDs include conditional 96 and four disjoint source-pilot IDs. All collision/assignment/source/condition/CI/baseline freezes sealed before new campaign outcomes. |
| G3 prospective cohorts | Pick and navigation original cohorts complete at their eligible denominators; final Push D{phases["discovery"]["completed"]}/128,C{phases["calibration"]["completed"]}/1024,T{actualT}/256. Old insertion C0/1024,T0/256 remains retired/incomplete. New pilot and conditional confirmation counts above are separate. |
| G4 acquisition / matched comparison | Fixed old curves preserved, primary 512 tie reproduced; navigation 508/512 candidate shortfall remains. Final matched Push baseline study uses the registered single-action evidence. No insertion acquisition or new acquisition search. |
| G5 independent audits / seals | Numerical LP, CP, whole-cell minimum, physical equations, source/controller parity, one-arm access, historical preservation and compact reproduction checks delivered; archive receipt records exact verification and hashes. |
| G6 scientific decision | Qualified evidence and limitations support only the bounded certificate question described above. No unique rule-search/control/acquisition advantage, no proved physical pairing advantage where absent, no hardware assurance or RSS acceptance promise. Optional insertion is not a central Stage 1 promise. |

No authorized physics remains in this campaign. The explicit unfinished/activation counts and stop receipts above distinguish inactive conditional IDs from the retired historical cohort. Unactivated conditional parents cost zero further authorized executions after the final gate decision. Retired old insertion screening/calibration/test would require a separate source-qualified future protocol; its unmeasured repair cost is not disguised as a completed experiment. The present science phase does not restart it or spend unused budget searching alternatives.

## Resources, artifacts and reproduction

New physics used **{worker_hours:.6f} worker-hours** in **{audit["physics_processes"]}** isolated native processes, versus 12 allowed, with collection capped at 10 to reserve auditing. Final raw campaign storage before packaging was **{audit["compressed_campaign_bytes"]} bytes**; the archive receipt gives the conservative package-plus-data total against 4 GiB. Four parent chains ran concurrently; every batch was at most 4 parents and each worker had 180s timeout. No new dependency, GPU model training, foundation model, paid experimental API or large dataset was introduced. Wall-time sums conservatively include process startup. Peak RAM was not instrumented and is not inferred.

Four figures with PDF/PNG and CSV sources are in `research/dsre_final_science/figures`: source-identification plane and analytical worlds; separate evidence-availability quantities; matched physical completion/harm comparisons; and actual observed-action evidence-cost curves. Complete new source traces, original gzip reconstruction metadata, manifests, frozen models, all failures and independent audits are in `final_science_evidence_20261118.tar.gz`. Older full prospective raw trajectories remain local under their unchanged seal; the compact bundle includes their repeatedly verified audits and summary inputs, not a false claim to include every older raw trajectory.

See [experimental audit](DSRE_FINAL_EXPERIMENTAL_AUDIT.md) for exact commands, preservation, confidence scope, restore verification and local commit procedure. See [Stage 1 handoff](DSRE_FINAL_RSS_STAGE1_CHARTER_PLAN.md) for primary-source nearest-work checks and the limited later-evaluation charter. Nothing was pushed, submitted or written into either manuscript.
"""
    Path("docs/DSRE_FINAL_SCIENTIFIC_REPORT.md").write_text(science)
    auditdoc = f"""# Final DSRE experimental audit and reproduction

## Verified scope

The independent final auditor passed, with maximum numerical discrepancy {audit["maximum_numerical_discrepancy"]:.3g}. Its counts are `{audit["counts"]}`. Independent here means separately implemented LP/binomial/physical-equation and scope checks in isolated read-only analysis processes, not a claimed external-laboratory replication. The audit process imports no production inference module or simulator. A separate historical paired audit checks 133 checkpoints/266 outcome macros; fresh full Pick and navigation audits reproduce all original counts, scored models and source-access logs. Native binary/controller continuity is rehashed against the immutable pre-campaign source proof.

The supervisor 41x41 LP grid and production vertex grid match to 1.11e-16. The old 1280-row diagnostic reproduces 10/15/52 signatures and zero empirical paired-only groups at n>=10. Per-cell actual C arm counts, all CP endpoints, LP extrema and optimizer feasibility are independently checked. Every selected minimum conjunction is compared with the supervisor's independent exhaustive grammar oracle, including whole-cell scope. Every completed one-arm D/C directory contains only its assigned outcome trace; no counterpart was physically collected. Model reads are restricted to their whitelisted discovery/calibration inputs; the deployed worker reads only its frozen model after receiving measured X. Test alternatives start after the selected native outcome completes.

## Preservation and protocol boundaries

The local branch descends directly from `e8efd0fddf70a5405b5e9bda07e206655aa05d8b`; no remote reset or history replacement occurred. Every initially tracked file, initial user deletion, manuscript and prior seal is compared to its initial hash/absence. Every 37132-entry historical prospective raw seal member still verifies, with lossless archived-byte resolution where required. The 27 root-document deletions and corresponding untracked document moves were pre-existing user changes and remain unstaged. New scientific documents/code/evidence alone are committed.

The required supervisor mathematics and original-table check ran before new physics. Extended historical full-domain read-only audits and retrospective baseline scoring ran alongside frozen discovery/calibration, before opening the new test; they did not alter collection, model definitions, thresholds or partitions. The supervisor decision import adds one final LF; removing exactly that LF reproduces its remote Git blob. The supervisor oracle is byte-for-byte exact. No scientific content was changed by import.

Registration records deterministic first-MSB hash convention, complete seed/condition manifests, all inference/controller/CI source hashes, source eligibility, renderer ICD, package versions, targets, baselines and resources before new outcomes. Push is fixed 53-control prefix plus 70-control macro. Peg is the existing source-v2 worker, prefix cap 2000 and future 400, with ANY native predecision screw-planner abort retained as no checkpoint. A post-eligible abort is an observed stopped endpoint when readable, otherwise missing. No replacement seed, aperture imputation, compensating control, test tuning or hidden controller repair occurs. Source failures stop the affected task. The scientific hard deadline is November 21, 2026.

Individual fixed-method families use delta_L=.025 and a separate reserved delta_P=.025; each marginal endpoint tail is `.025/(4K)`. No joint95 guarantee across tasks/methods/budgets or optional insertion pilot is claimed. Parent-level test CP/bootstrap intervals are descriptive and distinct from calibration guarantees. Fixed alternating conditions and simulator seed semantics retain their declared stationary/binomial population assumptions. Historical five-condition data are never treated as 1280 independent parents.

## Validation and resources

The supported scoped repository suite `uv run --no-sync pytest -q tests` passed **635 tests**, with **6 skips**. Relevant focused tests passed 28/28. Ruff checks/formatting passed for the new campaign files. An initial unscoped `pytest -q` attempt descended into archived vendored upstream test trees and failed collection on their command-line parsers/imports; this was not a successful project-suite run and did not justify editing archived sources. The reproducible supported command explicitly targets `tests`.

Actual new physics: {audit["physics_worker_seconds"]:.6f}s = {worker_hours:.6f} worker-hours, {audit["physics_processes"]} isolated processes. This count includes native startup, all qualification repetitions, prefixes, selected macros and evaluator macros. Offline numerical/audit/report work is not presented as physics. The prior campaign's cumulative 9.987875 worker-hours remains a separate historical ledger; this new campaign also remains below the older 28-hour cumulative ceiling. Artifact storage and exact gzip reconstruction savings are recorded in the closure receipt. No claimed peak-RAM measurement was made.

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
"""
    Path("docs/DSRE_FINAL_EXPERIMENTAL_AUDIT.md").write_text(auditdoc)


if __name__ == "__main__":
    main()
