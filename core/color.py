"""
Matematica de color compartida entre fuentes. Todo entra y sale en RGB
0-1 -- la conversion al formato que necesita cada dispositivo (hex HSV de
Tuya, bytes crudos de WLED, XY de Hue) es responsabilidad de cada modulo
de outputs/, no de aca.
"""

import colorsys


def dominant_color(rgb_array, sample_step=14):
    """
    rgb_array: array (alto, ancho, 3) en orden R,G,B, valores 0-255.
    Promedia una grilla de muestras en vez de todos los pixeles -- no hace
    falta mas precision para esto y es mucho mas rapido.
    """
    small = rgb_array[::sample_step, ::sample_step]
    r, g, b = small[:, :, 0].mean(), small[:, :, 1].mean(), small[:, :, 2].mean()
    return r / 255, g / 255, b / 255


def enhance(r, g, b, sat_boost=1.0, sat_floor=0.0, value_floor=0.0, black_cutoff=0.04):
    """
    Ajusta un color para que se vea bien en un LED en vez de lavado como
    se ve en una pantalla. Ver ambilight.py del proyecto anterior para el
    razonamiento completo de cada parametro -- probado ahi con una ventana
    blanca y negra real (llega a RGB puro 0,0,0 y 255,255,255).

    sat_boost: multiplica la saturacion.
    sat_floor: saturacion minima, pero SOLO si ya habia algo de color real
      (si es gris puro, no le inventa un matiz al azar).
    value_floor: brillo minimo, pero solo si no esta realmente muy oscuro
      (ver black_cutoff).
    black_cutoff: por debajo de este brillo crudo, se deja ir a negro en
      vez de aplicar value_floor.
    """
    h, s_raw, v = colorsys.rgb_to_hsv(r, g, b)
    s = min(1.0, s_raw * sat_boost)
    if s_raw > 0.02:
        s = max(s, sat_floor)
    if v > black_cutoff:
        v = max(v, value_floor)
    return colorsys.hsv_to_rgb(h, s, v)


class AutoGain:
    """
    Convierte un nivel crudo (RMS de audio, brillo de imagen, lo que sea) a
    0-1 relativo al MAXIMO reciente, no a un numero fijo. El techo sube de
    inmediato si algo es mas fuerte que antes, y baja despacio para que la
    referencia se adapte con el tiempo en vez de quedar pegada a un pico
    viejo.
    """

    def __init__(self, decay=0.997, floor=1e-4):
        self.ceiling = floor
        self.decay = decay
        self.floor = floor

    def normalize(self, raw):
        self.ceiling = max(raw, self.ceiling * self.decay, self.floor)
        return min(1.0, raw / self.ceiling)


class BeatDetector:
    """
    Detector de golpes simple: compara el valor de este bloque contra el
    promedio movil reciente. No es deteccion de tempo real, pero alcanza
    para "que la luz reaccione a la musica".
    """

    def __init__(self, factor=1.5, cooldown=0.12, avg_window=40):
        self.factor = factor
        self.cooldown = cooldown
        self.avg_window = avg_window
        self.history = []
        self.next_ok = 0.0

    def check(self, value, now):
        avg = sum(self.history) / len(self.history) if self.history else value
        self.history.append(value)
        if len(self.history) > self.avg_window:
            self.history.pop(0)

        is_beat = avg > 1e-6 and value > avg * self.factor and now >= self.next_ok
        if is_beat:
            self.next_ok = now + self.cooldown
        return is_beat
