from typing import (List, Optional, Union, Protocol, runtime_checkable, Tuple)

from dataclasses import dataclass
import numpy as np
from ouster.sdk import core
from ouster.sdk.core import (Version, AutoExposure, BeamUniformityCorrector,
                             LocalToneMapper)

from ouster.sdk._bindings.viz import Cloud, Image


@runtime_checkable
class FieldViewMode(Protocol):
    """LidarFrame field processor

    View modes define the process of getting the key data for
    the frame and return number as well as checks the possibility
    of showing data in that mode, see `enabled()`.
    """

    _info: Optional[core.SensorInfo]

    @property
    def name(self) -> str:
        """Name of the view mode"""
        ...

    @property
    def names(self) -> List[str]:
        """Name of the view mode per return number"""
        ...

    def _prepare_data(self,
                      ls: core.LidarFrame,
                      return_num: int = 0) -> Optional[np.ndarray]:
        """Prepares data for visualization given the frame and return number"""
        ...

    def enabled(self, ls: core.LidarFrame, return_num: int = 0) -> bool:
        """Checks the view mode availability for a frame and return number"""
        ...


@runtime_checkable
class ImageMode(FieldViewMode, Protocol):
    """Applies the view mode key to the viz.Image"""

    def set_image(self,
                  img: Image,
                  ls: core.LidarFrame,
                  return_num: int = 0) -> None:
        """Prepares the key data and sets the image key to it."""
        ...


@runtime_checkable
class CloudMode(FieldViewMode, Protocol):
    """Applies the view mode key to the viz.Cloud"""

    def set_cloud_color(self,
                        cloud: Cloud,
                        ls: core.LidarFrame,
                        *,
                        return_num: int = 0) -> None:
        """Prepares the key data and sets the cloud key to it."""
        ...


class ImageCloudMode(ImageMode, CloudMode, Protocol):
    """Applies the view mode to viz.Cloud and viz.Image"""
    pass


def _second_chan_field(field: str) -> Optional[str]:
    """Get the second return field name."""
    # yapf: disable
    second_fields = dict({
        core.ChanField.RANGE: core.ChanField.RANGE2,
        core.ChanField.SIGNAL: core.ChanField.SIGNAL2,
        core.ChanField.REFLECTIVITY: core.ChanField.REFLECTIVITY2,
        core.ChanField.FLAGS: core.ChanField.FLAGS2,
        core.ChanField.NORMALS: core.ChanField.NORMALS2,
        core.ChanField.GROUND: core.ChanField.GROUND2
    })
    # yapf: enable
    return second_fields.get(field, None)


class RingMode(CloudMode):
    """View mode to show laser ring."""

    def __init__(self, info: core.SensorInfo) -> None:
        """
        Args:
            info: sensor metadata
        """
        self._info = info
        self._key_data: Optional[np.ndarray] = None

    @property
    def name(self) -> str:
        return "RING"

    @property
    def names(self) -> List[str]:
        return ["RING"]

    def _prepare_data(self,
                      ls: core.LidarFrame,
                      return_num: int = 0) -> Optional[np.ndarray]:
        if self._key_data is None:
            key_data = np.empty((self._info.h, self._info.w), dtype=np.uint8)
            for i in range(0, self._info.h):
                key_data[i, :] = int((i / self._info.h) * 255.0)
            self._key_data = key_data
        return self._key_data

    def set_cloud_color(self,
                        cloud: Cloud,
                        ls: core.LidarFrame,
                        return_num: int = 0) -> None:
        self._prepare_data(ls, return_num)
        assert self._key_data is not None
        cloud.set_key(self._key_data)

    def enabled(self, ls: core.LidarFrame, return_num: int = 0):
        return True


class SensorMode(CloudMode):
    """View mode to show sensor index."""

    def __init__(self, info: core.SensorInfo, color: Tuple[int, int, int]) -> None:
        """
        Args:
            info: sensor metadata
        """
        self._info = info
        self._color = color
        self._key_data: Optional[np.ndarray] = None

    @property
    def name(self) -> str:
        return "SENSOR"

    @property
    def names(self) -> List[str]:
        return ["SENSOR"]

    def _prepare_data(self,
                      ls: core.LidarFrame,
                      return_num: int = 0) -> Optional[np.ndarray]:
        if self._key_data is None:
            self._key_data = np.empty((self._info.h, self._info.w, 3), dtype=np.uint8)
            self._key_data[:] = self._color
        return self._key_data

    def set_cloud_color(self,
                        cloud: Cloud,
                        ls: core.LidarFrame,
                        return_num: int = 0) -> None:
        self._prepare_data(ls, return_num)
        assert self._key_data is not None
        cloud.set_key(self._key_data)

    def enabled(self, ls: core.LidarFrame, return_num: int = 0):
        return True


class TimestampMode(CloudMode):
    """View mode to show column timestamp."""

    def __init__(self, info: core.SensorInfo) -> None:
        """
        Args:
            info: sensor metadata
        """
        self._info = info

    @property
    def name(self) -> str:
        return "TIMESTAMP"

    @property
    def names(self) -> List[str]:
        return ["TIMESTAMP"]

    def _prepare_data(self,
                      ls: core.LidarFrame,
                      return_num: int = 0) -> Optional[np.ndarray]:
        nonzero = np.nonzero(ls.status)
        min = np.min(ls.timestamp[nonzero])
        timestamps = (ls.timestamp - min).astype(np.float32, copy=True)
        delta = np.max(ls.timestamp) - min
        # handle case when all points have same value to avoid divide by zero
        if delta <= 0:
            delta = 1.0
        timestamps /= delta
        key_data = np.tile(timestamps, (ls.h, 1))
        return key_data

    def set_cloud_color(self,
                        cloud: Cloud,
                        ls: core.LidarFrame,
                        return_num: int = 0) -> None:
        key_data = self._prepare_data(ls, return_num)
        if key_data is not None:
            cloud.set_key(key_data)

    def enabled(self, ls: core.LidarFrame, return_num: int = 0):
        return True


class SimpleMode(ImageCloudMode):
    """Basic view mode with AutoExposure and BeamUniformityCorrector

    Handles single and dual returns frames.

    When AutoExposure is enabled its state updates only for return_num=0 but
    applies for both returns.
    """

    def __init__(self,
                 field: str,
                 *,
                 info: Optional[core.SensorInfo] = None,
                 prefix: Optional[str] = "",
                 suffix: Optional[str] = "",
                 use_ae: bool = True,
                 use_buc: bool = False,
                 scale: Optional[float] = None) -> None:
        """
        Args:
            info: sensor metadata used mainly for destaggering here
            field: name of field to process, second return is handled automatically
            prefix: name prefix
            suffix: name suffix
            use_ae: if True, use AutoExposure for the field
            use_buc: if True, use BeamUniformityCorrector for the field
            scale: if use_ae is false and this is set, use this to scale the values for display
        """
        self._info = info
        self._fields = [field]
        field2 = _second_chan_field(field)
        if field2:
            self._fields.append(field2)
        self._ae = AutoExposure() if use_ae else None
        self._buc = BeamUniformityCorrector() if use_buc else None
        self._prefix = f"{prefix}: " if prefix else ""
        self._suffix = f" ({suffix})" if suffix else ""
        self._wrap_name = lambda n: f"{self._prefix}{n}{self._suffix}"
        self._scale = scale

    @property
    def name(self) -> str:
        return self._wrap_name(str(self._fields[0]))

    @property
    def names(self) -> List[str]:
        return [self._wrap_name(str(f)) for f in self._fields]

    def _prepare_data(self,
                      ls: core.LidarFrame,
                      return_num: int = 0) -> Optional[np.ndarray]:
        if not self.enabled(ls, return_num):
            return None

        f = self._fields[return_num]
        field = ls.field(f)
        key_data = field.astype(np.float32, copy=True)

        if self._buc:
            self._buc.update(key_data)

        if self._ae:
            self._ae.update(key_data, update_state=(return_num == 0))
        elif self._scale is not None:
            key_data *= self._scale
        else:
            key_max = np.max(key_data)
            if key_max:
                key_data = key_data / key_max

        return key_data

    def set_image(self,
                  img: Image,
                  ls: core.LidarFrame,
                  return_num: int = 0) -> None:
        if self._info is None:
            raise ValueError(
                f"VizMode[{self.name}] requires metadata to make a 2D image")
        key_data = self._prepare_data(ls, return_num)
        if key_data is not None:
            img.set_image(core.destagger(self._info, key_data))

    def set_cloud_color(self,
                        cloud: Cloud,
                        ls: core.LidarFrame,
                        return_num: int = 0) -> None:
        key_data = self._prepare_data(ls, return_num)
        if key_data is not None:
            cloud.set_key(key_data)

    def enabled(self, ls: core.LidarFrame, return_num: int = 0):
        return (self._fields[return_num] in ls.fields
                if return_num < len(self._fields) else False)


class RGBMode(ImageCloudMode):
    """RGB view mode"""

    def __init__(self,
                 field: str,
                 *,
                 info: Optional[core.SensorInfo] = None) -> None:
        """
        Args:
            info: sensor metadata used mainly for destaggering here
            field: channel field to process
        """
        self._info = info
        self._field = field

    @property
    def name(self) -> str:
        return self._field

    @property
    def names(self) -> List[str]:
        return [self._field]

    def _prepare_data(self,
                      ls: core.LidarFrame,
                      return_num: int = 0) -> Optional[np.ndarray]:

        field = ls.field(self._field)
        if np.ndim(field) != 3 and field.shape != 3:
            raise TypeError(f"Unsupport field shape: {field.shape}")
        if field.dtype == np.uint8:
            return field
        elif field.dtype == np.uint16:
            return (field >> 8).astype(np.uint8)
        elif field.dtype == np.float32:
            key_data = field
        elif field.dtype == np.float64:
            key_data = field.astype(np.float32, copy=True)
        else:
            raise TypeError(f"Unsupport field type {field.dtype}")

        return key_data.clip(0, 1.0)

    def set_image(self,
                  img: Image,
                  ls: core.LidarFrame,
                  return_num: int = 0) -> None:
        if self._info is None:
            raise ValueError(
                f"VizMode[{self.name}] requires metadata to make a 2D image")
        key_data = self._prepare_data(ls)
        if key_data is not None:
            img.set_image(core.destagger(self._info, key_data))

    def set_cloud_color(self,
                        cloud: Cloud,
                        ls: core.LidarFrame,
                        return_num: int = 0) -> None:
        key_data = self._prepare_data(ls)
        if key_data is not None:
            cloud.set_key(key_data)

    def enabled(self, ls: core.LidarFrame, return_num: int = 0):
        field = ls.field(self._field)
        return np.ndim(field) == 3


class HDRRGBMode(ImageCloudMode):
    """RGB view mode using LocalToneMapper."""

    def __init__(self,
                 field: str,
                 info: core.SensorInfo) -> None:
        self._info = info
        self._field = field
        self._tonemapper = LocalToneMapper()
        self._last_frame: Optional[core.LidarFrame] = None
        self._last_data: Optional[np.ndarray] = None

    @property
    def name(self) -> str:
        return self._field

    @property
    def names(self) -> List[str]:
        return [self._field]

    def _prepare_data(self,
                      ls: core.LidarFrame,
                      return_num: int = 0) -> Optional[np.ndarray]:
        if not self.enabled(ls, return_num):
            return None
        if ls is self._last_frame:
            return self._last_data
        self._last_frame = ls

        field = ls.field(self._field)
        if field.dtype != np.float16:
            raise TypeError(f"Unsupported field type: {field.dtype}")

        f16_destag = core.destagger(self._info, field)
        sdr_destag = self._tonemapper.update(f16_destag)
        sdr_data = core.stagger(self._info, sdr_destag)
        self._last_data = sdr_data
        self._last_destag_data = sdr_destag
        return sdr_data

    def set_image(self,
                  img: Image,
                  ls: core.LidarFrame,
                  return_num: int = 0) -> None:
        if self._info is None:
            raise ValueError(
                f"VizMode[{self.name}] requires metadata to make a 2D image")
        key_data = self._prepare_data(ls, return_num)
        if key_data is not None:
            img.set_image(self._last_destag_data)

    def set_cloud_color(self,
                        cloud: Cloud,
                        ls: core.LidarFrame,
                        return_num: int = 0) -> None:
        key_data = self._prepare_data(ls, return_num)
        if key_data is not None:
            cloud.set_key(key_data)

    def enabled(self, ls: core.LidarFrame, return_num: int = 0) -> bool:
        field = ls.field(self._field)
        return np.ndim(field) == 3 and field.shape[2] == 3


class NormalsMode(ImageCloudMode):
    """Normals value remap [-1, 1] -> [0, 1]"""

    def __init__(self,
                 field: str,
                 *,
                 info: Optional[core.SensorInfo] = None) -> None:
        self._info = info
        self._fields = [field]
        field2 = _second_chan_field(field)
        if field2:
            self._fields.append(field2)

    @property
    def name(self) -> str:
        return str(self._fields[0])

    @property
    def names(self) -> List[str]:
        return [str(field) for field in self._fields]

    def _prepare_data(self,
                      ls: core.LidarFrame,
                      return_num: int = 0) -> Optional[np.ndarray]:
        if not self.enabled(ls, return_num):
            return None

        field = self._fields[return_num]
        data = ls.field(field)
        if np.ndim(data) != 3 or data.shape[-1] != 3:
            raise TypeError(f"Unsupported normal field shape: {data.shape}")
        key_data = np.asarray(data, dtype=np.float32)
        zero_mask = np.all(key_data == 0.0, axis=-1)
        np.clip(key_data, -1.0, 1.0, out=key_data)
        key_data = 0.5 * (key_data + 1.0)
        if np.any(zero_mask):
            key_data[zero_mask] = 0.0
        return key_data

    def set_image(self,
                  img: Image,
                  ls: core.LidarFrame,
                  return_num: int = 0) -> None:
        if self._info is None:
            raise ValueError(
                f"VizMode[{self.name}] requires metadata to make a 2D image")
        key_data = self._prepare_data(ls, return_num)
        if key_data is not None:
            img.set_image(core.destagger(self._info, key_data))

    def set_cloud_color(self,
                        cloud: Cloud,
                        ls: core.LidarFrame,
                        return_num: int = 0) -> None:
        key_data = self._prepare_data(ls, return_num)
        if key_data is not None:
            cloud.set_key(key_data)

    def enabled(self, ls: core.LidarFrame, return_num: int = 0):
        if return_num >= len(self._fields):
            return False

        field = self._fields[return_num]
        if field not in ls.fields:
            return False

        data = ls.field(field)
        return np.ndim(data) == 3 and data.shape[-1] == 3


class ReflMode(SimpleMode, ImageCloudMode):
    """Prepares image/cloud data for REFLECTIVITY channel"""

    def __init__(self, *, info: Optional[core.SensorInfo] = None) -> None:
        super().__init__(core.ChanField.REFLECTIVITY, info=info, use_ae=True)
        # used only for uncalibrated reflectivity in FW prior v2.1.0
        # TODO: should we check for calibrated reflectivity status from
        # metadata too?
        if self._info is not None:
            self._normalized_refl = (self._info.get_version() >=
                                     Version.from_string("v2.1.0"))
        else:
            # NOTE/TODO[pb]: ReflMode added through viz extra mode mechanism
            # may not have a correct normalized_refl set ... need a refactor.
            self._normalized_refl = True

    def _prepare_data(self,
                      ls: core.LidarFrame,
                      return_num: int = 0) -> Optional[np.ndarray]:
        if not self.enabled(ls, return_num):
            return None

        f = self._fields[return_num]
        refl_data = ls.field(f).astype(np.float32, copy=True)
        if self._normalized_refl:
            refl_data /= 255.0
        else:
            # mypy doesn't recognize that we always should have _ae here
            # so we have explicit check
            if self._ae:
                self._ae.update(refl_data, update_state=(return_num == 0))
        return refl_data


class MixedLightMode(SimpleMode):
    """Mixed light mode: average of R, G, B, NIR channels (4-channel composite).

    Works with both:
    - Separate R/G/B fields (native Rev8)
    - Combined RGB 3-channel field (OSF format)
    """

    def __init__(self, *, info: Optional[core.SensorInfo] = None) -> None:
        super().__init__("MIXED_LIGHT", info=info, use_ae=True, use_buc=False)

    def _extract_rgb_channels(self, ls):
        """Extract R, G, B arrays from available fields."""
        rgb = ls.field("RGB").astype(np.float32)
        return rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]

    def _prepare_data(self,
                      ls: core.LidarFrame,
                      return_num: int = 0) -> Optional[np.ndarray]:
        if not self.enabled(ls, return_num):
            return None
        nir = ls.field(core.ChanField.NEAR_IR).astype(np.float32)
        r, g, b = self._extract_rgb_channels(ls)
        # Normalize each channel to [0,1] before mixing
        # R/G/B range ~[0,46], NIR range ~[0,65535] — without normalization NIR dominates
        r_n = (r - r.min()) / (r.max() - r.min() + 1e-6)
        g_n = (g - g.min()) / (g.max() - g.min() + 1e-6)
        b_n = (b - b.min()) / (b.max() - b.min() + 1e-6)
        nir_n = nir / 65535.0
        key_data = (r_n + g_n + b_n + nir_n) / 4.0
        if self._buc:
            self._buc.update(key_data)
        if self._ae:
            self._ae.update(key_data, update_state=(return_num == 0))
        return key_data

    def enabled(self, ls: core.LidarFrame, return_num: int = 0) -> bool:
        # Work with either separate R/G/B or combined RGB
        has_separate = (ls.has_field(core.ChanField.R) and
                        ls.has_field(core.ChanField.G) and
                        ls.has_field(core.ChanField.B))
        has_composite = ls.has_field("RGB")
        return (has_separate or has_composite) and ls.has_field(core.ChanField.NEAR_IR)


class MixedLightSigMode(SimpleMode):
    """Mixed light + signal mode: average of R, G, B, NIR, SIGNAL channels (5-channel composite).

    Works with both:
    - Separate R/G/B fields (native Rev8)
    - Combined RGB 3-channel field (OSF format)
    """

    def __init__(self, *, info: Optional[core.SensorInfo] = None) -> None:
        super().__init__("MIXED_LIGHT_SIG", info=info, use_ae=True, use_buc=False)

    def _extract_rgb_channels(self, ls):
        """Extract R, G, B arrays from available fields."""
        rgb = ls.field("RGB").astype(np.float32)
        return rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]

    def _prepare_data(self,
                      ls: core.LidarFrame,
                      return_num: int = 0) -> Optional[np.ndarray]:
        if not self.enabled(ls, return_num):
            return None
        nir = ls.field(core.ChanField.NEAR_IR).astype(np.float32)
        sig = ls.field(core.ChanField.SIGNAL).astype(np.float32)
        r, g, b = self._extract_rgb_channels(ls)
        # Normalize each channel to [0,1] before mixing
        r_n = (r - r.min()) / (r.max() - r.min() + 1e-6)
        g_n = (g - g.min()) / (g.max() - g.min() + 1e-6)
        b_n = (b - b.min()) / (b.max() - b.min() + 1e-6)
        nir_n = nir / 65535.0
        sig_n = sig / 65535.0
        key_data = (r_n + g_n + b_n + nir_n + sig_n) / 5.0
        if self._buc:
            self._buc.update(key_data)
        if self._ae:
            self._ae.update(key_data, update_state=(return_num == 0))
        return key_data

    def enabled(self, ls: core.LidarFrame, return_num: int = 0) -> bool:
        has_separate = (ls.has_field(core.ChanField.R) and
                        ls.has_field(core.ChanField.G) and
                        ls.has_field(core.ChanField.B))
        has_composite = ls.has_field("RGB")
        return (has_separate or has_composite) and \
               ls.has_field(core.ChanField.NEAR_IR) and \
               ls.has_field(core.ChanField.SIGNAL)


class MixedLightCalRefMode(SimpleMode):
    """Mixed light + calibrated reflectivity: R+G+B+NIR+CalRef (5-channel normalized composite).

    Each channel independently normalized to [0,1] before mixing.
    CalRef (REFLECTIVITY) is already 8-bit calibrated, normalized to [0,1] via /255.
    """

    def __init__(self, *, info: Optional[core.SensorInfo] = None) -> None:
        super().__init__("MIXED_LIGHT_CALREF", info=info, use_ae=True, use_buc=False)

    def _extract_rgb_channels(self, ls):
        rgb = ls.field("RGB").astype(np.float32)
        return rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]

    def _prepare_data(self,
                      ls: core.LidarFrame,
                      return_num: int = 0) -> Optional[np.ndarray]:
        if not self.enabled(ls, return_num):
            return None
        nir = ls.field(core.ChanField.NEAR_IR).astype(np.float32)
        calref = ls.field(core.ChanField.REFLECTIVITY).astype(np.float32)
        r, g, b = self._extract_rgb_channels(ls)
        # Normalize each channel to [0,1]
        r_n = (r - r.min()) / (r.max() - r.min() + 1e-6)
        g_n = (g - g.min()) / (g.max() - g.min() + 1e-6)
        b_n = (b - b.min()) / (b.max() - b.min() + 1e-6)
        nir_n = nir / 65535.0
        calref_n = calref / 255.0
        key_data = (r_n + g_n + b_n + nir_n + calref_n) / 5.0
        if self._buc:
            self._buc.update(key_data)
        if self._ae:
            self._ae.update(key_data, update_state=(return_num == 0))
        return key_data

    def enabled(self, ls: core.LidarFrame, return_num: int = 0) -> bool:
        has_separate = (ls.has_field(core.ChanField.R) and
                        ls.has_field(core.ChanField.G) and
                        ls.has_field(core.ChanField.B))
        has_composite = ls.has_field("RGB")
        return (has_separate or has_composite) and \
               ls.has_field(core.ChanField.NEAR_IR) and \
               ls.has_field(core.ChanField.REFLECTIVITY)


class IMUWaveformMode(ImageCloudMode):
    """Oscilloscope-style rolling waveform of IMU accelerometer data."""
    _history = None  # class-level deque, initialized lazily
    _HISTORY_LEN = 128

    def __init__(self, *, info: Optional[core.SensorInfo] = None) -> None:
        self._info = info
        if IMUWaveformMode._history is None:
            from collections import deque
            IMUWaveformMode._history = deque(maxlen=self._HISTORY_LEN)

    @property
    def name(self) -> str:
        return "IMU_WAVEFORM"

    @property
    def names(self) -> List[str]:
        return ["IMU_WAVEFORM"]

    def _prepare_data(self,
                      ls: core.LidarFrame,
                      return_num: int = 0) -> Optional[np.ndarray]:
        if not self.enabled(ls, return_num):
            return None
        acc = ls.field("IMU_ACC").astype(np.float32)  # (256, 3)
        mean_xyz = acc.mean(axis=0)  # (3,)
        self._history.append(mean_xyz)

        H, W = 256, 2048
        img = np.zeros((H, W), dtype=np.float32)

        if len(self._history) < 2:
            return img

        data = np.array(self._history)  # (N, 3)
        n = len(data)

        # Auto-scale Y axis
        y_min = data.min() - 0.5
        y_max = data.max() + 0.5
        if y_max - y_min < 0.01:
            y_max = y_min + 1.0

        intensities = [0.6, 0.7, 0.8]  # R, G, B channel intensities
        for ch_idx, intensity in enumerate(intensities):
            vals = data[:, ch_idx]
            for i in range(n - 1):
                x0 = int((n - 1 - i) * (W - 1) / max(n - 1, 1))  # newest=left
                x1 = int((n - 2 - i) * (W - 1) / max(n - 1, 1))
                y0 = int((vals[i] - y_min) / (y_max - y_min) * (H - 1))
                y1 = int((vals[i + 1] - y_min) / (y_max - y_min) * (H - 1))
                y0 = max(0, min(H - 1, y0))
                y1 = max(0, min(H - 1, y1))
                # Draw line segment with linear interpolation
                steps = max(abs(x1 - x0), abs(y1 - y0)) + 1
                for s in range(steps):
                    t = s / max(steps - 1, 1)
                    x = int(x0 + t * (x1 - x0))
                    y = int(y0 + t * (y1 - y0))
                    x = max(0, min(W - 1, x))
                    y = max(0, min(H - 1, y))
                    img[y, x] = intensity

        # Draw center line (0 value)
        y_center = int((0 - y_min) / (y_max - y_min) * (H - 1))
        if 0 <= y_center < H:
            img[y_center, :] = 0.15  # dim center line

        return img

    def set_image(self,
                  img: Image,
                  ls: core.LidarFrame,
                  return_num: int = 0) -> None:
        key_data = self._prepare_data(ls, return_num)
        if key_data is not None:
            img.set_image(key_data)

    def set_cloud_color(self,
                        cloud: Cloud,
                        ls: core.LidarFrame,
                        *,
                        return_num: int = 0) -> None:
        pass

    def enabled(self, ls: core.LidarFrame, return_num: int = 0) -> bool:
        return ls.has_field("IMU_ACC")


class IMUCubeMode(ImageCloudMode):
    """3D wireframe cube that rotates based on IMU accelerometer orientation."""

    def __init__(self, *, info: Optional[core.SensorInfo] = None) -> None:
        self._info = info

    @property
    def name(self) -> str:
        return "IMU_CUBE"

    @property
    def names(self) -> List[str]:
        return ["IMU_CUBE"]

    def _prepare_data(self,
                      ls: core.LidarFrame,
                      return_num: int = 0) -> Optional[np.ndarray]:
        if not self.enabled(ls, return_num):
            return None
        acc = ls.field("IMU_ACC").astype(np.float32)  # (256, 3)
        mean_xyz = acc.mean(axis=0)  # (3,)

        ax, ay, az = mean_xyz
        # Compute pitch and roll from accelerometer
        pitch = np.arctan2(ax, np.sqrt(ay * ay + az * az))
        roll = np.arctan2(ay, az)

        H, W = 256, 2048
        img = np.zeros((H, W), dtype=np.float32)

        # Define 8 vertices of a unit cube centered at origin
        s = 0.8  # half-size
        vertices = np.array([
            [-s, -s, -s], [s, -s, -s], [s, s, -s], [-s, s, -s],
            [-s, -s, s],  [s, -s, s],  [s, s, s],  [-s, s, s],
        ], dtype=np.float32)

        # Rotation matrices
        cos_p, sin_p = np.cos(pitch), np.sin(pitch)
        cos_r, sin_r = np.cos(roll), np.sin(roll)

        # Rotate by pitch around Y axis, then roll around X axis
        Ry = np.array([
            [cos_p, 0, sin_p],
            [0, 1, 0],
            [-sin_p, 0, cos_p],
        ], dtype=np.float32)
        Rx = np.array([
            [1, 0, 0],
            [0, cos_r, -sin_r],
            [0, sin_r, cos_r],
        ], dtype=np.float32)

        rot = Rx @ Ry
        rotated = vertices @ rot.T  # (8, 3)

        # Orthographic projection: map x,y to image coordinates, z for depth
        # Scale and center
        cx, cy = W // 2, H // 2
        scale = min(H, W) * 0.3

        px = (rotated[:, 0] * scale + cx).astype(int)
        py = (-rotated[:, 1] * scale + cy).astype(int)  # flip y for image coords

        # 12 edges of the cube
        edges = [
            (0, 1), (1, 2), (2, 3), (3, 0),  # front face
            (4, 5), (5, 6), (6, 7), (7, 4),  # back face
            (0, 4), (1, 5), (2, 6), (3, 7),  # connecting edges
        ]

        for i0, i1 in edges:
            x0, y0 = px[i0], py[i0]
            x1, y1 = px[i1], py[i1]
            # Draw line with linear interpolation
            steps = max(abs(x1 - x0), abs(y1 - y0)) + 1
            for s_idx in range(steps):
                t = s_idx / max(steps - 1, 1)
                x = int(x0 + t * (x1 - x0))
                y = int(y0 + t * (y1 - y0))
                x = max(0, min(W - 1, x))
                y = max(0, min(H - 1, y))
                img[y, x] = 0.8

            # Draw thicker lines (3px wide)
            for offset in [-1, 1]:
                for s_idx in range(steps):
                    t = s_idx / max(steps - 1, 1)
                    x = int(x0 + t * (x1 - x0))
                    y = int(y0 + t * (y1 - y0)) + offset
                    x = max(0, min(W - 1, x))
                    y = max(0, min(H - 1, y))
                    img[y, x] = 0.4

        # Draw vertex dots
        for i in range(8):
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    yy = py[i] + dy
                    xx = px[i] + dx
                    if 0 <= yy < H and 0 <= xx < W:
                        img[yy, xx] = 1.0

        return img

    def set_image(self,
                  img: Image,
                  ls: core.LidarFrame,
                  return_num: int = 0) -> None:
        key_data = self._prepare_data(ls, return_num)
        if key_data is not None:
            img.set_image(key_data)

    def set_cloud_color(self,
                        cloud: Cloud,
                        ls: core.LidarFrame,
                        *,
                        return_num: int = 0) -> None:
        pass

    def enabled(self, ls: core.LidarFrame, return_num: int = 0) -> bool:
        return ls.has_field("IMU_ACC")


class IMUGaugeMode(ImageCloudMode):
    """Horizontal bar gauge showing current X/Y/Z accelerometer values."""

    def __init__(self, *, info: Optional[core.SensorInfo] = None) -> None:
        self._info = info

    @property
    def name(self) -> str:
        return "IMU_GAUGE"

    @property
    def names(self) -> List[str]:
        return ["IMU_GAUGE"]

    def _prepare_data(self,
                      ls: core.LidarFrame,
                      return_num: int = 0) -> Optional[np.ndarray]:
        if not self.enabled(ls, return_num):
            return None
        acc = ls.field("IMU_ACC").astype(np.float32)  # (256, 3)
        mean_xyz = acc.mean(axis=0)  # (3,)

        H, W = 256, 2048
        img = np.zeros((H, W), dtype=np.float32)

        max_val = 20.0  # m/s², max display range
        center_x = W // 2
        intensities = [0.9, 0.7, 0.5]  # X=bright, Y=mid, Z=dim

        # Draw center line
        img[:, center_x] = 0.15

        # Draw tick marks at ±1g intervals (9.81 m/s²)
        g = 9.81
        for mult in range(-2, 3):
            tick_x = int(center_x + mult * g / max_val * (W // 2))
            if 0 <= tick_x < W:
                img[:, tick_x] = 0.08

        # Draw 3 horizontal bars
        bar_height = H // 6  # height of each bar
        y_positions = [H // 6, H // 2, 5 * H // 6]  # top, middle, bottom

        for ch_idx, (y_center, intensity) in enumerate(zip(y_positions, intensities)):
            val = mean_xyz[ch_idx]
            # Map value to pixel width
            bar_len = int(abs(val) / max_val * (W // 2))
            bar_len = min(bar_len, W // 2)

            if val >= 0:
                x_start = center_x
                x_end = min(center_x + bar_len, W - 1)
            else:
                x_start = max(center_x - bar_len, 0)
                x_end = center_x

            y_top = max(y_center - bar_height // 2, 0)
            y_bot = min(y_center + bar_height // 2, H - 1)

            img[y_top:y_bot + 1, x_start:x_end + 1] = intensity

        return img

    def set_image(self,
                  img: Image,
                  ls: core.LidarFrame,
                  return_num: int = 0) -> None:
        key_data = self._prepare_data(ls, return_num)
        if key_data is not None:
            img.set_image(key_data)

    def set_cloud_color(self,
                        cloud: Cloud,
                        ls: core.LidarFrame,
                        *,
                        return_num: int = 0) -> None:
        pass

    def enabled(self, ls: core.LidarFrame, return_num: int = 0) -> bool:
        return ls.has_field("IMU_ACC")


class IMUAccHeatmapMode(ImageCloudMode):
    """IMU accelerometer data as a tiled heatmap image."""

    def __init__(self, *, info: Optional[core.SensorInfo] = None) -> None:
        self._info = info
        self._ae = AutoExposure()

    @property
    def name(self) -> str:
        return "IMU_ACC_HEATMAP"

    @property
    def names(self) -> List[str]:
        return ["IMU_ACC_HEATMAP"]

    def _prepare_data(self,
                      ls: core.LidarFrame,
                      return_num: int = 0) -> Optional[np.ndarray]:
        if not self.enabled(ls, return_num):
            return None
        data = ls.field("IMU_ACC").astype(np.float32, copy=True)  # (256, 3)
        target_w = self._info.w if self._info else 2048
        reps = (target_w + data.shape[1] - 1) // data.shape[1]
        tiled = np.tile(data, (1, reps))[:, :target_w]  # (256, 2048)
        col_min = tiled.min(axis=0, keepdims=True)
        col_max = tiled.max(axis=0, keepdims=True)
        denom = col_max - col_min
        denom[denom == 0] = 1.0
        tiled = (tiled - col_min) / denom
        if self._ae:
            self._ae.update(tiled, update_state=(return_num == 0))
        return tiled

    def set_image(self,
                  img: Image,
                  ls: core.LidarFrame,
                  return_num: int = 0) -> None:
        key_data = self._prepare_data(ls, return_num)
        if key_data is not None:
            img.set_image(key_data)

    def set_cloud_color(self,
                        cloud: Cloud,
                        ls: core.LidarFrame,
                        *,
                        return_num: int = 0) -> None:
        pass

    def enabled(self, ls: core.LidarFrame, return_num: int = 0) -> bool:
        return ls.has_field("IMU_ACC")


class IMUGyroHeatmapMode(ImageCloudMode):
    """IMU gyroscope data as a tiled heatmap image."""

    def __init__(self, *, info: Optional[core.SensorInfo] = None) -> None:
        self._info = info
        self._ae = AutoExposure()

    @property
    def name(self) -> str:
        return "IMU_GYRO_HEATMAP"

    @property
    def names(self) -> List[str]:
        return ["IMU_GYRO_HEATMAP"]

    def _prepare_data(self,
                      ls: core.LidarFrame,
                      return_num: int = 0) -> Optional[np.ndarray]:
        if not self.enabled(ls, return_num):
            return None
        data = ls.field("IMU_GYRO").astype(np.float32, copy=True)  # (256, 3)
        target_w = self._info.w if self._info else 2048
        reps = (target_w + data.shape[1] - 1) // data.shape[1]
        tiled = np.tile(data, (1, reps))[:, :target_w]  # (256, 2048)
        col_min = tiled.min(axis=0, keepdims=True)
        col_max = tiled.max(axis=0, keepdims=True)
        denom = col_max - col_min
        denom[denom == 0] = 1.0
        tiled = (tiled - col_min) / denom
        if self._ae:
            self._ae.update(tiled, update_state=(return_num == 0))
        return tiled

    def set_image(self,
                  img: Image,
                  ls: core.LidarFrame,
                  return_num: int = 0) -> None:
        key_data = self._prepare_data(ls, return_num)
        if key_data is not None:
            img.set_image(key_data)

    def set_cloud_color(self,
                        cloud: Cloud,
                        ls: core.LidarFrame,
                        *,
                        return_num: int = 0) -> None:
        pass

    def enabled(self, ls: core.LidarFrame, return_num: int = 0) -> bool:
        return ls.has_field("IMU_GYRO")


class RGBChannelMode(SimpleMode):
    """Extract a single channel (R/G/B) from the RGB 3-channel composite field.

    For sensors where R/G/B are stored as part of a combined RGB field
    rather than as separate ChanField entries.
    """

    def __init__(self, channel_name: str, channel_idx: int, *,
                 info: Optional[core.SensorInfo] = None) -> None:
        """
        Args:
            channel_name: display name ('R', 'G', or 'B')
            channel_idx: index into RGB last dimension (0=R, 1=G, 2=B)
            info: sensor metadata
        """
        super().__init__(channel_name, info=info, use_ae=True, use_buc=False)
        self._channel_name = channel_name
        self._channel_idx = channel_idx

    def _prepare_data(self,
                      ls: core.LidarFrame,
                      return_num: int = 0) -> Optional[np.ndarray]:
        if not self.enabled(ls, return_num):
            return None
        rgb = ls.field("RGB").astype(np.float32)
        key_data = rgb[:, :, self._channel_idx].copy()
        if self._buc:
            self._buc.update(key_data)
        if self._ae:
            self._ae.update(key_data, update_state=(return_num == 0))
        return key_data

    def enabled(self, ls: core.LidarFrame, return_num: int = 0) -> bool:
        return ls.has_field("RGB")


class RedChannelMode(RGBChannelMode):
    """Extract R channel from RGB composite."""
    def __init__(self, *, info=None):
        super().__init__("R", 0, info=info)


class GreenChannelMode(RGBChannelMode):
    """Extract G channel from RGB composite."""
    def __init__(self, *, info=None):
        super().__init__("G", 1, info=info)


class BlueChannelMode(RGBChannelMode):
    """Extract B channel from RGB composite."""
    def __init__(self, *, info=None):
        super().__init__("B", 2, info=info)


def is_norm_reflectivity_mode(mode: FieldViewMode) -> bool:
    """Checks whether the image/cloud mode is a normalized REFLECTIVITY mode
    """
    # NOTE[pb]: This is highly implementation specific and doesn't look nicely,
    # i.e. it's more like duck/duct plumbing .... but suits the need.
    return (isinstance(mode, ReflMode) and mode._normalized_refl)


LidarFrameVizMode = Union[ImageCloudMode, ImageMode, CloudMode]
"""Field view mode types"""


@dataclass
class CloudPaletteItem:
    """Palette with a name"""
    name: str
    palette: np.ndarray
