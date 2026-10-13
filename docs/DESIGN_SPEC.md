# Aperture — Desktop Video Player UI Spec

A reference for implementing the main window in code (Electron / Tauri / native).
Companion file: `reference.html` — a working, theme- and accent-switchable mockup
of the exact markup/CSS described below.

## Core system

- **Window**: fixed-feel chrome at 1440×900, layout scales fluidly (percentages /
  flex, not hard px, outside of the control-bar's own internal metrics).
- **Shape language — hybrid**: window chrome and panels use sharp geometric
  corners at 18–26px radius; every *interactive* control (play button, seek
  knob, volume fill-end, toggle buttons, accent swatch) is fully circular or
  pill-shaped. This contrast is the signature move — don't blur it by rounding
  the panels as much as the controls, or vice versa.
- **Typography**: Inter only, one family throughout. Title 34px/700,
  wordmark 13px/700 (0.14em tracking, uppercase), body/time 13–14px/500,
  labels 11px/600 (0.06–0.08em tracking, uppercase).
- **One accent, everywhere else fixed**: a single `--accent` custom property
  drives *only*: play/pause button fill + glow, seek-bar fill + scrubber knob,
  volume-fill, the accent swatch itself, and the small logo mark. Every other
  surface — window background, control-bar glass, text, icons, dividers — is
  locked to the theme and never reads from `--accent`.

## Color tokens

### Dark theme
| Token | Value | Use |
|---|---|---|
| `--bg-0` | `#111319` | window base |
| `--bg-1` | `#1A1D27` | back geometric layer |
| `--bg-2` | `#232733` | front geometric layer |
| `--bg-3` | `#2E3342` | accent circle (sun/moon) |
| `--text-primary` | `#F5F5F7` | titles, wordmark |
| `--text-secondary` | `rgba(245,245,247,.64)` | time, labels |
| `--text-tertiary` | `rgba(245,245,247,.42)` | micro-copy |
| `--bar-bg` | `rgba(24,25,31,.70)` | floating control bar glass |
| `--bar-border` | `rgba(255,255,255,.09)` | control bar / popover edge |
| `--track-bg` | `rgba(255,255,255,.18)` | seek / volume track (unfilled) |
| `--divider` | `rgba(255,255,255,.12)` | vertical separators, swatch ring |
| `--chip-bg` | `rgba(255,255,255,.07)` | settings/options chip |

### Light theme
| Token | Value | Use |
|---|---|---|
| `--bg-0` | `#F2F2F0` | window base |
| `--bg-1` | `#E7E7E3` | back geometric layer |
| `--bg-2` | `#DADAD5` | front geometric layer |
| `--bg-3` | `#CDCDC6` | accent circle (sun/moon) |
| `--text-primary` | `#17171A` | titles, wordmark |
| `--text-secondary` | `rgba(23,23,26,.64)` | time, labels |
| `--text-tertiary` | `rgba(23,23,26,.42)` | micro-copy |
| `--bar-bg` | `rgba(255,255,255,.72)` | floating control bar glass |
| `--bar-border` | `rgba(0,0,0,.07)` | control bar / popover edge |
| `--track-bg` | `rgba(0,0,0,.13)` | seek / volume track (unfilled) |
| `--divider` | `rgba(0,0,0,.10)` | vertical separators, swatch ring |
| `--chip-bg` | `rgba(0,0,0,.045)` | settings/options chip |

### Accent presets (same 3 across both themes)
- Vivid blue `#3D7FFF`
- Warm coral `#FF6A52`
- Muted green `#3FA671`
(picker also offers amber `#E8A23D` and violet `#8B6FE8` as extra options)

Icons and glyphs on the accent fill are always solid white — all three presets
pass contrast there.

## Layout

```
┌ window 1440×900 ───────────────────────────────────────────┐
│ top bar  (64h, 36px side pad)                                │
│   logo mark (28×28, 9r, accent bg) + "APERTURE" wordmark      │
│   — window controls (min / max / close, minimal line glyphs)  │
│                                                                │
│   video content fills the rest; geometric monochrome          │
│   background art (3 flat tonal layers + 1 circle) — never     │
│   uses --accent                                                │
│                                                                │
│   now-playing title block, bottom-left, 48px in, 150px up     │
│     title 34/700 · subtitle 14/500 secondary                  │
│                                                                │
│ ┌ floating control bar ──────────────────────────────────┐   │
│ │ 32px inset L/R/B · height 88 · radius 26 · glass blur(24)│   │
│ │                                                            │
│ │ [play 52⌀] elapsed  ───seek track/fill/knob───  remaining │
│ │   | [vol icon][vol pill 76×4]  | [list][expand]           │
│ │   [chip: settings icon + accent swatch 26⌀]                │
│ └────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────┘
```

- Control bar: `display:flex; align-items:center; gap:20px; padding:0 26px`.
- Seek bar: track `height:6px, radius:3px`; fill absolutely positioned on top;
  knob `14×14` circle, centered on fill's end, ring = 3px `--bar-bg` halo.
- Volume: icon button (32×32, 10r) + `76×4` pill track, same fill pattern.
- Vertical dividers: `1×26px`, `--divider`.
- Options chip: `padding:6px 10px; radius:16px; background:--chip-bg`,
  contains a settings (sliders) icon button and the circular accent swatch
  (26⌀, 2px `--bar-bg` ring + 1px `--divider` ring outside it).
- Clicking the swatch opens a popover (≈238px wide, radius 18, same glass
  treatment as the bar) anchored above it, showing 5 circular swatches
  (30⌀, 12px gap); the active one gets a 2px accent-colored outer ring plus a
  white check mark.

## States

- **Active / default**: control bar fully visible as above.
- **Idle** (no pointer movement during playback): top bar, title and the full
  control bar fade out entirely. What remains is a single thin progress line
  — `height:3px`, same 32px side inset, resting 52px off the bottom, track in
  `rgba(255,255,255,.14)` (dark) and accent-colored fill, with a soft
  accent-tinted glow. No icons, no text, no glass panel.

## Icons

All icons are inline stroke/fill SVG at 1.75px stroke, round caps — never
emoji, never a third-party icon font:
- **Play/Pause**: triangle fill / two rounded bars, white, inside the accent
  circle.
- **Speaker**: solid cone + two stroke arcs (volume waves).
- **Playlist**: three dots + three horizontal rules.
- **Fullscreen**: four independent corner-bracket strokes.
- **Settings**: two horizontal rules broken by two stroke circles (an
  equalizer-sliders mark) — deliberately not a cog, to keep the mark-making
  consistent with the rest of the geometric language.
- **Window controls** (min/max/close): minimal single-stroke line, square
  outline, and crossed lines — no colored traffic-light dots.

## Handoff notes for implementation

- Swap the monochrome geometric background for real video output; keep the
  top/bottom scrim gradients (`--scrim-top`, `--scrim-bottom`) over actual
  video for the same text legibility.
- `backdrop-filter: blur(24px) saturate(160%)` on the control bar and popover
  is load-bearing for the "floating glass" read — provide a solid-color
  fallback (`--bar-bg` at full opacity) for platforms without backdrop-filter
  support.
- The accent is a single CSS custom property (`--accent`) at the root; any
  element that should react to the user's chosen accent reads it directly,
  nothing else should.
