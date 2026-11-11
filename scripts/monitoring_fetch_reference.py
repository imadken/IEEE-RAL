"""Restore only the pinned, hash-verified LOGIV text reference; install nothing."""

import argparse
import hashlib
import json
import urllib.request
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument(
        "--cache", type=Path, default=Path(".cache/monitoring-upstream")
    )
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    if manifest["commit"] != "0ea7a7ff765016a33409c54572d733bed4503d4d":
        raise ValueError("Unapproved reference revision")
    restored = []
    for item in manifest["files"]:
        relative = Path(item["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Invalid reference path")
        target = args.cache / relative
        if target.exists():
            data = target.read_bytes()
        else:
            url = f"https://raw.githubusercontent.com/Enqiao-Lu/LOGIV/{manifest['commit']}/{relative.as_posix()}"
            with urllib.request.urlopen(url, timeout=30) as response:
                data = response.read(500_001)
        blob = hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()
        if len(data) != item["size"] or blob != item["sha"]:
            raise ValueError(f"Reference integrity mismatch: {relative}")
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_bytes(data)
        restored.append(
            {"path": str(target), "sha256": hashlib.sha256(data).hexdigest()}
        )
    print(json.dumps(restored, indent=2))


if __name__ == "__main__":
    main()
