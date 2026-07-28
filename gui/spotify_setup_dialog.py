"""
Configuracion de Spotify desde la propia app -- reemplaza tener que
correr spotify_auth_setup.py en una terminal aparte.

Mismo flujo OAuth de siempre (Spotify exige que el usuario autorice en su
navegador, eso no se puede saltear), pero integrado: abre el navegador,
levanta el servidor local que recibe la respuesta, y guarda todo en
config.json sin que el usuario tenga que tocar una consola.
"""

import http.server
import threading
import urllib.parse
import webbrowser

import requests
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout,
)

from core import config as cfgmod

REDIRECT_URI = 'http://127.0.0.1:8888/callback'
SCOPE = 'user-read-currently-playing user-read-playback-state'


class _CallbackHandler(http.server.BaseHTTPRequestHandler):
    result = {}

    def do_GET(self):
        qs = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(qs)
        if 'code' in params:
            _CallbackHandler.result['code'] = params['code'][0]
            body = '<html><body><h2>Listo, ya podes cerrar esta pestaña.</h2></body></html>'
        else:
            _CallbackHandler.result['error'] = params.get('error', ['desconocido'])[0]
            body = '<html><body><h2>No se pudo autorizar.</h2></body></html>'
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(body.encode('utf-8'))

    def log_message(self, *a):
        pass


class SpotifySetupDialog(QDialog):
    def __init__(self, parent, cfg):
        super().__init__(parent)
        self.cfg = cfg
        self.setWindowTitle('Configurar Spotify')
        self.setMinimumWidth(460)

        s = cfg.setdefault('capture', {}).setdefault('spotify', {})

        info = QLabel(
            '<b>Paso unico, despues queda guardado.</b><br><br>'
            '1) Entra a <a href="https://developer.spotify.com/dashboard">'
            'developer.spotify.com/dashboard</a> y crea una app (gratis, con '
            'tu cuenta normal de Spotify).<br>'
            '2) En "Redirect URIs" de esa app agregá <b>exactamente</b> esto:<br>'
            '<code>http://127.0.0.1:8888/callback</code><br>'
            '3) Pega el Client ID y el Client Secret aca abajo y apreta Autorizar.'
        )
        info.setWordWrap(True)
        info.setOpenExternalLinks(True)
        info.setTextFormat(Qt.RichText)

        self.client_id = QLineEdit(s.get('client_id', ''))
        self.client_secret = QLineEdit(s.get('client_secret', ''))
        self.client_secret.setEchoMode(QLineEdit.Password)

        form = QFormLayout()
        form.addRow(info)
        form.addRow('Client ID:', self.client_id)
        form.addRow('Client Secret:', self.client_secret)

        self.auth_btn = QPushButton('Autorizar con Spotify')
        self.auth_btn.setProperty('role', 'primary')
        self.auth_btn.clicked.connect(self._start_auth)

        self.status_lbl = QLabel('')
        self.status_lbl.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.auth_btn)
        layout.addWidget(self.status_lbl)

        self._server = None
        self._client_id = None
        self._client_secret = None
        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(200)
        self._poll_timer.timeout.connect(self._poll_result)

    def _start_auth(self):
        cid = self.client_id.text().strip()
        secret = self.client_secret.text().strip()
        if not cid or not secret:
            QMessageBox.warning(self, 'Faltan datos', 'Client ID y Client Secret son obligatorios.')
            return

        _CallbackHandler.result = {}
        try:
            self._server = http.server.HTTPServer(('127.0.0.1', 8888), _CallbackHandler)
        except OSError as e:
            QMessageBox.critical(
                self, 'No se pudo abrir el puerto 8888',
                f'{e}\n\n¿Hay otro programa usando ese puerto? Cerralo e intenta de nuevo.',
            )
            return
        threading.Thread(target=self._server.serve_forever, daemon=True).start()

        auth_url = 'https://accounts.spotify.com/authorize?' + urllib.parse.urlencode({
            'client_id': cid, 'response_type': 'code',
            'redirect_uri': REDIRECT_URI, 'scope': SCOPE,
        })
        webbrowser.open(auth_url)

        self._client_id, self._client_secret = cid, secret
        self.status_lbl.setText('Se abrio el navegador -- autoriza ahi. Esperando...')
        self.auth_btn.setEnabled(False)
        self._poll_timer.start()

    def _poll_result(self):
        if 'code' in _CallbackHandler.result:
            self._poll_timer.stop()
            self._server.shutdown()
            self._exchange_token(_CallbackHandler.result['code'])
        elif 'error' in _CallbackHandler.result:
            self._poll_timer.stop()
            self._server.shutdown()
            self.status_lbl.setText(f"Spotify devolvio un error: {_CallbackHandler.result['error']}")
            self.auth_btn.setEnabled(True)

    def _exchange_token(self, code):
        try:
            r = requests.post('https://accounts.spotify.com/api/token', data={
                'grant_type': 'authorization_code', 'code': code,
                'redirect_uri': REDIRECT_URI,
                'client_id': self._client_id, 'client_secret': self._client_secret,
            }, timeout=10)
            r.raise_for_status()
            tokens = r.json()
        except Exception as e:
            self.status_lbl.setText(f'No se pudo obtener el token: {e}')
            self.auth_btn.setEnabled(True)
            return

        s = self.cfg['capture']['spotify']
        s['client_id'] = self._client_id
        s['client_secret'] = self._client_secret
        s['refresh_token'] = tokens['refresh_token']
        cfgmod.save(self.cfg)

        self.status_lbl.setText('Listo. Spotify configurado.')
        self.accept()

    def closeEvent(self, event):
        self._poll_timer.stop()
        if self._server:
            try:
                self._server.shutdown()
            except Exception:
                pass
        super().closeEvent(event)
