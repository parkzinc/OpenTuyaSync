"""
Salida para dispositivos Tuya y las marcas blancas que usan el mismo
protocolo: LSC Smart Connect, Nedis SmartLife, Mirabella Genio, Treatlife.
Todas se emparejan con la app Smart Life / Tuya y usan el mismo Device ID
+ Clave Local, asi que un solo modulo les sirve a todas.

Probado extensivamente contra un foco real (ver el proyecto anterior en
Desktop/ambilight): encendido/apagado, color, brillo, temperatura de
blanco, y el modo "escena" (ciclo de colores propio del dispositivo).

Blancos/grises puros se mandan por dp de modo "white" en vez de "colour"
(ver WHITE_SATURATION_THRESHOLD y set_color()) -- esto NO esta probado
contra hardware real todavia, sale de un reporte de que el brillo maximo
en blanco se veia mas debil con ambilight que con la app oficial.
"""

import colorsys

import tinytuya

from core.plugin_base import OutputTarget


def rgb_to_tuya_hex(r, g, b):
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    return '%04x%04x%04x' % (round(h * 360) % 360, round(s * 1000), round(v * 1000))


# Por debajo de esta saturacion, un color se manda como blanco/gris puro
# en vez de HSV saturado -- ver el comentario en set_color().
WHITE_SATURATION_THRESHOLD = 0.03


class TuyaOutput(OutputTarget):
    name = 'tuya'
    display_name = 'Tuya / Smart Life (LSC, Nedis, Mirabella, Treatlife...)'

    def __init__(self, device_cfg):
        super().__init__(device_cfg)
        self.d = None
        self._scene_data = None

    def connect(self):
        t = self.device_cfg['tuya']
        self.d = tinytuya.Device(
            dev_id=t['dev_id'], address=t['ip'],
            local_key=t['local_key'], version=t['version'],
        )
        self.d.set_socketPersistent(True)
        self.d.set_socketTimeout(3)
        self._connected = True

    def disconnect(self):
        self.d = None
        self._connected = False

    def set_color(self, r, g, b):
        if not self.d:
            return
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        try:
            if s < WHITE_SATURATION_THRESHOLD:
                # Blanco/gris puro (por ejemplo, una pantalla toda blanca
                # o un flash). El modo "colour" prende los LEDs RGB por
                # separado, que en la gran mayoria de focos Tuya no llegan
                # a tanto brillo como el LED blanco dedicado del modo
                # "white" -- por eso se ve mas fuerte en la app oficial
                # (que usa "white" para blancos) que con ambilight (que
                # antes usaba "colour" para todo, blancos incluidos).
                # dp22 (bright_value) sigue la misma escala 0-1000 que ya
                # se usa para el V de "colour" en este mismo dispositivo.
                bright = max(10, round(v * 1000))
                self.d.set_multiple_values({'21': 'white', '22': bright}, nowait=True)
            else:
                hexv = rgb_to_tuya_hex(r, g, b)
                self.d.set_multiple_values({'21': 'colour', '24': hexv}, nowait=True)
        except Exception:
            # Un envio puntual que falla no es motivo de panico -- se
            # reintenta reconectando en el proximo intervalo.
            try:
                self.connect()
            except Exception:
                pass

    def turn_on(self):
        if self.d:
            self.d.set_value('20', True)

    def turn_off(self):
        if self.d:
            self.d.set_value('20', False)

    def save_previous_state(self):
        """Guarda el dato de escena (dp 25) actual, si el dispositivo
        tiene uno configurado desde la app Smart Life."""
        if not self.d:
            return
        try:
            dps = self.d.status().get('dps', {})
            self._scene_data = dps.get('25')
        except Exception:
            self._scene_data = None

    def restore_previous_state(self):
        if not self.d or not self._scene_data:
            return
        try:
            self.d.set_multiple_values({'21': 'scene', '25': self._scene_data})
        except Exception:
            pass

    def status_text(self):
        return 'conectado' if self._connected else 'sin conectar'
