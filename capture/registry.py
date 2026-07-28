"""
Registro de fuentes de captura disponibles. Agregar una fuente nueva es
agregar una linea aca (y el archivo capture_*.py correspondiente).
"""

from capture.dxcam_capture import ScreenCaptureSource
from capture.flash_capture import FlashCaptureSource
from capture.music_capture import MusicCaptureSource
from capture.spotify_capture import SpotifyCaptureSource
from capture.webcam_capture import WebcamCaptureSource

# nombre -> (clase, clave dentro de config['capture'])
CAPTURE_TYPES = {
    ScreenCaptureSource.name: (ScreenCaptureSource, 'screen'),
    MusicCaptureSource.name: (MusicCaptureSource, 'music'),
    FlashCaptureSource.name: (FlashCaptureSource, 'flash'),
    SpotifyCaptureSource.name: (SpotifyCaptureSource, 'spotify'),
    WebcamCaptureSource.name: (WebcamCaptureSource, 'webcam'),
}


def create_source(name, cfg):
    if name not in CAPTURE_TYPES:
        raise ValueError(f'Fuente desconocida: {name!r}')
    cls, cfg_key = CAPTURE_TYPES[name]
    return cls(cfg.get('capture', {}).get(cfg_key, {}))
