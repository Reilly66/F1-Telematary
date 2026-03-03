import sys
import matplotlib
matplotlib.use("QtAgg")

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import Qt

from utils.cache_manager import enable_cache
from gui.main_window import MainWindow


APP_STYLESHEET = """
QMainWindow, QWidget {
    background-color: #1a1a1a;
    color: #cccccc;
    font-family: -apple-system, "Segoe UI", Arial, sans-serif;
}
QMenuBar {
    background-color: #111;
    color: #ccc;
    border-bottom: 1px solid #333;
}
QMenuBar::item:selected { background: #2a2a2a; }
QMenu {
    background-color: #1e1e1e;
    color: #ccc;
    border: 1px solid #444;
}
QMenu::item:selected { background: #333; }
QGroupBox {
    border: 1px solid #3a3a3a;
    border-radius: 4px;
    margin-top: 10px;
    padding-top: 6px;
    color: #aaa;
    font-weight: bold;
    font-size: 10px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 4px;
}
QComboBox, QSpinBox {
    background-color: #252525;
    border: 1px solid #3a3a3a;
    border-radius: 3px;
    color: #ccc;
    padding: 3px 6px;
    min-height: 24px;
    selection-background-color: #E8002D;
}
QComboBox:focus, QSpinBox:focus { border-color: #E8002D; }
QComboBox::drop-down { border: none; subcontrol-origin: padding; width: 18px; }
QComboBox QAbstractItemView {
    background: #252525;
    border: 1px solid #444;
    color: #ccc;
    selection-background-color: #E8002D;
}
QPushButton {
    background-color: #2a2a2a;
    border: 1px solid #3a3a3a;
    border-radius: 4px;
    color: #ccc;
    padding: 5px 10px;
    font-size: 11px;
    min-height: 26px;
}
QPushButton:hover { background: #333; border-color: #555; }
QPushButton:disabled { color: #555; border-color: #2a2a2a; }
QPushButton#compare_btn {
    background-color: #E8002D;
    color: white;
    border: none;
    font-weight: bold;
    font-size: 12px;
    min-height: 32px;
}
QPushButton#compare_btn:hover { background-color: #ff1a3e; }
QPushButton#compare_btn:disabled { background-color: #5a0010; color: #888; }
QPushButton#load_btn {
    background-color: #1e3a5f;
    color: #7ab8f5;
    border-color: #2a5a8f;
}
QPushButton#load_btn:hover { background-color: #254a72; }
QProgressBar {
    border: none;
    background-color: #2a2a2a;
    border-radius: 2px;
}
QProgressBar::chunk { background-color: #E8002D; border-radius: 2px; }
QScrollArea { border: none; }
QScrollBar:vertical {
    background: #1a1a1a; width: 8px; margin: 0;
}
QScrollBar::handle:vertical { background: #444; border-radius: 4px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QLabel { color: #aaa; }
QSplitter::handle { background: #333; }
"""


def main():
    enable_cache()

    app = QApplication(sys.argv)
    app.setApplicationName("F1 Telemetry")
    app.setStyleSheet(APP_STYLESHEET)

    # Force dark palette so native widgets inherit it
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window,          QColor("#1a1a1a"))
    palette.setColor(QPalette.ColorRole.WindowText,      QColor("#cccccc"))
    palette.setColor(QPalette.ColorRole.Base,            QColor("#252525"))
    palette.setColor(QPalette.ColorRole.AlternateBase,   QColor("#2a2a2a"))
    palette.setColor(QPalette.ColorRole.ToolTipBase,     QColor("#1e1e1e"))
    palette.setColor(QPalette.ColorRole.ToolTipText,     QColor("#cccccc"))
    palette.setColor(QPalette.ColorRole.Text,            QColor("#cccccc"))
    palette.setColor(QPalette.ColorRole.Button,          QColor("#2a2a2a"))
    palette.setColor(QPalette.ColorRole.ButtonText,      QColor("#cccccc"))
    palette.setColor(QPalette.ColorRole.BrightText,      QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.Link,            QColor("#E8002D"))
    palette.setColor(QPalette.ColorRole.Highlight,       QColor("#E8002D"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
