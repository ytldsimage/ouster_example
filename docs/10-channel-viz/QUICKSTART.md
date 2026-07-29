# 🚀 Ouster 10-Channel Viz — 小白用户快速上手指南

> 适用于：刚安装了 Ouster SDK 的新用户，想要同时查看全部 10 个图像通道。

---

## 第一步：确认环境

### 1.1 已安装的软件

```bash
# 检查 Python 版本（需要 3.11+）
python3 --version

# 检查 Ouster SDK 是否已安装
pip show ouster-sdk

# 如果没有安装，执行：
pip install ouster-sdk
```

### 1.2 找到 SDK 安装路径

```bash
# 找到 viz 模块所在目录
python3 -c "import ouster.sdk.viz; import os; print(os.path.dirname(ouster.sdk.viz.__file__))"

# 输出类似：
# /Users/你的用户名/.hermes/hermes-agent/venv/lib/python3.11/site-packages/ouster/sdk/viz
```

记住这个路径，下面要用。

---

## 第二步：打补丁（只需一次）

> **为什么要打补丁？**  
> 原版 SDK 只能同时显示 2 个图像面板。我们需要改 3 个文件，让它支持 10 个面板。

### 2.1 下载补丁文件

把以下 3 个文件下载到你的电脑（从 GitHub 仓库获取）：

```
ouster_example/python/src/ouster/sdk/viz/
├── view_mode.py   ← 新增 R/G/B 单通道提取 + 混光模式
├── model.py       ← 10 面板布局 + 通道顺序 + 标签
└── core.py        ← 键盘快捷键 + OSD + 循环播放
```

### 2.2 覆盖原文件

```bash
# 设置路径（替换为你的实际路径）
VIZ_DIR="/Users/你的用户名/.hermes/hermes-agent/venv/lib/python3.11/site-packages/ouster/sdk/viz"
PATCH_DIR="/path/to/ouster_example/python/src/ouster/sdk/viz"

# 备份原文件（以防万一）
mkdir -p ~/ouster-viz-backup
cp "$VIZ_DIR/view_mode.py" ~/ouster-viz-backup/
cp "$VIZ_DIR/model.py" ~/ouster-viz-backup/
cp "$VIZ_DIR/core.py" ~/ouster-viz-backup/

# 覆盖
cp "$PATCH_DIR/view_mode.py" "$VIZ_DIR/"
cp "$PATCH_DIR/model.py" "$VIZ_DIR/"
cp "$PATCH_DIR/core.py" "$VIZ_DIR/"

# 清除缓存（重要！）
find "$VIZ_DIR" -name "__pycache__" -exec rm -rf {} + 2>/dev/null

echo "✅ 补丁已安装"
```

### 2.3 验证安装

```bash
python3 -c "
from ouster.sdk.viz.view_mode import MixedLightMode, RedChannelMode
from ouster.sdk.viz.model import SensorModel
import inspect
assert '_num_images = 10' in inspect.getsource(SensorModel.__init__)
print('✅ 验证通过：10 面板补丁已生效')
"
```

---

## 第三步：播放数据（显示 10 个通道）

### 3.1 播放 OSF 文件

```bash
# 最简单的方式
ouster-cli source 你的数据文件.osf viz

# 指定播放速率（0.5 = 慢放，1.0 = 正常，2.0 = 快放）
ouster-cli source 你的数据文件.osf viz --rate 0.5
```

### 3.2 播放 PCAP 文件

```bash
ouster-cli source 你的数据文件.pcap viz
```

### 3.3 连接实况传感器

```bash
ouster-cli source 传感器IP地址 viz
```

### 3.4 Python 脚本方式

```python
from ouster.sdk.open_source import open_source
from ouster.sdk.viz.core import SimpleViz

src = open_source("你的数据文件.osf")
sv = SimpleViz(src.sensor_info[0], rate=0.5)
sv.run(src)
```

---

## 第四步：理解 10 个通道

启动后，你会看到 10 个面板从上到下排列：

| 面板 | 显示内容 | 说明 |
|:----:|---------|------|
| 0 | **NIR** | 近红外（Near Infrared）— 16-bit |
| 1 | **Signal** | 信号强度 — 16-bit |
| 2 | **CalRef** | 校准反射率（Calibrated Reflectivity）— 8-bit |
| 3 | **Range** | 深度距离 — 19-bit |
| 4 | **RGB** | 彩色图像 — 48-bit (16b×3) |
| 5 | **R** | 红色通道 — 从 RGB 拆出 |
| 6 | **G** | 绿色通道 — 从 RGB 拆出 |
| 7 | **B** | 蓝色通道 — 从 RGB 拆出 |
| 8 | **MIX_4** | (R+G+B+NIR) / 4 混光均值 |
| 9 | **MIX_5** | (R+G+B+NIR+SIG) / 5 混光均值 |

> **注意**：非 Rev8 传感器（没有 RGB 通道的）默认只显示前 5 个面板。

---

## 第五步：切换视图模式

### 5.1 只看前 5 个通道（NIR/Signal/CalRef/Range/RGB）

**按 `t` 键**

每按一次 `h`，循环切换：

```
全部 10 个 (0-9)  →  前 5 个 (0-4)  →  后 5 个 (5-9)  →  全部 10 个 (0-9)  → ...
```

屏幕右上角会显示通知：`Panels: ALL (0-9)` 或 `Panels: FIRST 5 (0-4)` 或 `Panels: LAST 5 (5-9)`

### 5.2 只看后 5 个通道（R/G/B/MIX_4/MIX_5）

按两次 `t` 键（第一次切到前 5，第二次切到后 5）

### 5.3 恢复全部 10 个

再按一次 `t` 键

---

## 第六步：切换每个面板的显示内容

每个面板都可以独立切换到任意可用通道：

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

**示例**：想让面板 0 显示 RANGE，按 `b` 多次直到看到 `0:RANGE`

---

## 第七步：其他常用操作

| 按键 | 功能 |
|------|------|
| `SPACE` | 暂停 / 继续播放 |
| `,` / `.` | 后退 / 前进 1 帧 |
| `<` / `>` | 降低 / 提高播放速率 |
| `I` | 放大图像面板 |
| `SHIFT+I` | 缩小图像面板 |
| `CTRL+I` | 切换：全部显示 → 单面板 → 翻转 |
| `O` | 隐藏/显示 OSD 文字信息 |
| `?` | 显示所有快捷键帮助 |
| `ESC` | 退出 |

---

## 第八步：恢复原版 SDK

如果想恢复到原始 SDK：

```bash
VIZ_DIR="/Users/你的用户名/.hermes/hermes-agent/venv/lib/python3.11/site-packages/ouster/sdk/viz"

cp ~/ouster-viz-backup/view_mode.py "$VIZ_DIR/"
cp ~/ouster-viz-backup/model.py "$VIZ_DIR/"
cp ~/ouster-viz-backup/core.py "$VIZ_DIR/"

# 清除缓存
find "$VIZ_DIR" -name "__pycache__" -exec rm -rf {} + 2>/dev/null

echo "✅ 已恢复原版 SDK"
```

---

## 常见问题

### Q: 只看到 5 个面板，不是 10 个？

**A**: 按 `t` 键切换到全部 10 个模式。

### Q: 面板 5-9 是黑的？

**A**: 你的传感器可能没有 RGB 通道。只有 OS-1-MAX-256-RGB 或 Rev8 传感器才有 R/G/B 通道。

### Q: 后 5 个面板和前 5 个一样？

**A**: 这说明补丁没有正确安装。重新执行第二步，确保：
1. 文件已覆盖到正确路径
2. `__pycache__` 已清除
3. 没有旧的 Python 进程在运行

### Q: SDK 升级后补丁失效了？

**A**: 重新执行第二步打补丁。每次 `pip install --upgrade ouster-sdk` 后都需要重新打补丁。

### Q: 想保存截图？

**A**: 按 `SHIFT+Z` 截图，按 `SHIFT+X` 开始/停止连续截图。

---

## 一键安装脚本

保存为 `install_10ch_patch.sh`，以后一键执行：

```bash
#!/bin/bash
# 一键安装 10 通道补丁
set -e

VIZ_DIR=$(python3 -c "import ouster.sdk.viz; import os; print(os.path.dirname(ouster.sdk.viz.__file__))")
PATCH_DIR="${1:-.}"  # 默认当前目录，或传入补丁目录路径

echo "SDK viz 目录: $VIZ_DIR"
echo "补丁目录: $PATCH_DIR"

# 备份
mkdir -p ~/ouster-viz-backup
for f in view_mode.py model.py core.py; do
    cp "$VIZ_DIR/$f" ~/ouster-viz-backup/
done

# 覆盖
for f in view_mode.py model.py core.py; do
    cp "$PATCH_DIR/$f" "$VIZ_DIR/"
done

# 清缓存
find "$VIZ_DIR" -name "__pycache__" -exec rm -rf {} + 2>/dev/null

# 验证
python3 -c "
from ouster.sdk.viz.model import SensorModel
import inspect
assert '_num_images = 10' in inspect.getsource(SensorModel.__init__)
print('✅ 10 通道补丁安装成功！')
"
```

使用方式：

```bash
chmod +x install_10ch_patch.sh
./install_10ch_patch.sh /path/to/ouster_example/python/src/ouster/sdk/viz
```
