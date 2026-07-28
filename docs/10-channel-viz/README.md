# 10-Channel Multi-Image Visualization

## Overview

Extended Ouster SDK viz module supporting simultaneous display of 10 image channels, including two composite mixed-light modes for Rev8 native-color sensors.

## Quick Start

```bash
# Standard usage (loop playback enabled by default)
ouster-cli source data.osf viz

# Python API
from ouster.sdk.open_source import open_source
from ouster.sdk.viz.core import SimpleViz

src = open_source("data.osf")
sv = SimpleViz(src.sensor_info[0])
sv.run(src)
```

## Supported Channels

| # | Channel | Description | Rev8 Only |
|:-:|---------|-------------|:---------:|
| 0 | R | Red (16-bit passive) | ✅ |
| 1 | G | Green (16-bit passive) | ✅ |
| 2 | B | Blue (16-bit passive) | ✅ |
| 3 | RGB | Combined color (48-bit) | ✅ |
| 4 | NIR | Near-infrared (16-bit) | ❌ |
| 5 | SIG | Signal intensity (16-bit) | ❌ |
| 6 | REF | Calibrated reflectivity (8-bit) | ❌ |
| 7 | DEPTH | Range/depth (19-bit) | ❌ |
| 8 | MIX_4 | (R+G+B+NIR)/4 average | ✅ |
| 9 | MIX_5 | (R+G+B+NIR+SIG)/5 average | ✅ |

## Key Bindings

### Panel Mode Switching

| Panel | Forward | Backward |
|:-----:|:-------:|:--------:|
| 0 | `b` | `SHIFT+b` |
| 1 | `n` | `SHIFT+n` |
| 2 | `g` | `SHIFT+g` |
| 3 | `SHIFT+r` | `SHIFT+t` |
| 4 | `CTRL+j` | `CTRL+k` |
| 5 | `CTRL+l` | `CTRL+;` |
| 6 | `CTRL+z` | `CTRL+x` |
| 7 | `CTRL+a` | `CTRL+d` |
| 8 | `CTRL+q` | `CTRL+e` |
| 9 | `CTRL+w` | `s` |

### Playback Controls

| Key | Action |
|-----|--------|
| `SPACE` | Pause / Resume |
| `,` / `.` | Step backward / forward 1 frame |
| `<` / `>` | Decrease / increase playback rate |
| `I` / `SHIFT+I` | Increase / decrease image size |
| `CTRL+I` | Cycle image view mode (ALL → ONE → FLIPPED) |
| `O` | Toggle OSD (on-screen display) |
| `?` | Show key bindings help |

## Layout

- **≤ 4 panels**: Original vertical stack with aspect-ratio-aware sizing
- **> 4 panels**: Full-width vertical stack — each panel spans the full viewport width

## Architecture

```
SensorModel
├── _num_images = 10 (was 2)
├── _images = [Image() × 10]
└── _modes = [..., MixedLightMode, MixedLightSigMode]

LidarFrameVizModel
├── _panel_labels = [Label × 10]
├── _use_default_view_modes() → ALL panels get modes
└── update_image_size() → full-width layout for >4 panels

LidarFrameViz
├── Adds panel labels to viz
├── 10 key bindings for mode switching
└── OSD shows all 10 panel modes
```

## Mixed-Light Modes

### MixedLightMode (Panel 8)
Average of R, G, B, NIR channels. Useful for:
- Evaluating overall luminance across visible + IR spectrum
- Detecting material properties that differ in IR vs. visible

### MixedLightSigMode (Panel 9)
Average of R, G, B, NIR, SIGNAL channels. Useful for:
- Combined passive + active illumination analysis
- Signal quality assessment with color context

Both modes auto-disable on non-Rev8 sensors (R/G/B fields unavailable).

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Only 2 panels visible | Old SDK version | Apply patches to `viz/model.py` |
| Panels 2-9 are black | Non-Rev8 sensor | Use `b`/`n`/`g` keys to switch to available modes |
| Images too small | High aspect ratio | Press `I` to increase size |
| No video playback | `on_eof='exit'` | Default changed to `'loop'`; re-apply `core.py` patch |
| Labels not visible | Rendering order | Check label z-order; may need rebuild |

## Files Modified

| File | Lines Changed | Description |
|------|:-------------:|-------------|
| `view_mode.py` | +66 | `MixedLightMode`, `MixedLightSigMode` classes |
| `model.py` | +108/-43 | `_num_images=10`, layout, labels, mode assignment |
| `core.py` | +45 | Key bindings, OSD, `on_eof='loop'` default |

## Tested Configuration

- **SDK**: v1.0.0
- **Sensors**: OS-1-MAX-256-RGB (Rev8), OS-1-256-RGB
- **Platform**: macOS Apple M2, Metal 4.1
- **Python**: 3.11
