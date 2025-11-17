from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QFrame,
    QSizePolicy
)
from PyQt6.QtCore import pyqtSignal, Qt


class Sidebar(QWidget):
    """
    Left navigation bar.
    Emits an index for the main stacked widget to switch panels.
    Index mapping:
      0 - Dashboard
      1 - Scanner
      2 - Findings
      3 - Killchain
      4 - Issues
      5 - AI Panel
      6 - Report Viewer
    """

    navigate = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("Sidebar")
        self.buttons = {}

        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        title = QLabel("AraUltra")
        title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #f5f5f5;")
        layout.addWidget(title)

        subtitle = QLabel("Recon Assistant")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        subtitle.setStyleSheet("font-size: 11px; color: #aaaaaa;")
        layout.addWidget(subtitle)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("color: #444444;")
        layout.addWidget(divider)

        # Buttons
        self._add_button(layout, "Dashboard", 0)
        self._add_button(layout, "Scanner", 1)
        self._add_button(layout, "Findings", 2)
        self._add_button(layout, "Killchain", 3)
        self._add_button(layout, "Issues", 4)
        self._add_button(layout, "AI Panel", 5)
        self._add_button(layout, "Reports", 6)

        layout.addStretch(1)

        footer = QLabel("v0.1 • Local")
        footer.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        footer.setStyleSheet("font-size: 10px; color: #777777;")
        layout.addWidget(footer)

        self.setLayout(layout)

        # Default selected
        self._set_active(0)

    def _add_button(self, layout, text: str, index: int):
        btn = QPushButton(text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        btn.setProperty("navIndex", index)
        btn.clicked.connect(lambda _, i=index: self.on_click(i))
        btn.setStyleSheet(self._button_style(inactive=True))
        layout.addWidget(btn)
        self.buttons[text] = btn

    def _button_style(self, inactive: bool = False, highlighted: bool = False) -> str:
        base = """
            QPushButton {{
                border: none;
                padding: 8px 12px;
                text-align: left;
                border-radius: 6px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: #333333;
            }}
        """
        if highlighted:
            base += "QPushButton { background-color: #444444; color: #ffffff; font-weight: bold; }"
        elif inactive:
            base += "QPushButton { background-color: transparent; color: #cccccc; }"
        else:
            base += "QPushButton { background-color: #2a2a2a; color: #ffffff; font-weight: bold; }"
        return base

    def _set_active(self, index: int):
        # reset all
        for text, btn in self.buttons.items():
            btn.setStyleSheet(self._button_style(inactive=True))

        # activate selected
        mapping = {
            0: "Dashboard",
            1: "Scanner",
            2: "Findings",
            3: "Killchain",
            4: "Issues",
            5: "AI Panel",
            6: "Reports"
        }
        label = mapping.get(index)
        if label and label in self.buttons:
            self.buttons[label].setStyleSheet(self._button_style(inactive=False))

    def on_click(self, index: int):
        self._set_active(index)
        self.navigate.emit(index)

    def flash_section(self, name: str):
        """
        Temporarily highlight a section button to indicate new activity.
        Name must be one of: "Dashboard", "Scanner", "Findings", "Killchain", "Issues", "AI Panel", "Reports"
        """
        btn = self.buttons.get(name)
        if not btn:
            return

        # Apply highlighted style briefly
        btn.setStyleSheet(self._button_style(highlighted=True))
        # Qt timers would be ideal for automatic reset; keeping it simple so we don't
        # introduce extra complexity here. The next navigation change will reset styles.