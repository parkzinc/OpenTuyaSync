"""Dialogo para agregar/editar un dispositivo.

Para Tuya hay un boton de "Escanear red" que completa Device ID, IP y
Version solo (usa outputs/tuya_scan.py). La Clave Local sigue siendo
manual a proposito: el protocolo de Tuya no la deja ver por la red sin
conocerla de antes, asi que ni un sniffer real la consigue -- solo la
API de nube de Tuya podria, y en este proyecto se decidio no usarla.

WLED: solo la IP. Hue: flujo de emparejamiento con el boton fisico del
Bridge."""

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QComboBox, QDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPushButton, QStackedWidget, QVBoxLayout, QWidget,
)

from core import config as cfgmod
from outputs import hue_output


class _ScanThread(QThread):
    finished_scan = Signal(list)
    failed = Signal(str)

    def run(self):
        try:
            from outputs.tuya_scan import scan
            self.finished_scan.emit(scan())
        except Exception as e:
            self.failed.emit(str(e))


class DeviceDialog(QDialog):
    def __init__(self, parent=None, device=None):
        super().__init__(parent)
        self.setWindowTitle('Editar dispositivo' if device else 'Agregar dispositivo')
        self.setMinimumWidth(440)
        self.device = device if device is not None else {
            'id': cfgmod.new_device_id(), 'type': 'tuya', 'enabled': True,
        }
        self._scan_thread = None
        self._found_devices = []

        self.name_edit = QLineEdit(self.device.get('name', ''))

        self.type_combo = QComboBox()
        self.type_combo.addItem('Tuya / Smart Life (LSC, Nedis, Mirabella, Treatlife...)', 'tuya')
        self.type_combo.addItem('WLED', 'wled')
        self.type_combo.addItem('Philips Hue', 'hue')
        idx = self.type_combo.findData(self.device.get('type', 'tuya'))
        if idx >= 0:
            self.type_combo.setCurrentIndex(idx)

        self.tuya_page = self._build_tuya_page()
        self.wled_page = self._build_wled_page()
        self.hue_page = self._build_hue_page()

        self.stack = QStackedWidget()
        self.stack.addWidget(self.tuya_page)
        self.stack.addWidget(self.wled_page)
        self.stack.addWidget(self.hue_page)
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)

        form = QFormLayout()
        form.addRow('Nombre:', self.name_edit)
        form.addRow('Tipo:', self.type_combo)

        ok_btn = QPushButton('Guardar')
        cancel_btn = QPushButton('Cancelar')
        ok_btn.clicked.connect(self._on_save)
        cancel_btn.clicked.connect(self.reject)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(ok_btn)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.stack)
        layout.addLayout(btn_row)

        self._on_type_changed()

    def _hint(self, text):
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setStyleSheet('color: #8b84b3; font-size: 11px;')
        return lbl

    def _build_tuya_page(self):
        w = QWidget()
        f = QFormLayout(w)

        self.scan_btn = QPushButton('🔍 Escanear red')
        self.scan_btn.clicked.connect(self._start_scan)
        self.scan_status = QLabel('')
        self.scan_status.setWordWrap(True)
        self.scan_results = QComboBox()
        self.scan_results.setVisible(False)
        self.scan_results.currentIndexChanged.connect(self._apply_scan_selection)
        f.addRow(self.scan_btn)
        f.addRow(self.scan_status)
        f.addRow('Encontrados:', self.scan_results)

        t = self.device.get('tuya', {})
        self.tuya_devid = QLineEdit(t.get('dev_id', ''))
        self.tuya_ip = QLineEdit(t.get('ip', ''))
        self.tuya_key = QLineEdit(t.get('local_key', ''))
        self.tuya_version = QComboBox()
        self.tuya_version.addItems(['3.1', '3.2', '3.3', '3.4', '3.5'])
        self.tuya_version.setCurrentText(str(t.get('version', 3.5)))
        f.addRow('Device ID:', self.tuya_devid)
        f.addRow('IP:', self.tuya_ip)
        f.addRow('Clave Local:', self.tuya_key)
        f.addRow('Version:', self.tuya_version)
        f.addRow(self._hint(
            'El escaneo completa Device ID, IP y Version solo. La Clave Local '
            'NO se puede sacar de la red -- Tuya la genera del lado de su nube '
            'al emparejar y nunca viaja de forma escuchable. Sacala de la app '
            'Smart Life (Configuracion del dispositivo → Info del dispositivo). '
            'Mismo protocolo para LSC Smart Connect, Nedis SmartLife, Mirabella '
            'Genio y Treatlife.'
        ))
        return w

    def _start_scan(self):
        self.scan_btn.setEnabled(False)
        self.scan_status.setText('Buscando en la red local... (10-20 segundos)')
        self.scan_results.setVisible(False)
        self._scan_thread = _ScanThread()
        self._scan_thread.finished_scan.connect(self._on_scan_done)
        self._scan_thread.failed.connect(self._on_scan_failed)
        self._scan_thread.start()

    def _on_scan_done(self, devices):
        self.scan_btn.setEnabled(True)
        self._found_devices = devices
        if not devices:
            self.scan_status.setText('No se encontro ningun dispositivo Tuya en la red.')
            return
        self.scan_status.setText(f'{len(devices)} encontrado(s). Elegi uno para completar los datos:')
        self.scan_results.clear()
        for d in devices:
            self.scan_results.addItem(f"{d['ip']}  ·  {d['dev_id']}  ·  v{d['version']}")
        self.scan_results.setVisible(True)

    def _on_scan_failed(self, msg):
        self.scan_btn.setEnabled(True)
        self.scan_status.setText(f'No se pudo escanear: {msg}')

    def _apply_scan_selection(self, idx):
        if 0 <= idx < len(self._found_devices):
            d = self._found_devices[idx]
            self.tuya_devid.setText(d['dev_id'])
            self.tuya_ip.setText(d['ip'])
            self.tuya_version.setCurrentText(str(d['version']))

    def _build_wled_page(self):
        w = QWidget()
        f = QFormLayout(w)
        wl = self.device.get('wled', {})
        self.wled_ip = QLineEdit(wl.get('ip', ''))
        f.addRow('IP:', self.wled_ip)
        f.addRow(self._hint('NO PROBADO contra hardware real todavia.'))
        return w

    def _build_hue_page(self):
        w = QWidget()
        f = QFormLayout(w)
        h = self.device.get('hue', {})
        self.hue_bridge = QLineEdit(h.get('bridge_ip', ''))
        self.hue_username = QLineEdit(h.get('username', ''))
        self.hue_username.setReadOnly(True)
        self.hue_light = QLineEdit(h.get('light_id', ''))
        pair_btn = QPushButton('Emparejar (apreta el boton del Bridge y despues esto)')
        pair_btn.clicked.connect(self._pair_hue)
        f.addRow('IP del Bridge:', self.hue_bridge)
        f.addRow('', pair_btn)
        f.addRow('Usuario:', self.hue_username)
        f.addRow('ID de la luz:', self.hue_light)
        f.addRow(self._hint('NO PROBADO contra hardware real todavia.'))
        return w

    def _pair_hue(self):
        ip = self.hue_bridge.text().strip()
        if not ip:
            QMessageBox.warning(self, 'Falta la IP', 'Escribi la IP del Bridge primero.')
            return
        try:
            username = hue_output.pair(ip)
            self.hue_username.setText(username)
            QMessageBox.information(self, 'Listo', 'Emparejado correctamente.')
        except Exception as e:
            QMessageBox.critical(self, 'No se pudo emparejar', str(e))

    def _on_type_changed(self):
        page = {'tuya': self.tuya_page, 'wled': self.wled_page, 'hue': self.hue_page}[self.type_combo.currentData()]
        self.stack.setCurrentWidget(page)

    def _on_save(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, 'Falta el nombre', 'Ponele un nombre al dispositivo.')
            return

        t = self.type_combo.currentData()
        self.device['name'] = name
        self.device['type'] = t
        self.device.setdefault('enabled', True)

        if t == 'tuya':
            if not (self.tuya_devid.text().strip() and self.tuya_ip.text().strip() and self.tuya_key.text().strip()):
                QMessageBox.warning(self, 'Faltan datos', 'Device ID, IP y Clave Local son obligatorios.')
                return
            self.device['tuya'] = {
                'dev_id': self.tuya_devid.text().strip(),
                'ip': self.tuya_ip.text().strip(),
                'local_key': self.tuya_key.text().strip(),
                'version': float(self.tuya_version.currentText()),
            }
        elif t == 'wled':
            if not self.wled_ip.text().strip():
                QMessageBox.warning(self, 'Falta la IP', 'La IP es obligatoria.')
                return
            self.device['wled'] = {'ip': self.wled_ip.text().strip()}
        elif t == 'hue':
            if not (self.hue_bridge.text().strip() and self.hue_username.text().strip() and self.hue_light.text().strip()):
                QMessageBox.warning(self, 'Faltan datos', 'Bridge, usuario (emparejar primero) y luz son obligatorios.')
                return
            self.device['hue'] = {
                'bridge_ip': self.hue_bridge.text().strip(),
                'username': self.hue_username.text().strip(),
                'light_id': self.hue_light.text().strip(),
            }

        self.accept()

    def closeEvent(self, event):
        if self._scan_thread and self._scan_thread.isRunning():
            self._scan_thread.terminate()
            self._scan_thread.wait(1000)
        super().closeEvent(event)
