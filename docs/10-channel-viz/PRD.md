# PRD: Ouster SDK 10-Channel Multi-Image Visualization

> **Version**: 1.0.0  
> **Date**: 2026-07-28  
> **Author**: QNI (AI-assisted)  
> **Status**: Implemented  

## 1. Overview

Extend the Ouster SDK `viz` module to support simultaneous display of up to 10 image channels, including two new composite mixed-light modes. The original SDK hardcodes `_num_images = 2`, limiting visualization to two panels at a time.

## 2. Problem Statement

Users working with Ouster Rev8 native-color sensors (OS-1-MAX-256-RGB, etc.) need to visualize multiple data channels simultaneously for:
- Sensor calibration and validation
- Noise analysis across channels
- Color quality assessment (R/G/B/NIR)
- Signal vs. reflectivity comparison
- Mixed-light composite analysis

The original SDK only shows 2 panels, requiring constant manual switching with `B`/`N` keys.

## 3. Goals

| Goal | Success Metric |
|------|---------------|
| Display all available channels simultaneously | 10 panels visible at once |
| Support Rev8 native color (R/G/B/RGB) | Panels show R, G, B, RGB independently |
| Support standard channels | NIR, SIGNAL, REFLECTIVITY, RANGE always available |
| Support composite channels | MIXED_LIGHT (R+G+B+NIR), MIXED_LIGHT_SIG (+SIGNAL) |
| Per-panel mode switching | Each panel has independent key binding |
| Loop playback by default | `on_eof='loop'` in SimpleViz |
| Per-panel labels | Channel name displayed on each panel |

## 4. Non-Goals

- Modifying the 3D point cloud visualization
- Adding new sensor driver features
- Changing the OSF/PCAP file formats

## 5. Architecture

### 5.1 Files Modified

```
python/src/ouster/sdk/viz/
├── view_mode.py   # +66 lines: MixedLightMode, MixedLightSigMode
├── model.py       # +108/-43 lines: _num_images, layout, labels, mode assignment
└── core.py        # +45 lines: key bindings, OSD, on_eof default
```

### 5.2 Data Flow

```
SensorModel.__init__
  ├── _num_images = 10
  ├── _images = [Image() × 10]
  └── _modes = [..., MixedLightMode, MixedLightSigMode]

LidarFrameVizModel.__init__
  ├── _panel_labels = [Label × 10]
  └── _use_default_view_modes() → assigns mode to ALL panels

update_image_size()
  ├── n_imgs > 4 → full-width vertical stack
  └── positions labels at top-left of each panel

update()
  ├── sensor.update_images(mode_names, frame)
  └── updates label text with current mode name
```

### 5.3 Layout Strategy

| Panel Count | Layout |
|:-----------:|--------|
| ≤ 4 | Original vertical stack (aspect-ratio aware) |
| > 4 | Full-width vertical stack: each panel spans [-1, 1] horizontally |

For 10 panels with 256×2048 sensor (aspect=8):
- Each panel: 2.0 width × 0.2 height
- Panels stack top-to-bottom filling the viewport

## 6. Interface Specification

### 6.1 Key Bindings (10 Panels)

| Panel | Channel | Forward Key | Backward Key |
|:-----:|---------|:-----------:|:------------:|
| 0 | R/NEAR_IR | `b` | `SHIFT+b` |
| 1 | G/RANGE | `n` | `SHIFT+n` |
| 2 | B/REFLECTIVITY | `g` | `SHIFT+g` |
| 3 | RGB | `SHIFT+r` | `SHIFT+t` |
| 4 | NIR | `CTRL+j` | `CTRL+k` |
| 5 | SIG | `CTRL+l` | `CTRL+;` |
| 6 | REF | `CTRL+z` | `CTRL+x` |
| 7 | DEPTH | `CTRL+a` | `CTRL+d` |
| 8 | MIX_4 | `CTRL+q` | `CTRL+e` |
| 9 | MIX_5 | `CTRL+w` | `s` |

### 6.2 New ViewMode Classes

```python
class MixedLightMode(SimpleMode):
    """R+G+B+NIR average (4-channel composite)"""
    # Only enabled when R, G, B, NEAR_IR fields exist (Rev8)

class MixedLightSigMode(SimpleMode):
    """R+G+B+NIR+SIGNAL average (5-channel composite)"""
    # Only enabled when R, G, B, NEAR_IR, SIGNAL fields exist
```

### 6.3 OSD Display

```
image: b:NEAR_IR, n:RANGE, g:REFLECTIVITY, SHIFT+r:RGB, CTRL+j:SIGNAL, ...
```

## 7. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|:----------:|:------:|------------|
| Non-Rev8 sensors lack R/G/B fields | High | Low | `enabled()` returns False, panel shows black |
| 10 panels too small on low-res displays | Medium | Medium | `I`/`SHIFT+I` keys resize, `CTRL+I` cycles view mode |
| Key conflicts with SimpleViz | Low | High | Used modifier combinations to avoid conflicts |
| Performance with10 panels | Low | Low | GPU-accelerated rendering, minimal CPU overhead |

## 8. Environment Baseline

| Component | Version |
|-----------|---------|
| Ouster SDK | 1.0.0 |
| Python | 3.11 |
| OS | macOS (Apple M2, Metal 4.1) |
| Tested Sensors | OS-1-MAX-256-RGB, OS-1-256-RGB |

## 9. Verification Checklist

- [x] `_num_images = 10` creates10 Image objects
- [x] `_use_default_view_modes` assigns modes to ALL panels
- [x] Full-width layout for >4 panels
- [x] MixedLightMode + MixedLightSigMode registered
- [x]10 key bindings (panels 0-9)
- [x] OSD shows all10 panel modes
- [x] `on_eof='loop'` default
- [x] Panel labels created and positioned
- [x] Syntax check passes for all 3 files
