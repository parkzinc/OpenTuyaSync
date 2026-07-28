"""
Modo musica: reacciona a lo que sale por tus parlantes (loopback, no el
microfono). Auto-ganancia (se adapta al volumen real, no a un numero
fijo) + deteccion simple de golpes de grave.

El hilo de lectura de audio esta separado del calculo de color a
proposito -- mezclarlos causaba cortes de audio reales (avisos
"data discontinuity") cuando el envio a la lampara tardaba de mas. Ver
el proyecto anterior (Desktop/ambilight/music.py) para el detalle
completo, reproducido y confirmado con una prueba antes/despues.
"""

import colorsys
import ctypes
import threading
import time

import numpy as np

from core.color import AutoGain, BeatDetector
from core.plugin_base import CaptureSource

SAMPLE_RATE = 48000
BLOCK = 1024
BASS_HZ = 200


def analyze_block(mono, samplerate=SAMPLE_RATE):
    rms = float(np.sqrt(np.mean(mono ** 2))) if len(mono) else 0.0
    spec = np.abs(np.fft.rfft(mono))
    freqs = np.fft.rfftfreq(len(mono), 1 / samplerate)
    bass_energy = float(spec[freqs < BASS_HZ].sum())
    return rms, bass_energy


class _LoopbackReader(threading.Thread):
    """Hilo dedicado a leer audio, nunca se frena por nada del resto del
    programa. Inicializa COM a mano -- sin eso, el primer llamado desde
    este hilo revienta con Error 0x800401f0 (CO_E_NOTINITIALIZED)."""

    def __init__(self, mic, samplerate, block):
        super().__init__(daemon=True)
        self.mic = mic
        self.samplerate = samplerate
        self.block = block
        self._latest = None
        self._lock = threading.Lock()
        self._stop = threading.Event()

    def run(self):
        ctypes.windll.ole32.CoInitializeEx(None, 0)   # COINIT_MULTITHREADED
        try:
            with self.mic.recorder(samplerate=self.samplerate) as rec:
                while not self._stop.is_set():
                    data = rec.record(numframes=self.block)
                    mono = data.mean(axis=1)
                    with self._lock:
                        self._latest = mono
        finally:
            ctypes.windll.ole32.CoUninitialize()

    def latest(self):
        with self._lock:
            return self._latest

    def stop(self):
        self._stop.set()
        self.join(timeout=1)


class MusicCaptureSource(CaptureSource):
    name = 'music'
    display_name = 'Modo musica (audio)'

    def __init__(self, cfg=None):
        super().__init__(cfg)
        self._reader = None
        self._thread = None
        self._stop = threading.Event()
        self._color = None
        self._lock = threading.Lock()
        self.device_name = None

    def start(self):
        import soundcard as sc

        spk = sc.default_speaker()
        mic = sc.get_microphone(id=str(spk.name), include_loopback=True)
        self.device_name = spk.name

        self._reader = _LoopbackReader(mic, SAMPLE_RATE, BLOCK)
        self._reader.start()

        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self._running = True

    def _run(self):
        c = self.cfg
        gain = AutoGain()
        beats = BeatDetector(
            factor=c.get('beat_factor', 1.5),
            cooldown=c.get('beat_cooldown', 0.12),
        )
        min_v = c.get('min_brightness', 0.12)
        hue = 0.0

        while not self._stop.is_set():
            mono = self._reader.latest()
            if mono is None:
                time.sleep(0.01)
                continue

            rms, bass_energy = analyze_block(mono)
            now = time.time()
            level = gain.normalize(rms)
            is_beat = beats.check(bass_energy, now)

            if level < 0.03:
                s, v = 0.0, 0.0
            elif is_beat:
                hue = (hue + 35) % 360
                s, v = 1.0, 1.0
            else:
                hue = (hue + 0.5) % 360
                s, v = 1.0, max(min_v, min(1.0, level))

            r, g, b = colorsys.hsv_to_rgb(hue / 360, s, v)
            with self._lock:
                self._color = (r, g, b)
            time.sleep(0.015)

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1)
        if self._reader:
            self._reader.stop()
        self._running = False

    def get_color(self):
        with self._lock:
            return self._color
