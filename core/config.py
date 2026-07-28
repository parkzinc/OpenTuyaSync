"""
Config: ahora soporta VARIOS dispositivos (antes era uno solo, hardcoded).
Cada entrada de "devices" tiene un "type" que dice que OutputTarget usar
(ver outputs/registry.py) y un bloque con la config especifica de ese tipo.
"""

import json
import sys
import uuid
from pathlib import Path

# config.json se ESCRIBE (dispositivos, credenciales de Spotify) -- tiene
# que vivir al lado del .exe, no adentro de _internal/ (la carpeta de
# PyInstaller pensada para datos de solo lectura). Path(__file__) dentro
# de un .exe empaquetado apunta a _internal/core/config.py, dos niveles
# arriba se queda corto; sys.executable es la ruta real del .exe.
if getattr(sys, 'frozen', False):
    APP_DIR = Path(sys.executable).parent
else:
    APP_DIR = Path(__file__).parent.parent

CONFIG_FILE = APP_DIR / 'config.json'

DEFAULT_CONFIG = {
    'devices': [],
    'capture': {
        'screen': {
            'monitor': 1, 'interval_ms': 150, 'sample_step': 14, 'smoothing': 0.65,
            'min_change': 12, 'saturation_boost': 2.4, 'saturation_floor': 0.35,
            'value_floor': 0.15, 'black_cutoff': 0.04,
        },
        'music': {
            'beat_factor': 1.5, 'beat_cooldown': 0.12, 'min_brightness': 0.12,
            'send_interval_ms': 120,
        },
        'flash': {'hz': 2.5, 'colorful': True},
        'spotify': {
            'client_id': '', 'client_secret': '', 'refresh_token': '',
            'poll_interval_s': 2.5,
        },
        'webcam': {
            'device_index': 1, 'sample_step': 8, 'interval_ms': 200,
            'saturation_boost': 1.3, 'value_floor': 0.05,
        },
    },
    'restore_scene_on_exit': True,
    'start_minimized': False,
}


def _deep_merge(base, override):
    """Mezcla override sobre base sin perder claves nuevas que no esten
    en el archivo guardado (para que agregar settings nuevos no rompa
    configs viejas)."""
    out = dict(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load():
    if not CONFIG_FILE.exists():
        save(DEFAULT_CONFIG)
        return json.loads(json.dumps(DEFAULT_CONFIG))
    try:
        on_disk = json.loads(CONFIG_FILE.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, OSError):
        on_disk = {}
    merged = _deep_merge(DEFAULT_CONFIG, on_disk)
    # "devices" no se mergea por clave (es una lista) -- si el archivo
    # trae su propia lista de dispositivos, esa es la que vale.
    if 'devices' in on_disk:
        merged['devices'] = on_disk['devices']
    return merged


def save(cfg):
    CONFIG_FILE.write_text(
        json.dumps(cfg, indent=2, ensure_ascii=False),
        encoding='utf-8',
    )


def new_device_id():
    return uuid.uuid4().hex[:12]


def get_device(cfg, device_id):
    for d in cfg['devices']:
        if d['id'] == device_id:
            return d
    return None


def enabled_devices(cfg):
    return [d for d in cfg['devices'] if d.get('enabled')]
