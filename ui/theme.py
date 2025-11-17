# ui/theme.py
# Global Dark Theme Styling for AraUltra

from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import Qt

def apply_dark_theme(app):
    palette = QPalette()

    # Base colors
    palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30))
    palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Base, QColor(20, 20, 20))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(35, 35, 35))
    palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Button, QColor(45, 45, 45))
    palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Highlight, QColor(75, 110, 175))
    palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)

    app.setPalette(palette)

    # Additional styling
    app.setStyleSheet("""
        QWidget {
            font-family: 'Inter', 'Menlo', 'Consolas', monospace;
            font-size: 14px;
            color: #ffffff;
        }

        QFrame#sidebar {
            background-color: #1e1e1e;
            border-right: 1px solid #333;
        }

        QPushButton {
            background: #252526;
            padding: 8px 14px;
            border-radius: 6px;
            color: #c8c8c8;
        }
        QPushButton:hover {
            background: #333333;
            color: white;
        }
        QPushButton:pressed {
            background: #444444;
        }

        QLineEdit, QTextEdit, QPlainTextEdit {
            background: #1e1e1e;
            border: 1px solid #333333;
            padding: 6px;
            border-radius: 4px;
        }

        QListWidget, QTableWidget, QTreeWidget {
            background: #1a1a1a;
            border: 1px solid #2a2a2a;
        }

        QTabBar::tab {
            background: #1e1e1e;
            padding: 8px 16px;
            border: 1px solid #333;
            border-bottom: none;
        }
        QTabBar::tab:selected {
            background: #2d2d2d;
        }
    """)