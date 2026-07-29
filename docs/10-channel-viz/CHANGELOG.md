# CHANGELOG — Ouster 11-Channel Viz

## [2.1.0] - 2026-07-29

### Added
- **11th channel**: `MixedLightCalRefMode` — (R+G+B+NIR+CalRef)/5
- **norm_spec_and_audit.py**: Full normalization math spec + 31/31 runtime assertions

### Fixed
- **Old code interference**: Removed `_image_mode_ind[0/1]` assignment in `_use_default_view_modes` that overrode preferred_order
- **LAST 5 mode**: Changed `range(5, min(10, n_imgs))` → `range(5, n_imgs)` so panel 10 is visible in LAST 5 mode
- **Panel toggle repositioning**: `cycle_panel_view_mode` now calls `update_image_size(0)`

### Changed
- `_num_images`: 10 → 11
- preferred_order: added `MIXED_LIGHT_CALREF` as panel 10

## [2.0.0] - 2026-07-29

### Added
- 10 panels (NIR/SIG/CALREF/RANGE/RGB/R/G/B/MIX4/MIX5)
- Per-channel normalization for mixed channels (R/G/B min-max, NIR/SIG/CalRef fixed-max)
- `T` key panel toggle (ALL/FIRST5/LAST5)
- `RGBChannelMode`, `RedChannelMode`, `GreenChannelMode`, `BlueChannelMode`
- `MixedLightMode`, `MixedLightSigMode`
- Panel labels, OSD, loop playback

### Fixed
- NIR dominance in mixed channels (97% → 25% equal weight)
- `_use_default_view_modes` only setting 2 panels
- `sorted_image_mode_names` filtering out new modes
- `H` key conflict with SimpleViz

## [1.0.0] - 2026-07-28

### Added
- Initial 10-panel concept
- MixedLightMode (R+G+B+NIR)/4
- MixedLightSigMode (R+G+B+NIR+SIG)/5
