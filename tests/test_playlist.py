import random
from pathlib import Path

import pytest

from aperture.core import Playlist
from aperture.core.playlist import REPEAT_ALL, REPEAT_OFF, REPEAT_ONE


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


# --- repeat and shuffle --------------------------------------------------------------------


def test_repeat_off_stops_at_the_end():
    playlist = make(3, index=2)
    assert playlist.next_index(finished=True) is None
    assert not playlist.has_next


def test_repeat_all_wraps_both_ways():
    playlist = make(3, index=2)
    playlist.repeat = REPEAT_ALL
    assert playlist.next_index() == 0 and playlist.has_next
    playlist.select(0)
    assert playlist.previous_index() == 2


def test_repeat_one_replays_only_when_the_item_finished():
    playlist = make(3, index=1)
    playlist.repeat = REPEAT_ONE
    assert playlist.next_index(finished=True) == 1
    assert playlist.next_index() == 2  # pressing Next still moves on
    playlist.select(2)
    assert playlist.next_index() == 0  # and wraps, like repeat all


def test_unknown_repeat_mode_is_refused():
    with pytest.raises(ValueError):
        make(1).repeat = "sometimes"


def test_shuffle_plays_every_item_once_starting_from_the_current_one():
    playlist = Playlist(rng=random.Random(7))
    playlist.add(f"{i}.mp4" for i in range(10))
    playlist.select(4)
    playlist.shuffle = True
    played = [4]
    while (target := playlist.advance(finished=True)) is not None:
        playlist.select(target)
        played.append(target)
    assert sorted(played) == list(range(10))
    assert played != sorted(played)  # an actual shuffle (fixed seed)


def test_shuffle_with_repeat_all_reshuffles_each_round():
    playlist = Playlist(rng=random.Random(3))
    playlist.add(f"{i}.mp4" for i in range(6))
    playlist.repeat = REPEAT_ALL
    playlist.shuffle = True
    playlist.select(playlist.next_index())
    rounds = []
    for _ in range(3):
        played = []
        for _ in range(6):
            played.append(playlist.index)
            playlist.select(playlist.advance(finished=True))
        rounds.append(played)
    assert all(sorted(r) == list(range(6)) for r in rounds)
    assert len({tuple(r) for r in rounds}) > 1


def test_previous_retraces_the_shuffled_order():
    playlist = Playlist(rng=random.Random(1))
    playlist.add(f"{i}.mp4" for i in range(5))
    playlist.select(0)
    playlist.shuffle = True
    first, second = playlist.advance(), None
    playlist.select(first)
    second = playlist.advance()
    playlist.select(second)
    assert playlist.previous_index() == first


def test_items_added_while_shuffled_play_later_and_removal_keeps_order_valid():
    playlist = Playlist(rng=random.Random(5))
    playlist.add(["a.mp4", "b.mp4"])
    playlist.select(0)
    playlist.shuffle = True
    playlist.add(["c.mp4", "d.mp4"])
    playlist.remove(1)
    played = [playlist.index]
    while (target := playlist.advance()) is not None:
        playlist.select(target)
        played.append(target)
    assert sorted(played) == [0, 1, 2]


def test_turning_shuffle_off_returns_to_list_order():
    playlist = make(5, index=2)
    playlist.shuffle = True
    playlist.shuffle = False
    assert playlist.next_index() == 3 and playlist.previous_index() == 1
    assert playlist.repeat == REPEAT_OFF
