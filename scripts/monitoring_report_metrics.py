"""Reproducible report aggregates; frozen method code and endpoints stay intact."""

import argparse
import gzip
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from dual_rec.monitoring.analysis import PRIMARY_REGIMES, _load, _paired, _stats
from dual_rec.monitoring.contracts import Context
from dual_rec.monitoring.semantics import certify


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    split = args.root / "qualification"
    rows, skipped = _load(split / "decisions.jsonl.gz")
    primary = [r for r in rows if r.regime in PRIMARY_REGIMES and r.budget in (1, 2, 3)]
    methods = ("M0", "M1", "M2", "M3", "M3_no_consequence")
    result = {
        "primary_by_method": {
            m: _stats([r for r in primary if r.method == m], "report_primary_" + m)
            for m in methods
        },
        "primary_M1_minus_M0": _paired(primary, "M1", "M0", "report_primary_M1_M0"),
        "primary_M3_minus_M2": _paired(primary, "M3", "M2", "report_primary_M3_M2"),
        "skipped": skipped,
        "regime_pooled_budgets": {
            regime: {
                m: _stats(
                    [r for r in rows if r.method == m and r.regime == regime],
                    "report_" + regime + m,
                )
                for m in methods
            }
            for regime in ("complete", "delayed", "noise05", "invalidated")
        },
    }
    relevance = json.loads((split / "query_relevance.json").read_text())
    accurate = {
        "complete",
        "missing10",
        "missing30",
        "missing50",
        "structured",
        "delayed",
    }
    totals = {}
    for method in ("M0", "M1", "M2", "M3"):
        parts = [relevance["by_regime"][regime][method] for regime in accurate]
        totals[method] = {
            key: sum(p[key] for p in parts)
            for key in (
                "decisions",
                "query_events",
                "wholly_model_structurally_irrelevant_calls",
                "total_atom_reads",
                "atom_reads_outside_model_relevance_closure",
                "observed_answer_outside_prior_model_events",
            )
        }
    result["accurate_regime_query_relevance"] = totals
    with gzip.open(split / "episodes.jsonl.gz", "rt") as stream:
        episodes = {p["episode_id"]: p for p in (json.loads(s) for s in stream)}
    contexts = {}
    initial_status = {}
    secondary = defaultdict(
        lambda: {
            "decisions": 0,
            "permissions": 0,
            "false_current": 0,
            "invalid_suffix": 0,
            "recovery_invocations": 0,
            "certified_repairs": 0,
            "repair_limit_hits": 0,
            "actually_invalid_initially_unresolved": 0,
            "correctly_detected": 0,
            "detection_query_total": 0,
            "never_detected": 0,
            "recovery_cpu_seconds": 0.0,
        }
    )
    with gzip.open(split / "decisions.jsonl.gz", "rt") as stream:
        for line in stream:
            row = json.loads(line)
            if row.get("skip_reason"):
                continue
            key = row["method"] + "/" + row["regime"]
            group = secondary[key]
            group["decisions"] += 1
            group["permissions"] += row["continuation_permitted"]
            group["false_current"] += row["false_current_permission"]
            group["invalid_suffix"] += row["invalid_continuation_permission"]
            group["recovery_invocations"] += row["recovery_invoked"]
            group["certified_repairs"] += row["recovery_success"]
            group["repair_limit_hits"] += row["recovery"].get("limit_hits", 0)
            group["recovery_cpu_seconds"] += row["recovery"].get("cpu_seconds", 0.0)
            eid = row["episode_id"]
            if eid not in contexts:
                contexts[eid] = Context.model_validate(episodes[eid]["context"])
            if eid not in initial_status:
                ctx = contexts[eid]
                initial_status[eid] = certify(
                    ctx.model, ctx.evidence, ctx.plan, ctx.goal
                )
            if not row["oracle_plan_valid"] and initial_status[eid] == "UNRESOLVED":
                group["actually_invalid_initially_unresolved"] += 1
                detected = row["decision"]["status"] in {"INVALID", "CURRENT_INVALID"}
                group["correctly_detected"] += detected
                group["detection_query_total"] += row["query_count"] if detected else 0
                group["never_detected"] += not detected
    result["secondary_counts"] = dict(secondary)
    result["detection_scope"] = (
        "Actually invalid nominal suffix AND initial model-relative status UNRESOLVED; detection is final method INVALID/CURRENT_INVALID. Undetected retained explicitly."
    )
    (split / "report_metrics.json").write_text(
        json.dumps(result, indent=2, allow_nan=False)
    )
    print(
        json.dumps(
            {
                "primary_M1_minus_M0": result["primary_M1_minus_M0"],
                "accurate_query_relevance": totals,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
