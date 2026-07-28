"""
Ambilight de pantalla: captura con dxcam (Desktop Duplication API) y cae a
mss si dxcam no arranca. dxcam es importante para juegos en pantalla
completa exclusiva -- mss (GDI) no puede verlos. Ver el proyecto anterior
(Desktop/ambilight) para el detalle completo, probado con Counter-Strike.
"""

import ctypes
import threading
import time

import mss
import numpy as np

try:
    import dxcam
    HAVE_DXCAM = True
except ImportError:
    HAVE_DXCAM = False

from core.color import dominant_color, enhance
from core.plugin_base import CaptureSource


def list_monitors():
    out = []
    with mss.MSS() as sct:
        for i, m in enumerate(sct.monitors):
            tag = ' (todas combinadas)' if i == 0 else ''
            out.append(f"{i}: {m['width']}x{m['height']}{tag}")
    return out


class _RawGrabber:
    def __init__(self, monitor_idx):
        self.backend = None
        self._ctx = None
        if HAVE_DXCAM:
            try:
                idx = max(0, monitor_idx - 1)
                self.cam = dxcam.create(output_idx=idx, output_color='RGB')
                self.cam.start(target_fps=30, video_mode=True)
                self.backend = 'dxcam'
                return
            except Exception:
                pass

        self._ctx = mss.MSS()
        self.sct = self._ctx.__enter__()
        if monitor_idx >= len(self.sct.monitors):
            monitor_idx = 1
        self.mon = self.sct.monitors[monitor_idx]
        self.backend = 'mss'

    def grab(self):
        if self.backend == 'dxcam':
            return self.cam.get_latest_frame()
        arr = np.asarray(self.sct.grab(self.mon))
        return arr[:, :, [2, 1, 0]]   # mss da B,G,R,A -> nos quedamos con R,G,B

    def close(self):
        if self.backend == 'dxcam':
            try:
                self.cam.stop()
            except Exception:
                pass
        elif self._ctx is not None:
            try:
                self._ctx.__exit__(None, None, None)
            except Exception:
                pass


class ScreenCaptureSource(CaptureSource):
    name = 'screen'
    display_name = 'Ambilight (pantalla)'

    def __init__(self, cfg=None):
        super().__init__(cfg)
        self._thread = None
        self._stop = threading.Event()
        self._color = None
        self._lock = threading.Lock()
        self.backend = None

    def start(self):
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self._running = True

    def _run(self):
        c = self.cfg
        grabber = _RawGrabber(c.get('monitor', 1))
        self.backend = grabber.backend
        sample_step = c.get('sample_step', 14)
        alpha = c.get('smoothing', 0.65)
        interval = c.get('interval_ms', 150) / 1000
        smoothed = None

        try:
            while not self._stop.is_set():
                t0 = time.time()
                frame = grabber.grab()
                if frame is None:
                    time.sleep(0.01)
                    continue

                r, g, b = dominant_color(frame, sample_step)
                if smoothed is None:
                    smoothed = (r, g, b)
                else:
                    smoothed = tuple(
                        smoothed[i] * (1 - alpha) + (r, g, b)[i] * alpha
                        for i in range(3)
                    )
                rr, gg, bb = enhance(
                    *smoothed,
                    sat_boost=c.get('saturation_boost', 2.4),
                    sat_floor=c.get('saturation_floor', 0.35),
                    value_floor=c.get('value_floor', 0.15),
                    black_cutoff=c.get('black_cutoff', 0.04),
                )
                with self._lock:
                    self._color = (rr, gg, bb)

                elapsed = time.time() - t0
                time.sleep(max(0, interval - elapsed))
        finally:
            grabber.close()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1)
        self._running = False

    def get_color(self):
        with self._lock:
            return self._color
