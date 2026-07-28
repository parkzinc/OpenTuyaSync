"""
El motor: conecta UNA fuente de captura activa con TODOS los dispositivos
habilitados. Ninguno de los dos lados sabe nada del otro -- por eso se
pueden combinar libremente (ambilight -> Tuya + WLED al mismo tiempo, por
ejemplo).

Corre en su propio hilo. La fuente ya tiene su propio hilo interno (ver
core/plugin_base.py) y expone get_color() sin bloquear jamas; el motor
solo se encarga de, a un ritmo fijo, preguntarle el color a la fuente y
mandarselo a cada dispositivo.
"""

import threading
import time


class Engine:
    def __init__(self, send_interval_ms=150, on_state_change=None):
        self.send_interval = send_interval_ms / 1000
        self.on_state_change = on_state_change   # callback opcional para la UI

        self.source = None
        self.outputs = []   # lista de OutputTarget ya conectados

        self._thread = None
        self._stop = threading.Event()
        self.active_source_name = None

    def start(self, source, outputs):
        """source: una CaptureSource ya instanciada (sin arrancar).
        outputs: lista de OutputTarget ya conectados."""
        if self._thread and self._thread.is_alive():
            self.stop()

        self.source = source
        self.outputs = outputs
        self.active_source_name = source.name

        for out in self.outputs:
            out.save_previous_state()

        self.source.start()

        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self._notify()

    def _run(self):
        while not self._stop.is_set():
            t0 = time.time()
            color = self.source.get_color()
            if color is not None:
                r, g, b = color
                for out in self.outputs:
                    out.set_color(r, g, b)
            elapsed = time.time() - t0
            time.sleep(max(0, self.send_interval - elapsed))

    def stop(self, restore=True):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)
        if self.source:
            self.source.stop()
        if restore:
            for out in self.outputs:
                out.restore_previous_state()
        self.active_source_name = None
        self._notify()

    @property
    def running(self):
        return bool(self._thread and self._thread.is_alive())

    def _notify(self):
        if self.on_state_change:
            try:
                self.on_state_change()
            except Exception:
                pass
