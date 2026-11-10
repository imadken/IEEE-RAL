"""Record artifact and source integrity; model assets are bundled in locked wheels."""

import hashlib
import importlib.util
import json
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


assets = {}
for name in ["mani_skill", "robosuite", "sapien"]:
    root = Path(importlib.util.find_spec(name).origin).parent
    files = sorted(
        p
        for p in root.rglob("*")
        if p.is_file()
        and (
            p.suffix in {".xml", ".urdf", ".stl", ".obj", ".dae", ".so"}
            or ".so." in p.name
        )
    )
    inventory = {str(p.relative_to(root)): digest(p) for p in files}
    assets[name] = inventory
sources = {
    str(p): digest(p)
    for root in ["src", "scripts", "tests"]
    for p in Path(root).rglob("*.py")
}
sources.update({p: digest(Path(p)) for p in ["uv.lock", "pyproject.toml"]})
Path("results/integrity.json").write_text(
    json.dumps({"source": sources, "bundled_assets": assets}, indent=2)
)
print("Saved source and simulator asset SHA-256 inventory")
