"""
Registro de tipos de salida disponibles. Agregar una marca nueva es
agregar una linea aca (y el archivo output_*.py correspondiente) -- nada
mas del programa necesita saber que existe.
"""

from outputs.elk_bledob_output import ElkBledobOutput
from outputs.hue_output import HueOutput
from outputs.tuya_output import TuyaOutput
from outputs.wled_output import WledOutput

OUTPUT_TYPES = {
    TuyaOutput.name: TuyaOutput,
    WledOutput.name: WledOutput,
    HueOutput.name: HueOutput,
    ElkBledobOutput.name: ElkBledobOutput,
}


def create_output(device_cfg):
    cls = OUTPUT_TYPES.get(device_cfg['type'])
    if cls is None:
        raise ValueError(f"Tipo de dispositivo desconocido: {device_cfg['type']!r}")
    return cls(device_cfg)
