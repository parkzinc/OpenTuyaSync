"""
Interfaces base del sistema de plugins.

Una CaptureSource produce color (mira la pantalla, escucha audio, lee una
tapa de disco, lo que sea). Un OutputTarget lo manda a un dispositivo real
(Tuya, WLED, Hue). El Engine conecta una fuente activa con los targets
activos -- ninguno de los dos lados sabe nada del otro, por eso se pueden
combinar libremente (ambilight -> Tuya + WLED al mismo tiempo, por ejemplo).

Todas las fuentes corren su propio trabajo en un hilo de fondo y exponen
get_color() como algo que NUNCA bloquea -- devuelve lo ultimo que se
calculo, o None si todavia no hay nada. Esto es asi a proposito: mezclar
la lectura de la fuente (captura de pantalla, audio) con el envio de red
al dispositivo en el mismo loop fue lo que causaba cortes de audio reales
al construir el modo musica -- ver music.py del proyecto anterior. Separar
siempre evita ese problema de raiz, para cualquier fuente futura.
"""

from abc import ABC, abstractmethod


class CaptureSource(ABC):
    """
    name: nombre corto para mostrar en la UI.
    display_name: nombre largo, legible.
    """
    name = 'base'
    display_name = 'Fuente base'

    def __init__(self, cfg=None):
        self.cfg = cfg or {}
        self._running = False

    @abstractmethod
    def start(self):
        """Arranca la captura (tipicamente un hilo de fondo). No bloquea."""
        raise NotImplementedError

    @abstractmethod
    def stop(self):
        """Para la captura y libera lo que haya que liberar."""
        raise NotImplementedError

    @abstractmethod
    def get_color(self):
        """
        Devuelve (r, g, b) en 0-1, o None si todavia no hay nada que
        mostrar. Nunca bloquea.
        """
        raise NotImplementedError

    @property
    def running(self):
        return self._running


class OutputTarget(ABC):
    """
    name: identificador corto (usado en config.json para saber que tipo de
    dispositivo es cada entrada).
    display_name: nombre largo, legible, para la UI.
    """
    name = 'base'
    display_name = 'Salida base'

    def __init__(self, device_cfg):
        """device_cfg: el diccionario de ESTE dispositivo en particular
        (ver core/config.py), no la config global."""
        self.device_cfg = device_cfg
        self._connected = False

    @abstractmethod
    def connect(self):
        raise NotImplementedError

    @abstractmethod
    def disconnect(self):
        raise NotImplementedError

    @abstractmethod
    def set_color(self, r, g, b):
        """r,g,b en 0-1. Se llama seguido -- tiene que ser rapido y no
        tirar excepciones si falla un envio puntual (loguear y seguir)."""
        raise NotImplementedError

    @abstractmethod
    def turn_on(self):
        raise NotImplementedError

    @abstractmethod
    def turn_off(self):
        raise NotImplementedError

    def status_text(self):
        """Texto corto para mostrar en la UI. Opcional, por defecto generico."""
        return 'conectado' if self._connected else 'desconectado'

    def save_previous_state(self):
        """Opcional: guarda el estado actual para poder volver a el
        despues (por ejemplo, el modo escena de Tuya). Sin implementar
        por defecto -- no todos los dispositivos tienen algo asi."""
        pass

    def restore_previous_state(self):
        """Complemento de save_previous_state()."""
        pass

    @property
    def connected(self):
        return self._connected
