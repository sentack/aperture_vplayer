import struct
from array import array

import pytest

from aperture.core.chapters import Chapter, chapter_at, read_chapters
from aperture.core.gain import KNEE, boost, soft_limit
from aperture.core.keymap import Keymap

# --- building tiny Matroska files ---------------------------------------------------------


def ebml(element_id: int, payload: bytes, unknown_size: bool = False) -> bytes:
    if unknown_size:
        size = b"\x01\xff\xff\xff\xff\xff\xff\xff"
    else:
        size = b"\x01" + len(payload).to_bytes(7, "big")
    return element_id.to_bytes((element_id.bit_length() + 7) // 8, "big") + size + payload


def uint(element_id: int, value: int) -> bytes:
    return ebml(element_id, value.to_bytes(8, "big"))


def atom(start_ms: int, title: str, hidden: bool = False) -> bytes:
    display = ebml(0x80, ebml(0x85, title.encode()))
    flags = uint(0x98, 1) if hidden else b""
    return ebml(0xB6, uint(0x91, start_ms * 1_000_000) + flags + display)


EDITION = ebml(0x45B9, atom(0, "Intro") + atom(65_500, "Part 2") + atom(90_000, "Hidden", True))
CHAPTERS = ebml(0x1043A770, EDITION)
HEADER = ebml(0x1A45DFA3, ebml(0x4282, b"matroska"))
CLUSTER = ebml(0x1F43B675, b"\x00" * 64)


def test_matroska_chapters_before_media(tmp_path):
    path = tmp_path / "a.mkv"
    path.write_bytes(HEADER + ebml(0x18538067, ebml(0xEC, b"\x00" * 8) + CHAPTERS + CLUSTER))
    assert read_chapters(path) == [Chapter(0, "Intro"), Chapter(65_500, "Part 2")]


def test_matroska_chapters_after_media_via_seekhead(tmp_path):
    # Segment: SeekHead -> Cluster -> Chapters (the layout mkvmerge writes with cues first).
    seek_size = len(ebml(0x114D9B74, ebml(0x4DBB, uint(0x53AB, 0x1043A770) + uint(0x53AC, 0))))
    chapters_at = seek_size + len(CLUSTER)
    seek_head = ebml(0x114D9B74, ebml(0x4DBB, uint(0x53AB, 0x1043A770) + uint(0x53AC, chapters_at)))
    path = tmp_path / "b.webm"
    path.write_bytes(HEADER + ebml(0x18538067, seek_head + CLUSTER + CHAPTERS, unknown_size=True))
    assert [c.title for c in read_chapters(path)] == ["Intro", "Part 2"]


def test_matroska_without_chapters(tmp_path):
    path = tmp_path / "c.mkv"
    path.write_bytes(HEADER + ebml(0x18538067, CLUSTER))
    assert read_chapters(path) == []


# --- building tiny MP4 files --------------------------------------------------------------


def box(kind: bytes, payload: bytes) -> bytes:
    return struct.pack(">I4s", 8 + len(payload), kind) + payload


def chpl(entries, version=1) -> bytes:
    body = bytes([version, 0, 0, 0]) + (b"\x00" * 4 if version else b"") + bytes([len(entries)])
    for start_ms, title in entries:
        raw = title.encode()
        body += struct.pack(">Q", start_ms * 10_000) + bytes([len(raw)]) + raw
    return box(b"chpl", body)


@pytest.mark.parametrize("version", [0, 1])
def test_mp4_nero_chapters(tmp_path, version):
    path = tmp_path / "a.mp4"
    udta = box(b"udta", chpl([(0, "Start"), (125_250, "Ending")], version))
    moov = box(b"moov", box(b"mvhd", b"\x00" * 100) + udta)
    path.write_bytes(box(b"ftyp", b"isom\x00\x00\x02\x00") + moov + box(b"mdat", b"\x00" * 32))
    assert read_chapters(path) == [Chapter(0, "Start"), Chapter(125_250, "Ending")]


def test_unreadable_or_unknown_files(tmp_path):
    broken = tmp_path / "broken.mp4"
    broken.write_bytes(b"\x00\x00\x00\x10moov\xff\xff")
    assert read_chapters(broken) == []
    assert read_chapters(tmp_path / "missing.mkv") == []
    assert read_chapters(tmp_path / "x.avi") == []


def test_chapter_at():
    chapters = [Chapter(0, "a"), Chapter(10_000, "b"), Chapter(20_000, "c")]
    assert [chapter_at(chapters, t) for t in (0, 9_999, 10_000, 99_999)] == [0, 0, 1, 2]
    assert chapter_at([Chapter(5_000, "late")], 1_000) == -1


# --- audio boost --------------------------------------------------------------------------


def test_soft_limit_passes_quiet_audio_and_never_clips():
    assert soft_limit(0.5) == 0.5 and soft_limit(-KNEE) == -KNEE
    for x in (0.9, 1.5, 4.0, 100.0):
        assert KNEE < soft_limit(x) <= 1.0 and soft_limit(-x) == -soft_limit(x)
    assert soft_limit(0.9) < soft_limit(1.5) < soft_limit(4.0)  # still monotonic


def test_boost_float_and_int16():
    floats = boost(array("f", [0.1, -0.3, 0.9]), 2.0)
    assert floats[0] == pytest.approx(0.2) and floats[1] == pytest.approx(-0.6)
    assert 0.8 < floats[2] < 1.0
    ints = boost(array("h", [1000, -32000]), 2.0)
    assert ints[0] == 2000 and -32767 <= ints[1] < -26000


def test_boost_at_unity_is_untouched():
    samples = array("h", [123, -456])
    assert boost(samples, 1.0) is samples and list(samples) == [123, -456]



# --- phase 10 shortcuts -------------------------------------------------------------------


def test_phase_10_defaults():
    keymap = Keymap()
    assert keymap.key("mini_player") == "Ctrl+P"
    assert keymap.key("subtitle_earlier") == "G" and keymap.key("subtitle_later") == "H"
    assert keymap.key("chapter_next") == "Ctrl+." and keymap.key("chapter_previous") == "Ctrl+,"
    assert keymap.key("settings") == "Ctrl+Alt+S"
