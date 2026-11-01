"""The single-instance handoff: a second launch passes its files to the first, over Qt."""

import os
from pathlib import Path

import pytest

from aperture.core.launch import APPEND_WINDOW_S

QtCore = pytest.importorskip("PySide6.QtCore")
pytest.importorskip("PySide6.QtNetwork")
QtGui = pytest.importorskip("PySide6.QtGui")

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="module")
def app():
    # A QGuiApplication, like the other Qt tests: the first one created serves the whole run.
    return QtGui.QGuiApplication.instance() or QtGui.QGuiApplication([])


def spin(app, until, seconds=5.0):
    timer = QtCore.QElapsedTimer()
    timer.start()
    while not until() and timer.elapsed() < seconds * 1000:
        app.processEvents(QtCore.QEventLoop.ProcessEventsFlag.AllEvents, 50)
    return until()


class Recorder:
    def __init__(self):
        self.calls = []

    def opened(self, files):
        self.calls.append(("open", files))

    def added(self, files):
        self.calls.append(("add", files))

    def raised(self):
        self.calls.append(("raise",))


def router(clock, parent=None):
    from aperture.instance import LaunchRouter

    calls = Recorder()
    return LaunchRouter(calls.opened, calls.added, calls.raised, clock=clock), calls


def test_a_burst_of_launches_opens_one_sorted_playlist(app):
    now = [100.0]
    launches, calls = router(lambda: now[0])
    launches.submit(["/v/c.mp4"])
    launches.submit(["/v/a.mp4"], from_elsewhere=True)
    launches.submit(["/v/b.mp4"], from_elsewhere=True)
    launches.flush()
    assert calls.calls == [("open", ["/v/a.mp4", "/v/b.mp4", "/v/c.mp4"]), ("raise",)]


def test_a_straggler_joins_the_playlist_and_a_later_launch_replaces_it(app):
    now = [100.0]
    launches, calls = router(lambda: now[0])
    launches.submit(["/v/a.mp4"])
    launches.flush()
    now[0] += APPEND_WINDOW_S / 2
    launches.submit(["/v/b.mp4"], from_elsewhere=True)
    launches.flush()
    now[0] += APPEND_WINDOW_S * 2
    launches.submit(["/v/c.mp4"], from_elsewhere=True)
    launches.flush()
    assert calls.calls == [
        ("open", ["/v/a.mp4"]),
        ("add", ["/v/b.mp4"]),
        ("raise",),
        ("open", ["/v/c.mp4"]),
        ("raise",),
    ]


def test_starting_again_without_files_only_shows_the_window(app):
    launches, calls = router(lambda: 0.0)
    launches.submit([])
    launches.flush()
    launches.submit([], from_elsewhere=True)
    launches.flush()
    assert calls.calls == [("raise",)]


def test_a_second_launch_hands_its_files_to_the_first(app, tmp_path):
    from aperture.instance import claim

    forwarded, server = claim(tmp_path, [])
    assert not forwarded and server is not None
    received = []
    server.received.connect(received.append)
    try:
        files = [str(tmp_path / "one.mp4"), str(tmp_path / "two.mp4")]
        assert claim(tmp_path, files) == (True, None)
        assert spin(app, lambda: received)
        assert received == [files]
    finally:
        server.close()


def test_closing_hands_over_to_the_next_launch(app, tmp_path):
    from aperture.instance import claim

    _, first = claim(tmp_path, [])
    first.close()
    forwarded, second = claim(tmp_path, [])
    try:
        assert not forwarded and second is not None
    finally:
        second.close()


@pytest.mark.skipif(os.name == "nt", reason="the leftover is a Unix socket file")
def test_a_crashed_instances_socket_file_is_taken_over(app, tmp_path):
    from aperture.instance import claim, server_name

    # A socket file with nobody behind it, and no lock held: what a crash leaves behind.
    leftover = Path(QtCore.QDir.tempPath()) / server_name(tmp_path)
    leftover.touch()
    forwarded, server = claim(tmp_path, [])
    try:
        assert not forwarded and server is not None
    finally:
        server.close()


def test_switching_single_window_back_on_takes_over_only_a_free_role(app, tmp_path):
    from aperture.instance import claim, take_over

    _, first = claim(tmp_path, [])
    try:
        assert take_over(tmp_path) is None  # another window holds the role: stay separate
    finally:
        first.close()
    second = take_over(tmp_path)
    try:
        assert second is not None
        assert claim(tmp_path, ["/v/a.mp4"]) == (True, None)  # later launches reach it
    finally:
        second.close()
