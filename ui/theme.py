from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import Qt


def apply_theme(widget: QWidget):
    """
    Apply a dark theme to the entire application and some base styles.
    """

    app = QApplication.instance()
    if not app:
        return

    palette = QPalette()

    # Window
    palette.setColor(QPalette.ColorRole.Window, QColor("#181818"))
    palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)

    # Base
    palette.setColor(QPalette.ColorRole.Base, QColor("#202020"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#252525"))
    palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)

    # Text
    palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Button, QColor("#202020"))
    palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)

    # Links
    palette.setColor(QPalette.ColorRole.Link, QColor("#2f81f7"))

    # Highlights
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#2f81f7"))
    palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)

    app.setPalette(palette)

    # Global stylesheet
    app.setStyleSheet("""
        QMainWindow {
            background-color: #181818;
        }
        QWidget {
            color: #e0e0e0;
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", sans-serif;
            font-size: 13px;
        }
        QFrame#Card {
            background-color: #202020;
            border-radius: 10px;
            border: 1px solid #333333;
        }
        QLineEdit, QPlainTextEdit, QTextEdit, QComboBox {
            background-color: #202020;
            border: 1px solid #333333;
            border-radius: 6px;
            padding: 6px;
            selection-background-color: #2f81f7;
            selection-color: #ffffff;
        }
        QPushButton {
            background-color: #2f81f7;
            border-radius: 6px;
            padding: 6px 12px;
            color: #ffffff;
            font-weight: 500;
        }
        QPushButton:hover {
            background-color: #3b8eff;
        }
        QPushButton:disabled {
            background-color: #444444;
            color: #888888;
        }
        QTableWidget {
            background-color: #181818;
            gridline-color: #333333;
        }
        QHeaderView::section {
            background-color: #202020;
            padding: 4px;
            border: 1px solid #333333;
        }
        QStatusBar {
            background-color: #181818;
        }
    """)