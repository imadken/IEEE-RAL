"""Source-grounded Stage1 handoff; technical point contrasts are not H1/H2 tests."""

import argparse
import itertools
import json
from pathlib import Path

from rpd_isolation_audit import read_raw
from rpd_isolation_common import BASE, PREFIX, PRIOR, TASKS, jobs, sha, write_json
from rpd_pilot_audit import check_parity, compare_options

DOC = Path("docs/RPD_SOURCE_ISOLATION_AND_STAGE1_HANDOFF_20261119.md")


def technical_view():
    """Explicit mixed-provenance descriptive view of the already-exposed parent0."""
    summary = json.loads((BASE / "final_audit/summary.json").read_text())
    result = {
        "scope": "RETROSPECTIVE_TECHNICAL_PARENT0_ONLY_NOT_POPULATION_H1_TEST",
        "tasks": {},
    }
    for task in TASKS:
        indexed = {}
        for path in (PRIOR / "physics" / task / "parent_00").glob("*.json.xz"):
            raw = read_raw(path)
            row = raw["row"]
            indexed[(tuple(row["history"]), row["endpoint"], row["repeat"])] = (
                raw,
                str(path),
            )
        # New replicas of the exact original repeat0 row are kept as new technical replicas.
        # Their explicit mapping never changes the original missing-row journal or label.
        for job in jobs():
            if job.row.parent.task != task:
                continue
            path = BASE / "physics" / task / job.job_id / "native.json.xz"
            if path.exists():
                raw = read_raw(path)
                indexed[(job.row.history, job.row.endpoint, job.isolation_replica)] = (
                    raw,
                    str(path),
                )

        def option_set(history, indexed=indexed):
            refs = []
            selected = []
            for endpoint in ("continue", "recover"):
                pair = [indexed.get((tuple(history), endpoint, r)) for r in (0, 1)]
                if any(p is None for p in pair):
                    return None, refs
                for raw, path in pair:
                    refs.append(
                        {
                            "path": path,
                            "sha256": sha(path),
                            "macro_end": raw["macro_end_success"],
                            "deadline": raw["deadline_success"],
                        }
                    )
                if any(
                    raw["status"] != "COMPLETE" for raw, _ in pair
                ) or not check_parity(pair[0][0]["records"], pair[1][0]["records"]):
                    return None, refs
                if pair[0][0]["deadline_success"]:
                    selected.append(endpoint)
            return selected, refs

        probes = (
            ("micro_lift", "release_settle")
            if task == "PickCube-v1"
            else ("forward_tap", "lateral_sweep")
        )
        rows = []
        for history in [*((p,) for p in probes), *itertools.product(probes, repeat=2)]:
            hold = ("neutral10",) if len(history) == 1 else ("neutral20",)
            kp, pr = option_set(history)
            kh, hr = option_set(hold)
            parity = True
            anchors = []
            for source in pr + hr:
                raw = read_raw(source["path"])
                anchors.append(raw["records"][: PREFIX[task] + 1])
            if anchors:
                parity = all(check_parity(anchors[0], p) for p in anchors[1:])
            if not parity or not summary["tasks"][task]["limited_source_completion"]:
                kp = kh = None
            rows.append(
                {
                    "history": history,
                    "delay_ticks": 10 * len(history),
                    "K_probe": kp,
                    "K_hold": kh,
                    "root_parity": parity,
                    "probe_sources": pr,
                    "hold_sources": hr,
                    **compare_options(kh, kp),
                }
            )
        result["tasks"][task] = {
            "rows": rows,
            "independent_confirmation_parents": 0,
            "already_inspected_parents": 1,
            "original_pilot_status_unchanged": "SOURCE_NOT_QUALIFIED_INCOMPLETE",
            "two_probe_history_scope": "Technical secondary20tick histories; not the locked one10tick-probe H1 confirmation cohort",
        }
    return result


def report(json_only=False):
    view = json.loads(json.dumps(technical_view()))
    technical_path = BASE / "technical_matches.json"
    if technical_path.exists():
        assert json.loads(technical_path.read_text()) == view
    else:
        write_json(technical_path, view)
    if json_only:
        return
    summary = json.loads((BASE / "final_audit/summary.json").read_text())
    lines = [
        "# RPD source isolation and methodology-first Stage1 handoff",
        "",
        "19 November2026. This handoff follows the supplied methodology/charter lock",
        "verbatim copy in `research/rpd_source_isolation_20261119/supervisor/`.",
        "It is a source-engineering diagnostic and manuscript-ready scientific summary.",
        "No existing manuscript, figure, DSRE result or prior evidence seal is changed.",
        "",
        "## Source-completion claim actually established",
        "",
        "| Task | Failed-row isolated attempts | Neutral attempts | Returned complete | Passed source checks | Full-worker seconds | Task output bytes |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for task, r in summary["tasks"].items():
        checks = [c for c in summary["checks"] if c.get("task") == task]
        first = sum(c.get("phase") == "failed_row_replay" for c in checks)
        controls = sum(c.get("phase") == "neutral_control" for c in checks)
        lines.append(
            f"|{task}|{first}/2|{controls}/12|{r['returned_complete']}/{r['attempted']}|{r['passed_source_checks']}|{r['worker_wall_seconds']:.6f}|{r['output_bytes']}|"
        )
    lines += [
        "",
        f"Global four-row source gate passed: **{summary['four_row_gate']['passed']}**.",
        "The gate tested complete native return, original source/runtime configuration,",
        "full checkpoint/controller-memory parity, original20tick probe-prefix parity",
        "against its immediately preceding continue branch, and independent repeated",
        "full native traces. Macro task success=1 was NOT a gate requirement.",
        "",
        "Each row had its own fresh Python inferior and GDB supervisor. All actual",
        "process exits, console logs, measured endpoint labels, raw traces, native",
        "source/executable/environment hashes and prephysics input hashes are retained.",
        "Python faulthandler and native/Python GDB backtrace commands were armed.",
        "No diagnostic failure was replayed to get a second backtrace. Core dumping",
        "was already disabled in the inherited environment; no core capability is",
        "claimed. Review `process.json` and debugger logs for actual signal status.",
        "",
        "**Limited inference:** when the four-row gate and14row source checks pass,",
        "these exact failed-row inputs and neutral controls are reproducible under",
        "fresh one-row processes at the two already-inspected parent0 checkpoints.",
        "This does not establish general source stability, batching stability, other",
        "parents, all faults, the original full ten-parent pilot, or a crash cause.",
        "In particular, successful isolated execution does not prove accumulated",
        "native process state caused the original failure. The original two exit139",
        "attempts and missing outcomes remain unchanged and unknown.",
        "Debugger instrumentation and process lifetime both differ from the original",
        "long-lived driver. This was not a factorial causal test of those differences;",
        "GDB can affect timing. No uninstrumented source-stability claim follows.",
        "",
        "Both task caps are1,200worker seconds and100MiB; recorded costs include GDB",
        "and Python startup/teardown. Exactly the authorized rows were attempted; no",
        "replacement seed, extra failure-diagnosis rollout, physics-source upgrade,",
        "new sensor, old pilot resumption or Stage2 collection occurred.",
        "",
        "## Actual native terminal rows",
        "",
        "Each original failed row was replayed with its ORIGINAL repeat0 input twice.",
        "Replica IDs label independent OS-process repeats, not new parent samples.",
        "",
        "| Task | Phase | History | Macro | Technical replica | @macro end | @90 | Source passed |",
        "|---|---|---|---|---:|---|---|---|",
    ]
    for task, r in summary["tasks"].items():
        for row in r["outcomes"]:
            lines.append(
                f"|{task}|{row['phase']}|{' → '.join(row['history'])}|{row['endpoint']}|{row['replica']}|{row['macro_end']}|{row['deadline']}|{row['source_passed']}|"
            )
    lines += [
        "",
        "STOP has no macro-end label; its native deadline result is measured.",
        "All macros retain the frozen70control binding. Probe/hold delay is10/20",
        "controls; explicit padding makes the common post-checkpoint deadline90.",
        "@macro end therefore occurs at delay+70. State/controller clocks remain",
        "continuous within each episode; no reset, restore or teleport occurs.",
        "",
        "## Retrospective technical matched availability, without an H1 claim",
        "",
        "The following table combines old completed probe branches with new isolated",
        "technical recover/hold branches. Source paths/hashes and repeat checks are",
        "explicit in `technical_matches.json`; old missing labels are NOT overwritten.",
        "This is a single previously inspected parent/task, not a newly sampled",
        "confirmation cohort. All rows, including20tick secondary histories, are shown.",
        "",
        "| Task | History | Duration | K_hold | K_probe | Erasure | Creation | Lost actions |",
        "|---|---|---:|---|---|---|---|---|",
    ]
    for task, r in view["tasks"].items():
        for row in r["rows"]:
            lines.append(
                f"|{task}|{' → '.join(row['history'])}|{row['delay_ticks']}|{row['K_hold']}|{row['K_probe']}|{row['erasure']}|{row['creation']}|{row['lost']}|"
            )
    lines += [
        "",
        "None of these rows estimates prevalence, tests H1/H2, supplies calibratedG",
        "or proves a physical impossibility. The primary prospective H1 protocol is",
        "one10tick probe versus hold on independent held-out parents. A two-probe",
        "technical case must not replace it. Report any descriptive event exactly,",
        "without promoting it into a population or method-advantage claim.",
        "At these exposed checkpoints, no full repertoire erasure is observed in the",
        "retrospective technical contrasts. Pick release-containing histories lose the",
        "successful continue option relative to holding, while recover remains successful.",
        "Push retains both successful macros. These are correlated single-parent facts,",
        "not a frequency estimate, a null H1 test, or an excuse to weaken the H1 endpoint.",
        "",
        "Contact remains evaluator-only. The preserved contact audit distinguishes",
        "positive-gap/zero-impulse cached manifolds from active native contact evidence.",
        "A zero-delta hold advances arm feedback, gravity, contacts and task time; it",
        "is not a frozen physical state. Source success does not certify real robots,",
        "force, damage or continuous-time safety. No observation channel was invented.",
        "",
        "## Locked methodology for the Stage1 author",
        "",
        "**Question:** When does physical diagnosis preserve ordinary sampled state",
        "allowance yet eliminate an otherwise available terminal task recovery, beyond",
        "what equal-duration waiting would cause? RPD is a hypothesis-driven robotics",
        "measurement and decision methodology, not a new strong/POMDP solver.",
        "",
        "At an eligible predecision checkpoint s, fix macro catalogueA, native binary",
        "successU and absolute deadlineτ. The physical probeT_p^d and neutral holdH_d",
        "have the same duration and maintain the original controller/clock lineage.",
        "State includes time and controller memory. Define K_τ(x)={a∈A:U_τ(x,a)=1},",
        "including the registered macro and explicit terminal padding. Define",
        "L_p(s)=1[K_τ(H_d(s))≠∅ and K_τ(T_p^d(s))=∅], with creation and per-action",
        "loss/gain separately measured from actual matched simulator branches.",
        "",
        "Let C_p,C_H be the registered sampled geometric allowances along actual",
        "probe and hold paths. The primary event is the JOINT event J_p=L_p C_p C_H",
        "on the fixed eligible PRE-probe parent distribution. Report macro-path",
        "allowance separately, with the exact sampled interval declared. Do not",
        "condition the analysis on treatment-selected safety after the probe; that",
        "would change the estimand and can introduce selection bias. Parents with",
        "post-probe violations remain in the denominator, with adverse flags visible.",
        "",
        "Qualification requires reproducible checkpoints, actually executed controls,",
        "identical source/controller/horizon semantics, actual terminal labels and",
        "source-missingness accounting. It is catalogue-, horizon- and simulator-",
        "conditional. Paired alternative branches are offline evaluator evidence,",
        "never an online robot observation. No trial label is inferred from commands.",
        "",
        "OnlineX,Y_p contain ONLY seven arm qpos/qvel, FK TCPxyz and native clock.",
        "Native object pose/contact/fault/future outcomes remain evaluator-only; the",
        "unchanged native macros' internal ideal object/goal state privilege is",
        "disclosed as simulation-only. Information is incremental held-out prediction",
        "of evaluator targetZ from(X,Y_p) versusX, using a discovery-only frozen decoder.",
        "Do not call this Shannon information or train/test on these technical parents.",
        "",
        "**H1 remains untested:** a prospective independent-parent frequency of the",
        "joint event J_p beyond time-matched waiting. The primary experiment measures",
        "H1 and can yield an informative positive or null result after source qualification.",
        "**H2 remains untested:** where probes are informative and erasure is material,",
        "accounting for recovery options changes the completion/information tradeoff.",
        "No decoder, discovery fit, untouched policy test or statistical success",
        "calibration was run here. H2 is secondary, not needed to invent a positiveH1.",
        "",
        "## What the final Stage1 manuscript can say now",
        "",
        "The contribution is the source-qualified matched estimand, measurement protocol",
        "and decision criterion, plus a falsifiable validation design. Do not claim",
        "that disturbance, contact sensing, AND/OR planning or POMDPs are new. Existing",
        "full-model strong/POMDP planning is an equivalent positive control; one-step",
        "task consensus is a strong comparator. Preserve equal decisions and budgets.",
        """s-FEAST already studies active diagnosis with probabilistic state safety;
DA-GRD already includes physical scene changes and task-aware probing. The precise
target here is recovery-option loss beyond equal-duration waiting. See the prior
verified nearest-work matrix; do not restart a solver originality search.""",
        "",
        "Separate the constructed three-world illustration from physical observations.",
        """The old pilot provides38completed branches/task and two native failures;
this microprotocol provides bounded source transactions and measured technical
hold outcomes. Neither is a held-out H1/H2 study. Previous DSRE227/256 or253/256
outcomes are not RPD results and must not support RPD physical prevalence.""",
        "",
        """**Manuscript-ready abstract core:** Robots can diagnose a manipulation failure
by physically interacting with it, potentially changing which corrective actions
remain feasible. We define recovery options over a fixed executable macro catalogue
and terminal deadline, and specify a matched physical-intervention protocol that
compares each diagnostic probe with an equal-duration neutral hold. Actual terminal
outcomes identify catalogue-relative option loss, creation and individual-action
changes; a joint endpoint records option erasure together with sampled geometric
allowance without selecting on a post-treatment safety outcome. Established
information-seeking, consensus and full-model belief planning provide matched
decision controls. An analytical example illustrates the distinction between
information, state allowance and recoverability. Technical simulator replays assess
source feasibility only. A prospective independent-parent study will test physical
frequency and policy consequences, with explicit missingness and informative nulls.""",
        "",
        "The locked5+1page structure is: question/illustrativeFigure1; three distinct",
        "quantities and assumptions; matched formal protocol and conventional planning",
        "control; source-grounded experimental/statistical design; interpretations,",
        "closest work and Stage2 charter; directly verified references. Figure1 must",
        "label illustrative worlds and observed simulator evidence separately. The",
        "handoff is not an edit to either existing manuscript or final figure.",
        "",
        "## Fixed Stage2 charter, inactive",
        "",
        "One independently source-qualified contact-sensitive family is primary; the",
        "other fixed family is controlled replication if qualified. No favorable task",
        "or seed substitution. Freeze two10tick probes, neutral10, both unchanged70tick",
        "macros, common90deadline, sensors and native success. The primary protocol",
        "does not require length-two probe histories. Current28source episodes alone",
        "do not qualify arbitrary future parents or justify a completion-time promise.",
        "",
        "Use64independent discovery parents to assess contact/sensor coverage, option",
        "balance, analysis and precision/power assumptions, then freeze them BEFORE",
        "256new independent eligible test parents. Report original-seed attrition and",
        "qualified-checkpoint denominators without outcome-based replacement. Each",
        "test parent supplies six isolated terminal evaluations:two probes plushold",
        "times two fixed macros,1,536/task, plus separately preregistered replay audits.",
        "Discovery adds384, total1,920/task before those audit extras. Conditions and",
        "repeats within a parent are correlated; they are not extra independentN.",
        "",
        "Prespecify per-probe joint-erasure proportions, per-task and pooled scope,",
        "multiplicity and exact independent-parent intervals. For a single predeclared",
        f"event,0/256 has95%one-sided exact upper bound {100 * (1 - 0.05 ** (1 / 256)):.6f}%.",
        f"Four Bonferroni events atα=.05/4 instead give {100 * (1 - (0.05 / 4) ** (1 / 256)):.6f}%.",
        "These are ANALYTICAL DESIGN VALUES, not observed robot rates. MissingJ",
        "must stay unknown: with known-positive countz,missingm,original denominatorN,",
        "report at least the descriptive range[z/N,(z+m)/N] before statistical scope.",
        "Do not assert that complete-case inference transfers under informative crashes.",
        "",
        """H2 requires discovery-frozen sensing/model/decoder and untouched policies:
information-only, task consensus, task-aware and full-model positive control with
equivalent source access, data, time and actuation budgets. Retain policy equality;
do not manufacture an advantage through a transition-blind or weaker comparator.
If H1 is absent, or responses are uninformative, that limits H2 rather than authorizing
new probes, sensors, controllers or outcome-driven model changes.""",
        "",
        """Source qualification and measured fresh-process throughput precede discovery,
confirmation and audit. A future source failure is not a negative recoverability
result; an alternative source needs explicit scientific review. No full pilot,
randomized calibration, discovery or Stage2 is authorized or launched here.""",
        "",
        "## Author action and reproduction",
        "",
        "Proceed with the locked methodology-first RPD Stage1 writing independently of",
        "the source diagnosis. Preserve DSRE V5 as a separate fallback. The paper can",
        "state the complete methodology and testable charter without claiming an H1/H2",
        "physical win, novel solver or guaranteed RSS acceptance. No public push or",
        "submission occurred. This source-engineering authorization is now exhausted.",
        "",
        "```bash",
        "export UV_CACHE_DIR=/tmp/dsre-evidence-uv PYTHONPATH=src:scripts:.",
        "uv run --no-sync python scripts/rpd_isolation_reproduce.py --verify",
        "uv run --no-sync python scripts/rpd_isolation_reproduce.py --clean --output /tmp/rpd-isolation-review",
        "uv run --no-sync pytest -q tests",
        "```",
        "",
        "Use a fresh output directory. Reproduction is offline and launches no simulator.",
        "",
    ]
    DOC.parent.mkdir(exist_ok=True)
    DOC.write_text("\n".join(lines))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-only", action="store_true")
    report(parser.parse_args().json_only)
