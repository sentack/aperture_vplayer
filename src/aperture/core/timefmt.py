"""Playback clock formatting."""


def format_time(seconds: float) -> str:
    """`14:22` under an hour, `1:02:03` beyond. Negative clamps to zero."""
    total = max(0, int(seconds))
    hours, rest = divmod(total, 3600)
    minutes, secs = divmod(rest, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}" if hours else f"{minutes}:{secs:02d}"
