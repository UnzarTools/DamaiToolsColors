"""
ColorMod Engine
===============
System-wide screen color filter using two Windows APIs in parallel:

  GDI32 SetDeviceGammaRamp  →  Brightness / Contrast / Exposure / Gamma
  Magnification API matrix  →  Saturation / Vibrance / Hue / Color Temperature

The engine runs a daemon heartbeat thread that reapplies settings every 5 s
so they survive display sleep, reconnect, or resolution changes.
"""

import ctypes
import numpy as np
import threading
import time
import math

# ── Windows API handles ────────────────────────────────────────────────────────
try:
    _gdi32  = ctypes.windll.gdi32
    _user32 = ctypes.windll.user32
    _gdi32.SetDeviceGammaRamp.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    _gdi32.SetDeviceGammaRamp.restype = ctypes.c_int
    _GDI_OK = True
except Exception:
    _GDI_OK = False

try:
    _mag    = ctypes.windll.magnification
    _MAG_LOADED = True
except Exception:
    _MAG_LOADED = False


# MAGCOLOREFFECT: 5×5 float matrix consumed by MagSetFullscreenColorEffect
class MAGCOLOREFFECT(ctypes.Structure):
    _fields_ = [("transform", (ctypes.c_float * 5) * 5)]


# ─────────────────────────────────────────────────────────────────────────────

class ColorEngine:
    """
    Manages all system-wide color corrections.

    Usage
    -----
    engine = ColorEngine()
    engine.update(saturation=120, brightness=10)
    engine.apply_preset({"saturation": 80, "gamma": 1.1, ...})
    engine.shutdown()   # called on app close — resets the display
    """

    # Factory defaults (= identity / no effect)
    DEFAULTS: dict = {
        "brightness":  0,     # int    -100 … +100
        "contrast":    0,     # int    -100 … +100
        "exposure":    0.0,   # float  -2.0 … +2.0  (EV stops)
        "gamma":       1.0,   # float   0.5 … 3.0
        "saturation":  0,     # int    -100 … +200   (0 = normal)
        "vibrance":    0,     # int    -100 … +100
        "hue_shift":   0,     # int    -180 … +180  (degrees)
        "color_temp":  0,     # int    -100 … +100   (neg=cool, pos=warm)
    }

    def __init__(self):
        self._params:  dict          = dict(self.DEFAULTS)
        self._lock:    threading.Lock = threading.Lock()
        self._active:  bool          = True
        self._paused:  bool          = False   # True while window is hidden

        # Grab the virtual-desktop device context (entire screen)
        self._hdc = _user32.GetDC(0) if _GDI_OK else None

        # Initialise Magnification API
        self._mag_ok = False
        if _MAG_LOADED:
            try:
                if _mag.MagInitialize():
                    self._mag_ok = True
            except Exception:
                pass

        # Heartbeat: reapply every 5 s (handles sleep/reconnect)
        self._thread = threading.Thread(
            target=self._heartbeat, daemon=True, name="ColorMod-Engine"
        )
        self._thread.start()

    # ── Public API ─────────────────────────────────────────────────────────────

    def update(self, **kw):
        """Update individual parameter(s) and apply immediately."""
        with self._lock:
            self._params.update(kw)
        self._push()

    def apply_preset(self, preset: dict):
        """
        Apply a complete preset (replaces every parameter).
        Missing keys fall back to DEFAULTS.
        """
        with self._lock:
            self._params = {**self.DEFAULTS, **preset}
        self._push()

    def get_params(self) -> dict:
        with self._lock:
            return dict(self._params)

    def set_paused(self, paused: bool):
        """
        Call with True when the window is minimised / hidden.
        The heartbeat interval doubles to 10 s and _push() is skipped,
        saving CPU while the colour effects remain applied.
        """
        self._paused = paused

    def reset(self):
        """Reset all params to defaults and restore the display."""
        with self._lock:
            self._params = dict(self.DEFAULTS)
        self._reset_gamma()
        self._reset_mag()

    def shutdown(self):
        """Clean exit: stop the engine and restore the display to defaults."""
        self._active = False
        self.reset()
        if self._mag_ok:
            try:
                _mag.MagUninitialize()
            except Exception:
                pass
        if _GDI_OK and self._hdc:
            try:
                _user32.ReleaseDC(0, self._hdc)
            except Exception:
                pass

    @property
    def mag_available(self) -> bool:
        return self._mag_ok

    # ── Internal ───────────────────────────────────────────────────────────────

    def _heartbeat(self):
        while self._active:
            time.sleep(10 if self._paused else 5)
            if self._active and not self._paused:
                try:
                    self._push()
                except Exception:
                    pass

    def _push(self):
        """Read current params and apply both APIs."""
        with self._lock:
            p = dict(self._params)
        self._push_gamma(p)
        if self._mag_ok:
            self._push_mag(p)

    # ── Gamma Ramp (Brightness / Contrast / Exposure / Gamma) ─────────────────

    def _push_gamma(self, p: dict):
        if not _GDI_OK or not self._hdc:
            return

        brightness = p["brightness"] / 100.0    # -1 … +1
        contrast   = float(p["contrast"])       # -100 … +100
        exposure   = p["exposure"]              # EV
        gamma      = max(p["gamma"], 0.01)

        # Start with a linear [0 … 1] ramp
        ramp = np.linspace(0.0, 1.0, 256, dtype=np.float64)

        # 1. Exposure (photographic EV stops)
        ramp *= 2.0 ** exposure

        # 2. Contrast  (classic Photoshop formula)
        if contrast:
            f    = (259.0 * (contrast + 255.0)) / (255.0 * (259.0 - contrast))
            ramp = f * (ramp - 0.5) + 0.5

        # 3. Brightness (additive offset)
        ramp += brightness * 0.5

        # 4. Gamma power curve
        ramp = np.clip(ramp, 1e-9, 1.0) ** (1.0 / gamma)

        # Convert to 16-bit WORD range expected by SetDeviceGammaRamp
        ramp = np.clip(ramp * 65535.0, 0, 65535).astype(np.uint16)

        # Interleave as R, G, B (same curve for all channels)
        buf = np.concatenate([ramp, ramp, ramp])
        try:
            _gdi32.SetDeviceGammaRamp(ctypes.c_void_p(self._hdc), buf.ctypes.data_as(ctypes.c_void_p))
        except Exception:
            pass

    def _reset_gamma(self):
        if not _GDI_OK or not self._hdc:
            return
        ramp = np.arange(256, dtype=np.uint16) * 257   # linear 0 … 65535
        buf  = np.concatenate([ramp, ramp, ramp])
        try:
            _gdi32.SetDeviceGammaRamp(ctypes.c_void_p(self._hdc), buf.ctypes.data_as(ctypes.c_void_p))
        except Exception:
            pass

    # ── Magnification Color Matrix (Sat / Vibrance / Hue / Temp) ──────────────

    def _push_mag(self, p: dict):
        # Map saturation: -100 → 0 (grayscale), 0 → 1 (normal), +200 → 3 (vivid)
        sat   = max(0.0, (p["saturation"]  / 100.0) + 1.0)
        vib   =         p["vibrance"]   / 100.0        # -1 … +1
        hue   =         p["hue_shift"]                 # degrees
        temp  =         p["color_temp"] / 100.0        # -1 … +1

        # Base saturation matrix
        M = self._sat_mat(sat)

        # Vibrance: smart saturation that biases toward already-muted colours
        # Approximated by blending toward a stronger saturation value
        if vib != 0:
            vib_sat = max(0.0, sat + vib * 0.9)
            M_vib   = self._sat_mat(vib_sat)
            t       = abs(vib)
            M       = (1.0 - t) * M + t * M_vib

        # Chain hue rotation then temperature shift
        M = M @ self._hue_mat(hue) @ self._temp_mat(temp)
        
        # Magnification API applies matrix as: Output = InputRowVector * M
        # Our SVG matrices are built as: Output = M * InputColumnVector
        # Therefore, we MUST transpose the matrix to get correct colour mapping.
        M = M.T

        effect = MAGCOLOREFFECT()
        for i in range(5):
            for j in range(5):
                effect.transform[i][j] = float(M[i, j])
        try:
            _mag.MagSetFullscreenColorEffect(ctypes.byref(effect))
        except Exception:
            pass

    def _reset_mag(self):
        if not self._mag_ok:
            return
        I = MAGCOLOREFFECT()
        for k in range(5):
            I.transform[k][k] = 1.0   # identity
        try:
            _mag.MagSetFullscreenColorEffect(ctypes.byref(I))
        except Exception:
            pass

    # ── Matrix Builders ────────────────────────────────────────────────────────

    @staticmethod
    def _sat_mat(s: float) -> np.ndarray:
        """
        SVG feColorMatrix saturation.
        s=0 → grayscale, s=1 → identity, s>1 → boosted.
        """
        m = np.eye(5, dtype=np.float32)
        m[0] = [0.213 + 0.787*s,  0.715 - 0.715*s,  0.072 - 0.072*s,  0, 0]
        m[1] = [0.213 - 0.213*s,  0.715 + 0.285*s,  0.072 - 0.072*s,  0, 0]
        m[2] = [0.213 - 0.213*s,  0.715 - 0.715*s,  0.072 + 0.928*s,  0, 0]
        return m

    @staticmethod
    def _hue_mat(degrees: float) -> np.ndarray:
        """SVG feColorMatrix hueRotate formula."""
        rad  = math.radians(degrees)
        c, s = math.cos(rad), math.sin(rad)
        m = np.eye(5, dtype=np.float32)
        m[0] = [0.213+c*0.787-s*0.213,  0.715-c*0.715-s*0.715,  0.072-c*0.072+s*0.928, 0, 0]
        m[1] = [0.213-c*0.213+s*0.143,  0.715+c*0.285+s*0.140,  0.072-c*0.072-s*0.283, 0, 0]
        m[2] = [0.213-c*0.213-s*0.787,  0.715-c*0.715+s*0.715,  0.072+c*0.928+s*0.072, 0, 0]
        return m

    @staticmethod
    def _temp_mat(t: float) -> np.ndarray:
        """
        Colour temperature shift.
        t > 0 → warm (orange), t < 0 → cool (blue).
        """
        m = np.eye(5, dtype=np.float32)
        if t > 0:           # warm
            m[0][0] = 1.0 + t * 0.25
            m[1][1] = 1.0 + t * 0.06
            m[2][2] = 1.0 - t * 0.28
        else:               # cool
            m[0][0] = 1.0 + t * 0.18
            m[2][2] = 1.0 - t * 0.32
        return m
