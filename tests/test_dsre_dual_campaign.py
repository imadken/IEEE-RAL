"""Source immutability and whole-cohort sidecar sealing without physics."""

import gzip
import json
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def scripts(monkeypatch):
    monkeypatch.syspath_prepend(str(Path("scripts").resolve()))


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


def test_source_and_native_drift_block_before_physics(tmp_path):
    from dsre_dual_adjudication import sha
    from dsre_dual_campaign import environment
    from dsre_runtime_recovery import ENV_FIELDS, configured_environment

    source = tmp_path / "frozen_source"
    source.write_text("unchanged")
    native = tmp_path / "native_library"
    native.write_text("unchanged")
    override = {"VK_ICD_FILENAMES": "/usr/share/vulkan/icd.d/lvp_icd.x86_64.json"}
    env = configured_environment(override)
    put(
        tmp_path / "source_freeze.json",
        {"source_sha256": {str(source): sha(source)}, "input_sha256": {}},
    )
    put(
        tmp_path / "execution_configuration.json",
        {
            "overrides": override,
            "process_configuration": {name: env.get(name) for name in ENV_FIELDS},
        },
    )
    put(
        tmp_path / "runtime_candidate_fingerprint.json",
        {
            "native_binaries": {str(native): {"sha256": sha(native)}},
            "old_package_hash_comparison": {"files": []},
        },
    )
    assert environment(tmp_path)["VK_ICD_FILENAMES"] == override["VK_ICD_FILENAMES"]
    source.write_text("drift")
    with pytest.raises(AssertionError):
        environment(tmp_path)
    source.write_text("unchanged")
    native.write_text("drift")
    with pytest.raises(AssertionError):
        environment(tmp_path)


def test_all128_sidecars_are_sealed_and_b7_shares_the_same_claim(tmp_path, monkeypatch):
    import dsre_source_risk
    from dsre_dual_adjudication import read, sha
    from dsre_dual_campaign import seal_test

    from dual_rec.dsre.dual_obligation import calibrate

    rows = [
        {
            "seed": n,
            "condition": str(i),
            "c": False,
            "r": False,
            "proposals": {"DSRE_risk": "recover", "CART2_beta10": "recover"},
        }
        for n in range(256)
        for i in range(5)
    ]
    put(
        tmp_path / "dual_calibration.json",
        {"bounds": calibrate(rows, tuple(range(256)))},
    )
    put(
        tmp_path / "dual_calibration_audit.json",
        {"calibration_sha256": sha(tmp_path / "dual_calibration.json")},
    )
    put(tmp_path / "study_plan.json", {"test_seeds": list(range(18000000, 18000128))})
    monkeypatch.setattr(
        dsre_source_risk,
        "seal_test",
        lambda root: put(
            root / "test_recommendation_seal.json", {"mock_transport_only": True}
        ),
    )
    for seed in range(18000000, 18000128):
        directory = tmp_path / "test" / str(seed)
        screen = directory / "nominal" / "screen.json.gz"
        screen.parent.mkdir(parents=True)
        with gzip.open(screen, "wt") as stream:
            json.dump(
                {
                    "scenarios": {
                        "clean": {
                            "point_proposal": {
                                name: {"action": "recover"}
                                for name in ("DSRE_risk", "B7_risk", "CART2_beta10")
                            }
                        }
                    }
                },
                stream,
            )
        put(directory / "decision.json", {"screens": {"nominal": sha(screen)}})
    seal_test(tmp_path)
    seal = read(tmp_path / "dual_test_seal.json")
    assert seal["parent_count"] == len(seal["parents"]) == 128
    for seed, expected in seal["parents"].items():
        path = tmp_path / "test" / seed / "dual_decision.json"
        assert sha(path) == expected
        data = read(path)["decisions"]["nominal"]
        assert data["DSRE_risk"] == data["B7_risk"]
        assert data["DSRE_risk"]["absolute"]["action"] is None
        assert (
            data["DSRE_risk"]["nondegradation"]["annotation"]
            == "TASK_NONDEGRADATION_QUALIFIED_ONLY"
        )
