"""
Modo Spotify: sigue el color dominante de la tapa del disco que esta
sonando. Distinto del modo musica (que escucha el audio real que sale por
los parlantes) -- este mira metadata de la cancion via la API de Spotify.

Necesita credenciales propias (client_id/secret/refresh_token en
config.json bajo "capture.spotify"). Correr spotify_auth_setup.py una vez
para conseguirlas -- ver ese archivo para el detalle. Sin configurar, esta
fuente avisa con SpotifyNotConfigured en vez de arrancar en silencio.
"""

import threading
import time
from io import BytesIO

import numpy as np
import requests
from PIL import Image

from core.color import dominant_color, enhance
from core.plugin_base import CaptureSource

TOKEN_URL = 'https://accounts.spotify.com/api/token'
NOW_PLAYING_URL = 'https://api.spotify.com/v1/me/player/currently-playing'


class SpotifyNotConfigured(Exception):
    pass


def refresh_access_token(client_id, client_secret, refresh_token):
    r = requests.post(TOKEN_URL, data={
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': client_id,
        'client_secret': client_secret,
    }, timeout=5)
    r.raise_for_status()
    return r.json()['access_token']


def album_color(image_url, sample_step=4):
    """Descarga la tapa del disco y saca su color promedio. Separado del
    resto para poder probarlo con cualquier imagen, sin necesitar
    credenciales de Spotify."""
    r = requests.get(image_url, timeout=5)
    r.raise_for_status()
    img = Image.open(BytesIO(r.content)).convert('RGB')
    arr = np.asarray(img)
    return dominant_color(arr, sample_step)


class SpotifyCaptureSource(CaptureSource):
    name = 'spotify'
    display_name = 'Spotify (color de la tapa)'

    def __init__(self, cfg=None):
        super().__init__(cfg)
        self._thread = None
        self._stop = threading.Event()
        self._color = None
        self._lock = threading.Lock()

    def start(self):
        c = self.cfg
        if not c.get('client_id') or not c.get('refresh_token'):
            raise SpotifyNotConfigured(
                'Falta configurar Spotify. Corre: python spotify_auth_setup.py'
            )
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self._running = True

    def _run(self):
        c = self.cfg
        poll = c.get('poll_interval_s', 2.5)
        access_token = None
        token_time = 0
        last_track_id = None
        cached_color = None

        while not self._stop.is_set():
            try:
                if access_token is None or time.time() - token_time > 1800:
                    access_token = refresh_access_token(
                        c['client_id'], c['client_secret'], c['refresh_token'],
                    )
                    token_time = time.time()

                r = requests.get(
                    NOW_PLAYING_URL,
                    headers={'Authorization': f'Bearer {access_token}'},
                    timeout=5,
                )
                if r.status_code == 200 and r.content:
                    data = r.json()
                    item = data.get('item') or {}
                    track_id = item.get('id')
                    images = (item.get('album') or {}).get('images') or []
                    if track_id and track_id != last_track_id and images:
                        cached_color = album_color(images[-1]['url'])   # la mas chica alcanza
                        last_track_id = track_id
                    if cached_color:
                        rr, gg, bb = enhance(*cached_color, sat_boost=1.4, value_floor=0.2)
                        with self._lock:
                            self._color = (rr, gg, bb)
                # 200 sin item, o 204 = no hay nada sonando -- se deja el ultimo color
            except Exception:
                pass   # un fallo de red puntual no tira todo abajo

            time.sleep(poll)

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1)
        self._running = False

    def get_color(self):
        with self._lock:
            return self._color
