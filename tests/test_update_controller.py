"""Pieces of the updater that need Qt installed but no network."""

import io
import json
import tarfile
from datetime import date

import pytest

from aperture.build import load_build_info

pytest.importorskip("PySide6.QtNetwork")

from aperture.update.controller import (  # noqa: E402
    PENDING_FILE,
    apply_pending,
    mark_launched,
    safe_extract,
    sha256_of,
)
from aperture.update.install import Installation  # noqa: E402


def test_build_info(tmp_path):
    stamped = tmp_path / "build_info.json"
    stamped.write_text(json.dumps({"date": "2026-11-02", "commit": "0123456789abcdef"}))
    info = load_build_info(stamped)
    assert info.released == date(2026, 11, 2) and info.commit == "0123456789ab"
    assert load_build_info(tmp_path / "missing.json").released is None


def write_pending(data_dir, **fields):
    (data_dir / PENDING_FILE).write_text(json.dumps(fields))


def test_pending_update_for_an_older_version_is_discarded(tmp_path):
    new = tmp_path / "Aperture.AppImage.update"
    new.write_bytes(b"x")
    write_pending(tmp_path, kind="appimage", file=str(new), version="0.0.1", sha256=sha256_of(new))
    install = Installation("appimage", tmp_path / "Aperture.AppImage")
    assert apply_pending(tmp_path, install) is False
    assert not new.exists() and not (tmp_path / PENDING_FILE).exists()


def test_pending_update_with_a_bad_checksum_is_discarded(tmp_path):
    new = tmp_path / "setup.exe"
    new.write_bytes(b"tampered")
    fields = {"kind": "windows-installer", "file": str(new), "version": "99.0.0"}
    write_pending(tmp_path, sha256="0" * 64, **fields)
    assert apply_pending(tmp_path, Installation("windows-installer", tmp_path)) is False
    assert not new.exists()


def test_pending_update_for_another_install_kind_is_ignored(tmp_path):
    write_pending(tmp_path, kind="appimage", file="x", version="99.0.0", sha256="")
    assert apply_pending(tmp_path, Installation("tarball", tmp_path)) is False


def test_mark_launched(tmp_path):
    mark_launched(tmp_path)
    assert (tmp_path / "launched").read_text()


def make_tar(path, members):
    with tarfile.open(path, "w:xz") as tar:
        for name, data in members.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))


def test_safe_extract(tmp_path):
    good = tmp_path / "good.tar.xz"
    make_tar(good, {"aperture/aperture": b"#!/bin/sh\n"})
    safe_extract(good, tmp_path / "out")
    assert (tmp_path / "out" / "aperture" / "aperture").is_file()


def test_safe_extract_refuses_escaping_paths(tmp_path):
    evil = tmp_path / "evil.tar.xz"
    make_tar(evil, {"../outside.txt": b"gotcha"})
    with pytest.raises(tarfile.TarError):
        safe_extract(evil, tmp_path / "out")
    assert not (tmp_path / "outside.txt").exists()
