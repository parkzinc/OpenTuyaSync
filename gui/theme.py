"""
Tema visual: cyberpunk oscuro. Fondo casi negro con violeta, acentos
neon (magenta + cian) para botones, bordes y estados activos. Todo via
QSS -- sin imagenes, asi el .exe no crece y es facil de retocar.

Se mantiene la barra de titulo nativa de Windows a proposito: una barra
de titulo propia (sin marco) necesita reimplementar arrastre, resize y
snap a mano, que es fragil. El QSS de aca cubre todo el CONTENIDO de la
ventana, que es donde se nota el 95% del cambio visual.
"""

BG = '#0c0a17'
PANEL = '#17142a'
PANEL_ALT = '#1e1a35'
BORDER = '#332c55'
TEXT = '#e9e6f7'
DIM = '#8b84b3'
MAGENTA = '#ff2ec4'
CYAN = '#00e5ff'
PURPLE = '#9b5cf6'

STYLESHEET = f"""
QMainWindow, QWidget {{
    background-color: {BG};
    color: {TEXT};
    font-family: 'Segoe UI', 'Consolas', sans-serif;
    font-size: 13px;
}}

QLabel[role="heading"] {{
    color: {CYAN};
    font-weight: 700;
    font-size: 13px;
    letter-spacing: 1px;
    text-transform: uppercase;
    padding-bottom: 2px;
}}

QLabel[role="footer"] {{
    color: {DIM};
    font-size: 11px;
    padding: 6px;
}}

QGroupBox {{
    background-color: {PANEL};
    border: 1px solid {BORDER};
    border-radius: 10px;
    margin-top: 6px;
    padding: 10px 8px 8px 8px;
}}

QTabWidget::pane {{
    border: 1px solid {BORDER};
    border-radius: 10px;
    background-color: {PANEL};
    top: -1px;
}}
QTabBar::tab {{
    background-color: {BG};
    color: {DIM};
    border: 1px solid {BORDER};
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: 7px 16px;
    margin-right: 2px;
}}
QTabBar::tab:selected {{
    background-color: {PANEL};
    color: {MAGENTA};
    font-weight: 600;
}}
QTabBar::tab:hover:!selected {{
    color: {TEXT};
}}

QListWidget {{
    background-color: {PANEL_ALT};
    border: 1px solid {BORDER};
    border-radius: 10px;
    padding: 4px;
    outline: none;
}}
QListWidget::item {{
    padding: 7px 6px;
    border-radius: 6px;
    margin: 2px 0;
    color: {TEXT};
}}
QListWidget::item:selected {{
    background-color: {MAGENTA};
    color: #1a0316;
}}
QListWidget::item:hover:!selected {{
    background-color: #2a2447;
}}

QPushButton {{
    background-color: {PANEL_ALT};
    color: {CYAN};
    border: 1.5px solid {CYAN};
    border-radius: 8px;
    padding: 7px 14px;
    font-weight: 600;
}}
QPushButton:hover {{
    background-color: {CYAN};
    color: #001b22;
}}
QPushButton:pressed {{
    background-color: #00a8c2;
    border-color: #00a8c2;
}}
QPushButton:disabled {{
    color: #4a4568;
    border-color: #2a2547;
    background-color: {PANEL};
}}

QPushButton[role="primary"] {{
    background-color: {MAGENTA};
    color: #1a0316;
    border: 1.5px solid {MAGENTA};
    font-size: 14px;
    padding: 10px;
}}
QPushButton[role="primary"]:hover {{
    background-color: #ff5cd6;
    border-color: #ff5cd6;
}}
QPushButton[role="primary"]:checked {{
    background-color: {CYAN};
    border-color: {CYAN};
    color: #001b22;
}}

QPushButton[role="swatch"] {{
    border-radius: 8px;
    border: 2px solid {BORDER};
}}

QRadioButton, QCheckBox {{
    padding: 4px 2px;
    spacing: 8px;
    color: {TEXT};
}}
QRadioButton::indicator, QCheckBox::indicator {{
    width: 15px;
    height: 15px;
    border-radius: 8px;
    border: 2px solid {PURPLE};
    background-color: {PANEL_ALT};
}}
QRadioButton::indicator:checked {{
    background-color: {MAGENTA};
    border-color: {MAGENTA};
}}
QCheckBox::indicator {{
    border-radius: 4px;
}}
QCheckBox::indicator:checked {{
    background-color: {CYAN};
    border-color: {CYAN};
}}

QSlider::groove:horizontal {{
    height: 6px;
    background: {PANEL_ALT};
    border: 1px solid {BORDER};
    border-radius: 3px;
}}
QSlider::sub-page:horizontal {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {CYAN}, stop:1 {MAGENTA});
    border-radius: 3px;
}}
QSlider::handle:horizontal {{
    width: 18px;
    height: 18px;
    margin: -7px 0;
    border-radius: 9px;
    background: {TEXT};
    border: 3px solid {MAGENTA};
}}
QSlider::handle:horizontal:hover {{
    border-color: {CYAN};
}}

QComboBox, QLineEdit {{
    background-color: {PANEL_ALT};
    border: 1.5px solid {BORDER};
    border-radius: 6px;
    padding: 5px 8px;
    color: {TEXT};
    selection-background-color: {MAGENTA};
}}
QComboBox:focus, QLineEdit:focus {{
    border-color: {MAGENTA};
}}
QComboBox::drop-down {{
    border: none;
    width: 20px;
}}
QComboBox QAbstractItemView {{
    background-color: {PANEL_ALT};
    color: {TEXT};
    selection-background-color: {MAGENTA};
    border: 1px solid {BORDER};
}}

QScrollBar:vertical {{
    background: transparent;
    width: 10px;
}}
QScrollBar::handle:vertical {{
    background: {BORDER};
    border-radius: 5px;
    min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{
    background: {MAGENTA};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QMessageBox {{
    background-color: {PANEL};
}}

QToolTip {{
    background-color: {PANEL_ALT};
    color: {TEXT};
    border: 1px solid {MAGENTA};
    padding: 4px;
}}
"""
