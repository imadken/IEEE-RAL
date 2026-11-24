"""Build one compact private handoff; validate old seals and fresh ZIP read-back."""

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

BASE = Path(__file__).resolve().parents[1]
REPO = BASE.parents[1]
RELATIVE = BASE.relative_to(REPO).as_posix()
NAME = "RPD_RSS2027_V45_FROZEN_AND_PILOT_HANDOFF.zip"
FREEZE = "e644addb5848545e8c114974a62e52eb7a080682"
OLD = (
    REPO
    / "research/rpd_assembly_preliminary_20261120/delivery/RPD_V21_ASSEMBLY_COMPLETE_HANDOFF_20261120.zip"
)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def git(*args):
    return subprocess.check_output(["git", *args], cwd=REPO, text=True).strip()


def safe(name):
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"Unsafe archive path: {name}")


def main():
    output = BASE / NAME
    if output.exists():
        raise FileExistsError("Refuse to overwrite an existing handoff")
    assert not git("diff", FREEZE, "--", f"{RELATIVE}/paper_freeze/V45_FROZEN")
    assert not git("status", "--porcelain", "--", RELATIVE), (
        "Commit scoped handoff changes first"
    )
    payload = {}
    for raw in git("ls-files", "--", RELATIVE).splitlines():
        path = REPO / raw
        local = path.relative_to(BASE).as_posix()
        if local.startswith("paper_freeze/V45_FROZEN/"):
            name = "paper_frozen/" + local.removeprefix("paper_freeze/V45_FROZEN/")
        elif local.startswith("paper_frozen/"):
            continue
        else:
            name = local
        safe(name)
        assert name not in payload
        payload[name] = path.read_bytes()
    with zipfile.ZipFile(OLD) as old:
        assert old.testzip() is None
        manifest = json.loads(old.read("BUNDLE_MANIFEST.json"))
        assert manifest["commit"] == "280f821cdfb9e3b714bceccd6fa053bf45f9f28c"
        for name, expected in manifest["files"].items():
            content = old.read(name)
            assert digest(content) == expected["sha256"], name
        for name in old.namelist():
            safe(name)
            if not name.endswith("/"):
                payload["reproduce/historical_v21/" + name] = old.read(name)
    dev = json.loads((BASE / "experiments/LOCAL_DEVELOPMENT_COMMIT.json").read_text())
    commits = {
        "handoff": git("rev-parse", "HEAD"),
        "paper_freeze": FREEZE,
        "paper_freeze_tree": git(
            "rev-parse", f"{FREEZE}:{RELATIVE}/paper_freeze/V45_FROZEN"
        ),
        "development_registration": dev["prospective_source_jobs"],
        "development_outcomes": dev["outcomes_and_independent_audit"],
        "development_final": dev["development_final_commit"],
        "historical_source": "280f821cdfb9e3b714bceccd6fa053bf45f9f28c",
    }
    payload["LOCAL_COMMITS.json"] = (json.dumps(commits, indent=2) + "\n").encode()
    payload["START_HERE.md"] += (
        "\nExact handoff commit: `" + commits["handoff"] + "`.\n"
    ).encode()
    payload["reproduce/provenance_path_map.json"] = (
        json.dumps(
            {
                "repository_prefix": RELATIVE,
                "new_repo_paths": "Strip repository_prefix; paper_freeze/V45_FROZEN maps to paper_frozen",
                "historical_repo_paths": "reproduce/historical_v21/repo/<repository relative path>",
                "scope": "Complete current assembly source evidence and preserved V2.1; not every historical repository artifact",
                "historical_archive_sha256": digest(OLD.read_bytes()),
            },
            indent=2,
        )
        + "\n"
    ).encode()
    sha_manifest = "".join(
        f"{digest(content)}  {name}\n" for name, content in sorted(payload.items())
    )
    payload["SHA256SUMS.txt"] = sha_manifest.encode()
    temporary = output.with_suffix(".zip.tmp")
    with zipfile.ZipFile(
        temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        for name, content in sorted(payload.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 11, 21, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, content, compresslevel=9)
    # Read the written archive anew, including all raw source traces and failures.
    with zipfile.ZipFile(temporary) as archive:
        assert archive.testzip() is None
        for name, expected in payload.items():
            assert digest(archive.read(name)) == digest(expected), name
        with tempfile.TemporaryDirectory(
            prefix="rpd-v45-zip-reproduction-"
        ) as directory:
            root = Path(directory)
            for name in archive.namelist():
                if name.startswith("paper_frozen/"):
                    safe(name)
                    destination = root / name
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(archive.read(name))
            command = [
                sys.executable,
                str(root / "paper_frozen/build_paper.py"),
                "--source",
                str(root / "paper_frozen"),
                "--output",
                str(root / "fresh_build"),
            ]
            result = subprocess.run(
                command, capture_output=True, text=True, timeout=240, check=False
            )
            if result.returncode:
                raise RuntimeError(result.stdout + result.stderr)
            expected = digest(
                payload["paper_frozen/submission/rpd_stage1_anonymous_V45_FROZEN.pdf"]
            )
            assert digest((root / "fresh_build/main.pdf").read_bytes()) == expected
            build = json.loads((root / "fresh_build/build_check.json").read_text())
    receipt = {
        "payload_members_verified": len(payload),
        "all_CRCs_passed": True,
        "every_payload_SHA256_verified_by_fresh_read_back": True,
        "original_historical_manifest_checked": True,
        "SHA256SUMS_sha256": digest(payload["SHA256SUMS.txt"]),
        "frozen_source_build_from_fresh_ZIP_extraction": True,
        "extracted_build_PDF_binary_identical": True,
        "frozen_PDF_sha256": expected,
        "pages": build["pages"],
        "content_pages": build["content_pages"],
        "reference_pages": build["reference_pages"],
        "receipt_self_hash_excluded": True,
        "scope": "Payload verified before adding this receipt; whole final ZIP protected by externally supplied SHA256",
    }
    with zipfile.ZipFile(
        temporary, "a", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        archive.writestr(
            "ZIP_VERIFICATION_RECEIPT.json", json.dumps(receipt, indent=2) + "\n"
        )
    with zipfile.ZipFile(temporary) as archive:
        assert archive.testzip() is None
        for name, content in payload.items():
            assert digest(archive.read(name)) == digest(content), name
        assert json.loads(archive.read("ZIP_VERIFICATION_RECEIPT.json")) == receipt
    assert temporary.stat().st_size <= 50_000_000, "Handoff exceeds user's50MB maximum"
    os.replace(temporary, output)
    receipt.update(
        {
            "ZIP_sha256": digest(output.read_bytes()),
            "ZIP_bytes": output.stat().st_size,
            "final_archive_fresh_read_back_passed": True,
            "commits": commits,
        }
    )
    (BASE / "ZIP_VERIFICATION_RECEIPT.json").write_text(
        json.dumps(receipt, indent=2) + "\n"
    )
    (BASE / "LOCAL_COMMITS.json").write_text(json.dumps(commits, indent=2) + "\n")
    (BASE / "SHA256SUMS.txt").write_text(sha_manifest)
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
