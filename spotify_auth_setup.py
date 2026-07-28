"""
Configuracion de Spotify para el modo "color de la tapa" -- se corre UNA
sola vez.

Antes de correr esto:
  1. Anda a https://developer.spotify.com/dashboard y creá una app (gratis,
     con tu cuenta de Spotify normal).
  2. En la configuracion de la app, "Redirect URIs", agregá exactamente:
         http://127.0.0.1:8888/callback
  3. Copiá el Client ID y el Client Secret que te muestra el dashboard.

Despues corré:
    python spotify_auth_setup.py

Te va a pedir esos dos datos, abrir el navegador para que autorices con tu
cuenta, y guardar todo en config.json solo. No hace falta volver a
correrlo salvo que quites el permiso desde tu cuenta de Spotify.
"""

import http.server
import sys
import threading
import time
import urllib.parse
import webbrowser

import requests

sys.path.insert(0, '.')
from core import config

REDIRECT_URI = 'http://127.0.0.1:8888/callback'
SCOPE = 'user-read-currently-playing user-read-playback-state'

_result = {}


class _CallbackHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        qs = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(qs)
        if 'code' in params:
            _result['code'] = params['code'][0]
            body = '<html><body><h2>Listo, ya podes cerrar esta pestaña.</h2></body></html>'
        else:
            _result['error'] = params.get('error', ['desconocido'])[0]
            body = '<html><body><h2>No se pudo autorizar.</h2></body></html>'
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(body.encode('utf-8'))

    def log_message(self, *args):
        pass


def main():
    print(__doc__)
    client_id = input('Client ID: ').strip()
    client_secret = input('Client Secret: ').strip()
    if not client_id or not client_secret:
        sys.exit('Hacen falta los dos.')

    server = http.server.HTTPServer(('127.0.0.1', 8888), _CallbackHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    auth_url = 'https://accounts.spotify.com/authorize?' + urllib.parse.urlencode({
        'client_id': client_id,
        'response_type': 'code',
        'redirect_uri': REDIRECT_URI,
        'scope': SCOPE,
    })
    print(f'\nAbriendo el navegador para autorizar...')
    print(f'Si no se abre solo, pega esto: {auth_url}\n')
    webbrowser.open(auth_url)

    print('Esperando que autorices en el navegador (Ctrl+C para cancelar)...')
    try:
        while 'code' not in _result and 'error' not in _result:
            time.sleep(0.1)
    except KeyboardInterrupt:
        server.shutdown()
        sys.exit('\nCancelado.')
    server.shutdown()

    if 'error' in _result:
        sys.exit(f"Spotify devolvio un error: {_result['error']}")

    r = requests.post('https://accounts.spotify.com/api/token', data={
        'grant_type': 'authorization_code',
        'code': _result['code'],
        'redirect_uri': REDIRECT_URI,
        'client_id': client_id,
        'client_secret': client_secret,
    })
    r.raise_for_status()
    tokens = r.json()

    cfg = config.load()
    cfg['capture']['spotify']['client_id'] = client_id
    cfg['capture']['spotify']['client_secret'] = client_secret
    cfg['capture']['spotify']['refresh_token'] = tokens['refresh_token']
    config.save(cfg)

    print('\nListo. Guardado en config.json -- ya podes usar el modo Spotify.')


if __name__ == '__main__':
    main()
