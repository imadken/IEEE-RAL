"""Independent vector/count audit of Stage 1 sensitivity, figures and preservation."""

import argparse
import hashlib
import json
import re
import subprocess
from collections import defaultdict
from pathlib import Path

import numpy as np
from dsre_final_verify import load_trace
from dsre_followup_batch import atomic, read, sha
from dsre_operational_analysis import qualified
from dsre_stage1_analysis import PRIOR, REFERENCE, TASKS


def has_reference_heading(text):
    return bool(re.search(r"(?m)^\s*R\s*E\s*F\s*E\s*R\s*E\s*N\s*C\s*E\s*S\b", text))


def preservation(root):
    initial = read(root / "initial.json")
    for filename, expected in initial["tracked_sha256"].items():
        if filename not in initial["allowed_existing_changes"]:
            assert sha(Path(filename)) == expected, filename
    for filename, expected in initial["unrelated_sha256"].items():
        assert sha(Path(filename)) == expected, filename
    for filename, expected in initial["historical_seals"].items():
        assert sha(Path(filename)) == expected, filename
    seal = read(PRIOR / "completion_manifest.json")
    for filename, expected in seal["files"].items():
        assert sha(PRIOR / filename) == expected, filename
    for filename, expected in seal["maintained_files"].items():
        original = subprocess.check_output(
            ["git", "show", initial["base"] + ":" + filename]
        )
        assert hashlib.sha256(original).hexdigest() == expected, filename
    transitive = {}
    for directory in (
        Path("results/dsre-operational/20261114T140659Z"),
        Path("results/dsre-followup/20261113T205403Z"),
    ):
        previous = read(directory / "completion_manifest.json")
        for filename, expected in previous["files"].items():
            assert sha(directory / filename) == expected, filename
        transitive[str(directory)] = len(previous["files"])
    for filename, expected in read(
        Path("results/dsre-followup/20261113T205403Z/initial.json")
    )["prior_run_members"].items():
        assert sha(Path(filename)) == expected, filename
    return {
        "status": "PASS",
        "old_sealed_members": len(seal["files"]),
        "historical_seals_manifests": len(initial["historical_seals"]),
        "tracked_at_start": len(initial["tracked_sha256"]),
        "full_master_tex_pdf_byte_identical": True,
        "transitive_immutable_members": transitive,
        "unrelated_files_unchanged": len(initial["unrelated_sha256"]),
    }


def weighted_interval(values, parent, weights):
    total = np.bincount(parent, weights=values, minlength=weights.shape[1])
    n = np.bincount(parent, minlength=weights.shape[1])
    return np.percentile((weights @ total) / (weights @ n), [2.5, 97.5]).tolist()


def independent_sensitivity(root):
    _, raw_rows, _ = qualified(PRIOR)
    raw = {}
    for r in raw_rows:
        trace = load_trace(r)
        raw[r["id"]] = (r, trace)
    frozen = read(PRIOR / "test_records.json")
    result = read(root / "stop_sensitivity.json")
    count_checks = interval_checks = 0
    for task_index, task in enumerate(TASKS):
        ids = sorted(k for k, (r, _) in raw.items() if r["task"] == task)
        rows = [raw[k][0] for k in ids]
        groups = sorted({r["group"] for r in rows})
        parent = np.asarray([groups.index(r["group"]) for r in rows])
        truth = np.asarray(
            [
                [
                    bool(raw[k][1]["traces"][a]["frames"][-1]["state"]["success"])
                    for a in ("continue", "recover")
                ]
                for k in ids
            ]
        )
        initial = np.asarray(
            [bool(raw[k][1]["canonical_start"]["success"]) for k in ids]
        )
        rng = np.random.Generator(np.random.PCG64(2026111401 + task_index))
        weights = np.asarray(
            [
                np.bincount(s, minlength=len(groups))
                for s in rng.integers(len(groups), size=(4000, len(groups)))
            ]
        )
        for mode in ("proposal", "calibrated"):
            methods = sorted({r["method"] for r in frozen})
            scores = {}
            for method in methods:
                decisions = {
                    r["id"]: r
                    for r in frozen
                    if r["task"] == task and r["mode"] == mode and r["method"] == method
                }
                action = np.asarray(
                    [
                        {"continue": 0, "recover": 1, None: -1}[decisions[k]["action"]]
                        for k in ids
                    ]
                )
                defer = action < 0
                for composition, fallback in (
                    ("primary", -1),
                    ("fallback_continue", 0),
                    ("fallback_recover", 1),
                ):
                    selected = np.where(defer, fallback, action)
                    acted = selected >= 0
                    good = acted & truth[np.arange(len(ids)), np.maximum(selected, 0)]
                    bad = acted & ~good
                    required = good & (selected == 1) & ~initial & ~truth[:, 0]
                    key = f"{task}|{mode}|{method}|{composition}"
                    scores[method, composition] = good.astype(int)
                    populations = {"": np.ones(len(ids), dtype=bool)}
                    for pop in (
                        "nominal",
                        "offset002",
                        "misaligned",
                        "continue_only",
                        "recover_only",
                        "both",
                        "neither",
                        "initial_success",
                        "initial_failure",
                    ):
                        populations["|" + pop] = np.asarray(
                            [
                                pop
                                in (
                                    r["condition"],
                                    decisions[k]["category"],
                                    "initial_success" if init else "initial_failure",
                                )
                                for r, k, init in zip(rows, ids, initial, strict=True)
                            ]
                        )
                    for suffix, mask in populations.items():
                        expected = result["counts"][key + suffix]
                        metrics = {
                            "N": int(mask.sum()),
                            "parents": len(set(parent[mask])),
                            "good": int((good & mask).sum()),
                            "bad": int((bad & mask).sum()),
                            "stop": int((~acted & mask).sum()),
                            "success_at_defer": int((defer & initial & mask).sum()),
                            "unsuccessful_at_defer": int(
                                (defer & ~initial & mask).sum()
                            ),
                            "required_recovery": int((required & mask).sum()),
                            "maintained": int((good & initial & mask).sum()),
                            "parent_any_error": len(set(parent[mask & bad])),
                        }
                        for field, v in metrics.items():
                            assert expected[field] == v, (
                                key,
                                suffix,
                                field,
                                v,
                                expected[field],
                            )
                            count_checks += 1
                        for a, label in enumerate(("continue", "recover")):
                            assert expected["assignment_errors"][label] == {
                                "assigned_parents": len(
                                    set(parent[mask & (selected == a)])
                                ),
                                "error_parents": len(
                                    set(parent[mask & bad & (selected == a)])
                                ),
                            }
                        if not mask.any():
                            assert expected["status"] == "EMPTY_NO_TRIALS"
                    ci = result["parent_completion_intervals"][key]
                    assert np.allclose(
                        weighted_interval(good.astype(int), parent, weights),
                        ci["ci95"],
                        rtol=0,
                        atol=1e-12,
                    )
                    assert float(good.mean()) == ci["value"]
                    interval_checks += 1
            for method in methods:
                for composition in ("primary", "fallback_continue", "fallback_recover"):
                    delta = (
                        scores["DSRE_risk", composition] - scores[method, composition]
                    )
                    key = f"{task}|{mode}|DSRE_risk-{method}|{composition}"
                    ci = result["paired_completion_contrasts"][key]
                    assert np.allclose(
                        weighted_interval(delta, parent, weights),
                        ci["ci95"],
                        rtol=0,
                        atol=1e-12,
                    )
                    assert float(delta.mean()) == ci["value"]
                    interval_checks += 1
    return {
        "status": "PASS",
        "count_fields_from_raw": count_checks,
        "intervals_recomputed_with_parent_weights": interval_checks,
        "new_fits_physics_calibration_updates": 0,
    }


def figures(root):
    data = read(root / "stage1_figure_data.json")
    sensitivity = read(root / "stop_sensitivity.json")["counts"]
    summary = read(root / "source_audit.json")["summary"]
    checked = 0
    for point in data["outcomes"]:
        task, label, field = (point[n] for n in ("task", "label", "field"))
        if label.startswith("Raw"):
            _, rows, _ = qualified(PRIOR)
            rs = [r for r in rows if r["task"] == task]
            action = "continue" if label == "Raw C" else "recover"
            good = [r for r in rs if r["outcomes"][action + "_value"]]
            required = [
                r
                for r in good
                if action == "recover"
                and not r["initial_success"]
                and not r["outcomes"]["continue_value"]
            ]
            maintained = [r for r in good if r["initial_success"]]
            expected = {
                "maintained": len(maintained),
                "required_recovery": len(required),
                "other": len(good) - len(required) - len(maintained),
                "bad": len(rs) - len(good),
                "stop": 0,
            }[field]
        else:
            method = {
                "Strict": "DSRE_strict",
                "Risk": "DSRE_risk",
                "Ord./CART": "CART2_beta10",
                "Gated R": "B0_recover",
            }[label]
            row = sensitivity[f"{task}|calibrated|{method}|primary"]
            expected = (
                row["good"] - row["maintained"] - row["required_recovery"]
                if field == "other"
                else row[field]
            )
        assert point["count"] == expected and point["N"] == summary[task]["N"]
        checked += 1
    reference = [json.loads(s) for s in REFERENCE.read_text().splitlines()]
    robust = read(PRIOR / "heldout_robustness.json")["parent_intervals"]
    for point in data["limits"]:
        if point["kind"] == "finite":
            rs = [r for r in reference if r["task"] == point["task"]]
            b = point["budget"]
            indices = [] if b == 0 else [0] if b == 1 else list(range(6))
            groups = defaultdict(list)
            for r in rs:
                x = tuple(r["features"] + [r["optional_features"][i] for i in indices])
                groups[x].append(
                    int(r["outcomes"]["continue_value"])
                    + 2 * int(r["outcomes"]["recover_value"])
                )
            mass = sum(len(v) for v in groups.values() if np.bitwise_and.reduce(v))
            assert point["count"] == mass and point["N"] == len(rs)
        else:
            expected = robust[
                f"PickCube-v1|DSRE_strict|proposal|{point['scenario']}|all"
            ][point["metric"]]
            assert (
                point["value"] == expected["value"]
                and point["parent_percentile95"] == expected["parent_percentile95"]
            )
        checked += 1
    return {"status": "PASS", "numerical_points_checked": checked}


def pdf_checks(root):
    p = "rss2027/dsre_stage1.pdf"
    info = subprocess.check_output(["pdfinfo", p], text=True)
    text = subprocess.check_output(["pdftotext", "-layout", p, "-"], text=True)
    pages = [s for s in text.split("\f") if s.strip()]
    assert len(pages) == 6
    assert "REFERENCES" in pages[-1].replace(" ", "").upper()
    assert has_reference_heading(pages[-1])
    assert all(not has_reference_heading(s) for s in pages[:5])
    assert len(pages[4].split()) >= 350, "Page 5 must contain substantive content"
    for bad in (
        "imad",
        "/home/",
        "IEEE-RAL",
        "github.com",
        "http://",
        "https://",
        "acknowledgment",
        "acknowledgement",
    ):
        assert bad.lower() not in (info + text).lower(), bad
    assert not re.search(r"^Author:\s*\S", info, re.MULTILINE)
    assert all(
        not re.search(r"^\s*\d+\s*$", s.splitlines()[-1] if s.splitlines() else "")
        for s in pages
    )
    fonts = subprocess.check_output(["pdffonts", p], text=True)
    assert all("Type 1" in s and s.split()[-5] == "yes" for s in fonts.splitlines()[2:])
    source = Path("rss2027/dsre_stage1.tex").read_text()
    for bad in (
        r"\geometry",
        r"\textheight",
        r"\textwidth=",
        r"\baselinestretch",
        r"\vspace{-",
        r"\small",
        r"\scriptsize",
    ):
        assert bad not in source
    assert (
        sha(Path("rss2027/IEEEtran.cls"))
        == read(root / "initial.json")["tracked_sha256"]["rss2027/IEEEtran.cls"]
    )
    (root / "pdfinfo.txt").write_text(info)
    (root / "pdffonts.txt").write_text(fonts)
    (root / "paper_text.txt").write_text(text)
    return {
        "status": "PASS",
        "pages": 6,
        "content_pages": 5,
        "references_pages": 1,
        "words_by_page": [len(s.split()) for s in pages],
        "anonymous": True,
        "fonts_embedded_type1": True,
        "template_unchanged": True,
    }


def manuscript_claims(root):
    from dual_rec.dsre.repair_oracle import Oracle

    text = Path("rss2027/dsre_stage1.tex").read_text()
    audit = read(root / "source_audit.json")
    sensitivity = read(root / "stop_sensitivity.json")
    rows = read(root / "primary_rows.json")
    checks = []
    for task, first, last in (
        (TASKS[0], 8000181, 8000259),
        (TASKS[1], 9000180, 9000259),
    ):
        assert {r["group"] for r in rows if r["task"] == task} == {
            f"{task}/{s}" for s in range(first, last + 1)
        }
        s = audit["summary"][task]
        classes = "/".join(
            str(s["categories"][key]) for key in ("10", "01", "11", "00")
        )
        assert classes in text and f"{s['raw_continue']}/{s['raw_recover']}" in text
        assert str(s["N"]) in text and str(s["parents"]) in text
        for method in {r["method"] for r in read(PRIOR / "test_records.json")}:
            c = sensitivity["counts"][f"{task}|calibrated|{method}|primary"]
            token = f"{c['good']}/{c['bad']}/{c['stop']}"
            assert token in text, (task, method, token)
        for comp in ("primary", "fallback_continue", "fallback_recover"):
            c = sensitivity["paired_completion_contrasts"][
                f"{task}|calibrated|DSRE_risk-DSRE_strict|{comp}"
            ]
            lo, hi = c["ci95"]
            assert f"[{100 * lo:.2f},{100 * hi:.2f}]" in text
            assert f"{100 * c['value']:.2f}" in text
        for method in ("DSRE_strict", "DSRE_risk", "B0_continue", "B0_recover"):
            for comp in ("fallback_continue", "fallback_recover"):
                c = sensitivity["counts"][f"{task}|calibrated|{method}|{comp}"]
                assert f"{c['good']}/{c['bad']}" in text
        checks.append(
            {
                "task": task,
                "primary_source": str(PRIOR / "test_records.json"),
                "classes": classes,
                "raw_C_R": [s["raw_continue"], s["raw_recover"]],
                "all_method_rows_and_fixed_fallback_intervals_checked": True,
            }
        )
    cal = read(PRIOR / "calibration_decision.json")["strata"]
    for key in (
        "DSRE_risk|PickCube-v1|continue",
        "DSRE_risk|PickCube-v1|recover",
        "DSRE_risk|PushCube-v1|recover",
    ):
        c = cal[key]
        assert f"{c['assigned_parents']}/{c['error_parents']}" in text
        assert f"{100 * c['upper']:.3f}" in text
    predictions = read(PRIOR / "test_records.json")
    by = {
        (r["id"], r["method"]): r["action"]
        for r in predictions
        if r["mode"] == "calibrated"
    }
    for method in ("B7_risk", "CART1_beta10", "CART2_beta10"):
        assert all(
            by[r["id"], method] == r["action"]
            for r in predictions
            if r["method"] == "DSRE_risk" and r["mode"] == "calibrated"
        )
    frozen = read(PRIOR / "frozen_routers.json")
    cases = read(PRIOR / "physical_examples.json")["cases"]
    for case in cases[:5]:
        for budget, diagnosis in case["finite_reference_diagnoses"].items():
            task = case["id"].split("/")[0]
            setting = frozen["tasks"][task][budget]
            query = {
                "scope": setting["table"]["scope"],
                "features": case["features"]
                + [case["optional_features"][i] for i in setting["selected"]],
            }
            Oracle(setting["table"], setting["parent_groups"]).verify(query, diagnosis)
    case = cases[0]["finite_reference_diagnoses"]["1"]
    assert len(case["evidence"]) == 3 and case["independent_parents"] == 5
    setting = frozen["tasks"][TASKS[0]]["1"]
    signature = cases[0]["features"] + [
        cases[0]["optional_features"][i] for i in setting["selected"]
    ]
    matches = [r for r in setting["table"]["rows"] if r["features"] == signature]
    assert len({setting["parent_groups"][r["id"]] for r in matches}) == 2
    assert cases[5]["diagnosis"]["independent_parents"] == 1
    assert cases[5]["outcomes"] == {"continue_value": False, "recover_value": False}
    f = cases[5]
    setting = frozen["tasks"][f["id"].split("/")[0]]["1"]
    query = {
        "scope": setting["full_table"]["scope"],
        "features": f["features"] + f["optional_features"],
    }
    Oracle(setting["full_table"], setting["parent_groups"]).verify(
        query, f["diagnosis"]
    )
    g = cases[6]
    assert sha(Path(g["reference"])) == g["reference_sha256"]
    setting = read(Path(g["reference"]))
    query = {
        "scope": setting["table"]["scope"],
        "features": g["features"]
        + [g["optional_features"][i] for i in setting["selected"]],
    }
    assert not any(r["features"] == query["features"] for r in setting["table"]["rows"])
    assert (
        Oracle(setting["table"], setting["parent_groups"]).rule(query)["action"]
        == "continue"
    )
    assert g["outcomes"] == {"continue_value": False, "recover_value": True}
    history = read(Path("results/dsre-followup/20261113T205403Z/suffix_results.json"))
    pick = [r for r in history["decision_necessity_records"] if r["task"] == TASKS[0]]
    assert (
        sum(r["b0_success"] for r in pick) == 145
        and sum(r["b1_success"] for r in pick) == 187
    )
    assert sum(r["success_difference"] for r in pick if r["initial_success"]) == 40
    assert sum(r["required_recovery_success_difference"] for r in pick) == 1
    assert history["tables"]["PickCube-v1|1|CART2_beta10|all"]["successful"] == 240
    crossfit = read(
        Path("results/dsre-rss2027/20261113T193554Z/reused_stratified_tables.json")
    )
    for b, good, bad, failed in ((0, 202, 1, 19), (1, 242, 2, 18)):
        assert crossfit[f"PickCube-v1|{b}|DSRE|all"]["successful"] == good
        assert crossfit[f"PickCube-v1|{b}|DSRE|all"]["unacceptable"] == bad
        assert crossfit[f"PickCube-v1|{b}|DSRE|initial_failure"]["successful"] == failed
    robust = read(PRIOR / "heldout_robustness.json")["parent_intervals"]
    for scenario, metric in (
        ("noise005", "unacceptable"),
        ("delay5", "unacceptable"),
        ("noise005", "false_confidence"),
    ):
        value = robust[f"{TASKS[0]}|DSRE_strict|proposal|{scenario}|all"][metric][
            "value"
        ]
        assert f"{100 * value:.2f}" in text
    assert "preregistered primary" in text and "Post Hoc Abstention" in text
    assert (
        "No human escalation cost, hold effect or new risk qualification is inferred"
        in text
    )
    return {
        "status": "PASS",
        "task_claims": checks,
        "minimum_rule_and_literal_witnesses_independently_verified": True,
        "all_seventeen_methods_present": True,
        "historical_negatives_and_uncertified_strata_preserved": True,
        "metric_scope": "Primary unchanged; B observes defer state only; C unqualified post hoc policy composition",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument(
        "--stage", choices=("numerical", "pdf", "paper", "preservation"), required=True
    )
    args = parser.parse_args()
    value = {
        "numerical": lambda r: {
            "sensitivity": independent_sensitivity(r),
            "figures": figures(r),
        },
        "pdf": pdf_checks,
        "paper": manuscript_claims,
        "preservation": preservation,
    }[args.stage](args.root)
    atomic(args.root / f"stage1_{args.stage}_audit.json", value)
    print(json.dumps(value), flush=True)
