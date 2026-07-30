"""
Salida para tiras/barras LED genericas tipo "ELK-BLEDOB", controladas por
la app LotusLamp X -- asi vienen varias marcas de Amazon/AliExpress (entre
ellas NBBUFF, Ledagic y clones parecidos). A diferencia de Tuya/WLED/Hue,
esto NO tiene API publica ni documentacion oficial: el protocolo de abajo
sale de la ingenieria inversa que ya hizo un tercero para Home Assistant
(https://github.com/8none1/elk-bledob), no de un vendor.

Bluetooth LE, no WiFi -- se conecta por direccion MAC en vez de IP (ver
_scan() para descubrirla). bleak es asincronico; como el resto del
programa llama a estos metodos de forma sincronica (ver core/engine.py),
cada instancia levanta su propio hilo con un event loop de asyncio propio,
y cada llamada se puentea con run_coroutine_threadsafe().

Sin lectura de estado confiable: el dispositivo no confirma que un comando
le llego (notify no responde de forma consistente segun el proyecto de
referencia), asi que esto opera en modo optimista -- manda el comando y
asume que funciono. save_previous_state()/restore_previous_state() quedan
sin implementar (el default de OutputTarget) por lo mismo: no hay forma de
leer el estado antes de tocarlo.

*** NO PROBADO CONTRA HARDWARE REAL *** -- no hay uno de estos dispositivos
disponible para verificar esto, y encima el protocolo es de un tercero, no
del fabricante. Puede que tu unidad puntual varie (otro UUID, otro orden de
bytes, un byte de checksum distinto). Probalo y avisame que onda.
"""

import asyncio
import threading

from bleak import BleakClient, BleakScanner

from core.plugin_base import OutputTarget

WRITE_CHAR_UUID = '0000fff3-0000-1000-8000-00805f9b34fb'
CONNECT_TIMEOUT = 15
WRITE_TIMEOUT = 3


def _power_packet(on):
    return bytes.fromhex('7e 07 04 ff 00 01 02 01 ef') if on \
        else bytes.fromhex('7e 07 04 00 00 00 02 01 ef')


def _color_packet(r, g, b):
    rgb = bytes((round(r * 255), round(g * 255), round(b * 255)))
    return bytes.fromhex('7e 07 05 03') + rgb + bytes.fromhex('10 ef')


class ElkBledobOutput(OutputTarget):
    name = 'elk_bledob'
    display_name = 'ELK-BLEDOB / LotusLamp X (NBBUFF, Ledagic y clones) -- Bluetooth, NO PROBADO'

    def __init__(self, device_cfg):
        super().__init__(device_cfg)
        self._client = None
        self._loop = None
        self._thread = None

    # -------------------------------------------------------------- puente
    # bleak es async; todo lo demas del programa llama sincronico. Un hilo
    # dedicado con su propio loop, y run_coroutine_threadsafe() para cada
    # operacion, es el patron estandar para mezclar los dos mundos.

    def _ensure_loop(self):
        if self._loop:
            return
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._thread.start()

    def _run(self, coro, timeout):
        self._ensure_loop()
        fut = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return fut.result(timeout=timeout)

    # ------------------------------------------------------------- OutputTarget

    def connect(self):
        address = self.device_cfg['elk_bledob']['mac']
        self._ensure_loop()
        try:
            self._run(self._connect_async(address), CONNECT_TIMEOUT)
            self._connected = True
        except Exception:
            self._connected = False
            raise

    async def _connect_async(self, address):
        self._client = BleakClient(address)
        await self._client.connect()

    def disconnect(self):
        if self._client:
            try:
                self._run(self._client.disconnect(), 5)
            except Exception:
                pass
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)
        self._client = None
        self._loop = None
        self._thread = None
        self._connected = False

    def _write(self, data):
        if not self._client:
            return
        try:
            self._run(
                self._client.write_gatt_char(WRITE_CHAR_UUID, data, response=False),
                WRITE_TIMEOUT,
            )
        except Exception:
            pass   # modo optimista: un envio puntual que falla no se puede confirmar igual

    def set_color(self, r, g, b):
        self._write(_color_packet(r, g, b))

    def turn_on(self):
        self._write(_power_packet(True))

    def turn_off(self):
        self._write(_power_packet(False))

    def status_text(self):
        return ('conectado' if self._connected else 'sin conectar') + ' (no verificado)'


def scan(timeout=8):
    """
    Busca dispositivos BLE cercanos que se anuncien con nombre (no todos
    lo hacen). No filtra por "ELK-BLEDOB" especificamente porque los
    clones de distintas marcas capaz se anuncian con otro nombre -- se
    muestran todos y el usuario elige el que reconozca.

    Devuelve una lista de dicts: [{'name', 'address'}, ...]
    """
    async def _scan_async():
        devices = await BleakScanner.discover(timeout=timeout)
        return [{'name': d.name or '(sin nombre)', 'address': d.address} for d in devices]

    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_scan_async())
    finally:
        loop.close()
