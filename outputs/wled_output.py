"""
Salida para tiras/controladores WLED (firmware ESP8266/ESP32 muy usado en
la comunidad DIY de ambilight).

*** NO PROBADO CONTRA HARDWARE REAL *** -- no hay un dispositivo WLED
disponible para verificar esto. La implementacion sigue la API JSON HTTP
documentada oficialmente (https://kno.wled.ge/interfaces/json-api/), que
es estable y publica, pero "implementado segun la documentacion" no es lo
mismo que "probado funcionando". Antes de confiar en esto, probalo con un
WLED real y avisame si algo no anda -- lo mas probable es un problema de
timing (rate limit) o de como WLED interpreta el color en el segmento.

Usa la API JSON en vez del protocolo UDP "realtime" (que tambien existe y
es mas rapido) porque la JSON API no necesita saber cuantos LEDs tiene la
tira -- el color se aplica a todo el segmento sin importar el largo. El
protocolo UDP si necesita saber el conteo exacto de LEDs, y sin hardware
para probar no quiero arriesgarme a una implementacion que mande datos con
la cantidad de bytes equivocada.
"""

import time

import requests

from core.plugin_base import OutputTarget

MIN_INTERVAL = 0.08   # WLED recomienda no saturar la API JSON por HTTP


class WledOutput(OutputTarget):
    name = 'wled'
    display_name = 'WLED (tiras ESP8266/ESP32) -- NO PROBADO'

    def __init__(self, device_cfg):
        super().__init__(device_cfg)
        self.base_url = None
        self._last_send = 0.0

    def connect(self):
        ip = self.device_cfg['wled']['ip']
        self.base_url = f'http://{ip}'
        try:
            r = requests.get(f'{self.base_url}/json/info', timeout=3)
            r.raise_for_status()
            self._connected = True
        except Exception:
            self._connected = False
            raise

    def disconnect(self):
        self._connected = False

    def set_color(self, r, g, b):
        now = time.time()
        if now - self._last_send < MIN_INTERVAL:
            return
        rgb = [round(r * 255), round(g * 255), round(b * 255)]
        try:
            requests.post(
                f'{self.base_url}/json/state',
                json={'on': True, 'seg': [{'col': [rgb]}]},
                timeout=1.5,
            )
            self._last_send = now
        except Exception:
            pass   # un envio que falla no tira todo abajo, se reintenta solo

    def turn_on(self):
        try:
            requests.post(f'{self.base_url}/json/state', json={'on': True}, timeout=2)
        except Exception:
            pass

    def turn_off(self):
        try:
            requests.post(f'{self.base_url}/json/state', json={'on': False}, timeout=2)
        except Exception:
            pass

    def status_text(self):
        return ('conectado' if self._connected else 'sin conectar') + ' (no verificado)'
