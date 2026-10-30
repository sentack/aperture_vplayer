from pathlib import Path

import pytest

from aperture.core import Playlist


def make(n: int, index: int = -1) -> Playlist:
    playlist = Playlist()
    playlist.add(f"{i}.mp4" for i in range(n))
    if index >= 0:
        playlist.select(index)
    return playlist


def test_empty():
    playlist = Playlist()
    assert len(playlist) == 0
    assert playlist.index == -1
    assert playlist.current is None
    assert not playlist.has_next and not playlist.has_previous


def test_add_keeps_cursor_and_converts_paths():
    playlist = make(2, index=1)
    assert playlist.add(["x.mkv"]) == 1
    assert playlist.index == 1
    assert playlist.items[-1] == Path("x.mkv")


def test_navigation_bounds():
    playlist = make(3, index=0)
    assert playlist.has_next and not playlist.has_previous
    playlist.select(2)
    assert playlist.has_previous and not playlist.has_next


@pytest.mark.parametrize("index", [-1, 3])
def test_select_out_of_range(index):
    with pytest.raises(IndexError):
        make(3).select(index)


def test_remove_before_cursor_shifts_it():
    playlist = make(3, index=2)
    playlist.remove(0)
    assert playlist.index == 1
    assert playlist.current == Path("2.mp4")


def test_remove_after_cursor_keeps_it():
    playlist = make(3, index=0)
    playlist.remove(2)
    assert playlist.current == Path("0.mp4")


def test_remove_current_moves_to_successor():
    playlist = make(3, index=1)
    playlist.remove(1)
    assert playlist.current == Path("2.mp4")


def test_remove_current_last_moves_to_new_last():
    playlist = make(3, index=2)
    playlist.remove(2)
    assert playlist.current == Path("1.mp4")


def test_remove_only_item_empties_cursor():
    playlist = make(1, index=0)
    playlist.remove(0)
    assert playlist.index == -1 and playlist.current is None


def test_remove_rejects_negative_index():
    with pytest.raises(IndexError):
        make(2, index=0).remove(-1)


def test_clear():
    playlist = make(3, index=1)
    playlist.clear()
    assert len(playlist) == 0 and playlist.index == -1


def test_stream_urls_are_kept_verbatim():
    playlist = Playlist()
    playlist.add(["https://example.com/live.m3u8", "local.mp4"])
    assert playlist.items == ("https://example.com/live.m3u8", Path("local.mp4"))
