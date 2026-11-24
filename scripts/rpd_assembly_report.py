"""Report every fixed assembly candidate and measured branch; no new physics."""

import csv
import io
import json
import lzma

import numpy as np
from rpd_assembly_contract import BASE, active_registration_path, sha


def report():
    audit = json.loads((BASE / "audit/independent_summary.json").read_text())
    registry = json.loads(active_registration_path().read_text())
    gate = json.loads(
        (
            BASE / f"qualification_sourcefix{registry['source_revision']:02d}.json"
        ).read_text()
    )
    data = []
    for path in sorted((BASE / "episodes").glob("*/result.json.xz")):
        with lzma.open(path, "rt") as stream:
            row = json.load(stream)
        process = json.loads(path.with_name("process.json").read_text())
        data.append((path, row, process))
    complete = [(p, r, t) for p, r, t in data if r["status"] == "COMPLETE"]
    screens = {
        r["job"]["candidate"]["index"]: (p, r, t)
        for p, r, t in complete
        if r["job"]["intervention"] == "screen"
    }
    terminals = [(p, r, t) for p, r, t in complete if "terminal" in r]
    unique = [(p, r, t) for p, r, t in terminals if r["job"]["repeat"] == 0]
    times = [t["wall_seconds"] for _, _, t in terminals]
    screen_times = [t["wall_seconds"] for _, _, t in screens.values()]
    counts = audit["candidate_counts"]
    measured = []
    for index, (path, row, _) in sorted(screens.items()):
        root = row["root"]
        frames = [
            json.loads(line)
            for line in path.with_name("trace.jsonl").read_text().splitlines()
        ]
        measured.append(
            {
                "index": index,
                "candidate_id": row["job"]["candidate"]["candidate_id"],
                "disposition": row["eligibility"]["disposition"],
                "reasons": ";".join(row["eligibility"]["reasons"]),
                "evaluator_Z": row["configuration"]["fault_evaluator_only"]["Z"],
                "half_length_mm": row["configuration"]["length"] * 1000,
                "half_width_mm": row["configuration"]["radius"] * 1000,
                "last_005s_min_contact_N": min(
                    f["peg_fixture_force_N"] for f in frames[144:150]
                )
                if len(frames) >= 150
                else None,
                "root_native_grasp": root["frame"]["native_grasp"] if root else None,
                "root_TCP_residual_mm": root["frame"]["tcp_residual_m"] * 1000
                if root
                else None,
                "source": str(path),
                "source_sha256": sha(path),
            }
        )
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(measured[0]))
    writer.writeheader()
    writer.writerows(measured)
    csv_path = BASE / "audit/checkpoint_measurements.csv"
    if csv_path.exists():
        assert csv_path.read_bytes() == stream.getvalue().encode(), (
            "Derived checkpoint measurements changed"
        )
    else:
        csv_path.write_bytes(stream.getvalue().encode())
    branch_rows = []
    for path, row, process in terminals:
        frames = [
            json.loads(line)
            for line in path.with_name("trace.jsonl").read_text().splitlines()
        ]
        root_and_path = [row["root"]["frame"]] + frames[150:]
        violations = {
            k: sum(not f["constraint_checks"][k] for f in root_and_path)
            for k in root_and_path[0]["constraint_checks"]
        }
        branch_rows.append(
            {
                "candidate_id": row["job"]["candidate"]["candidate_id"],
                "intervention": row["job"]["intervention"],
                "action": row["job"]["action"],
                "repeat": row["job"]["repeat"],
                **row["terminal"],
                "wall_seconds": process["wall_seconds"],
                "registered_simulated_seconds": row["actual_physics_substeps"] / 100,
                "maximum_peg_fixture_force_N": max(
                    f["peg_fixture_force_N"] for f in root_and_path
                ),
                "nonfinger_contact_violation_samples": violations[
                    "nonfinger_robot_contact"
                ],
                "violations_100Hz": violations,
                "trace": str(path.with_name("trace.jsonl")),
                "trace_sha256": sha(path.with_name("trace.jsonl")),
                "actual_response_samples": [
                    frames[i]["online_Y_sample"] for i in range(154, 200, 5)
                ]
                if row["job"]["intervention"] != "direct"
                else None,
            }
        )
    (BASE / "audit/terminal_measurements.json").write_text(
        json.dumps(branch_rows, indent=2) + "\n"
    )
    comparisons = [c for p in audit["parents"] for c in p["option_comparisons"]]
    resources = {
        "source_episodes_attempted": len(data),
        "independent_qualification_candidates": len(screens),
        "source_complete_episodes": len(complete),
        "failed_instrumentation_attempts": len(data) - len(complete),
        "unique_terminal_branches": len(unique),
        "parity_repeat_episodes": len(terminals) - len(unique),
        "terminal_episodes": len(terminals),
        "worker_seconds_including_failed_attempts": sum(
            t["wall_seconds"] for _, _, t in data
        ),
        "worker_hours": sum(t["wall_seconds"] for _, _, t in data) / 3600,
        "registered_trace_physics_substeps": sum(
            r["actual_physics_substeps"] for _, r, _ in data
        ),
        "median_terminal_episode_seconds": float(np.median(times)) if times else None,
        "p95_terminal_episode_seconds": float(np.percentile(times, 95))
        if times
        else None,
        "median_screen_episode_seconds": float(np.median(screen_times))
        if screen_times
        else None,
        "p95_screen_episode_seconds": float(np.percentile(screen_times, 95))
        if screen_times
        else None,
        "declared_qualification_cap_seconds": 10800,
        "new_artifact_bytes_before_final_seal": sum(
            p.stat().st_size for p in BASE.rglob("*") if p.is_file()
        ),
        "full_primary_median_timing_scenario_hours": (
            4096 * np.median(times)
            + 576 * np.median(screen_times)
            + 16 * np.median(times)
        )
        / 3600
        if times
        else None,
        "scope": "Process wall time includes startup/hashing;registered trace time excludes environment construction. Full-study scenario is conditional extrapolation,not a resource or qualification guarantee.",
    }
    (BASE / "audit/resource_ledger.json").write_text(
        json.dumps(resources, indent=2) + "\n"
    )
    (BASE / "exploratory_not_run.json").write_text(
        json.dumps(
            {
                "reason": gate["reason"],
                "qualification_passed": gate["passed"],
                "fixed_exploratory_parents": 24,
                "attempted_exploratory_parents": counts["exploratory"]["fixed"]
                - counts["exploratory"]["NOT_ATTEMPTED"],
                "confirmation_parents_attempted": 0,
                "no_replacement_or_retuning": True,
            },
            indent=2,
        )
        + "\n"
    )
    lines = [
        "# RPD V2.1 and fixed assembly source-qualification results",
        "",
        (
            "The supplied editorial V2.1 has been integrated and rebuilt as five content pages plus one references page. "
            "The immutable original V2, official template, previous manuscripts, raw evidence and user changes are preserved. "
            "Sections II onward and bibliography are byte-identical to the preceding editable source; only documented editorial prose/caption changes were transcribed from the supplied PDF."
        ),
        "",
        "## Scientific decision",
        "",
        (
            f"**SOURCE QUALIFICATION: {'PASS' if gate['passed'] else 'FAIL'} — {gate['reason']}.** "
            f"Exactly {len(screens)}/12 fixed candidates were screened: {counts['qual']['KNOWN_ELIGIBLE']} eligible, "
            f"{counts['qual']['KNOWN_INELIGIBLE']} known ineligible, {counts['qual']['UNKNOWN']} unresolved parent eligibilities. "
            "The frozen source gate requires at least eight eligible roots. No threshold, fault severity or seed was changed to cross it. "
            "The 24-parent exploratory study was not opened. No discovery or 512-parent confirmation physics ran."
        ),
        "",
        (
            "This is qualification evidence at inspected technical checkpoints, not the registered exploratory sample, "
            "independent calibrated risk support or a validation of H1/H2. Both macros used the fixed nominal grasp transform; "
            "no final learned RPD, IG selector, predictor or same-objective baseline was trained/evaluated on these labels."
        ),
        "",
        (
            f"**The nominal recovery catalogue did not work at these inspected checkpoints:** "
            f"{sum(r['terminal']['completion'] for _, r, _ in unique)}/{len(unique)} distinct terminal branches completed the stable goal, "
            f"and {sum(r['terminal']['whole_postroot_compliant'] for _, r, _ in unique)}/{len(unique)} complied over the whole post-root path. "
            "Both hold-followed-by-recovery arms also had zero successes. Empty probe and hold repertoires therefore provide no "
            "working opportunity whose erasure could be demonstrated. Zero observed erasure is not evidence that diagnosis is harmless "
            "or a test of a final learned recovery catalogue. This is a separate scientific limitation, not an added performance gate."
        ),
        "",
        "## Complete denominators and missingness",
        "",
        (
            f"There were {len(data)} source-process attempts: {len(complete)} complete and {len(data) - len(complete)} preserved instrumentation failures. "
            f"Complete work comprises {len(screens)} screens and {len(terminals)} terminal episodes: {len(unique)} distinct parent/intervention/action branches "
            f"plus {len(terminals) - len(unique)} parity repeats at the first two eligible parents. These remain twelve candidate parents, seven eligible technical parents; "
            "branches and repeats never increase independent n. The first two qual/0 attempts failed before prefix tick/substep 0 (absent optional pad view, then NumPy Boolean serialization). "
            "Their outcomes remain unavailable, never failed goals. Both input-preserving repairs were reviewed/sealed before any prefix or terminal outcome. "
            "Original failed registrations/gates/attempts are intact; the repaired qual/0 is the identical ID, not a replacement."
        ),
        "",
        (
            "All five ineligibilities are retained, including nonpersistent-contact cases; neither their potential macro outcomes nor any unattempted exploratory outcome is imputed. "
            "The completed matched technical branches have their actual stable-goal labels and all path violations retained. "
            "See `audit/independent_summary.json` for every candidate/attempt, `audit/checkpoint_measurements.csv` for root measurements and "
            "`audit/terminal_measurements.json` for every terminal trace, actual Y, compliance and contact/goal outcome."
        ),
        "",
        "## Root contact and eligibility",
        "",
        "|ID|Disposition|Minimum contact over final .05s (N)|TCP residual (mm)|Native grasp|Reason|",
        "|---|---|---:|---:|---|---|",
    ]
    for r in measured:
        force = (
            f"{r['last_005s_min_contact_N']:.9g}"
            if r["last_005s_min_contact_N"] is not None
            else "UNAVAILABLE"
        )
        residual = (
            f"{r['root_TCP_residual_mm']:.9g}"
            if r["root_TCP_residual_mm"] is not None
            else "UNAVAILABLE"
        )
        lines.append(
            f"|{r['index']}|{r['disposition']}|{force}|{residual}|{r['root_native_grasp']}|{r['reasons'] or 'none'}|"
        )
    lines += [
        "",
        "## Measured stable-goal outcomes",
        "",
        (
            "Distinct technical parents only; repeats are excluded. All paths have the same 4-second remaining deadline, "
            "including the .5-second probe/hold. Direct a0 has the full deadline. Native head-only success is a separate secondary metric."
        ),
        "",
        "|Intervention|Macro|Measured branches|Stable-goal successes|Whole post-root compliant|Native goal at deadline|",
        "|---|---|---:|---:|---:|---:|",
    ]
    for intervention, action in [
        (p, a) for p in ("hold", "preload", "dither") for a in ("a0", "a1")
    ] + [("direct", "a0")]:
        selected = [
            r
            for _, r, _ in unique
            if r["job"]["intervention"] == intervention and r["job"]["action"] == action
        ]
        lines.append(
            f"|{intervention}|{action}|{len(selected)}|{sum(r['terminal']['completion'] for r in selected)}|"
            f"{sum(r['terminal']['whole_postroot_compliant'] for r in selected)}|{sum(r['terminal']['native_goal_at_deadline'] for r in selected)}|"
        )
    unique_measurements = [r for r in branch_rows if r["repeat"] == 0]
    lines += [
        "",
        "|Post-root constraint|Distinct branches with any violation|",
        "|---|---:|",
    ]
    for name in unique_measurements[0]["violations_100Hz"]:
        lines.append(
            f"|{name}|{sum(r['violations_100Hz'][name] > 0 for r in unique_measurements)}/{len(unique_measurements)}|"
        )
    lines += [
        "",
        (
            f"Peak measured peg-fixture net force across distinct terminal branches: {max(r['maximum_peg_fixture_force_N'] for r in unique_measurements):.9g} N. "
            "Constraint violations remain measured outcomes, not source failures or discarded parents."
        ),
    ]
    lines += [
        "",
        "## Recovery-option contrasts",
        "",
        (
            "K contains successful declared macros under the strengthened stable goal, not all possible controllers. "
            "Each source-grounded comparison uses both macro outcomes after probe and equal-duration hold at one replayed parent. "
            "C checks probe/hold paths separately; a later macro constraint violation is recorded but does not redefine primary goal-only K. "
            "Native contact-manifold net impulses/timestep, not invented force sensors, provide evaluator-only force channels; "
            "the non-finger monitor uses the maximum native contact-manifold net-force norm. All contact records, including zero-impulse manifolds, remain available."
        ),
        "",
        "|Parent|Probe|K hold|K probe|Lost options|Created options|Full erasure|Probe/hold compliant|Joint compliant erasure|",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for p in audit["parents"]:
        for c in p["option_comparisons"]:
            fmt = lambda xs: ",".join(xs) if xs else "EMPTY"
            lines.append(
                f"|{p['candidate_id']}|{c['probe']}|{fmt(c['K_hold'])}|{fmt(c['K_probe'])}|{fmt(c['individual_options_lost'])}|"
                f"{fmt(c['individual_options_created'])}|{c['full_erasure']}|{c['probe_and_hold_compliant']}|{c['joint_compliant_erasure']}|"
            )
    lines += [
        "",
        (
            f"Across {len(comparisons)} matched probe-parent contrasts (clustered within seven technical parents), "
            f"there are {sum(c['full_erasure'] for c in comparisons)} full erasures, "
            f"{sum(c['joint_compliant_erasure'] for c in comparisons)} compliant joint erasures, "
            f"{sum(len(c['individual_options_lost']) for c in comparisons)} individual-option losses, "
            f"{sum(len(c['individual_options_created']) for c in comparisons)} individual-option creations and "
            f"{sum(c['full_creation'] for c in comparisons)} full creations. "
            "This is an exhaustive table, not favorable-case selection. Trace paths and SHA256s for all branches are in the independent summary. "
            "An empty repertoire on hold and probe indicates inadequate nominal skill coverage, not probe-induced erasure."
        ),
        "",
        "## Independent audits and limitations",
        "",
        (
            "The separately coded verifier recomputes stable-goal dwell, native-clock alignment, finite-state support, "
            "root eligibility, native grasp from measured forces/directions, slip and sampled constraint flags. "
            "A second offline implementation reconstructs every command/coordinate conversion and every whitelisted X/Y scalar, "
            "and checks all fourteen full-trace repeat pairs. Clean-directory audit reproduction must match the full independent summary. "
            "Exact receipts are under `audit/reproduction/`. Original source/error rows are never overwritten."
        ),
        "",
        (
            "Both failed pre-prefix instrumentation checks remain counted; no native crash is hidden. "
            "A source-repair attempt is not an independent parent. Seed uniqueness does not prove sampling independence, "
            "and fourteen repeats at two parents do not establish universal simulator stability. "
            "These are sampled simulation constraints, not calibrated physical/hardware safety or zero stochastic failure probabilities. "
            "Raw response availability is not statistical diagnostic informativeness; no predictor was fit to pilot/test labels. "
            "The command checker initially used rounded native hole pose instead of the declared public calibration, producing a 13 nm discrepancy; "
            "its frame was corrected, without changing simulation or relaxing tolerances."
        ),
        "",
        "## Runtime and remaining cost",
        "",
        (
            f"Total source worker time, including the two failed attempts: {resources['worker_seconds_including_failed_attempts']:.6f}s "
            f"({resources['worker_hours']:.6f}h), below the 3h cap. Terminal median/p95: "
            f"{resources['median_terminal_episode_seconds']:.6f}/{resources['p95_terminal_episode_seconds']:.6f}s; "
            f"screen median/p95: {resources['median_screen_episode_seconds']:.6f}/{resources['p95_screen_episode_seconds']:.6f}s. "
            f"Registered traces contain {resources['registered_trace_physics_substeps']} physics samples at 100 Hz. "
            "Process times include imports/hashing; no real-time sensing or energy saving is inferred."
        ),
        "",
        (
            f"At measured median timings, the full-eligibility 4,096-terminal +576-screen +16-parity primary scenario is "
            f"{resources['full_primary_median_timing_scenario_hours']:.3f} worker-hours. This is a conditional extrapolation, "
            "not guaranteed completion or a source pass. Runtime was not the blocker; the eight-root eligibility guard failed. "
            "The unrun exploratory budget remains at most 24 screens +144 terminal episodes (10,080s at the 60s hard ceiling). "
            "The registered 64-discovery/512-confirmation study and all sensitivity branches remain unrun. No resource amendment "
            "can by itself fix contact eligibility; any task/source amendment requires author review before new outcomes."
        ),
        "",
        "## Legitimate Stage 1 handoff and exact next action",
        "",
        (
            "The editorial V2.1 source/PDF is a preserved pre-physics snapshot; no pilot result was silently inserted into it. "
            "Its prospective sentence saying the pilots have not run now predates this qualification attempt and must be updated "
            "by the author if the paper is revised to incorporate this report. The user decides inclusion."
        ),
        "",
        (
            "Publication-defensible additions are the exact attempted/eligible/ineligible denominators, successful trace execution/parity "
            "at inspected roots, nominal-macro outcomes and the exhaustive matched option-set table with compliance scope. "
            "They can strengthen a candid feasibility/boundary note, never an eight-root qualification pass or material prevalence claim. "
            "H1's 10% compliant erasure plus diagnostic-signal conditions and H2's 5pp policy benefit remain untested. "
            "There is no new solver novelty or superiority to same-objective planning; prior baseline equivalences and DSRE results remain untouched."
        ),
        "",
        (
            "**Next action:** hand the twelve fixed source screens and five nonpersistent-contact traces to the scientific author "
            "for a source-feasibility decision and final Stage1 writing. Do not add a thirteenth candidate, replace seeds, lower the "
            "eight-root/contact guard, tune faults, open the 24/512 cohorts or launch another task. Any later revised source protocol "
            "must be explicitly reviewed/frozen before new outcomes; none is executed here."
        ),
        "",
        "Reproduction (offline, from repository root):",
        "",
        "```bash",
        "make -C papers/rss2027_rpd_stage1 check reproduce verify-originals verify-prior-seal",
        "PYTHONPATH=src:scripts UV_CACHE_DIR=/tmp/rss-rpd-uv uv run --offline --no-sync python scripts/rpd_assembly_audit.py --output /tmp/rpd-assembly-audit.json",
        "PYTHONPATH=src:scripts UV_CACHE_DIR=/tmp/rss-rpd-uv uv run --offline --no-sync python scripts/rpd_assembly_reproduce.py --reference research/rpd_assembly_preliminary_20261120/audit/independent_summary.json --output-dir /tmp/rpd-assembly-reproduction-new",
        "PYTHONPATH=src:scripts UV_CACHE_DIR=/tmp/rss-rpd-uv uv run --offline --no-sync pytest -q tests",
        "```",
        "",
        "Native execution commands and immutable inputs are in README.md; replaying them is physics and is not part of offline reproduction.",
    ]
    (BASE / "SCIENTIFIC_REPORT.md").write_text("\n".join(lines) + "\n")
    print(
        json.dumps(
            {
                "report": str(BASE / "SCIENTIFIC_REPORT.md"),
                "counts": counts,
                "resources": resources,
            }
        )
    )


if __name__ == "__main__":
    report()
