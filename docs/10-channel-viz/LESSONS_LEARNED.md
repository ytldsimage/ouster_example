# LESSONS_LEARNED.md — Ouster 11-Channel Viz

## 1. SDK Architecture Pitfalls

### 1.1 `_num_images = 2` Hardcoded
**Symptom**: Only 2 image panels.  
**Fix**: `_num_images = 11`.

### 1.2 `_use_default_view_modes` Only Sets 2 Panels
**Symptom**: Panels 2-10 black.  
**Fix**: `range(2)` → `range(self._max_images)` + preferred_order.

### 1.3 Old Code Overriding preferred_order
**Symptom**: Depth shown twice, RANGE appearing on wrong panels.  
**Root cause**: Old code at lines 1045-1067 set `_image_mode_ind[0]` to REFLECTIVITY and `_image_mode_ind[1]` to RGB BEFORE the preferred_order loop. Even though preferred_order overwrote `_image_mode_names`, `_image_mode_ind` was still wrong, causing `cycle_img_mode` to jump to wrong modes.  
**Fix**: Remove the entire old code block. Only set `_cloud_mode_ind` and let preferred_order handle everything.

### 1.4 `sorted_image_mode_names` Filters New Modes
**Symptom**: R/G/B/MIXED_LIGHT modes registered but not found.  
**Root cause**: `sorted_image_mode_names()` uses `& self._known_fields` intersection. `_known_fields` comes from `frame.fields` — OSF only has `RGB`, not `R`/`G`/`B`.  
**Fix**: Use `all_mode_set = set(sensor._image_modes.keys())` for preferred_order lookup.

### 1.5 OSF Doesn't Expose Independent R/G/B
**Symptom**: `ChanField.R/G/B` not in `frame.fields`.  
**Root cause**: OSF v2.2.0 wraps R/G/B in RGB 3-channel array.  
**Fix**: `RGBChannelMode` extracts from `RGB[:,:,0/1/2]`.

## 2. Layout Pitfalls

### 2.1 `panel_view_mode==2` Hid Panel 10
**Symptom**: LAST 5 mode only showed panels 5-9, hiding MIX_CALREF.  
**Root cause**: `range(5, min(10, n_imgs))` — `min(10, 11)=10`, so range(5,10) = [5,6,7,8,9].  
**Fix**: `range(5, n_imgs)` — shows all remaining panels.

### 2.2 Panels Too Narrow
**Symptom**: 11 panels invisible at default size.  
**Fix**: `_img_size_fraction = 12`.

## 3. Key Binding Pitfalls

### 3.1 `H` Key Conflict with SimpleViz
**Symptom**: H key does nothing.  
**Root cause**: `SimpleViz.__init__` binds `(ord('H'), 0)` → `adjust_subframes`. Handler stack priority means SimpleViz catches it first.  
**Fix**: Changed to `T` key (free in both handlers).

### 3.2 `cycle_panel_view_mode` Didn't Reposition
**Symptom**: `_panel_view_mode` changes but panels don't move.  
**Root cause**: Only called `model.update()` (data), not `update_image_size()` (layout).  
**Fix**: Added `self.update_image_size(0)`.

## 4. Data Pitfalls

### 4.1 NIR Dominates Mixed Channels
**Symptom**: MIX_4/MIX_5 look identical to NIR.  
**Root cause**: R/G/B ~[0,46], NIR ~[0,65535]. Equal-weight average: NIR contributes 97%.  
**Fix**: Per-channel normalization:
- R/G/B: `(x-min)/(max-min+1e-6)` (min-max)
- NIR/SIGNAL: `/65535.0` (uint16 max)
- REFLECTIVITY: `/255.0` (uint8 max)

### 4.2 Collator Returns Empty frame.fields
**Symptom**: Iterating OSF source gives empty fields list.  
**Fix**: Use `lfv._model._frame_set[0]` for runtime frame access.

## 5. API Reference

| API | Usage | Notes |
|-----|-------|-------|
| `Label.set_text(str)` | Set text | Not `.text =` |
| `Label.set_position(x, y)` | Set position | Not `.position =` |
| `Label.set_rgba((r,g,b,a))` | Set color | **Pass tuple**, not 4 args |
| `SimpleViz(m, on_eof='loop')` | Loop playback | Now default |
| `lfv._model._frame_set[0]` | Internal frame | For data assertions |
| `ChanField.R/G/B` | String "R"/"G"/"B" | Not independent in OSF |
| `ChanField.RGB` | String "RGB" | shape (H,W,3), float16 |

## 6. File Summary

| File | Δ Lines | Key Changes |
|------|:-------:|------------|
| `view_mode.py` | +150 | 6 new mode classes, all normalized |
| `model.py` | +85/-35 | 11 panels, preferred_order, cleaned old code |
| `core.py` | +20 | 11 key bindings, T toggle, update_image_size(0) |

## 7. TODO

- [ ] Support CLI `--num-images` parameter
- [ ] User-customizable panel order via Python API
- [ ] Panel label z-order fix (labels may not render)
- [ ] CHANGELOG.rst in repo root
