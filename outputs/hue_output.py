"""
Salida para Philips Hue, via el Bridge local (API v1 CLIP, HTTP plano en
la red local -- no pasa por la nube de Philips).

*** NO PROBADO CONTRA HARDWARE REAL *** -- no hay un Bridge disponible
para verificar esto. Implementado segun la documentacion oficial
(https://developers.meethue.com/develop/get-started-2/), que es estable,
pero no es lo mismo que haberlo probado. Antes de confiar en esto, probalo
con un Bridge real.

El emparejamiento con Hue es un paso obligatorio de su API, no algo que se
pueda saltear: hay que apretar el boton fisico del Bridge y despues, DENTRO
de los siguientes 30 segundos, pedir un usuario/api-key. pair() hace ese
pedido -- llamala justo despues de apretar el boton.
"""

import colorsys

import requests

from core.plugin_base import OutputTarget


def pair(bridge_ip, app_name='opentuya_sync#pc'):
    """
    Llamar DESPUES de apretar el boton fisico del Bridge (dentro de los
    30 segundos siguientes). Devuelve el "username"/api-key a guardar en
    la config de este dispositivo, o levanta una excepcion con el motivo
    si todavia no se aprieto el boton.
    """
    r = requests.post(f'http://{bridge_ip}/api', json={'devicetype': app_name}, timeout=5)
    r.raise_for_status()
    data = r.json()
    if data and 'success' in data[0]:
        return data[0]['success']['username']
    reason = data[0].get('error', {}).get('description', 'error desconocido') if data else 'sin respuesta'
    raise RuntimeError(f'No se pudo emparejar: {reason}. ¿Apretaste el boton del Bridge?')


def list_lights(bridge_ip, username):
    """Para la UI: que luces hay en este Bridge, id -> nombre."""
    r = requests.get(f'http://{bridge_ip}/api/{username}/lights', timeout=5)
    r.raise_for_status()
    return {lid: info.get('name', lid) for lid, info in r.json().items()}


class HueOutput(OutputTarget):
    name = 'hue'
    display_name = 'Philips Hue -- NO PROBADO'

    def __init__(self, device_cfg):
        super().__init__(device_cfg)
        h = device_cfg['hue']
        self.bridge_ip = h['bridge_ip']
        self.username = h['username']
        self.light_id = h['light_id']
        self.base = f'http://{self.bridge_ip}/api/{self.username}/lights/{self.light_id}'

    def connect(self):
        r = requests.get(self.base, timeout=3)
        r.raise_for_status()
        self._connected = True

    def disconnect(self):
        self._connected = False

    def set_color(self, r, g, b):
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        body = {
            'on': True,
            'hue': round(h * 65535),
            'sat': round(s * 254),
            'bri': max(1, round(v * 254)),
        }
        try:
            requests.put(f'{self.base}/state', json=body, timeout=1.5)
        except Exception:
            pass

    def turn_on(self):
        try:
            requests.put(f'{self.base}/state', json={'on': True}, timeout=2)
        except Exception:
            pass

    def turn_off(self):
        try:
            requests.put(f'{self.base}/state', json={'on': False}, timeout=2)
        except Exception:
            pass

    def status_text(self):
        return ('conectado' if self._connected else 'sin conectar') + ' (no verificado)'
