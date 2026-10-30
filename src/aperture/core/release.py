"""Reading GitHub release data: versions, the right download for this system, checksums.

The release workflow publishes, for every version, one asset per platform plus
`SHA256SUMS.txt`. Nothing here touches the network; the update controller feeds it JSON.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime

CHECKSUMS_ASSET = "SHA256SUMS.txt"

_VERSION = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?$")


def parse_version(text: str) -> tuple[int, int, int, tuple[object, ...]] | None:
    """`v0.4.0` / `0.4.0-beta.2` as a comparable key, or None if it is not a version.

    A pre-release sorts before its release (0.5.0-beta < 0.5.0), as in semantic versioning.
    """
    match = _VERSION.match(text.strip())
    if match is None:
        return None
    major, minor, patch, pre = match.groups()
    # The release itself gets an empty-but-larger marker so it outranks any pre-release.
    pre_key: tuple[object, ...] = (1,) if pre is None else (0, *_pre_parts(pre))
    return int(major), int(minor), int(patch), pre_key


def _pre_parts(pre: str) -> tuple[object, ...]:
    return tuple((0, int(p)) if p.isdigit() else (1, p) for p in pre.split("."))


def is_newer(candidate: str, current: str) -> bool:
    new, old = parse_version(candidate), parse_version(current)
    return new is not None and old is not None and new > old


@dataclass(frozen=True, slots=True)
class Asset:
    name: str
    url: str
    size: int


@dataclass(frozen=True, slots=True)
class Release:
    version: str  # without the leading "v"
    published: datetime | None
    notes: str
    page: str
    assets: tuple[Asset, ...] = field(default_factory=tuple)

    def asset(self, name: str) -> Asset | None:
        return next((a for a in self.assets if a.name == name), None)


def parse_release(data: object) -> Release | None:
    """A Release from the GitHub `releases/latest` JSON, or None if it does not look like one."""
    if not isinstance(data, dict) or data.get("draft"):
        return None
    tag = data.get("tag_name")
    if not isinstance(tag, str) or parse_version(tag) is None:
        return None
    published = None
    stamp = data.get("published_at")
    if isinstance(stamp, str):
        try:
            published = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
        except ValueError:
            published = None
    assets = []
    for item in data.get("assets") or []:
        if not isinstance(item, dict):
            continue
        name, url, size = item.get("name"), item.get("browser_download_url"), item.get("size", 0)
        if isinstance(name, str) and isinstance(url, str) and url.startswith("https://"):
            assets.append(Asset(name, url, size if isinstance(size, int) else 0))
    notes = data.get("body") if isinstance(data.get("body"), str) else ""
    page = data.get("html_url") if isinstance(data.get("html_url"), str) else ""
    return Release(tag.lstrip("v"), published, notes, page, tuple(assets))


# How each kind of installation finds its file among a release's assets.
_PATTERNS = {
    "windows-installer": re.compile(r"^Aperture-[^/]+-windows-x64-setup\.exe$"),
    "macos-dmg": re.compile(r"^Aperture-[^/]+-macos-arm64\.dmg$"),
    "appimage": re.compile(r"^Aperture-[^/]+-x86_64\.AppImage$"),
    "tarball": re.compile(r"^Aperture-[^/]+-linux-x64\.tar\.xz$"),
}


def pick_asset(release: Release, install_kind: str) -> Asset | None:
    pattern = _PATTERNS.get(install_kind)
    if pattern is None:
        return None
    return next((a for a in release.assets if pattern.match(a.name)), None)


def parse_checksums(text: str) -> dict[str, str]:
    """`sha256sum` output (`<hex>  <name>`, or `<hex> *<name>`) as name -> lowercase hex."""
    sums = {}
    for line in text.splitlines():
        match = re.match(r"^([0-9a-fA-F]{64}) [ *](.+)$", line.strip())
        if match:
            sums[match[2].strip()] = match[1].lower()
    return sums


def changelog_summary(notes: str, max_lines: int = 40) -> str:
    """Release notes without the title and Downloads section, trimmed for the About tab."""
    out, skipping = [], False
    for line in notes.replace("\r\n", "\n").split("\n"):
        if line.startswith("# "):
            continue  # the title repeats the version shown right above it
        if line.startswith("## "):
            skipping = line[3:].strip().lower() == "downloads"
            if skipping:
                continue
        if not skipping:
            out.append(line)
    text = "\n".join(out).strip()
    lines = text.split("\n")
    if len(lines) > max_lines:
        text = "\n".join(lines[:max_lines]).rstrip() + "\n\n…"
    return text
