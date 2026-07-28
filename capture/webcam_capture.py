"""
Luz ambiente: promedia lo que ve una camara web y lo manda a la lampara.
Sirve para que la luz siga el tono general del cuarto en vez de la
pantalla o el audio.
"""

import threading
import time

import cv2

from core.color import dominant_color, enhance
from core.plugin_base import CaptureSource


def list_webcams(max_check=4):
    """Prueba los primeros indices y devuelve los que responden de verdad
    (abrir el dispositivo no alcanza, hay que poder leer un frame)."""
    out = []
    for i in range(max_check):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        if cap.isOpened():
            ok, _ = cap.read()
            if ok:
                out.append(i)
        cap.release()
    return out


class WebcamCaptureSource(CaptureSource):
    name = 'webcam'
    display_name = 'Luz ambiente (camara web)'

    def __init__(self, cfg=None):
        super().__init__(cfg)
        self._thread = None
        self._stop = threading.Event()
        self._color = None
        self._lock = threading.Lock()

    def start(self):
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self._running = True

    def _run(self):
        c = self.cfg
        idx = c.get('device_index', 1)
        sample_step = c.get('sample_step', 8)
        interval = c.get('interval_ms', 200) / 1000

        cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap = cv2.VideoCapture(idx)

        try:
            while not self._stop.is_set():
                t0 = time.time()
                ok, frame_bgr = cap.read()
                if not ok:
                    time.sleep(0.05)
                    continue

                frame_rgb = frame_bgr[:, :, ::-1]
                r, g, b = dominant_color(frame_rgb, sample_step)
                rr, gg, bb = enhance(
                    r, g, b,
                    sat_boost=c.get('saturation_boost', 1.3),
                    value_floor=c.get('value_floor', 0.05),
                    black_cutoff=0.02,
                )
                with self._lock:
                    self._color = (rr, gg, bb)

                elapsed = time.time() - t0
                time.sleep(max(0, interval - elapsed))
        finally:
            cap.release()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1)
        self._running = False

    def get_color(self):
        with self._lock:
            return self._color
