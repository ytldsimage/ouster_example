# 10-Channel Multi-Image Visualization

## Overview

Extended Ouster SDK viz module supporting simultaneous display of 10 image channels, including two composite mixed-light modes for Rev8 native-color sensors.

---

## 1. CLI 调用方式

### 1.1 基本启动

```bash
# 播放 OSF 文件（默认循环播放）
ouster-cli source data.osf viz

# 播放 PCAP 文件
ouster-cli source data.pcap viz

# 连接实况传感器
ouster-cli source <sensor_hostname> viz

# 指定播放速率
ouster-cli source data.osf viz --rate 0.5

# 暂停在第 0 帧（方便观察初始状态）
ouster-cli source data.osf viz --pause-at 0
```

### 1.2 Python API 调用

```python
from ouster.sdk.open_source import open_source
from ouster.sdk.viz.core import SimpleViz

src = open_source("data.osf")
m = src.sensor_info[0]

# 默认循环播放（on_eof='loop'）
sv = SimpleViz(m)
sv.run(src)

# 指定播放速率 + 单次播放
sv = SimpleViz(m, rate=1.0, on_eof='exit')
sv.run(src)

# 暂停在第 0 帧
sv = SimpleViz(m, pause_at=0)
sv.run(src)
```

### 1.3 直接使用 LidarFrameViz（高级）

```python
from ouster.sdk.open_source import open_source
from ouster.sdk._bindings.viz import PointViz
from ouster.sdk.viz.core import LidarFrameViz

src = open_source("data.osf")
metas = src.sensor_info

viz = PointViz("My 10-Channel Viz")
lfv = LidarFrameViz(metas, viz, _add_default_controls=True)

# 手动喂帧
for scans in src:
    lfv.update(scans, 0)
    lfv.draw()
    break  # 先停在第 0 帧

# 手动控制模式
lfv.select_img_mode(0, "NEAR_IR")    # 面板 0 显示 NEAR_IR
lfv.select_img_mode(1, "RGB")         # 面板 1 显示 RGB
lfv.select_img_mode(2, "SIGNAL")      # 面板 2 显示 SIGNAL

# 继续播放剩余帧
frame_count = 1
for scans in src:
    lfv.update(scans, frame_count)
    lfv.draw()
    frame_count += 1

lfv.run()
```

---

## 2. 支持的 10 个通道

| 面板 # | 默认通道 | 说明 | Rev8 专属 |
|:------:|---------|------|:---------:|
| 0 | NEAR_IR | 近红外（16-bit） | ❌ |
| 1 | SIGNAL | 信号强度（16-bit） | ❌ |
| 2 | REFLECTIVITY | 校准反射率（8-bit） | ❌ |
| 3 | RANGE | 深度距离（19-bit） | ❌ |
| 4 | RGB | 合成彩色（48-bit） | ✅ |
| 5 | R | 红色（16-bit） | ✅ |
| 6 | G | 绿色（16-bit） | ✅ |
| 7 | B | 蓝色（16-bit） | ✅ |
| 8 | MIX_4 | (R+G+B+NIR)/4 混光均值 | ✅ |
| 9 | MIX_5 | (R+G+B+NIR+SIG)/5 混光均值 | ✅ |

> **注意**：非 Rev8 传感器（无 R/G/B 通道）默认只显示前 5 个面板（NEAR_IR/SIGNAL/REFLECTIVITY/RANGE/RGB）。按 `t` 键切换前 5 / 后 5 / 全部。

---

## 3. 切换通道模式（每个面板独立）

每个面板都可以独立切换到任意可用通道。按对应键**向前**循环，加 `SHIFT` **向后**循环。

| 面板 | 向前切换 | 向后切换 |
|:----:|:--------:|:--------:|
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

**示例**：
- 按 `b` → 面板 0 切换到下一个通道（如 NEAR_IR → RANGE）
- 按 `SHIFT+b` → 面板 0 切换到上一个通道
- 按 `g` → 面板 2 切换到下一个通道
- 连续按 `b` 可在所有可用通道间循环：NEAR_IR → RANGE → REFLECTIVITY → RGB → SIGNAL → NEAR_IR → ...

---

## 4. 调整面板顺序

面板顺序由 `_use_default_view_modes()` 自动分配，按可用通道的字母顺序排列。要自定义顺序，使用 Python API：

```python
from ouster.sdk.open_source import open_source
from ouster.sdk._bindings.viz import PointViz
from ouster.sdk.viz.core import LidarFrameViz

src = open_source("data.osf")
metas = src.sensor_info

viz = PointViz("Custom Order")
lfv = LidarFrameViz(metas, viz, _add_default_controls=True)

# 先喂一帧让模式被发现
for scans in src:
    lfv.update(scans, 0)
    lfv.draw()
    break

# 自定义面板顺序（设置每个面板显示哪个通道）
custom_order = {
    0: "RGB",           # 面板 0 → RGB
    1: "NEAR_IR",       # 面板 1 → NIR
    2: "SIGNAL",        # 面板 2 → 信号强度
    3: "REFLECTIVITY",  # 面板 3 → 反射率
    4: "RANGE",         # 面板 4 → 深度
    5: "MIXED_LIGHT",   # 面板 5 → 混光 4 通道
    6: "MIXED_LIGHT_SIG", # 面板 6 → 混光 5 通道
    7: "RANGE",         # 面板 7 → 深度（重复）
    8: "SIGNAL",        # 面板 8 → 信号（重复）
    9: "NEAR_IR",       # 面板 9 → NIR（重复）
}

for panel_idx, mode_name in custom_order.items():
    lfv.select_img_mode(panel_idx, mode_name)

# 继续播放
frame_count = 1
for scans in src:
    lfv.update(scans, frame_count)
    lfv.draw()
    frame_count += 1

lfv.run()
```

---

## 5. 开关不同通道（显示/隐藏面板）

### 5.1 显示/隐藏全部图像

| 按键 | 功能 |
|------|------|
| `CTRL+I` | 循环切换：全部显示 → 全部翻转 → 单面板 → 单面板翻转 |

### 5.2 只看单个面板

按 `CTRL+I` 切换到 `ONE` 模式，只显示面板 0。再按 `CTRL+I` 恢复全部显示。

### 5.3 隐藏特定面板（Python API）

```python
# 隐藏面板 3-9（只看前 3 个）
for i in range(3, 10):
    lfv._model._images[i].set_position(1000, 0, 0, 0)  # 移到屏幕外

# 恢复显示（重新调用 update_image_size）
lfv.update_image_size(0)
```

### 5.4 切换 3D 点云显示

| 按键 | 功能 |
|------|------|
| `1` | 显示/隐藏第一回波点云 |
| `2` | 显示/隐藏第二回波点云 |
| `M` | 切换点云着色模式（RANGE → SIGNAL → REFLECTIVITY → RGB → ...） |
| `F` | 切换点云调色板 |

---

## 6. 放大/缩小图像

### 6.1 图像面板缩放

| 按键 | 功能 |
|------|------|
| `I` | 放大图像（增加面板高度） |
| `SHIFT+I` | 缩小图像（减少面板高度） |

- 图像尺寸共 20 级（`_img_size_fraction` 从 0 到 20）
- 初始值为 12（适合 10 面板同时显示）
- 按 `I` 放大后，面板会变高变宽，但超出视口的面板会被裁剪
- 按 `SHIFT+I` 缩小后，面板变窄，更多面板能同时显示

### 6.2 3D 点云缩放

| 按键 | 功能 |
|------|------|
| `=` / `-` | 放大/缩小点云（鼠标滚轮也可） |
| `P` / `SHIFT+P` | 增大/减小点的大小 |
| 鼠标拖拽 | 旋转视角 |
| `SHIFT` + 鼠标拖拽 | 平移视角 |

### 6.3 相机控制

| 按键 | 功能 |
|------|------|
| `W` / `S` | 相机向下/向上倾斜 |
| `A` / `D` | 相机向右/向左旋转 |
| `Q` / `E` | 相机向左/向右翻滚 |
| `U` | 切换相机模式（跟随 → 固定 → 平滑） |
| `SHIFT+1` | 俯视图 |
| `SHIFT+2` | 前视图 |
| `SHIFT+3` | 左视图 |

---

## 7. 显示/隐藏 Label（通道名称标注）

### 7.1 面板标签（Per-Panel Labels）

每个面板左上角自动显示黄色标签，格式为 `面板号:通道名`，例如：
- `0:NEAR_IR`
- `1:RANGE`
- `2:REFLECTIVITY`
- `3:RGB`
- `8:MIXED_LIGHT`

标签会随通道切换自动更新。

### 7.2 OSD（屏幕信息叠加）

| 按键 | 功能 |
|------|------|
| `O` | 切换 OSD 显示/隐藏 |

OSD 显示内容：
- 所有 10 个面板的当前通道名和快捷键
- 点云状态（ON/OFF）
- 点云着色模式
- 调色板名称
- 传感器信息（型号、序列号、固件版本）
- 帧号和时间戳

### 7.3 帮助信息

| 按键 | 功能 |
|------|------|
| `?` | 显示完整键绑定帮助（覆盖 OSD） |

### 7.4 自定义标签样式（Python API）

```python
# 修改标签颜色（RGBA）
for lbl in lfv._model._panel_labels:
    lbl.set_rgba((0.0, 1.0, 0.0, 1.0))  # 绿色

# 修改标签大小
for lbl in lfv._model._panel_labels:
    lbl.set_scale(1.0)  # 更大

# 修改标签位置（x, y 坐标，范围 -1 到 1）
for lbl in lfv._model._panel_labels:
    lbl.set_position(0.0, 0.95)  # 移到顶部居中
```

---

## 8. 完整键绑定速查表

### 图像面板

| 按键 | 功能 |
|------|------|
| `b` / `SHIFT+b` | 面板 0 向前/向后切换 |
| `n` / `SHIFT+n` | 面板 1 向前/向后切换 |
| `g` / `SHIFT+g` | 面板 2 向前/向后切换 |
| `SHIFT+r` / `SHIFT+t` | 面板 3 向前/向后切换 |
| `CTRL+j` / `CTRL+k` | 面板 4 向前/向后切换 |
| `CTRL+l` / `CTRL+;` | 面板 5 向前/向后切换 |
| `CTRL+z` / `CTRL+x` | 面板 6 向前/向后切换 |
| `CTRL+a` / `CTRL+d` | 面板 7 向前/向后切换 |
| `CTRL+q` / `CTRL+e` | 面板 8 向前/向后切换 |
| `CTRL+w` / `s` | 面板 9 向前/向后切换 |
| `t` | 切换面板视图: 全部(0-9) → 前5(0-4) → 后5(5-9) |
| `I` / `SHIFT+I` | 放大/缩小图像 |
| `CTRL+I` | 切换图像视图模式 |

### 播放控制

| 按键 | 功能 |
|------|------|
| `SPACE` | 暂停/继续 |
| `,` / `.` | 后退/前进 1 帧 |
| `<` / `>` | 降低/提高播放速率 |

### 3D 点云

| 按键 | 功能 |
|------|------|
| `1` / `2` | 显示/隐藏第一/第二回波 |
| `M` | 切换点云着色模式 |
| `F` | 切换点云调色板 |
| `P` / `SHIFT+P` | 增大/减小点大小 |

### 相机

| 按键 | 功能 |
|------|------|
| `W` / `S` | 向下/向上倾斜 |
| `A` / `D` | 向右/向左旋转 |
| `Q` / `E` | 向左/向右翻滚 |
| `U` | 切换相机模式 |
| `SHIFT+1/2/3` | 俯视/前视/左视图 |

### 界面

| 按键 | 功能 |
|------|------|
| `O` | 切换 OSD |
| `?` | 显示帮助 |
| `CTRL+O` | 切换 OSD 缩放 |
| `ESC` | 退出 |

---

## 9. 常见工作流

### 9.1 传感器标定验证

```bash
# 启动后同时查看 RGB + NIR + SIGNAL
ouster-cli source sensor_data.osf viz
# 按 g 切换面板 2 到 SIGNAL
# 按 CTRL+j 切换面板 4 到 RGB
# 按 O 隐藏 OSD 获得更大视野
```

### 9.2 噪声分析

```bash
# 同时查看 RANGE + SIGNAL + REFLECTIVITY
ouster-cli source noisy_data.osf viz
# 面板 0-2 已默认显示这三个通道
# 按 SPACE 暂停，按 ,/. 逐帧对比
```

### 9.3 Rev8 彩色质量评估

```bash
# 同时查看 R + G + B + RGB + NIR + MIX_4 + MIX_5
ouster-cli source rev8_color.osf viz
# 默认 10 面板已覆盖所有通道
# 按 I 放大仔细看单个通道
# 按 CTRL+I 切换到单面板模式聚焦
```

### 9.4 截图保存

```bash
# 播放时按 SHIFT+Z 截图
# 连续截图：按 SHIFT+X 开始/停止
# 截图分辨率：按 V / SHIFT+V 调整
```

---

## 10. Layout

- **≤ 4 panels**: Original vertical stack with aspect-ratio-aware sizing
- **> 4 panels**: Full-width vertical stack — each panel spans the full viewport width

---

## 11. Architecture

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

---

## 12. Mixed-Light Modes

### MixedLightMode (Panel 8)
Average of R, G, B, NIR channels. Useful for:
- Evaluating overall luminance across visible + IR spectrum
- Detecting material properties that differ in IR vs. visible

### MixedLightSigMode (Panel 9)
Average of R, G, B, NIR, SIGNAL channels. Useful for:
- Combined passive + active illumination analysis
- Signal quality assessment with color context

Both modes auto-disable on non-Rev8 sensors (R/G/B fields unavailable).

---

## 13. Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Only 2 panels visible | Old SDK version | Apply patches to `viz/model.py` |
| Panels 2-9 are black | Non-Rev8 sensor | Use `b`/`n`/`g` keys to switch to available modes |
| Images too small | High aspect ratio | Press `I` to increase size |
| No video playback | `on_eof='exit'` | Default changed to `'loop'`; re-apply `core.py` patch |
| Labels not visible | Rendering order | Check label z-order; may need rebuild |

---

## 14. Files Modified

| File | Lines Changed | Description |
|------|:-------------:|-------------|
| `view_mode.py` | +66 | `MixedLightMode`, `MixedLightSigMode` classes |
| `model.py` | +108/-43 | `_num_images=10`, layout, labels, mode assignment |
| `core.py` | +45 | Key bindings, OSD, `on_eof='loop'` default |

---

## 15. Tested Configuration

- **SDK**: v1.0.0
- **Sensors**: OS-1-MAX-256-RGB (Rev8), OS-1-256-RGB
- **Platform**: macOS Apple M2, Metal 4.1
- **Python**: 3.11
