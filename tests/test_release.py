from datetime import datetime, timezone

import pytest

from aperture.core.release import (
    changelog_summary,
    is_newer,
    parse_checksums,
    parse_release,
    parse_version,
    pick_asset,
)

API = {
    "tag_name": "v0.5.0",
    "published_at": "2026-11-02T10:15:00Z",
    "html_url": "https://github.com/sentack/aperture_vplayer/releases/tag/v0.5.0",
    "body": "# Aperture 0.5.0\n\nIntro.\n\n## Downloads\n- exe\n- dmg\n\n## New\n- About tab\n",
    "draft": False,
    "assets": [
        {"name": n, "browser_download_url": f"https://github.com/x/{n}", "size": 10}
        for n in (
            "Aperture-0.5.0-windows-x64-setup.exe",
            "Aperture-0.5.0-macos-arm64.dmg",
            "Aperture-0.5.0-x86_64.AppImage",
            "Aperture-0.5.0-linux-x64.tar.xz",
            "SHA256SUMS.txt",
        )
    ]
    + [{"name": "evil.exe", "browser_download_url": "http://insecure/evil.exe"}],
}


@pytest.mark.parametrize(
    ("newer", "older"),
    [
        ("v0.5.0", "0.4.0"),
        ("0.10.0", "0.9.9"),
        ("1.0.0", "0.99.99"),
        ("0.5.0", "0.5.0-beta.2"),
        ("0.5.0-beta.10", "0.5.0-beta.2"),
        ("0.5.0-rc.1", "0.5.0-beta.9"),
    ],
)
def test_version_order(newer, older):
    assert is_newer(newer, older)
    assert not is_newer(older, newer)


def test_same_or_invalid_versions_are_not_newer():
    assert not is_newer("0.4.0", "v0.4.0")
    assert not is_newer("latest", "0.4.0")
    assert parse_version("0.4") is None


def test_parse_release():
    release = parse_release(API)
    assert release.version == "0.5.0"
    assert release.published == datetime(2026, 11, 2, 10, 15, tzinfo=timezone.utc)
    assert release.page.endswith("/v0.5.0")
    assert release.asset("SHA256SUMS.txt") is not None
    assert release.asset("evil.exe") is None  # non-HTTPS download links are dropped


@pytest.mark.parametrize(
    "data", [None, [], {"tag_name": "nightly"}, {"tag_name": "v1.0.0", "draft": True}]
)
def test_parse_release_rejects_non_releases(data):
    assert parse_release(data) is None


@pytest.mark.parametrize(
    ("kind", "name"),
    [
        ("windows-installer", "Aperture-0.5.0-windows-x64-setup.exe"),
        ("macos-dmg", "Aperture-0.5.0-macos-arm64.dmg"),
        ("appimage", "Aperture-0.5.0-x86_64.AppImage"),
        ("tarball", "Aperture-0.5.0-linux-x64.tar.xz"),
    ],
)
def test_pick_asset(kind, name):
    assert pick_asset(parse_release(API), kind).name == name


def test_pick_asset_unknown_kind():
    assert pick_asset(parse_release(API), "source") is None


def test_parse_checksums():
    text = (
        "a" * 64 + "  Aperture-0.5.0-x86_64.AppImage\n"
        + "B" * 64 + " *Aperture-0.5.0-windows-x64-setup.exe\n"
        + "not a checksum line\n"
    )
    assert parse_checksums(text) == {
        "Aperture-0.5.0-x86_64.AppImage": "a" * 64,
        "Aperture-0.5.0-windows-x64-setup.exe": "b" * 64,
    }


def test_changelog_summary_drops_title_and_downloads():
    assert changelog_summary(API["body"]) == "Intro.\n\n## New\n- About tab"


def test_changelog_summary_is_trimmed():
    summary = changelog_summary("\n".join(f"- item {i}" for i in range(100)), max_lines=5)
    assert summary.count("\n- item") == 4 and summary.endswith("…")
