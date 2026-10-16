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

- UI spec: [docs/DESIGN_SPEC.md](docs/DESIGN_SPEC.md)
- Mockup: [docs/reference.html](docs/reference.html)
