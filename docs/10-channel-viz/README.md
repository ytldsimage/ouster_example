# 11-Channel Multi-Image Visualization

## 1. CLI 调用方式

```bash
# 播放 OSF 文件（默认循环）
ouster-cli source data.osf viz

# 指定速率
ouster-cli source data.osf viz --rate 0.5

# Python API
python3 -c "
from ouster.sdk.open_source import open_source
from ouster.sdk.viz.core import SimpleViz
src = open_source('data.osf')
sv = SimpleViz(src.sensor_info[0])
sv.run(src)
"
```

## 2. 支持的 11 个通道

| 面板 | 通道 | 数据源 | 归一化 |
|:----:|------|--------|:------:|
| 0 | NEAR_IR | `ChanField.NEAR_IR` (uint16) | AutoExposure |
| 1 | SIGNAL | `ChanField.SIGNAL` (uint16) | AutoExposure |
| 2 | REFLECTIVITY | `ChanField.REFLECTIVITY` (uint8) | /255 |
| 3 | RANGE | `ChanField.RANGE` (uint32) | AutoExposure |
| 4 | RGB | `ChanField.RGB` (3ch float16) | ToneMapper |
| 5 | R | `RGB[:,:,0]` (float16) | AutoExposure |
| 6 | G | `RGB[:,:,1]` (float16) | AutoExposure |
| 7 | B | `RGB[:,:,2]` (float16) | AutoExposure |
| 8 | MIX_4 | (R+G+B+NIR)/4 | 各通道 [0,1] |
| 9 | MIX_5 | (R+G+B+NIR+SIG)/5 | 各通道 [0,1] |
| 10 | MIX_CALREF | (R+G+B+NIR+CalRef)/5 | 各通道 [0,1] |

## 3. 切换通道模式

| 面板 | 向前 | 向后 |
|:----:|:----:|:----:|
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

## 4. 切换面板视图

| 按键 | 功能 |
|------|------|
| `T` | 全部11 (0-10) → 前5 (0-4) → 后5 (5-10) → 全部 |

## 5. 调整面板顺序

```python
# Python API 自定义
lfv.select_img_mode(0, "RGB")
lfv.select_img_mode(1, "NEAR_IR")
# ...
```

## 6. 开关不同通道

| 按键 | 功能 |
|------|------|
| `T` | 切换 前5/后5/全部 |
| `CTRL+I` | 切换：全部 → 单面板 → 翻转 |
| `1`/`2` | 显示/隐藏点云 |

## 7. 放大/缩小图像

| 按键 | 功能 |
|------|------|
| `I` | 放大 |
| `SHIFT+I` | 缩小 |

## 8. 显示/隐藏 Label

| 按键 | 功能 |
|------|------|
| `O` | 隐藏/显示 OSD 文字 |
| `?` | 显示完整键绑定帮助 |

每个面板左上角自动显示黄色标签：`面板号:通道名`

## 9. 完整键绑定速查表

### 图像面板

| 按键 | 功能 |
|------|------|
| `b`/`SHIFT+b` | 面板0 向前/向后 |
| `n`/`SHIFT+n` | 面板1 向前/向后 |
| `g`/`SHIFT+g` | 面板2 向前/向后 |
| `SHIFT+r`/`SHIFT+t` | 面板3 向前/向后 |
| `CTRL+j`/`CTRL+k` | 面板4 向前/向后 |
| `CTRL+l`/`CTRL+;` | 面板5 向前/向后 |
| `CTRL+z`/`CTRL+x` | 面板6 向前/向后 |
| `CTRL+a`/`CTRL+d` | 面板7 向前/向后 |
| `CTRL+q`/`CTRL+e` | 面板8 向前/向后 |
| `CTRL+w`/`s` | 面板9 向前/向后 |
| `r`/`SHIFT+r` | 面板10 向前/向后 |
| `t` | 切换 前5/后5/全部 |
| `I`/`SHIFT+I` | 放大/缩小 |
| `CTRL+I` | 切换图像视图模式 |

### 播放

| 按键 | 功能 |
|------|------|
| `SPACE` | 暂停/继续 |
| `,`/`.` | 后退/前进1帧 |
| `<`/`>` | 降低/提高速率 |

### 点云

| 按键 | 功能 |
|------|------|
| `1`/`2` | 切换第一/第二回波 |
| `M` | 切换着色模式 |
| `F` | 切换调色板 |
| `P`/`SHIFT+P` | 增大/减小点大小 |

### 相机

| 按键 | 功能 |
|------|------|
| `W`/`S` | 向下/向上倾斜 |
| `A`/`D` | 向右/向左旋转 |
| `Q`/`E` | 向左/向右翻滚 |
| `U` | 切换相机模式 |

### 界面

| 按键 | 功能 |
|------|------|
| `O` | 切换OSD |
| `?` | 显示帮助 |
| `SHIFT+Z` | 截图 |
| `ESC` | 退出 |

## 10. 常见工作流

### 传感器标定
```bash
ouster-cli source sensor.osf viz
# 按 T 切到前5，看 NIR/SIG/CALREF/RANGE/RGB
# 按 T 切到后5，看 R/G/B/MIX4/MIX5/MIX_CALREF
```

### 弱光信噪分析
```bash
# 混光通道已归一化，可直接对比
# MIX_5 = (R+G+B+NIR+SIG)/5
# MIX_CALREF = (R+G+B+NIR+CalRef)/5
```

## 11. 混光通道归一化

各通道数值范围差异巨大，不归一化时 NIR 主导：

| 通道 | 原始范围 | 归一化方法 |
|------|---------|-----------|
| R/G/B | ~[0, 46] (float16) | min-max: `(x-min)/(max-min+1e-6)` |
| NIR | ~[0, 65535] (uint16) | `/65535.0` |
| SIGNAL | ~[0, 65535] (uint16) | `/65535.0` |
| REFLECTIVITY | ~[0, 255] (uint8) | `/255.0` |

## 12. Troubleshooting

| 问题 | 原因 | 解决 |
|------|------|------|
| 只看到5个面板 | 非彩色传感器 | 按 T 切到全部 |
| 面板5-10是黑的 | 无RGB通道 | 非Rev8传感器无R/G/B |
| 混光通道偏暗 | NIR主导 | 已修复：各通道独立归一化 |
| 按T无反应 | 旧版本 | 重新打补丁 |
| SDK升级后失效 | 补丁被覆盖 | 重新执行安装脚本 |

## 13. 文件变更

| 文件 | 行数 | 说明 |
|------|:----:|------|
| `view_mode.py` | +150 | RGBChannelMode, Red/Green/BlueChannelMode, MixedLightCalRefMode |
| `model.py` | +100/-20 | _num_images=11, preferred_order, all_mode_set, panel_view_mode |
| `core.py` | +20 | 11 key bindings, T key toggle, OSD, on_eof=loop |

## 14. 测试配置

- **SDK**: v1.0.0
- **传感器**: OS-1-MAX-256-RGB (Rev8), OS-1-256-RGB
- **平台**: macOS Apple M2, Metal 4.1
- **Python**: 3.11
