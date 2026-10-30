"""Check for updates, download one in the background, verify it, and hand it to the updater.

Exposed to QML as `updates`. Checks happen only when the user asks (GitHub allows 60
unauthenticated API requests an hour per address). Every download is checked against the
release's SHA256SUMS.txt while it streams in; a release without checksums is not installed.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import shutil
import tarfile
import threading
from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import Property, QObject, QProcess, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

from aperture import __version__
from aperture.build import BuildInfo
from aperture.core.release import (
    CHECKSUMS_ASSET,
    Release,
    changelog_summary,
    is_newer,
    parse_checksums,
    parse_release,
    pick_asset,
)
from aperture.core.storage import read_json, write_json
from aperture.update.install import Installation
from aperture.update.scripts import POSIX_UPDATER, WINDOWS_UPDATER

log = logging.getLogger(__name__)

REPO = "sentack/aperture_vplayer"
LATEST_URL = f"https://api.github.com/repos/{REPO}/releases/latest"
RELEASES_PAGE = f"https://github.com/{REPO}/releases"
PENDING_FILE = "pending_update.json"
LAUNCH_MARKER = "launched"  # written on every successful start; the updater waits for it


def _date_label(value) -> str:
    return f"{value:%B} {value.day}, {value.year}" if value else ""


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def mark_launched(data_dir: Path) -> None:
    """Tell a waiting updater this version started fine."""
    try:
        (data_dir / LAUNCH_MARKER).write_text(__version__, encoding="utf-8")
    except OSError:
        log.warning("cannot write the launch marker", exc_info=True)


def start_updater(data_dir: Path, installation: Installation, new: Path) -> bool:
    """Write the updater for this platform and start it detached; the caller then quits."""
    folder = data_dir / "updates"
    folder.mkdir(parents=True, exist_ok=True)
    marker = data_dir / LAUNCH_MARKER
    process = QProcess()
    process.setStandardOutputFile(str(folder / "updater.log"), QProcess.OpenModeFlag.Append)
    process.setStandardErrorFile(str(folder / "updater.log"), QProcess.OpenModeFlag.Append)
    if installation.kind == "windows-installer":
        script = folder / "updater.ps1"
        script.write_text(WINDOWS_UPDATER, encoding="utf-8")
        process.setProgram("powershell")
        process.setArguments([
            "-NoProfile", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden",
            "-File", str(script), "-AppPid", str(os.getpid()), "-Installer", str(new),
            "-AppDir", str(installation.target), "-Marker", str(marker),
        ])  # fmt: skip
    else:
        script = folder / "updater.sh"
        script.write_text(POSIX_UPDATER, encoding="utf-8")
        process.setProgram("sh")
        process.setArguments([
            str(script), str(os.getpid()), str(new), str(installation.target),
            installation.kind, str(marker), "30",
        ])  # fmt: skip
    result = process.startDetached()  # (started, pid) in PySide6
    started = bool(result[0] if isinstance(result, tuple) else result)
    if not started:
        log.warning("could not start the updater: %s", process.errorString())
    return started


def apply_pending(data_dir: Path, installation: Installation) -> bool:
    """Install an update the user deferred ("later"). True means: quit now, the updater runs."""
    pending_path = data_dir / PENDING_FILE
    pending = read_json(pending_path) if pending_path.is_file() else None
    pending_path.unlink(missing_ok=True)
    if not isinstance(pending, dict) or pending.get("kind") != installation.kind:
        return False
    new = Path(str(pending.get("file", "")))
    if not is_newer(str(pending.get("version", "")), __version__) or not new.exists():
        _discard(new)  # already on that version (or newer), or the file went away
        return False
    expected = pending.get("sha256")
    if new.is_file() and (not isinstance(expected, str) or sha256_of(new) != expected):
        log.warning("deferred update %s failed verification; discarded", new)
        new.unlink(missing_ok=True)
        return False
    return start_updater(data_dir, installation, new)


def _discard(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)
    else:
        path.unlink(missing_ok=True)


def safe_extract(archive: Path, destination: Path) -> None:
    """Unpack a .tar.xz, refusing members that would land outside `destination`."""
    with tarfile.open(archive, "r:xz") as tar:
        try:
            tar.extractall(destination, filter="data")
        except TypeError:  # Python before 3.11.4 has no extraction filters
            root = destination.resolve()
            for member in tar.getmembers():
                if not (root / member.name).resolve().is_relative_to(root) or member.issym():
                    raise tarfile.TarError(f"unsafe path in archive: {member.name}") from None
            tar.extractall(destination)


class UpdateController(QObject):
    changed = Signal()
    progressChanged = Signal()
    noticed = Signal(str)
    _extracted = Signal(str, str)  # (staged folder or "", error), from the extraction thread

    def __init__(
        self,
        data_dir: Path,
        installation: Installation,
        build: BuildInfo,
        quit_app: Callable[[], None],
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._data_dir = data_dir
        self._install = installation
        self._build = build
        self._quit = quit_app
        self._network = QNetworkAccessManager(self)
        self._state = "idle"  # idle checking current available downloading ready opened error
        self._error = ""
        self._release: Release | None = None
        self._progress = 0.0
        self._reply: QNetworkReply | None = None
        self._ready: Path | None = None  # verified download (file) or staged folder
        self._ready_sha = ""
        self._extracted.connect(self._on_extracted)

    # --- state for QML -----------------------------------------------------

    @Property(str, notify=changed)
    def state(self) -> str:
        return self._state

    @Property(str, notify=changed)
    def error(self) -> str:
        return self._error

    @Property(str, constant=True)
    def currentVersion(self) -> str:
        return self._build.version

    @Property(str, constant=True)
    def currentDate(self) -> str:
        return _date_label(self._build.released)

    @Property(str, notify=changed)
    def latestVersion(self) -> str:
        return self._release.version if self._release else ""

    @Property(str, notify=changed)
    def latestDate(self) -> str:
        return _date_label(self._release.published) if self._release else ""

    @Property(str, notify=changed)
    def changelog(self) -> str:
        return changelog_summary(self._release.notes) if self._release else ""

    @Property(float, notify=progressChanged)
    def progress(self) -> float:
        return self._progress

    @Property(bool, constant=True)
    def canDownload(self) -> bool:
        return self._install.downloads

    @Property(bool, constant=True)
    def selfUpdates(self) -> bool:
        return self._install.self_updates

    @Property(str, constant=True)
    def hint(self) -> str:
        return self._install.hint

    @Property(str, notify=changed)
    def releasePage(self) -> str:
        return self._release.page if self._release and self._release.page else RELEASES_PAGE

    # --- commands ----------------------------------------------------------

    @Slot()
    def check(self) -> None:
        if self._state in ("checking", "downloading"):
            return
        self._set_state("checking")
        reply = self._network.get(self._request(QUrl(LATEST_URL), api=True))
        reply.finished.connect(lambda: self._on_checked(reply))

    @Slot()
    def update(self) -> None:
        """Download the build for this installation, verified against SHA256SUMS.txt."""
        release = self._release
        if release is None or self._state != "available" or not self._install.downloads:
            return
        asset = pick_asset(release, self._install.kind)
        sums = release.asset(CHECKSUMS_ASSET)
        if asset is None or sums is None:
            self._fail("This release has no verified download for your system. "
                       "Get it from the release page instead.")  # fmt: skip
            return
        self._set_state("downloading")
        self._set_progress(0.0)
        reply = self._network.get(self._request(QUrl(sums.url)))
        reply.finished.connect(lambda: self._on_checksums(reply, asset.name, asset.url))

    @Slot()
    def cancel(self) -> None:
        if self._reply is not None:
            self._reply.abort()

    @Slot()
    def restartNow(self) -> None:
        if self._state != "ready" or self._ready is None:
            return
        if start_updater(self._data_dir, self._install, self._ready):
            self._quit()
        else:
            self._fail("Couldn't start the updater. Try again, or install from the release page.")

    @Slot()
    def later(self) -> None:
        """Keep the verified update and install it the next time Aperture starts."""
        if self._state != "ready" or self._ready is None:
            return
        write_json(self._data_dir / PENDING_FILE, {
            "kind": self._install.kind, "file": str(self._ready),
            "version": self.latestVersion, "sha256": self._ready_sha,
        })  # fmt: skip
        self._set_state("scheduled")
        self.noticed.emit(f"Aperture {self.latestVersion} will install next time you open it")

    @Slot()
    def openReleasePage(self) -> None:
        QDesktopServices.openUrl(QUrl(self.releasePage))

    # --- network -----------------------------------------------------------

    def _request(self, url: QUrl, api: bool = False) -> QNetworkRequest:
        request = QNetworkRequest(url)
        request.setRawHeader(b"User-Agent", f"Aperture/{__version__}".encode())
        if api:
            request.setRawHeader(b"Accept", b"application/vnd.github+json")
        request.setAttribute(
            QNetworkRequest.Attribute.RedirectPolicyAttribute,
            QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy,
        )  # GitHub serves assets through a redirect to its file host, still HTTPS
        request.setTransferTimeout(30_000)
        return request

    def _on_checked(self, reply: QNetworkReply) -> None:
        reply.deleteLater()
        status = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        if reply.error() != QNetworkReply.NetworkError.NoError and status is None:
            self._fail("Couldn't reach GitHub. Check your internet connection and try again.")
            return
        if status in (403, 429):
            self._fail("GitHub limits update checks to 60 an hour. Try again a little later.")
            return
        if status == 404:
            self._fail("No published release was found.")
            return
        try:
            release = parse_release(json.loads(bytes(reply.readAll()).decode("utf-8")))
        except ValueError:
            release = None
        if release is None:
            self._fail("GitHub sent release information Aperture couldn't read.")
            return
        self._release = release
        self._set_state("available" if is_newer(release.version, __version__) else "current")

    def _on_checksums(self, reply: QNetworkReply, name: str, url: str) -> None:
        reply.deleteLater()
        if reply.error() != QNetworkReply.NetworkError.NoError:
            self._fail("Couldn't download the checksums for this release.")
            return
        expected = parse_checksums(bytes(reply.readAll()).decode("utf-8", "replace")).get(name)
        if expected is None:
            self._fail("This release can't be verified, so it won't be installed.")
            return
        target = self._download_path(name)
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            handle = target.open("wb")
        except OSError as exc:
            self._fail(f"Can't save the update: {exc.strerror or exc}")
            return
        digest = hashlib.sha256()
        reply = self._network.get(self._request(QUrl(url)))
        self._reply = reply

        def write() -> None:
            chunk = bytes(reply.readAll())
            digest.update(chunk)
            handle.write(chunk)

        reply.readyRead.connect(write)
        reply.downloadProgress.connect(
            lambda done, total: self._set_progress(done / total if total > 0 else 0.0)
        )
        reply.finished.connect(lambda: self._on_downloaded(reply, handle, digest, target, expected))

    def _on_downloaded(self, reply, handle, digest, target: Path, expected: str) -> None:
        self._reply = None
        reply.deleteLater()
        if reply.error() == QNetworkReply.NetworkError.NoError:
            chunk = bytes(reply.readAll())
            digest.update(chunk)
            handle.write(chunk)
        handle.close()
        if reply.error() == QNetworkReply.NetworkError.OperationCanceledError:
            target.unlink(missing_ok=True)
            self._set_state("available")
            return
        if reply.error() != QNetworkReply.NetworkError.NoError:
            target.unlink(missing_ok=True)
            self._fail("The download stopped. Check your connection and try again.")
            return
        if digest.hexdigest() != expected:
            target.unlink(missing_ok=True)
            self._fail("The download didn't match its checksum, so nothing was installed.")
            return
        self._ready_sha = expected
        if self._install.kind == "tarball":
            self._set_state("downloading")  # still busy: unpacking
            threading.Thread(target=self._extract, args=(target,), daemon=True).start()
            return
        self._finish_ready(target)

    # --- after a verified download -----------------------------------------

    def _download_path(self, name: str) -> Path:
        if self._install.kind == "appimage":
            # Same folder as the AppImage, so the updater's final move is atomic.
            return self._install.target.parent / f".{self._install.target.name}.update"
        return self._data_dir / "updates" / name

    def _extract(self, archive: Path) -> None:
        """Unpack the tarball next to the installed folder (runs on a worker thread)."""
        staging = self._install.target.parent / ".aperture-update"
        try:
            shutil.rmtree(staging, ignore_errors=True)
            staging.mkdir(parents=True)
            safe_extract(archive, staging)
            folder = staging / "aperture"
            if not (folder / "aperture").is_file():
                raise OSError("the archive has no aperture/aperture program")
            self._extracted.emit(str(folder), "")
        except (OSError, tarfile.TarError) as exc:
            shutil.rmtree(staging, ignore_errors=True)
            self._extracted.emit("", str(exc))
        finally:
            archive.unlink(missing_ok=True)

    def _on_extracted(self, folder: str, error: str) -> None:
        if error:
            self._fail(f"Couldn't unpack the update: {error}")
            return
        self._ready_sha = ""  # a folder is not re-hashed; the archive was verified
        self._finish_ready(Path(folder))

    def _finish_ready(self, path: Path) -> None:
        self._ready = path
        if self._install.kind == "macos-dmg":
            # Gatekeeper wants apps installed from their signed image: open it for the user.
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
            self._set_state("opened")
            return
        self._set_state("ready")

    def _set_progress(self, value: float) -> None:
        self._progress = value
        self.progressChanged.emit()

    def _set_state(self, state: str) -> None:
        self._state = state
        if state != "error":
            self._error = ""
        self.changed.emit()

    def _fail(self, message: str) -> None:
        log.warning("update: %s", message)
        self._error = message
        self._state = "error"
        self.changed.emit()
