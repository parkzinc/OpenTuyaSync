"""
Escaneo de red para Tuya. Encuentra Device ID, IP y version de los
dispositivos en la LAN -- pero NO la Clave Local.

Eso no es una limitacion de esta funcion: el protocolo de Tuya genera la
clave del lado de la nube al emparejar el dispositivo y nunca la manda
por la red de forma escuchable sin conocerla de antes. Confirmado en la
practica -- el campo 'key' que devuelve el escaneo siempre llega vacio
para dispositivos ya emparejados. La unica forma de conseguirla sin la
app Smart Life es la API de nube de Tuya (developer account), que en
este proyecto se decidio no usar.
"""

import tinytuya


def scan(retries=None):
    """
    Tarda entre 10 y 20 segundos (tinytuya escucha broadcasts UDP en la
    red). Llamar desde un hilo aparte, no desde el hilo de la GUI.

    Devuelve una lista de dicts: [{'dev_id', 'ip', 'version'}, ...]
    """
    raw = tinytuya.deviceScan(verbose=False, maxretry=retries)
    out = []
    for ip, info in raw.items():
        out.append({
            'dev_id': info.get('gwId') or info.get('id', ''),
            'ip': ip,
            'version': float(info.get('version', 3.3) or 3.3),
        })
    return out
