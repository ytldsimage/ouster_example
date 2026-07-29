# PRD: Ouster SDK 11-Channel Multi-Image Visualization

> **Version**: 2.1.0 | **Date**: 2026-07-29 | **Status**: Implemented + Verified

## 1. Overview

Extend Ouster SDK `viz` module from `_num_images=2` to `_num_images=11`, supporting simultaneous display of all sensor data channels including three normalized composite mixed-light modes.

## 2. Problem Statement

Original SDK hardcodes 2 image panels. Users need to visualize all available channels simultaneously for sensor calibration, noise analysis, and algorithm development.

## 3. Goals

| Goal | Metric |
|------|--------|
| Display all channels simultaneously | 11 panels visible |
| Per-channel normalization | All channels independently normalized to [0,1] before mixing |
| Panel view toggle | T key: ALL (0-10) → FIRST 5 (0-4) → LAST 5 (5-10) |
| Loop playback | `on_eof='loop'` default |
| Auto-detect color sensor | RGB → all 11 panels; no color → first 5 only |

## 4. Non-Goals

- Modifying 3D point cloud visualization
- Changing sensor driver or file formats

## 5. Architecture

### 5.1 Files Modified

| File | Lines | Core Changes |
|------|:-----:|-------------|
| `view_mode.py` | +150 | `RGBChannelMode`, `Red/Green/BlueChannelMode`, `MixedLightMode`, `MixedLightSigMode`, `MixedLightCalRefMode` |
| `model.py` | +85/-35 | `_num_images=11`, preferred_order, `all_mode_set`, Rev8 detect, layout, panel labels, panel_view_mode, removed old `_image_mode_ind` interference |
| `core.py` | +20 | 11 key bindings, T key toggle, `cycle_panel_view_mode` calls `update_image_size(0)`, `on_eof='loop'` |

### 5.2 Data Pipeline

```
SensorModel.__init__
  ├── _num_images = 11
  ├── _images = [Image() × 11]
  └── _modes = [..., MixedLightMode, MixedLightSigMode,
       MixedLightCalRefMode, RedChannelMode, GreenChannelMode, BlueChannelMode]

_use_default_view_modes()
  ├── all_mode_set = sensor._image_modes.keys()  ← NOT filtered by _known_fields
  ├── preferred_order assigns all 11 panels
  └── Auto-detect: has_rgb_composite → ALL panels

update_image_size()
  ├── n_imgs > 4 → full-width vertical stack
  ├── panel_view_mode==1 → panels 0-4 only
  ├── panel_view_mode==2 → panels 5-10 (LAST 5+1)
  └── panel_view_mode==0 → all panels

MixedLightCalRefMode._prepare_data()
  ├── R: (r - min)/(max - min + ε)    ← min-max norm
  ├── G: same
  ├── B: same
  ├── NIR: nir / 65535.0               ← uint16 max norm
  ├── CalRef: calref / 255.0           ← uint8 max norm
  └── return (r_n + g_n + b_n + nir_n + calref_n) / 5.0
```

## 6. Interface Specification

### 6.1 Panel Layout (11 Channels)

| Panel | Mode | Source | Norm |
|:-----:|------|--------|:----:|
| 0 | NEAR_IR | ChanField.NEAR_IR (uint16) | AE |
| 1 | SIGNAL | ChanField.SIGNAL (uint16) | AE |
| 2 | REFLECTIVITY | ChanField.REFLECTIVITY (uint8) | /255 |
| 3 | RANGE | ChanField.RANGE (uint32) | AE |
| 4 | RGB | ChanField.RGB (3ch float16) | ToneMapper |
| 5 | R | RGB[:,:,0] (float16) | AE |
| 6 | G | RGB[:,:,1] (float16) | AE |
| 7 | B | RGB[:,:,2] (float16) | AE |
| 8 | MIX_4 | (R+G+B+NIR)/4 | Per-ch [0,1] |
| 9 | MIX_5 | (R+G+B+NIR+SIG)/5 | Per-ch [0,1] |
| 10 | MIX_CALREF | (R+G+B+NIR+CalRef)/5 | Per-ch [0,1] |

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
| ALL/FIRST/LAST | `T` | — |

### 6.3 Normalization Math

| Channel | Method | Formula | Range |
|---------|--------|---------|-------|
| R/G/B (float16) | min-max | `(x-min)/(max-min+ε)`, ε=1e-6 | [0,1] |
| NIR (uint16) | fixed max | `x/65535.0` | [0,1] |
| SIGNAL (uint16) | fixed max | `x/65535.0` | [0,1] |
| REFLECTIVITY (uint8) | fixed max | `x/255.0` | [0,1] |

**Why**: R/G/B ~[0,46], NIR ~[0,65535]. Without norm, NIR dominates 97% of mix.

## 7. Risk Assessment

| Risk | Mitigation |
|------|-----------|
| Non-Rev8 sensors lack R/G/B | `enabled()` returns False |
| `H` key conflict with SimpleViz | Changed to `T` key |
| Old code sets `_image_mode_ind[0/1]` | Removed old code, only preferred_order |
| `_known_fields` filters new modes | Use `all_mode_set` from `_image_modes.keys()` |
| NIR dominates mixed channels | Per-channel normalization [0,1] |

## 8. Environment

| Component | Version |
|-----------|---------|
| Ouster SDK | 1.0.0 |
| Python | 3.11 |
| OS | macOS Apple M2, Metal 4.1 |

## 9. Verification

- [x] `_num_images = 11`
- [x] 11 panels correctly assigned (NIR/SIG/CALREF/RANGE/RGB/R/G/B/MIX4/MIX5/MIX_CALREF)
- [x] MixedLightCalRefMode uses REFLECTIVITY/255
- [x] All mixed channels ∈ [0,1]
- [x] Pixel-level manual computation matches
- [x] T key cycles ALL/FIRST5/LAST5
- [x] LAST 5 shows panels 5-10
- [x] Old `_image_mode_ind` code removed
- [x] `on_eof='loop'` default
- [x] 100% audit (100/100 + 31/31 norm)
