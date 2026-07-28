"""
Modo flash: destella a un ritmo fijo. No apaga y prende el rele de verdad
-- alterna el brillo entre maximo y cero dentro de un color, para no
estresar el hardware con encendidos rapidos repetidos.

Aviso: las luces destellando rapido pueden ser incomodas para
fotosensibilidad.
"""

import colorsys
import random
import threading
import time

from core.plugin_base import CaptureSource


class FlashCaptureSource(CaptureSource):
    name = 'flash'
    display_name = 'Modo flash (destellos)'

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
        hz = c.get('hz', 2.5)
        colorful = c.get('colorful', True)
        period = 1.0 / hz
        on = False

        while not self._stop.is_set():
            on = not on
            if on:
                h = random.random() if colorful else 0.0
                s = 1.0 if colorful else 0.0
                color = colorsys.hsv_to_rgb(h, s, 1.0)
            else:
                color = (0.0, 0.0, 0.0)
            with self._lock:
                self._color = color
            time.sleep(period / 2)

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1)
        self._running = False

    def get_color(self):
        with self._lock:
            return self._color
