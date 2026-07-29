# 🚀 Ouster 11-Channel Viz — 小白快速上手

---

## 第一步：确认环境

```bash
python3 --version          # 需要 3.11+
pip show ouster-sdk        # 确认已安装
```

## 第二步：打补丁（只需一次）

```bash
VIZ_DIR=$(python3 -c "import ouster.sdk.viz; import os; print(os.path.dirname(ouster.sdk.viz.__file__))")
PATCH_DIR="/path/to/ouster_example/python/src/ouster/sdk/viz"

# 备份
mkdir -p ~/ouster-viz-backup
cp "$VIZ_DIR"/{view_mode,model,core}.py ~/ouster-viz-backup/

# 覆盖
cp "$PATCH_DIR"/{view_mode,model,core}.py "$VIZ_DIR/"
find "$VIZ_DIR" -name "__pycache__" -exec rm -rf {} + 2>/dev/null

echo "✅ 补丁已安装"
```

## 第三步：播放

```bash
ouster-cli source 你的数据.osf viz
```

## 第四步：11 个通道

| 面板 | 显示 |
|:----:|------|
| 0 | NIR（近红外） |
| 1 | Signal（信号强度） |
| 2 | CalRef（校准反射率） |
| 3 | Range（深度） |
| 4 | RGB（彩色） |
| 5 | R（红） |
| 6 | G（绿） |
| 7 | B（蓝） |
| 8 | MIX_4 = (R+G+B+NIR)/4 |
| 9 | MIX_5 = (R+G+B+NIR+SIG)/5 |
| 10 | MIX_CALREF = (R+G+B+NIR+CalRef)/5 |

## 第五步：切换视图

**按 `T` 键**循环切换：
- 全部 11 个 (0-10)
- 前 5 个 (0-4)
- 后 5 个 (5-10)

## 第六步：切换单个面板

每个面板有独立快捷键（见 README 完整列表）

## 第七步：常用操作

| 按键 | 功能 |
|------|------|
| `SPACE` | 暂停/继续 |
| `T` | 切换 前5/后5/全部 |
| `I`/`SHIFT+I` | 放大/缩小 |
| `O` | 隐藏/显示文字 |
| `?` | 帮助 |
| `ESC` | 退出 |

## 恢复原版

```bash
cp ~/ouster-viz-backup/{view_mode,model,core}.py "$VIZ_DIR/"
find "$VIZ_DIR" -name "__pycache__" -exec rm -rf {} + 2>/dev/null
```

## 一键安装脚本

```bash
#!/bin/bash
set -e
VIZ_DIR=$(python3 -c "import ouster.sdk.viz; import os; print(os.path.dirname(ouster.sdk.viz.__file__))")
PATCH_DIR="${1:-.}"
mkdir -p ~/ouster-viz-backup
for f in view_mode.py model.py core.py; do
    cp "$VIZ_DIR/$f" ~/ouster-viz-backup/
    cp "$PATCH_DIR/$f" "$VIZ_DIR/"
done
find "$VIZ_DIR" -name "__pycache__" -exec rm -rf {} + 2>/dev/null
python3 -c "from ouster.sdk.viz.model import SensorModel; import inspect; assert '_num_images = 11' in inspect.getsource(SensorModel.__init__); print('✅ 11通道补丁安装成功')"
```
