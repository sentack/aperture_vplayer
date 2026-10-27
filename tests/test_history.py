import json
from pathlib import Path

from aperture.core.history import (
    END_MARGIN_MS,
    MIN_RESUME_MS,
    RECENT_LIMIT,
    RESUME_LIMIT,
    History,
)

HOUR = 3_600_000


def test_touch_orders_most_recent_first_without_duplicates():
    history = History()
    for name in ("a.mp4", "b.mp4", "a.mp4"):
        history.touch(name)
    assert [p.name for p in history.recent] == ["a.mp4", "b.mp4"]


def test_recent_is_capped():
    history = History()
    for i in range(RECENT_LIMIT + 3):
        history.touch(f"{i}.mp4")
    assert len(history.recent) == RECENT_LIMIT
    assert history.recent[0].name == f"{RECENT_LIMIT + 2}.mp4"


def test_remove_and_clear_recent():
    history = History()
    history.touch("a.mp4")
    history.touch("b.mp4")
    history.remove_recent("a.mp4")
    assert [p.name for p in history.recent] == ["b.mp4"]
    history.clear_recent()
    assert history.recent == []


def test_paths_are_absolute_keys():
    history = History()
    history.touch("a.mp4")
    assert history.recent[0] == Path("a.mp4").absolute()
    history.remember_position("a.mp4", 60_000, HOUR)
    assert history.resume_point(Path("a.mp4").absolute()) == 60_000


def test_remember_mid_file():
    history = History()
    history.remember_position("a.mp4", 862_000, HOUR)
    assert history.resume_point("a.mp4") == 862_000


def test_near_start_is_not_remembered_and_clears_old_point():
    history = History()
    history.remember_position("a.mp4", 60_000, HOUR)
    history.remember_position("a.mp4", MIN_RESUME_MS - 1, HOUR)
    assert history.resume_point("a.mp4") is None


def test_near_end_counts_as_finished():
    history = History()
    history.remember_position("short.mp4", 60_000 - END_MARGIN_MS + 1, 60_000)
    history.remember_position("long.mp4", HOUR - HOUR // 50 + 1, HOUR)
    assert history.resume_point("short.mp4") is None
    assert history.resume_point("long.mp4") is None


def test_unknown_duration_still_remembers():
    history = History()
    history.remember_position("stream.ts", 30_000, 0)
    assert history.resume_point("stream.ts") == 30_000


def test_resume_evicts_least_recently_updated():
    history = History()
    for i in range(RESUME_LIMIT):
        history.remember_position(f"{i}.mp4", 60_000, HOUR)
    history.remember_position("0.mp4", 61_000, HOUR)  # refresh oldest
    history.remember_position("new.mp4", 60_000, HOUR)
    assert history.resume_point("0.mp4") == 61_000
    assert history.resume_point("1.mp4") is None


def test_forget_position():
    history = History()
    history.remember_position("a.mp4", 60_000, HOUR)
    history.forget_position("a.mp4")
    assert history.resume_point("a.mp4") is None


def test_round_trip(tmp_path):
    path = tmp_path / "nested" / "history.json"
    history = History(path)
    history.touch("a.mp4")
    history.remember_position("a.mp4", 60_000, HOUR)
    history.save()

    loaded = History(path)
    assert loaded.recent == history.recent
    assert loaded.resume_point("a.mp4") == 60_000
    assert not list(path.parent.glob(".history-*"))


def test_missing_file_starts_empty(tmp_path):
    history = History(tmp_path / "absent.json")
    assert history.recent == []


def test_corrupt_file_starts_empty(tmp_path):
    path = tmp_path / "history.json"
    path.write_text("{not json")
    assert History(path).recent == []


def test_malformed_entries_are_dropped(tmp_path):
    path = tmp_path / "history.json"
    data = {
        "recent": ["/a.mp4", 3, None],
        "resume": {"/a.mp4": 9000, "/b.mp4": "x", "/c.mp4": True},
    }
    path.write_text(json.dumps(data))
    history = History(path)
    assert history.recent == [Path("/a.mp4").absolute()]
    assert history.resume_point("/a.mp4") == 9000
    assert history.resume_point("/b.mp4") is None
    assert history.resume_point("/c.mp4") is None


def test_in_memory_save_is_noop():
    History().save()
