"""Ventana principal: lista de dispositivos + pestana Automatico (fuentes
reactivas) + pestana Manual (color a mano). Cerrar con la X no cierra el
programa -- lo esconde a la bandeja (ver main.py)."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup, QFrame, QGroupBox, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QMainWindow, QMessageBox, QPushButton, QRadioButton,
    QTabWidget, QVBoxLayout, QWidget,
)

from capture.registry import create_source
from capture.spotify_capture import SpotifyNotConfigured
from core import config as cfgmod
from core.engine import Engine
from gui.device_dialog import DeviceDialog
from gui.manual_control import ManualControl
from gui.spotify_setup_dialog import SpotifySetupDialog
from outputs.registry import create_output

SOURCE_LABELS = {
    'screen': 'Ambilight (pantalla)',
    'music': 'Modo musica (audio)',
    'flash': 'Modo flash (destellos)',
    'spotify': 'Spotify (color de la tapa)',
    'webcam': 'Camara web (luz ambiente)',
}


class MainWindow(QMainWindow):
    state_changed = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle('OpenTuya Sync')
        self.resize(680, 560)

        self.cfg = cfgmod.load()
        self.engine = Engine(send_interval_ms=150, on_state_change=self._notify_state_changed)
        self.state_changed.connect(self._refresh_status)

        # Conexiones reusadas tanto por las fuentes reactivas como por el
        # control manual -- sin este pool, cada slider movido reconectaria
        # el dispositivo, que es lento e innecesario.
        self.output_pool = {}

        self._build_ui()
        self._reload_devices()

    # ---------------------------------------------------------------- UI

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(14, 14, 14, 0)
        root.setSpacing(10)

        body = QHBoxLayout()
        body.setSpacing(14)
        root.addLayout(body, 1)

        body.addWidget(self._build_devices_panel(), 2)
        body.addWidget(self._build_tabs(), 3)

        root.addWidget(self._build_footer())

    def _heading(self, text):
        lbl = QLabel(text)
        lbl.setProperty('role', 'heading')
        return lbl

    def _build_devices_panel(self):
        box = QGroupBox()
        layout = QVBoxLayout(box)
        layout.addWidget(self._heading('Dispositivos'))

        self.device_list = QListWidget()
        self.device_list.itemChanged.connect(self._on_device_checked)
        layout.addWidget(self.device_list)

        btn_row = QHBoxLayout()
        add_btn = QPushButton('+ Agregar')
        edit_btn = QPushButton('Editar')
        del_btn = QPushButton('Quitar')
        add_btn.clicked.connect(self._add_device)
        edit_btn.clicked.connect(self._edit_device)
        del_btn.clicked.connect(self._delete_device)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(edit_btn)
        btn_row.addWidget(del_btn)
        layout.addLayout(btn_row)
        return box

    def _build_tabs(self):
        tabs = QTabWidget()
        tabs.addTab(self._build_auto_tab(), 'Automatico')
        tabs.addTab(self._build_manual_tab(), 'Manual')
        return tabs

    def _build_auto_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.addWidget(self._heading('Fuente'))

        source_box = QGroupBox()
        source_layout = QVBoxLayout(source_box)
        self.source_group = QButtonGroup(self)
        self.source_radios = {}
        for name, label in SOURCE_LABELS.items():
            rb = QRadioButton(label)
            self.source_radios[name] = rb
            self.source_group.addButton(rb)
            source_layout.addWidget(rb)
        self.source_radios['screen'].setChecked(True)
        layout.addWidget(source_box)

        self.start_btn = QPushButton('Iniciar')
        self.start_btn.setProperty('role', 'primary')
        self.start_btn.setCheckable(True)
        self.start_btn.clicked.connect(self.toggle_engine)
        layout.addWidget(self.start_btn)

        self.status_label = QLabel('Detenido.')
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        layout.addStretch()
        return w

    def _build_manual_tab(self):
        self.manual = ManualControl()
        self.manual.color_changed.connect(self._on_manual_color)
        self.manual.power_on.connect(self._on_manual_power_on)
        self.manual.power_off.connect(self._on_manual_power_off)
        return self.manual

    def _build_footer(self):
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet('color: #332c55;')

        footer = QLabel('Developed by Chemikl Project')
        footer.setProperty('role', 'footer')
        footer.setAlignment(Qt.AlignCenter)

        wrap = QWidget()
        wl = QVBoxLayout(wrap)
        wl.setContentsMargins(0, 6, 0, 0)
        wl.setSpacing(0)
        wl.addWidget(line)
        wl.addWidget(footer)
        return wrap

    # ------------------------------------------------------------ dispositivos

    def _reload_devices(self):
        self.device_list.blockSignals(True)
        self.device_list.clear()
        for d in self.cfg['devices']:
            item = QListWidgetItem(f"{d['name']}  [{d['type']}]")
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if d.get('enabled') else Qt.Unchecked)
            item.setData(Qt.UserRole, d['id'])
            self.device_list.addItem(item)
        self.device_list.blockSignals(False)

    def _on_device_checked(self, item):
        d = cfgmod.get_device(self.cfg, item.data(Qt.UserRole))
        if d:
            d['enabled'] = item.checkState() == Qt.Checked
            cfgmod.save(self.cfg)

    def _selected_device(self):
        item = self.device_list.currentItem()
        return cfgmod.get_device(self.cfg, item.data(Qt.UserRole)) if item else None

    def _add_device(self):
        dlg = DeviceDialog(self)
        if dlg.exec():
            self.cfg['devices'].append(dlg.device)
            cfgmod.save(self.cfg)
            self._reload_devices()

    def _edit_device(self):
        d = self._selected_device()
        if not d:
            QMessageBox.information(self, 'Elegi uno', 'Selecciona un dispositivo de la lista primero.')
            return
        dlg = DeviceDialog(self, device=d)
        if dlg.exec():
            cfgmod.save(self.cfg)
            self._drop_pooled(d['id'])   # la conexion vieja puede tener datos obsoletos
            self._reload_devices()

    def _delete_device(self):
        d = self._selected_device()
        if not d:
            return
        if QMessageBox.question(self, 'Confirmar', f"¿Quitar \"{d['name']}\"?") == QMessageBox.Yes:
            self.cfg['devices'] = [x for x in self.cfg['devices'] if x['id'] != d['id']]
            cfgmod.save(self.cfg)
            self._drop_pooled(d['id'])
            self._reload_devices()

    def _drop_pooled(self, device_id):
        out = self.output_pool.pop(device_id, None)
        if out:
            try:
                out.disconnect()
            except Exception:
                pass

    # ------------------------------------------------------------ conexiones

    def _connected_enabled_outputs(self):
        """Devuelve las salidas ya conectadas de cada dispositivo tildado,
        reusando el pool. Si alguna falla, avisa y sigue con las demas."""
        outs = []
        for d in cfgmod.enabled_devices(self.cfg):
            out = self.output_pool.get(d['id'])
            if out is None or not out.connected:
                try:
                    out = create_output(d)
                    out.connect()
                    self.output_pool[d['id']] = out
                except Exception as e:
                    QMessageBox.warning(self, 'Error de conexion', f"{d['name']}: {e}")
                    continue
            outs.append(out)
        return outs

    # ------------------------------------------------------------ modo automatico

    def toggle_engine(self):
        if self.engine.running:
            self.engine.stop()
            return

        outs = self._connected_enabled_outputs()
        if not outs:
            self.start_btn.setChecked(False)
            QMessageBox.warning(self, 'Sin dispositivos',
                                 'Tilda al menos un dispositivo de la lista para mandarle color.')
            return

        source_name = next(n for n, rb in self.source_radios.items() if rb.isChecked())
        try:
            src = create_source(source_name, self.cfg)
        except Exception as e:
            self.start_btn.setChecked(False)
            QMessageBox.critical(self, 'No se pudo iniciar', str(e))
            return

        try:
            self.engine.start(src, outs)
        except SpotifyNotConfigured:
            # En vez de solo avisar que falta configurar, se ofrece
            # hacerlo ahi mismo -- y si sale bien, reintenta iniciar solo.
            self.start_btn.setChecked(False)
            dlg = SpotifySetupDialog(self, self.cfg)
            if dlg.exec():
                self.toggle_engine()
        except Exception as e:
            # source.start() puede fallar aca (camara no disponible, etc.)
            # -- sin este try/except la excepcion quedaba en la consola y
            # la ventana no avisaba nada.
            self.start_btn.setChecked(False)
            QMessageBox.critical(self, 'No se pudo iniciar', str(e))

    def _notify_state_changed(self):
        self.state_changed.emit()   # cruza al hilo de la GUI (el motor corre en otro)

    def _refresh_status(self):
        running = self.engine.running
        self.start_btn.setChecked(running)
        self.start_btn.setText('Detener' if running else 'Iniciar')
        self.status_label.setText(
            f'Activo: {SOURCE_LABELS.get(self.engine.active_source_name, "?")}' if running else 'Detenido.'
        )
        self.manual.setEnabled(not running)

    # ------------------------------------------------------------ modo manual

    def _on_manual_color(self, r, g, b):
        for out in self._connected_enabled_outputs():
            out.set_color(r, g, b)

    def _on_manual_power_on(self):
        for out in self._connected_enabled_outputs():
            out.turn_on()

    def _on_manual_power_off(self):
        for out in self._connected_enabled_outputs():
            out.turn_off()

    # ------------------------------------------------------------ ventana

    def closeEvent(self, event):
        event.ignore()
        self.hide()
