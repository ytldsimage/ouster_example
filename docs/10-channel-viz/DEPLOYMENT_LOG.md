# DEPLOYMENT LOG — Ouster 11-Channel Viz

## 2026-07-29 v2.0.0 — 11 Channel Release

### 环境
- macOS Apple M2, Metal 4.1
- Python 3.11 (venv)
- Ouster SDK 1.0.0

### 变更文件
| 文件 | 操作 | 说明 |
|------|------|------|
| `view_mode.py` | 修改 | +150行: RGBChannelMode, MixedLightCalRefMode |
| `model.py` | 修改 | +100/-20行: _num_images=11, preferred_order, panel_view_mode |
| `core.py` | 修改 | +20行: 11 key bindings, T key toggle |

### 部署路径
- 源码: `/Users/oslidar/ouster_example/python/src/ouster/sdk/viz/`
- 安装: `~/.hermes/hermes-agent/venv/lib/python3.11/site-packages/ouster/sdk/viz/`
- 备份: `~/ouster-viz-patch/`

### 测试数据
| 文件 | 传感器 | 结果 |
|------|--------|------|
| soccer.osf | OS-1-MAX-256-RGB | ✅ 10面板显示（非Rev8，无独立R/G/B） |
| Warehouse_aisle_in_Native_Color.osf | OS-1-256-RGB | ✅ 11面板显示 |

### 审计结果
- 静态代码: 21/21 PASS
- 运行时注册: 21/21 PASS
- 数据断言: 30/30 PASS (含像素级精度验证)
- 文档: 20/20 PASS
- **总计: 100/100 PASS**

### 关键发现
1. OSF 格式不暴露独立 R/G/B ChanField，只有 RGB 合成字段 (shape 256×2048×3, dtype float16)
2. `_known_fields` 过滤导致 R/G/B/MIXED_LIGHT 模式被排除，改用 `all_mode_set`
3. SimpleViz 的 H 键绑定 `adjust_subframes` 优先捕获，改用 T 键
4. R/G/B (~9) vs NIR (~930) 数值范围差100倍，必须归一化

### 回滚方案
```bash
cp ~/ouster-viz-backup/{view_mode,model,core}.py ~/.hermes/hermes-agent/venv/lib/python3.11/site-packages/ouster/sdk/viz/
```
