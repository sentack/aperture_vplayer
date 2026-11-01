"""Separate launches merging into one playlist: the rules, without Qt."""

import pytest

from aperture.core.launch import (
    APPEND_WINDOW_S,
    absolute_args,
    decode_message,
    encode_message,
    joins_previous,
    merge_launches,
)


def test_absolute_args_resolve_against_the_launch_folder(tmp_path):
    stream = "https://example.com/live.m3u8"
    absolute = str(tmp_path / "b.mkv")
    args = absolute_args(["a.mp4", absolute, stream, ""], tmp_path)
    assert args == [str(tmp_path / "a.mp4"), absolute, stream]


def test_absolute_args_turn_file_urls_into_paths(tmp_path):
    url = (tmp_path / "My Movie.mkv").as_uri()
    assert absolute_args([url], "/elsewhere") == [str(tmp_path / "My Movie.mkv")]


def test_messages_round_trip():
    args = ["/videos/Épisode 1.mkv", "https://example.com/a.mp4"]
    data = encode_message(args)
    assert data.endswith(b"\n") and data.count(b"\n") == 1
    assert decode_message(data.rstrip(b"\n")) == args


@pytest.mark.parametrize(
    "data", [b"", b"not json", b"[1, 2]", b'{"args": "a"}', b'{"args": [1]}', b"\xff\xfe"]
)
def test_malformed_messages_are_refused(data):
    assert decode_message(data) is None


def test_one_launch_keeps_its_own_order():
    assert merge_launches([["b.mp4", "a.mp4", "b.mp4"]]) == ["b.mp4", "a.mp4"]


def test_racing_launches_merge_in_name_order():
    launches = [["/v/Episode 10.mkv"], ["/v/Episode 2.mkv"], ["/v/episode 1.mkv"]]
    assert merge_launches(launches) == ["/v/episode 1.mkv", "/v/Episode 2.mkv", "/v/Episode 10.mkv"]


def test_joins_previous_only_within_the_window():
    assert not joins_previous(10.0, None)
    assert joins_previous(10.0 + APPEND_WINDOW_S - 0.1, 10.0)
    assert not joins_previous(10.0 + APPEND_WINDOW_S, 10.0)
    assert not joins_previous(9.0, 10.0)  # clock went backwards
