"""
Control manual: rueda de color (matiz + saturacion, cualquier punto del
circulo) + slider de brillo + selector de color exacto + on/off.

Los cambios se acotan con un timer antes de emitirse -- mandarle a Tuya
un color por cada pixel que se arrastra el mouse lo satura (ver
core/engine.py y toda la sesion anterior: ~100-150ms entre envios es lo
que se probo confiable).
"""

import colorsys

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QColorDialog, QHBoxLayout, QLabel, QPushButton, QSlider, QVBoxLayout, QWidget,
)

from gui.color_wheel import ColorWheel

SEND_DEBOUNCE_MS = 90


class ManualControl(QWidget):
    color_changed = Signal(float, float, float)   # r, g, b en 0-1
    power_on = Signal()
    power_off = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._h, self._s, self._v = 0.78, 1.0, 1.0
        self._suspend = False   # evita bucles al actualizar desde codigo

        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(SEND_DEBOUNCE_MS)
        self._debounce.timeout.connect(self._emit_color)

        self._build_ui()
        self._set_hsv(self._h, self._s, self._v)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(10)

        top_row = QHBoxLayout()
        self.wheel = ColorWheel()
        self.wheel.color_changed.connect(self._on_wheel_changed)
        top_row.addWidget(self.wheel, 1)

        side_col = QVBoxLayout()
        self.swatch = QPushButton()
        self.swatch.setProperty('role', 'swatch')
        self.swatch.setMinimumHeight(60)
        self.swatch.setToolTip('Elegir color exacto')
        self.swatch.clicked.connect(self._pick_color)
        side_col.addWidget(self.swatch)
        side_col.addStretch()
        top_row.addLayout(side_col)

        layout.addLayout(top_row)

        self.val_slider, self.val_lbl = self._add_slider(layout, 'Brillo', 0, 100)
        self.val_slider.valueChanged.connect(self._on_value_changed)

        power_row = QHBoxLayout()
        on_btn = QPushButton('Prender')
        off_btn = QPushButton('Apagar')
        on_btn.clicked.connect(self.power_on.emit)
        off_btn.clicked.connect(self.power_off.emit)
        power_row.addWidget(on_btn)
        power_row.addWidget(off_btn)
        layout.addLayout(power_row)
        layout.addStretch()

    def _add_slider(self, layout, label, lo, hi):
        row = QHBoxLayout()
        lbl = QLabel(label)
        lbl.setFixedWidth(50)
        sl = QSlider(Qt.Horizontal)
        sl.setRange(lo, hi)
        val_lbl = QLabel('')
        val_lbl.setFixedWidth(38)
        val_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        row.addWidget(lbl)
        row.addWidget(sl)
        row.addWidget(val_lbl)
        layout.addLayout(row)
        return sl, val_lbl

    def _on_wheel_changed(self, hue, sat):
        if self._suspend:
            return
        self._h, self._s = hue, sat
        self._update_swatch()
        self._debounce.start()

    def _on_value_changed(self, value):
        self.val_lbl.setText(f'{value}%')
        if self._suspend:
            return
        self._v = value / 100
        self._update_swatch()
        self._debounce.start()

    def _update_swatch(self):
        r, g, b = colorsys.hsv_to_rgb(self._h, self._s, self._v)
        hexc = '#%02x%02x%02x' % (round(r * 255), round(g * 255), round(b * 255))
        self.swatch.setStyleSheet(f'background-color: {hexc};')

    def _emit_color(self):
        r, g, b = colorsys.hsv_to_rgb(self._h, self._s, self._v)
        self.color_changed.emit(r, g, b)

    def _pick_color(self):
        r, g, b = colorsys.hsv_to_rgb(self._h, self._s, self._v)
        initial = QColor(round(r * 255), round(g * 255), round(b * 255))
        c = QColorDialog.getColor(initial, self, 'Elegir color')
        if c.isValid():
            h, s, v, _ = c.getHsvF()
            self._set_hsv(max(0.0, h), s, v)
            self._emit_color()

    def _set_hsv(self, h, s, v):
        self._h, self._s, self._v = h, s, v
        self._suspend = True
        self.wheel.set_hs(h, s)
        self.val_slider.setValue(round(v * 100))
        self.val_lbl.setText(f'{round(v * 100)}%')
        self._suspend = False
        self._update_swatch()
