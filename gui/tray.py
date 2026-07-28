"""Icono de bandeja del sistema -- queda al lado del reloj, como Hue,
Philips o cualquier app de este estilo. Clic simple/doble abre la
ventana; el menu contextual tiene iniciar/detener y salir."""

from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon


class Tray(QSystemTrayIcon):
    def __init__(self, window, icon_path):
        super().__init__(QIcon(str(icon_path)))
        self.window = window
        self.setToolTip('OpenTuya Sync')

        menu = QMenu()
        open_action = QAction('Abrir', self)
        open_action.triggered.connect(self._show_window)
        self.toggle_action = QAction('Iniciar', self)
        self.toggle_action.triggered.connect(self.window.toggle_engine)
        quit_action = QAction('Salir', self)
        quit_action.triggered.connect(self._quit)

        menu.addAction(open_action)
        menu.addAction(self.toggle_action)
        menu.addSeparator()
        menu.addAction(quit_action)
        self.setContextMenu(menu)

        self.activated.connect(self._on_activated)
        window.state_changed.connect(self._refresh)
        self._refresh()
        self.show()

    def _on_activated(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self._show_window()

    def _show_window(self):
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()

    def _refresh(self):
        self.toggle_action.setText('Detener' if self.window.engine.running else 'Iniciar')

    def _quit(self):
        if self.window.engine.running:
            self.window.engine.stop()
        QApplication.quit()
