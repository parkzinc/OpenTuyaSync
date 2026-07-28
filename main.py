"""
OpenTuya Sync -- punto de entrada.

Uso: python main.py
"""

import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

APP_DIR = Path(__file__).parent
sys.path.insert(0, str(APP_DIR))

from core import config as cfgmod
from gui import theme
from gui.main_window import MainWindow
from gui.tray import Tray

# Empaquetado con PyInstaller, los datos (--add-data) quedan en
# sys._MEIPASS, no al lado de main.py -- Path(__file__).parent apuntaba
# a un lugar que no existe dentro del .exe, por eso el icono no se veia.
BASE_DIR = Path(getattr(sys, '_MEIPASS', APP_DIR))
ICON = BASE_DIR / 'assets' / 'icon.ico'


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)   # se queda vivo en la bandeja al cerrar la ventana
    app.setStyleSheet(theme.STYLESHEET)
    # Sin esto, la barra de titulo y la barra de tareas de Windows usan un
    # icono generico -- el --icon de PyInstaller solo cubre el icono del
    # archivo .exe (el que se ve en el Explorador), no el de la ventana
    # en ejecucion. Hay que setearlo tambien aca.
    app.setWindowIcon(QIcon(str(ICON)))

    window = MainWindow()
    tray = Tray(window, ICON)   # noqa: F841 -- referencia viva, si se pierde el icono desaparece

    cfg = cfgmod.load()
    if not cfg.get('start_minimized'):
        window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
