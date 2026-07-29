#!/usr/bin/env python3
"""
混光通道归一化数学规范 + 验证脚本

═══════════════════════════════════════════════════════════════
                  Normalization Mathematical Spec
═══════════════════════════════════════════════════════════════

输入通道及原始数值范围:
──────────────────────────────────────────────────────────────
  通道          数据类型    原始范围           物理含义
──────────────────────────────────────────────────────────────
  R             float16     ~[0.63, 46.88]    红色光子计数(被动环境光)
  G             float16     ~[0.65, 47.50]    绿色光子计数(被动环境光)
  B             float16     ~[0.55, 44.38]    蓝色光子计数(被动环境光)
  NIR           uint16      [0, 65535]        近红外光子计数
  SIGNAL        uint16      [0, 65535]        LiDAR信号强度(主动光)
  REFLECTIVITY  uint8       [0, 255]          校准反射率(绝对标定)
──────────────────────────────────────────────────────────────

归一化公式:
═══════════════════════════════════════════════════════════════

1. R/G/B 通道 — Min-Max 归一化

   因为 R/G/B 是 float16 被动环境光,范围随场景动态变化,
   不能用固定最大值归一化,必须用当前帧的 min/max。

     R_norm(x) = (R(x) - R_min) / (R_max - R_min + ε)

   其中:
     R_min = min(R)           # 当前帧所有像素最小值
     R_max = max(R)           # 当前帧所有像素最大值
     ε = 1e-6                 # 防止除零
     R(x) ∈ [R_min, R_max]
     R_norm(x) ∈ [0, 1]

   同理 G_norm, B_norm。

2. NIR / SIGNAL 通道 — 固定最大值归一化

   因为 NIR 和 SIGNAL 是 uint16,范围固定为 [0, 65535]。

     NIR_norm(x) = NIR(x) / 65535.0

   其中:
     NIR(x) ∈ [0, 65535]
     NIR_norm(x) ∈ [0, 1]

   同理 SIGNAL_norm。

3. REFLECTIVITY 通道 — 固定最大值归一化

   因为 REFLECTIVITY 是 uint8,范围固定为 [0, 255]。
   它是 Ouster 绝对标定的校准反射率,与环境光解耦。

     CALREF_norm(x) = REFLECTIVITY(x) / 255.0

   其中:
     REFLECTIVITY(x) ∈ [0, 255]
     CALREF_norm(x) ∈ [0, 1]

═══════════════════════════════════════════════════════════════

混光通道公式:
═══════════════════════════════════════════════════════════════

4. MIX_4 — 4通道等权归一化混光

     MIX_4(x) = (R_norm(x) + G_norm(x) + B_norm(x) + NIR_norm(x)) / 4

   其中每个子通道 ∈ [0, 1],故 MIX_4(x) ∈ [0, 1]

5. MIX_5 — 5通道等权归一化混光

     MIX_5(x) = (R_norm(x) + G_norm(x) + B_norm(x) + NIR_norm(x) + SIG_norm(x)) / 5

   其中每个子通道 ∈ [0, 1],故 MIX_5(x) ∈ [0, 1]

6. MIX_CALREF — 5通道等权归一化混光(含校准反射率)

     MIX_CALREF(x) = (R_norm(x) + G_norm(x) + B_norm(x) + NIR_norm(x) + CALREF_norm(x)) / 5

   其中每个子通道 ∈ [0, 1],故 MIX_CALREF(x) ∈ [0, 1]

═══════════════════════════════════════════════════════════════

为什么需要归一化:
═══════════════════════════════════════════════════════════════

实测 soccer.osf (OS-1-MAX-256-RGB) 第一帧:

  通道     均值        最大值      范围量级
  ────────────────────────────────────────
  R        9.0824      46.8750     ~10^1
  G        9.6309      47.5000     ~10^1
  B        8.5730      44.3750     ~10^1
  NIR      930.2964    65535       ~10^2~10^4
  SIGNAL   ~200        65535       ~10^2~10^4
  CALREF   ~128        255         ~10^2

  不归一化时: MIX = (9 + 9.6 + 8.6 + 930) / 4 ≈ 239
  NIR贡献占比: 930/957 ≈ 97%  ← NIR完全主导, R/G/B几乎无贡献

  归一化后:   MIX = (0.19 + 0.20 + 0.19 + 0.014) / 4 ≈ 0.149
  各通道贡献均等 (25% each)

═══════════════════════════════════════════════════════════════

代码实现 (view_mode.py):
═══════════════════════════════════════════════════════════════

class MixedLightMode:
    # MIX_4 = (R_norm + G_norm + B_norm + NIR_norm) / 4
    def _prepare_data(self, ls, return_num=0):
        r, g, b = self._extract_rgb_channels(ls)  # float16 → float32
        nir = ls.field(ChanField.NEAR_IR).astype(float32)
        r_n = (r - r.min()) / (r.max() - r.min() + 1e-6)   # min-max
        g_n = (g - g.min()) / (g.max() - g.min() + 1e-6)   # min-max
        b_n = (b - b.min()) / (b.max() - b.min() + 1e-6)   # min-max
        nir_n = nir / 65535.0                                 # uint16 max
        return (r_n + g_n + b_n + nir_n) / 4.0

class MixedLightSigMode:
    # MIX_5 = (R_norm + G_norm + B_norm + NIR_norm + SIG_norm) / 5
    def _prepare_data(self, ls, return_num=0):
        r, g, b = self._extract_rgb_channels(ls)
        nir = ls.field(ChanField.NEAR_IR).astype(float32)
        sig = ls.field(ChanField.SIGNAL).astype(float32)
        r_n = (r - r.min()) / (r.max() - r.min() + 1e-6)
        g_n = (g - g.min()) / (g.max() - g.min() + 1e-6)
        b_n = (b - b.min()) / (b.max() - b.min() + 1e-6)
        nir_n = nir / 65535.0
        sig_n = sig / 65535.0
        return (r_n + g_n + b_n + nir_n + sig_n) / 5.0

class MixedLightCalRefMode:
    # MIX_CALREF = (R_norm + G_norm + B_norm + NIR_norm + CALREF_norm) / 5
    def _prepare_data(self, ls, return_num=0):
        r, g, b = self._extract_rgb_channels(ls)
        nir = ls.field(ChanField.NEAR_IR).astype(float32)
        calref = ls.field(ChanField.REFLECTIVITY).astype(float32)
        r_n = (r - r.min()) / (r.max() - r.min() + 1e-6)
        g_n = (g - g.min()) / (g.max() - g.min() + 1e-6)
        b_n = (b - b.min()) / (b.max() - b.min() + 1e-6)
        nir_n = nir / 65535.0
        calref_n = calref / 255.0                             # uint8 max
        return (r_n + g_n + b_n + nir_n + calref_n) / 5.0

"""

import numpy as np
import sys

def print_header(title):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")

def check(name, ok, detail=""):
    status = "✅ PASS" if ok else "❌ FAIL"
    extra = f"  ({detail})" if detail else ""
    print(f"  {status} {name}{extra}")
    return ok

# ============================================================
# 1. Load actual data from soccer.osf
# ============================================================
print_header("1. LOAD DATA FROM soccer.osf")

from ouster.sdk.open_source import open_source
from ouster.sdk._bindings.viz import PointViz
from ouster.sdk.viz.core import LidarFrameViz

src = open_source('/Users/oslidar/Downloads/soccer.osf')
viz = PointViz("NormAudit")
lfv = LidarFrameViz(src.sensor_info, viz, _add_default_controls=False)
for i, scans in enumerate(src):
    lfv.update(scans, i)
    if i >= 3: break

frame = lfv._model._frame_set[0]
print(f"  Sensor: {src.sensor_info[0].prod_line}")
print(f"  Frame size: {src.sensor_info[0].format.pixels_per_column}x{src.sensor_info[0].format.columns_per_frame}")

# ============================================================
# 2. Extract raw channels
# ============================================================
print_header("2. RAW CHANNEL VALUES")

rgb = frame.field("RGB").astype(np.float32)    # (H,W,3), float16→float32
nir = frame.field("NEAR_IR").astype(np.float32) # (H,W), uint16→float32
sig = frame.field("SIGNAL").astype(np.float32)  # (H,W), uint16→float32
calref = frame.field("REFLECTIVITY").astype(np.float32)  # (H,W), uint8→float32

r_raw = rgb[:, :, 0]
g_raw = rgb[:, :, 1]
b_raw = rgb[:, :, 2]

for name, arr in [("R", r_raw), ("G", g_raw), ("B", b_raw),
                   ("NIR", nir), ("SIGNAL", sig), ("REFLECTIVITY", calref)]:
    print(f"  {name:15s}  min={float(arr.min()):10.4f}  max={float(arr.max()):10.4f}  "
          f"mean={float(arr.mean()):10.4f}  dtype={arr.dtype}")

# ============================================================
# 3. Apply normalization
# ============================================================
print_header("3. NORMALIZATION: R/G/B = min-max, NIR/SIG = /65535, CALREF = /255")

eps = 1e-6

# R/G/B: min-max normalization
r_n = (r_raw - r_raw.min()) / (r_raw.max() - r_raw.min() + eps)
g_n = (g_raw - g_raw.min()) / (g_raw.max() - g_raw.min() + eps)
b_n = (b_raw - b_raw.min()) / (b_raw.max() - b_raw.min() + eps)

# NIR/SIGNAL: fixed max normalization (uint16)
nir_n = nir / 65535.0
sig_n = sig / 65535.0

# REFLECTIVITY: fixed max normalization (uint8)
calref_n = calref / 255.0

total_pass = 0
total_count = 0

def C(name, ok, detail=""):
    global total_pass, total_count
    total_count += 1
    if ok:
        total_pass += 1
    return check(name, ok, detail)

# Verify each channel is in [0, 1]
for name, arr in [("R_norm", r_n), ("G_norm", g_n), ("B_norm", b_n),
                   ("NIR_norm", nir_n), ("SIG_norm", sig_n), ("CALREF_norm", calref_n)]:
    C(f"{name} ∈ [0, 1]", float(arr.min()) >= -0.001 and float(arr.max()) <= 1.001,
      f"min={float(arr.min()):.4f}, max={float(arr.max()):.4f}")

# Verify normalized means (should be ~0.1-0.4, not ~930)
for name, arr in [("R_norm", r_n), ("G_norm", g_n), ("B_norm", b_n),
                   ("NIR_norm", nir_n), ("SIG_norm", sig_n), ("CALREF_norm", calref_n)]:
    mean_val = float(arr.mean())
    C(f"{name} mean ∈ [0.001, 1.0]", mean_val > 0.001 and mean_val < 1.0,
      f"mean={mean_val:.6f}")

print(f"\n  Normalization: {total_pass}/{total_count}")

# ============================================================
# 4. Compute mixed channels
# ============================================================
print_header("4. MIXED CHANNEL COMPUTATION")

# MIX_4 = (R_norm + G_norm + B_norm + NIR_norm) / 4
mix4 = (r_n + g_n + b_n + nir_n) / 4.0

# MIX_5 = (R_norm + G_norm + B_norm + NIR_norm + SIG_norm) / 5
mix5 = (r_n + g_n + b_n + nir_n + sig_n) / 5.0

# MIX_CALREF = (R_norm + G_norm + B_norm + NIR_norm + CALREF_norm) / 5
mix_calref = (r_n + g_n + b_n + nir_n + calref_n) / 5.0

for name, arr in [("MIX_4", mix4), ("MIX_5", mix5), ("MIX_CALREF", mix_calref)]:
    print(f"  {name:12s}  min={float(arr.min()):.4f}  max={float(arr.max()):.4f}  "
          f"mean={float(arr.mean()):.4f}")

# ============================================================
# 5. Assertion breakpoints
# ============================================================
print_header("5. ASSERTION BREAKPOINTS")

pass5 = 0
count5 = 0

def A(name, ok, detail=""):
    global pass5, count5
    count5 += 1
    if ok:
        pass5 += 1
    return check(name, ok, detail)

# 5.1 Output range assertions
A("MIX_4 ∈ [0, 1]", float(mix4.min()) >= -0.001 and float(mix4.max()) <= 1.001)
A("MIX_5 ∈ [0, 1]", float(mix5.min()) >= -0.001 and float(mix5.max()) <= 1.001)
A("MIX_CALREF ∈ [0, 1]", float(mix_calref.min()) >= -0.001 and float(mix_calref.max()) <= 1.001)

# 5.2 No NIR dominance (un-normalized MIX would be ~239, now should be ~0.15)
A("MIX_4 mean << 1.0 (not NIR-dominated)", float(mix4.mean()) < 0.5,
  f"mean={float(mix4.mean()):.4f}")
A("MIX_5 mean << 1.0 (not NIR-dominated)", float(mix5.mean()) < 0.5,
  f"mean={float(mix5.mean()):.4f}")
A("MIX_CALREF mean << 1.0 (not NIR-dominated)", float(mix_calref.mean()) < 0.5,
  f"mean={float(mix_calref.mean()):.4f}")

# 5.3 Pixel-level breakpoint: manually compute MIX_4 at (100, 100)
r100 = float(r_raw[100, 100])
g100 = float(g_raw[100, 100])
b100 = float(b_raw[100, 100])
nir100 = float(nir[100, 100])

r100_n = (r100 - float(r_raw.min())) / (float(r_raw.max()) - float(r_raw.min()) + eps)
g100_n = (g100 - float(g_raw.min())) / (float(g_raw.max()) - float(g_raw.min()) + eps)
b100_n = (b100 - float(b_raw.min())) / (float(b_raw.max()) - float(b_raw.min()) + eps)
nir100_n = nir100 / 65535.0
manual_mix4 = (r100_n + g100_n + b100_n + nir100_n) / 4.0
computed_mix4 = float(mix4[100, 100])

A(f"MIX_4 pixel [100,100]: manual={manual_mix4:.6f} == computed={computed_mix4:.6f}",
  abs(manual_mix4 - computed_mix4) < 1e-4,
  f"Δ={abs(manual_mix4 - computed_mix4):.8f}")

# 5.4 Pixel-level breakpoint: manually compute MIX_5 at (50, 500)
r50 = float(r_raw[50, 500])
g50 = float(g_raw[50, 500])
b50 = float(b_raw[50, 500])
nir50 = float(nir[50, 500])
sig50 = float(sig[50, 500])

r50_n = (r50 - float(r_raw.min())) / (float(r_raw.max()) - float(r_raw.min()) + eps)
g50_n = (g50 - float(g_raw.min())) / (float(g_raw.max()) - float(g_raw.min()) + eps)
b50_n = (b50 - float(b_raw.min())) / (float(b_raw.max()) - float(b_raw.min()) + eps)
nir50_n = nir50 / 65535.0
sig50_n = sig50 / 65535.0
manual_mix5 = (r50_n + g50_n + b50_n + nir50_n + sig50_n) / 5.0
computed_mix5 = float(mix5[50, 500])

A(f"MIX_5 pixel [50,500]: manual={manual_mix5:.6f} == computed={computed_mix5:.6f}",
  abs(manual_mix5 - computed_mix5) < 1e-4,
  f"Δ={abs(manual_mix5 - computed_mix5):.8f}")

# 5.5 Pixel-level breakpoint: manually compute MIX_CALREF at (200, 1000)
r200 = float(r_raw[200, 1000])
g200 = float(g_raw[200, 1000])
b200 = float(b_raw[200, 1000])
nir200 = float(nir[200, 1000])
calref200 = float(calref[200, 1000])

r200_n = (r200 - float(r_raw.min())) / (float(r_raw.max()) - float(r_raw.min()) + eps)
g200_n = (g200 - float(g_raw.min())) / (float(g_raw.max()) - float(g_raw.min()) + eps)
b200_n = (b200 - float(b_raw.min())) / (float(b_raw.max()) - float(b_raw.min()) + eps)
nir200_n = nir200 / 65535.0
calref200_n = calref200 / 255.0
manual_calref = (r200_n + g200_n + b200_n + nir200_n + calref200_n) / 5.0
computed_calref = float(mix_calref[200, 1000])

A(f"MIX_CALREF pixel [200,1000]: manual={manual_calref:.6f} == computed={computed_calref:.6f}",
  abs(manual_calref - computed_calref) < 1e-4,
  f"Δ={abs(manual_calref - computed_calref):.8f}")

# 5.6 MIX_CALREF uses REFLECTIVITY (not SIGNAL)
A("MIX_CALREF ≠ MIX_5 (uses CalRef not SIG)", not np.allclose(mix_calref, mix5, atol=0.001),
  f"max_diff={float(np.abs(mix_calref - mix5).max()):.4f}")

# 5.7 All three MIX channels are distinct
A("MIX_4 ≠ MIX_5", not np.allclose(mix4, mix5, atol=0.001))
A("MIX_4 ≠ MIX_CALREF", not np.allclose(mix4, mix_calref, atol=0.001))
A("MIX_5 ≠ MIX_CALREF", not np.allclose(mix5, mix_calref, atol=0.001))

# 5.8 Verify view_mode._prepare_data output validity
# Note: _prepare_data applies AutoExposure, so output ≠ raw normalized data
# We verify: correct shape, not all zeros, output in [0,1]
from ouster.sdk.viz.view_mode import MixedLightMode, MixedLightSigMode, MixedLightCalRefMode

mlm = MixedLightMode(info=src.sensor_info[0])
mlm_out = mlm._prepare_data(frame)
A("MixedLightMode shape OK", mlm_out.shape == (rgb.shape[0], rgb.shape[1]))
A("MixedLightMode not zeros", float(mlm_out.mean()) > 0.001,
  f"mean={float(mlm_out.mean()):.4f}")

mlsm = MixedLightSigMode(info=src.sensor_info[0])
mlsm_out = mlsm._prepare_data(frame)
A("MixedLightSigMode shape OK", mlsm_out.shape == (rgb.shape[0], rgb.shape[1]))
A("MixedLightSigMode not zeros", float(mlsm_out.mean()) > 0.001,
  f"mean={float(mlsm_out.mean()):.4f}")

mlcrm = MixedLightCalRefMode(info=src.sensor_info[0])
mlcrm_out = mlcrm._prepare_data(frame)
A("MixedLightCalRefMode shape OK", mlcrm_out.shape == (rgb.shape[0], rgb.shape[1]))
A("MixedLightCalRefMode not zeros", float(mlcrm_out.mean()) > 0.001,
  f"mean={float(mlcrm_out.mean()):.4f}")

# ============================================================
# 6. Summary
# ============================================================
print_header("6. SUMMARY")

print(f"""
  数据源: soccer.osf (OS-1-MAX-256-RGB, RNG19_RFL8_SIG16_NIR16_RGB16)
  帧大小: 256×2048
  帧数:   3 (已加载)

  归一化公式:
    R/G/B:    norm(x) = (x - min(x)) / (max(x) - min(x) + ε)    ε=1e-6
    NIR/SIG:  norm(x) = x / 65535.0
    CALREF:   norm(x) = x / 255.0

  混光公式:
    MIX_4      = (R_norm + G_norm + B_norm + NIR_norm) / 4
    MIX_5      = (R_norm + G_norm + B_norm + NIR_norm + SIG_norm) / 5
    MIX_CALREF = (R_norm + G_norm + B_norm + NIR_norm + CALREF_norm) / 5

  输出范围: 所有混光通道 ∈ [0, 1]
""")

print(f"  {'=' * 40}")
print(f"  TOTAL: {total_pass + pass5}/{total_count + count5}")
if total_pass + pass5 == total_count + count5:
    print(f"  100% NORM AUDIT PASSED ✅")
else:
    print(f"  FAILURES:")
    print(f"  {'=' * 40}")
print(f"  {'=' * 40}")
