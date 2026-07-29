# CHANGELOG — Ouster 11-Channel Viz

## [2.0.0] - 2026-07-29

### Added
- **11th channel**: `MixedLightCalRefMode` — (R+G+B+NIR+CalRef)/5, each channel independently normalized
- **Per-channel normalization** for all mixed-light modes:
  - R/G/B: min-max normalization `(x-min)/(max-min+1e-6)`
  - NIR/SIGNAL: `/65535.0` (uint16 max)
  - REFLECTIVITY: `/255.0` (uint8 max)
- **Panel view toggle** (`T` key): cycles ALL (0-10) → FIRST 5 (0-4) → LAST 5 (5-10)
- **`update_image_size(0)` call in `cycle_panel_view_mode`** — fixes panels not repositioning on toggle
- **Full documentation suite**: PRD.md, README.md, QUICKSTART.md, LESSONS_LEARNED.md

### Fixed
- **NIR dominance in mixed channels**: R/G/B range ~[0,46] vs NIR ~[0,65535] — now normalized before mixing
- **`_use_default_view_modes` only setting 2 panels**: changed `range(2)` to `range(self._max_images)`
- **`sorted_image_mode_names` filtering out R/G/B modes**: changed to use `all_mode_set = sensor._image_modes.keys()`
- **H key conflict**: SimpleViz binds H to `adjust_subframes`, changed to T key
- **Panel view toggle not repositioning**: added `update_image_size(0)` call

### Changed
- `_num_images`: 2 → 11
- `_img_size_fraction`: 4 → 12
- Default `on_eof`: 'exit' → 'loop'
- Preferred panel order: NIR/SIG/CALREF/RANGE/RGB/R/G/B/MIX4/MIX5/MIX_CALREF

## [1.0.0] - 2026-07-28

### Added
- Initial 10-channel support
- MixedLightMode (R+G+B+NIR)/4
- MixedLightSigMode (R+G+B+NIR+SIG)/5
- RGBChannelMode, RedChannelMode, GreenChannelMode, BlueChannelMode
- 10 panel key bindings
- Panel labels (yellow text)
- Rev8 auto-detect (RGB composite → all panels)
- Full-width vertical stack layout for >4 panels
