#!/usr/bin/env python3
"""Install a locally supplied, trusted paper workspace without publishing it.

A release contains exactly one papers/<name>/ workspace and a SHA256SUMS.txt
inventory. Use --base papers/<current> to preserve the author's existing LaTeX
and Figure 1 while replacing only Figure 2 in the new sibling workspace.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path, PurePosixPath
import shutil
import stat
import subprocess
import tempfile
import zipfile


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract_workspace(archive: Path, temp: Path) -> Path:
    with zipfile.ZipFile(archive) as bundle:
        names = bundle.namelist()
        if len(names) != len(set(names)):
            raise ValueError("Duplicate ZIP member")
        roots = set()
        for member in bundle.infolist():
            p = PurePosixPath(member.filename)
            if p.is_absolute() or ".." in p.parts or "\\" in member.filename:
                raise ValueError(f"Unsafe ZIP path: {member.filename}")
            if stat.S_ISLNK(member.external_attr >> 16):
                raise ValueError(f"Symbolic links are not allowed: {member.filename}")
            if p.parts[:1] == ("papers",) and len(p.parts) >= 2:
                roots.add(p.parts[1])
        if len(roots) != 1:
            raise ValueError("Expected exactly one paper workspace")
        if bundle.testzip() is not None:
            raise ValueError("Damaged ZIP")
        bundle.extractall(temp)
    root = temp / "papers" / roots.pop()
    manifest = root / "SHA256SUMS.txt"
    for line in manifest.read_text().splitlines():
        expected, name = line.split("  ", 1)
        p = PurePosixPath(name)
        if p.is_absolute() or ".." in p.parts or not p.parts:
            raise ValueError(f"Unsafe manifest path: {name}")
        if digest(root / p) != expected:
            raise ValueError(f"Checksum mismatch: {name}")
    return root


def overlay_local_source(stage: Path, base: Path) -> None:
    """Preserve the existing source and Figure 1; install the release's Figure 2."""
    local = base / "manuscript"
    if not (local / "main.tex").is_file() or not (local / "figures/figure1.pdf").is_file():
        raise ValueError("Base must be a paper workspace with manuscript/ and Figure 1")
    figure_dir = stage / "manuscript/figures"
    replacement = {name: (figure_dir / name).read_bytes() for name in ("figure2.pdf", "figure2.svg")}
    previous = figure_dir / "archive" / "author_local_base"
    shutil.copytree(local / "figures", previous, dirs_exist_ok=False)
    shutil.copytree(local, stage / "manuscript", dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("*.aux", "*.bbl", "*.blg", "*.log", "*.out", "main.pdf"))
    for name, content in replacement.items():
        (figure_dir / name).write_bytes(content)
    (stage / "docs/LOCAL_BASE_RECEIPT.txt").write_text(
        "Existing manuscript source and Figure 1 preserved.\n"
        f"Local body.tex SHA256: {digest(local / 'body.tex')}\n"
        f"Local Figure 1 PDF SHA256: {digest(local / 'figures/figure1.pdf')}\n"
    )


def exclude_locally(repo: Path, relative: Path) -> None:
    result = subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "--path-format=absolute", "--git-path", "info/exclude"],
        text=True,
    ).strip()
    exclude = Path(result)
    exclude.parent.mkdir(parents=True, exist_ok=True)
    prior = exclude.read_text() if exclude.exists() else ""
    pattern = f"/{relative.as_posix()}/"
    if pattern not in prior.splitlines():
        with exclude.open("a") as f:
            f.write(f"\n{pattern}\n")


def install(archive: Path, repo: Path, base: Path | None = None) -> Path:
    repo = Path(subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "--show-toplevel"], text=True
    ).strip()).resolve()
    with tempfile.TemporaryDirectory(prefix="private-paper-") as temp:
        stage = extract_workspace(archive, Path(temp))
        relative = Path("papers") / stage.name
        dest = repo / relative
        if dest.exists():
            raise FileExistsError(f"Refusing to overwrite {dest}")
        if base is not None:
            base = (repo / base).resolve() if not base.is_absolute() else base.resolve()
            if not base.is_relative_to(repo / "papers"):
                raise ValueError("Base must be inside the repository's papers/ directory")
            overlay_local_source(stage, base)
        subprocess.run(["make", "paper"], cwd=stage, check=True)
        subprocess.run(["make", "check"], cwd=stage, check=True)
        shutil.rmtree(stage / "build", ignore_errors=True)
        files = sorted(p for p in stage.rglob("*") if p.is_file() and p.name != "SHA256SUMS.txt")
        (stage / "SHA256SUMS.txt").write_text("".join(
            f"{digest(p)}  {p.relative_to(stage).as_posix()}\n" for p in files
        ))
        exclude_locally(repo, relative)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(stage, dest)
    return dest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, help="Trusted local workspace ZIP")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--base", type=Path, help="Existing local paper workspace to preserve")
    args = parser.parse_args()
    result = install(args.archive.resolve(), args.repo.resolve(), args.base)
    print(f"Installed privately: {result}")
    print(f"PDF: {result / 'submission/rss2027_stage1_anonymous.pdf'}")
    print("No manuscript files were committed or pushed.")


if __name__ == "__main__":
    main()
