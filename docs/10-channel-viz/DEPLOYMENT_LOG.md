# DEPLOYMENT LOG — Ouster 11-Channel Viz

## 2026-07-29 v2.1.0 — 11 Channel Final

### Environment
- macOS Apple M2, Metal 4.1, Python 3.11, Ouster SDK 1.0.0

### Changes from v2.0.0
| Change | Detail |
|--------|--------|
| +1 panel | MIX_CALREF (R+G+B+NIR+CalRef)/5 |
| Remove old code | `_image_mode_ind[0/1]` override removed from `_use_default_view_modes` |
| Fix LAST 5 | `range(5, min(10))` → `range(5, n_imgs)` |
| Fix toggle repositioning | `cycle_panel_view_mode` calls `update_image_size(0)` |
| Norm math doc | `norm_spec_and_audit.py` — 31/31 runtime assertions |

### File Status
| File | Status | Lines |
|------|--------|:-----:|
| `view_mode.py` | ✅ Synced | 752 |
| `model.py` | ✅ Synced | ~1820 |
| `core.py` | ✅ Synced | ~2195 |
| `PRD.md` | ✅ v2.1.0 | ~150 |
| `README.md` | ✅ Updated | ~150 |
| `QUICKSTART.md` | ✅ Updated | ~80 |
| `LESSONS_LEARNED.md` | ✅ v2.1.0 | ~120 |
| `CHANGELOG.md` | ✅ v2.1.0 | ~50 |
| `DEPLOYMENT_LOG.md` | ✅ This file | ~60 |
| `norm_spec_and_audit.py` | ✅ 31/31 | ~410 |

### Paths
- Source: `/Users/oslidar/ouster_example/python/src/ouster/sdk/viz/`
- Installed: `~/.hermes/hermes-agent/venv/lib/python3.11/site-packages/ouster/sdk/viz/`
- Backup: `~/ouster-viz-patch/`

### Test Results
| Test | Result |
|------|--------|
| soccer.osf (OS-1-MAX-256-RGB) | ✅ 11 panels, no duplicates |
| Warehouse_aisle_in_Native_Color.osf (OS-1-256-RGB) | ✅ 11 panels, no duplicates |
| Static code (21 checks) | ✅ 21/21 |
| Runtime registration (21 checks) | ✅ 21/21 |
| Data assertions (30 checks) | ✅ 30/30 |
| Documentation (20 checks) | ✅ 20/20 |
| Normalization (31 checks) | ✅ 31/31 |
| **Total** | **124/124** |

### Rollback
```bash
cp ~/ouster-viz-backup/{view_mode,model,core}.py ~/.hermes/hermes-agent/venv/lib/python3.11/site-packages/ouster/sdk/viz/
```
