# PRD: Ouster SDK 11-Channel Multi-Image Visualization

> **Version**: 2.0.0  
> **Date**: 2026-07-29  
> **Author**: QNI (AI-assisted)  
> **Status**: Implemented + Verified  

## 1. Overview

Extend the Ouster SDK `viz` module to support simultaneous display of 11 image channels, including three composite mixed-light modes with per-channel normalization. The original SDK hardcodes `_num_images = 2`.

## 2. Problem Statement

Users working with Ouster Rev8 native-color sensors need to visualize multiple data channels simultaneously for:
- Sensor calibration and validation
- Noise analysis across channels
- Color quality assessment (R/G/B/NIR)
- Signal vs. reflectivity comparison
- Mixed-light composite analysis with calibrated reflectivity

## 3. Goals

| Goal | Success Metric |
|------|---------------|
| Display all available channels simultaneously | 11 panels visible at once |
| Support Rev8 native color (R/G/B/RGB) | Panels show R, G, B, RGB independently |
| Support standard channels | NIR, SIGNAL, REFLECTIVITY, RANGE always available |
| Support composite channels | MIX_4, MIX_5, MIX_CALREF with normalization |
| Per-panel mode switching | Each panel has independent key binding |
| Panel view toggle | T key cycles ALL → FIRST 5 → LAST 5 |
| Loop playback by default | `on_eof='loop'` in SimpleViz |
| Per-panel labels | Channel name displayed on each panel |
| Rev8 auto-detect | Color sensors → all 11 panels; non-color → first 5 only |

## 4. Non-Goals

- Modifying the 3D point cloud visualization
- Adding new sensor driver features
- Changing the OSF/PCAP file formats

## 5. Architecture

### 5.1 Files Modified

```
python/src/ouster/sdk/viz/
├── view_mode.py   # +150 lines: RGBChannelMode, Red/Green/BlueChannelMode,
│                  #   MixedLightMode, MixedLightSigMode, MixedLightCalRefMode
├── model.py       # +100/-20 lines: _num_images=11, preferred_order,
│                  #   all_mode_set, Rev8 detect, grid layout, panel labels, panel_view_mode
└── core.py        # +20 lines: 11 key bindings, T key toggle, OSD, on_eof=loop
```

### 5.2 Channel Pipeline

```
SensorModel.__init__
  ├── _num_images = 11
  ├── _images = [Image() × 11]
  └── _modes = [..., MixedLightMode, MixedLightSigMode,
       MixedLightCalRefMode, RedChannelMode, GreenChannelMode, BlueChannelMode]

LidarFrameVizModel._use_default_view_modes()
  ├── all_mode_set = sensor._image_modes.keys()  (NOT filtered by _known_fields)
  ├── preferred_order assigns 11 panels
  └── Auto-detect: has_rgb_composite → panel_view_mode=0 (ALL)

update_image_size()
  ├── n_imgs > 4 → full-width vertical stack (11 panels × viewport width)
  └── panel_view_mode filters: ALL / FIRST 5 / LAST 5

MixedLightCalRefMode._prepare_data()
  ├── R: (r - r.min()) / (r.max() - r.min() + 1e-6)  [min-max norm]
  ├── G: same
  ├── B: same
  ├── NIR: nir / 65535.0  [uint16 max norm]
  ├── CalRef: calref / 255.0  [uint8 max norm]
  └── return (r_n + g_n + b_n + nir_n + calref_n) / 5.0
```

## 6. Interface Specification

### 6.1 Panel Layout (11 Channels)

| Panel | Mode Name | Data Source | Normalization |
|:-----:|-----------|-------------|:-------------:|
| 0 | NEAR_IR | `ChanField.NEAR_IR` (uint16) | AutoExposure |
| 1 | SIGNAL | `ChanField.SIGNAL` (uint16) | AutoExposure |
| 2 | REFLECTIVITY | `ChanField.REFLECTIVITY` (uint8) | /255 |
| 3 | RANGE | `ChanField.RANGE` (uint32) | AutoExposure |
| 4 | RGB | `ChanField.RGB` (3ch float16) | HDRRGBMode/ToneMapper |
| 5 | R | `RGB[:,:,0]` (float16) | AutoExposure |
| 6 | G | `RGB[:,:,1]` (float16) | AutoExposure |
| 7 | B | `RGB[:,:,2]` (float16) | AutoExposure |
| 8 | MIX_4 | `(R+G+B+NIR)/4` | Each channel [0,1] |
| 9 | MIX_5 | `(R+G+B+NIR+SIG)/5` | Each channel [0,1] |
| 10 | MIX_CALREF | `(R+G+B+NIR+CalRef)/5` | Each channel [0,1] |

### 6.2 Key Bindings

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
| 10 | `r` | `SHIFT+r` |

| Key | Action |
|-----|--------|
| `T` | Toggle panels: ALL (0-10) → FIRST 5 (0-4) → LAST 5 (5-10) |

### 6.3 Normalization Strategy

Each channel is independently normalized to [0,1] before mixing:

| Channel Type | Method | Rationale |
|-------------|--------|-----------|
| R/G/B (float16) | min-max: `(x-min)/(max-min+1e-6)` | Range ~[0,46], varies per frame |
| NIR (uint16) | `/65535.0` | Fixed range [0,65535] |
| SIGNAL (uint16) | `/65535.0` | Fixed range [0,65535] |
| REFLECTIVITY (uint8) | `/255.0` | Calibrated, fixed range [0,255] |

Without normalization, NIR (~930) dominates R/G/B (~9) by 100×.

## 7. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|:----------:|:------:|------------|
| Non-Rev8 sensors lack R/G/B fields | High | Low | `enabled()` returns False, panel shows black |
| 11 panels too small on low-res displays | Medium | Medium | T key switches to 5-panel mode |
| H key conflict with SimpleViz | High | High | Changed to T key |
| NIR dominates mixed channels | High | High | Per-channel normalization to [0,1] |
| `_known_fields` filters out new modes | High | High | Use `all_mode_set` from `_image_modes.keys()` |

## 8. Environment Baseline

| Component | Version |
|-----------|---------|
| Ouster SDK | 1.0.0 |
| Python | 3.11 |
| OS | macOS (Apple M2, Metal 4.1) |
| Tested Sensors | OS-1-MAX-256-RGB, OS-1-256-RGB |

## 9. Verification Checklist

- [x] `_num_images = 11` creates 11 Image objects
- [x] `_use_default_view_modes` assigns modes to ALL panels
- [x] Full-width layout for >4 panels
- [x] MixedLightMode + MixedLightSigMode + MixedLightCalRefMode registered
- [x] RedChannelMode + GreenChannelMode + BlueChannelMode registered
- [x] 11 key bindings (panels 0-10)
- [x] T key toggles panel view (ALL/FIRST5/LAST5)
- [x] OSD shows all 11 panel modes
- [x] `on_eof='loop'` default
- [x] Panel labels created and positioned
- [x] Per-channel normalization in MIX_4/MIX_5/MIX_CALREF
- [x] RGB composite detection → ALL 11 panels
- [x] Non-color sensor → FIRST 5 only
- [x] Data assertion: R≠G≠B, MIX4 pixel-level, MIX5 pixel-level
- [x] Data assertion: MIX_CALREF uses REFLECTIVITY/255
- [x] 100% audit passed (100/100)
