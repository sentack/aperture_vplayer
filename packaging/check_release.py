"""Check a set of built files is exactly what a release publishes, and write SHA256SUMS.txt.

Run by the release workflow right before publishing, and by every pull request into main
on the PR's own build, so a release cannot fail on something a PR did not catch.

    python packaging/check_release.py dist
"""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHECKSUMS = "SHA256SUMS.txt"


def version() -> str:
    text = (ROOT / "src" / "aperture" / "__init__.py").read_text(encoding="utf-8")
    return re.search(r'__version__ = "([^"]+)"', text)[1]


def expected_files(ver: str) -> list[str]:
    return [
        f"Aperture-{ver}-windows-x64-setup.exe",
        f"Aperture-{ver}-macos-arm64.dmg",
        f"Aperture-{ver}-x86_64.AppImage",
        f"Aperture-{ver}-linux-x64.tar.xz",
    ]


def check(dist: Path, notes: Path, ver: str) -> list[str]:
    problems = []
    for name in expected_files(ver):
        path = dist / name
        if not path.is_file() or path.stat().st_size == 0:
            problems.append(f"missing or empty: {name}")
    try:
        title = notes.read_text(encoding="utf-8").splitlines()[0].strip()
    except (OSError, IndexError):
        title = ""
    if title != f"# Aperture {ver}":
        problems.append(f"{notes.name} must start with '# Aperture {ver}', found '{title}'")
    return problems


def write_checksums(dist: Path) -> Path:
    """sha256sum-format list of every file in `dist` (the in-app updater verifies against it)."""
    lines = []
    for path in sorted(p for p in dist.iterdir() if p.is_file() and p.name != CHECKSUMS):
        digest = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                digest.update(chunk)
        lines.append(f"{digest.hexdigest()}  {path.name}")
    out = dist / CHECKSUMS
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def main(argv: list[str]) -> int:
    dist = Path(argv[1] if len(argv) > 1 else "dist")
    ver = version()
    problems = check(dist, ROOT / "RELEASE_NOTES.md", ver)
    for problem in problems:
        print(problem, file=sys.stderr)
    if problems:
        return 1
    print(write_checksums(dist).read_text(encoding="utf-8"), end="")
    print(f"release {ver}: all files present, notes titled, checksums written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
