"""One running Aperture per user: later launches hand their files over and exit.

The first launch takes a lock file and listens on a local socket (a Unix socket, or a named
pipe on Windows). A later launch finds it, sends its arguments, and quits before opening a
window, so a multi-file selection that the file manager opens as one process per file still
ends up as one playlist in one window. LaunchRouter turns those arrivals into playlist
changes; core.launch holds the rules.
"""

from __future__ import annotations

import hashlib
import logging
import sys
import time
from collections.abc import Callable, Sequence
from pathlib import Path

from PySide6.QtCore import QLockFile, QObject, QTimer, Signal
from PySide6.QtNetwork import QLocalServer, QLocalSocket

from aperture.core.launch import (
    MAX_MESSAGE_BYTES,
    decode_message,
    encode_message,
    joins_previous,
    merge_launches,
)

log = logging.getLogger(__name__)

LOCK_FILE = "instance.lock"
CONNECT_TIMEOUT_MS = 1000
# A launch that cannot reach the instance holding the lock keeps retrying for this long (it
# may still be starting up), then runs on its own rather than not at all.
CLAIM_TIMEOUT_S = 10.0
# Arrivals this close together are one burst; the burst then opens as one playlist.
SETTLE_MS = 250


def server_name(data_dir: Path) -> str:
    """Socket name for this user's data folder. Separate data folders run separately."""
    digest = hashlib.sha256(str(data_dir.resolve()).encode("utf-8")).hexdigest()[:16]
    return f"aperture-{digest}"


class InstanceServer(QObject):
    """The running instance's end: emits each later launch's arguments."""

    received = Signal(list)

    def __init__(self, name: str, lock: QLockFile, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._name = name
        self._lock = lock
        self._server = QLocalServer(self)
        self._server.setSocketOptions(QLocalServer.SocketOption.UserAccessOption)
        self._server.newConnection.connect(self._accept)

    def listen(self) -> bool:
        QLocalServer.removeServer(self._name)  # a crashed run's socket file (we hold the lock)
        if self._server.listen(self._name):
            return True
        log.warning("cannot listen on %s: %s", self._name, self._server.errorString())
        return False

    def close(self) -> None:
        """Stop being the running instance, so a new process (a restart) can take over."""
        self._server.close()
        self._lock.unlock()

    def _accept(self) -> None:
        while (socket := self._server.nextPendingConnection()) is not None:
            buffer = bytearray()
            socket.readyRead.connect(lambda s=socket, b=buffer: self._read(s, b))
            socket.disconnected.connect(lambda s=socket, b=buffer: self._finish(s, b))
            if socket.bytesAvailable():
                self._read(socket, buffer)

    def _read(self, socket: QLocalSocket, buffer: bytearray) -> None:
        buffer.extend(socket.readAll().data())
        if b"\n" in buffer or len(buffer) > MAX_MESSAGE_BYTES:
            socket.disconnectFromServer()  # emits disconnected -> _finish

    def _finish(self, socket: QLocalSocket, buffer: bytearray) -> None:
        if buffer:
            args = decode_message(bytes(buffer).split(b"\n", 1)[0])
            buffer.clear()  # disconnected can follow _read's own disconnect: handle once
            if args is None:
                log.warning("ignored a malformed message from another launch")
            else:
                self.received.emit(args)
        socket.deleteLater()


def forward(name: str, args: Sequence[str]) -> bool:
    """Send `args` to the running instance. False if there is none to receive them."""
    socket = QLocalSocket()
    socket.connectToServer(name)
    if not socket.waitForConnected(CONNECT_TIMEOUT_MS):
        return False
    if sys.platform == "win32":
        # Let the running window come to the front: Windows only allows that to a process
        # the user just started, which is this one, not the instance receiving the files.
        import ctypes

        ctypes.windll.user32.AllowSetForegroundWindow(-1)  # ASFW_ANY
    socket.write(encode_message(args))
    while socket.bytesToWrite() and socket.waitForBytesWritten(CONNECT_TIMEOUT_MS):
        pass
    sent = socket.bytesToWrite() == 0
    socket.disconnectFromServer()
    if socket.state() != QLocalSocket.LocalSocketState.UnconnectedState:
        socket.waitForDisconnected(CONNECT_TIMEOUT_MS)
    return sent


def claim(data_dir: Path, args: Sequence[str]) -> tuple[bool, InstanceServer | None]:
    """Become the running instance, or hand `args` to the one already running.

    Returns `(forwarded, server)`: forwarded means another instance took the arguments and
    this launch should quit. Otherwise `server` is this launch's, or None if neither worked
    (the launch then runs on its own rather than not at all).
    """
    name = server_name(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    lock = QLockFile(str(data_dir / LOCK_FILE))
    # Never "stale" by age: the instance may run for days. A lock left by a process that
    # died is still taken over, because QLockFile checks whether its owner is alive.
    lock.setStaleLockTime(0)
    deadline = time.monotonic() + CLAIM_TIMEOUT_S
    while time.monotonic() < deadline:
        if forward(name, args):
            return True, None
        if lock.tryLock(100):
            server = InstanceServer(name, lock)
            if server.listen():
                return False, server
            lock.unlock()
            return False, None
        # Someone holds the lock but is not listening yet: it is starting. Try again.
        time.sleep(0.1)
    log.warning("another Aperture holds %s but does not answer; running separately", LOCK_FILE)
    return False, None


class LaunchRouter(QObject):
    """Opens what this launch and later ones ask for, a burst of launches as one playlist.

    `open_files` replaces the playlist, `add_files` appends to it. `bring_to_front` runs
    whenever another launch arrived, files or not (starting Aperture again shows the window).
    """

    def __init__(
        self,
        open_files: Callable[[list[str]], None],
        add_files: Callable[[list[str]], None],
        bring_to_front: Callable[[], None],
        clock: Callable[[], float] = time.monotonic,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._open = open_files
        self._add = add_files
        self._bring_to_front = bring_to_front
        self._clock = clock
        self._launches: list[list[str]] = []
        self._from_elsewhere = False
        self._last_open: float | None = None
        self._settle = QTimer(self, singleShot=True, interval=SETTLE_MS)
        self._settle.timeout.connect(self.flush)

    def submit(self, args: Sequence[str], from_elsewhere: bool = False) -> None:
        if args:
            self._launches.append(list(args))
        self._from_elsewhere |= from_elsewhere
        self._settle.start()

    def flush(self) -> None:
        self._settle.stop()
        launches, self._launches = self._launches, []
        from_elsewhere, self._from_elsewhere = self._from_elsewhere, False
        if launches:
            files = merge_launches(launches)
            now = self._clock()
            if joins_previous(now, self._last_open):
                self._add(files)
            else:
                self._open(files)
            self._last_open = now
        if from_elsewhere:
            self._bring_to_front()
