"""
Selector de color circular: el angulo es el matiz, la distancia al
centro es la saturacion. Click o arrastre en cualquier punto elige ese
color exacto -- no una lista fija de opciones.

El brillo no entra en la rueda (es una tercera dimension, matiz+saturacion
ya ocupan las dos que tiene un circulo) -- se controla aparte con un
slider en ManualControl.

La rueda se genera una sola vez con numpy (vectorizado, no pixel por
pixel en Python puro) y se cachea; solo se recalcula si cambia el
tamaño del widget.
"""

import numpy as np
from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QWidget

WHEEL_RES = 256


def _render_wheel(size=WHEEL_RES):
    y, x = np.mgrid[0:size, 0:size].astype(np.float64)
    c = (size - 1) / 2
    dx = (x - c) / (size / 2)
    dy = (y - c) / (size / 2)
    dist = np.sqrt(dx ** 2 + dy ** 2)
    angle = np.arctan2(-dy, dx)              # 0 = derecha, +90° = arriba
    hue = (angle / (2 * np.pi)) % 1.0
    sat = np.clip(dist, 0, 1)

    h6 = hue * 6.0
    i = (np.floor(h6).astype(int)) % 6
    f = h6 - np.floor(h6)
    v = np.ones_like(hue)
    p = v * (1 - sat)
    q = v * (1 - f * sat)
    t = v * (1 - (1 - f) * sat)

    conds = [i == 0, i == 1, i == 2, i == 3, i == 4, i == 5]
    r = np.select(conds, [v, q, p, p, t, v])
    g = np.select(conds, [t, v, v, q, p, p])
    b = np.select(conds, [p, p, t, v, v, q])

    rgba = np.zeros((size, size, 4), dtype=np.uint8)
    rgba[..., 0] = (r * 255).astype(np.uint8)
    rgba[..., 1] = (g * 255).astype(np.uint8)
    rgba[..., 2] = (b * 255).astype(np.uint8)
    rgba[..., 3] = (dist <= 1.0).astype(np.uint8) * 255

    img = QImage(rgba.tobytes(), size, size, QImage.Format_RGBA8888)
    return img.copy()   # copy: el buffer de numpy muere al salir de la funcion


class ColorWheel(QWidget):
    color_changed = Signal(float, float)   # hue, saturacion -- 0.0 a 1.0

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(170, 170)
        self._hue = 0.78
        self._sat = 1.0
        self._dragging = False
        self._wheel_img = _render_wheel()
        self._cached_pix = None
        self._cached_size = -1

    def set_hs(self, hue, sat):
        self._hue, self._sat = hue, min(1.0, sat)
        self.update()

    def _side(self):
        return min(self.width(), self.height())

    def paintEvent(self, event):
        side = self._side()
        if side <= 4:
            return
        if self._cached_size != side:
            self._cached_pix = QPixmap.fromImage(
                self._wheel_img.scaled(side, side, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
            self._cached_size = side

        cx, cy = self.width() / 2, self.height() / 2

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.drawPixmap(int(cx - side / 2), int(cy - side / 2), self._cached_pix)

        radius = side / 2
        angle = self._hue * 2 * np.pi
        dist = self._sat * radius
        ix = cx + dist * np.cos(angle)
        iy = cy - dist * np.sin(angle)

        p.setPen(QPen(Qt.white, 3))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QPoint(int(ix), int(iy)), 8, 8)
        p.setPen(QPen(Qt.black, 1))
        p.drawEllipse(QPoint(int(ix), int(iy)), 8, 8)

    def mousePressEvent(self, event):
        self._dragging = True
        self._pick(event.position())

    def mouseMoveEvent(self, event):
        if self._dragging:
            self._pick(event.position())

    def mouseReleaseEvent(self, event):
        self._dragging = False

    def _pick(self, pos):
        cx, cy = self.width() / 2, self.height() / 2
        dx, dy = pos.x() - cx, pos.y() - cy
        radius = self._side() / 2
        if radius <= 0:
            return
        dist = (dx ** 2 + dy ** 2) ** 0.5
        self._sat = min(1.0, dist / radius)
        self._hue = (np.arctan2(-dy, dx) / (2 * np.pi)) % 1.0
        self.update()
        self.color_changed.emit(self._hue, self._sat)
