import pytest

from aperture.core import dialog_filters, format_time, is_video


@pytest.mark.parametrize(
    ("seconds", "expected"),
    [(0, "0:00"), (9.9, "0:09"), (862, "14:22"), (3600, "1:00:00"), (3723, "1:02:03"), (-5, "0:00")],
)
def test_format_time(seconds, expected):
    assert format_time(seconds) == expected


@pytest.mark.parametrize(("name", "expected"), [("a.MKV", True), ("b.mp4", True), ("c.txt", False)])
def test_is_video(name, expected):
    assert is_video(name) is expected


def test_dialog_filters():
    media, video, audio, everything = dialog_filters()
    assert "*.mkv" in video and "*.avi" in video and "*.mp3" not in video
    assert "*.mp3" in audio and "*.flac" in audio
    assert "*.mkv" in media and "*.mp3" in media
    assert everything == "All files (*)"
