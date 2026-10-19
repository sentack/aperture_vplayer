# Aperture

Cross-platform desktop video player for Windows and Linux, built on PySide6 (Qt Quick + Qt Multimedia).

## Run

```sh
python -m venv .venv
. .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
aperture [video ...]
```

## Test

```sh
pytest
```

## Phase 1 — core

- Open MP4, MKV, AVI, MOV, WebM and more (Qt Multimedia FFmpeg backend)
- Play, pause, stop, seek by click or drag
- Volume and mute
- Fullscreen: button, double-click video, Esc to leave
- Playlist: add, remove, clear, next/previous, auto-advance
- Controls fade after 2.5 s still pointer during playback

## Phase 2 — everyday usability

- Drag and drop files or folders: on video replaces queue, on playlist panel appends
- Recent files on start screen, with resume point
- Resume where you left off (kept per file, cleared once finished)
- Playback speed 0.25×–2× from options chip or keys
- Keyboard shortcuts:

| Key | Action |
|---|---|
| Space, K | Play / pause |
| ← / → | Seek 5 s |
| J / L | Seek 10 s |
| Shift+← / Shift+→ | Seek 30 s |
| Home | Back to start |
| ↑ / ↓ | Volume ±5% |
| M | Mute |
| N / P | Next / previous |
| [ / ] | Slower / faster |
| = | Normal speed |
| F, F11 | Fullscreen |
| Esc | Leave fullscreen |
| Ctrl+O | Open files |

History lives in the platform app-data folder (`~/.local/share/Aperture/history.json` on Linux, `%APPDATA%\Aperture\history.json` on Windows).

- UI spec: [docs/DESIGN_SPEC.md](docs/DESIGN_SPEC.md)
- Mockup: [docs/reference.html](docs/reference.html)
