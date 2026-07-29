# LESSONS_LEARNED.md — Ouster SDK 10-Channel Viz

> 沉淀自 2026-07-28 开发迭代，记录所有踩坑、根因与修复方案。

---

## 1. SDK 架构层踩坑

### 1.1 `_num_images = 2` 硬编码

**现象**：原版 SDK 只能同时显示 2 个图像面板。  
**根因**：`model.py:370` 的 `SensorModel.__init__` 中 `_num_images = 2` 硬编码。  
**修复**：改为 `_num_images = 10`。  
**教训**：所有 Image 对象在 `__init__` 中一次性创建，数量由 `_num_images` 决定。

### 1.2 `_use_default_view_modes` 只给前 2 个面板分配模式

**现象**：10 个面板都创建了，但面板 2-9 全是黑色。  
**根因**：`model.py:1054` 原代码 `for i in range(2)` 只给面板 0 和 1 设 `_image_mode_names`。  
**修复**：改为 `for i in range(self._max_images)` + preferred_order 优先分配。

### 1.3 `sorted_image_mode_names()` 的 `_known_fields` 过滤

**现象**：R/G/B/MIXED_LIGHT 模式已注册到 `_image_modes`，但 `preferred_order` 查找时找不到。  
**根因**：`sorted_image_mode_names()` 用 `& self._known_fields` 做交集过滤。`_known_fields` 来自 `frame.fields`，OSF 格式只有 `RGB` 合成字段，没有独立的 `R`/`G`/`B`。  
**修复**：`preferred_order` 查找改用 `all_mode_set = set(sensor._image_modes.keys())`，不依赖 `_known_fields`。  
**教训**：`_image_modes`（已注册模式）≠ `_known_fields`（frame 中发现的字段）。两者不能混用。

### 1.4 OSF 格式不暴露独立 R/G/B ChanField

**现象**：用户说 OSF 有独立 R/G/B 16-bit，但 `frame.fields` 只有 `RGB` (shape 256×2048×3, dtype float16)。  
**根因**：OSF v2.2.0 将 R/G/B 封装在 RGB 3 通道数组中，不作为独立 ChanField 暴露。  
**修复**：新增 `RGBChannelMode` 类，从 `RGB[:,:,0/1/2]` 提取单通道。`RedChannelMode`/`GreenChannelMode`/`BlueChannelMode` 继承自它。

---

## 2. 布局层踩坑

### 2.1 面板太窄看不见

**现象**：10 个面板创建了，但用户只看到 2 个。  
**根因**：OS-1-MAX-256-RGB 宽高比 = 2048/256 = 8:1。默认 `_img_size_fraction = 4` 时每个面板宽度只有屏幕的 1.25%。  
**修复**：改为 `_img_size_fraction = 12`。  
**教训**：高宽高比传感器（>4:1）需要更大的 `_img_size_fraction`。

### 2.2 10 面板竖排超出视口

**现象**：面板 5-9 在视口下方被裁剪。  
**根因**：竖排布局 `image_h * 10 > 2.0`（视口总高度）。  
**修复**：当 `n_imgs > 4` 时切换为全宽竖排（每面板占满视口宽度，`cell_h = 2.0 / n_imgs`）。

---

## 3. 键绑定踩坑

### 3.1 `H` 键被 SimpleViz 抢占

**现象**：按 `H` 键无反应，面板视图不切换。  
**根因**：`SimpleViz.__init__` 已绑定 `(ord('H'), 0) → adjust_subframes`。SimpleViz handler 在栈顶优先捕获按键，LidarFrameViz handler 永远收不到。  
**修复**：改用 `T` 键（`(ord('T'), 0)` 在两个 handler 中都未被占用）。  
**教训**：添加键绑定前必须检查 `SimpleViz` 和 `LidarFrameViz` 两层 handler 的冲突。GLFW key code 用大写字母（`ord('H')=72`）。

### 3.2 `cycle_panel_view_mode` 没有重新定位面板

**现象**：`_panel_view_mode` 值正确切换了（0→1→2→0），但面板位置不变。  
**根因**：`cycle_panel_view_mode` 只调了 `model.update()`（更新数据），没调 `update_image_size(0)`（重新定位）。  
**修复**：在 `cycle_panel_view_mode` 中加 `self.update_image_size(0)`。

---

## 4. 数据层踩坑

### 4.1 混光通道被 NIR 主导

**现象**：MIX_4/MIX_5 面板看起来和 NIR 面板几乎一样。  
**根因**：R/G/B 数值范围 ~[0, 46]（float16），NIR ~[0, 65535]（uint16），直接等权平均时 NIR 权重约 100 倍。  
**修复**：每个通道独立归一化到 [0, 1] 后再混合：
- R/G/B: `(x - min) / (max - min + 1e-6)`（min-max 归一化）
- NIR/SIG: `x / 65535.0`（uint16 最大值归一化）

### 4.2 Collator 返回空 `frame.fields`

**现象**：直接迭代 `src` 获得的 FrameSet 的 `fields` 为空列表。  
**根因**：OSF Collator 格式与直接 `frame.fields` 访问不同。  
**修复**：数据断言必须用 `lfv._model._frame_set[0]`（viz 运行时内部帧），不能用迭代器直接获得的 frame。

---

## 5. 检测逻辑踩坑

### 5.1 `"RGB" in sorted_set` 误判为 10 通道

**现象**：OS-1-MAX-256-RGB 只有 5 个可用模式（NIR/SIG/REF/RANGE/RGB），但被检测为"有 10 通道"，面板 5-9 回退到循环重复。  
**根因**：`"RGB" in sorted_set` 表示有合成 RGB，但不等于有独立 R/G/B。  
**修复**：三级检测：
- `has_native_rgb`：独立 R+G+B 存在 → 全部 10 面板
- `has_rgb_composite`：只有合成 RGB → 全部 10 面板（R/G/B 从 RGB 拆出）
- `has_no_rgb`：无彩色 → 只显示前 5 面板

---

## 6. Python/SDK 技术细节

| API | 用法 | 注意 |
|-----|------|------|
| `Label.set_text(str)` | 设置标签文字 | 不是 `.text = ` |
| `Label.set_position(x, y)` | 设置位置 | 不是 `.position = ` |
| `Label.set_rgba((r,g,b,a))` | 设置颜色 | **传元组**，不是4个参数 |
| `Label.set_scale(float)` | 设置大小 | |
| `SimpleViz(m, on_eof='loop')` | 循环播放 | 默认已改为 `'loop'` |
| `SimpleViz(m, rate=0.5)` | 指定速率 | 0.1/0.25/0.5/0.75/1.0/1.5/2.0/3.0 |
| `lfv._model._frame_set[0]` | 获取内部帧 | 用于数据断言，不能用迭代器 |
| `ChanField.R` | 字符串 `"R"` | OSF 中不是独立字段 |
| `ChanField.RGB` | 字符串 `"RGB"` | shape (H,W,3), dtype float16 |

---

## 7. 文件变更清单

| 文件 | 行数变更 | 核心改动 |
|------|:--------:|---------|
| `view_mode.py` | +102/-12 | `RGBChannelMode`/`RedChannelMode`/`GreenChannelMode`/`BlueChannelMode` + `MixedLightMode`/`MixedLightSigMode` 归一化 |
| `model.py` | +94/-18 | `_num_images=10` + preferred_order + all_mode_set + Rev8 检测 + 全宽布局 + panel labels + panel_view_mode |
| `core.py` | +11 | 10 面板键绑定 + `T` 键切换 + `cycle_panel_view_mode` 调 `update_image_size(0)` |
| `PRD.md` | 新建 | 功能需求文档 |
| `README.md` | 新建 | 使用指南（中文） |
| `QUICKSTART.md` | 新建 | 小白快速上手 |

---

## 8. 待办 / 后续优化

- [ ] 混光通道归一化改为可配置（min-max vs uint16 max vs percentile）
- [ ] 面板标签可见性调试（Label z-order 问题）
- [ ] CHANGELOG.rst 追加条目
- [ ] 支持用户自定义面板顺序（Python API）
- [ ] 支持 CLI 参数 `--num-images` 控制面板数
