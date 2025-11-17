# ui/sidebar.py
# Navigation panel for AraUltra

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QFrame
from PyQt6.QtCore import Qt

class SideBar(QFrame):
    def __init__(self, main_window):
        super().__init__()
        self.setObjectName("sidebar")
        self.main = main_window

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Buttons for each page
        buttons = [
            ("Dashboard", 0),
            ("Scanner", 1),
            ("Findings", 2),
            ("AI Analyst", 3),
            ("Issues", 4),
            ("Reasoning", 5),
            ("Kill Chain", 6),
            ("Report", 7),
        ]

        for text, index in buttons:
            btn = QPushButton(text)
            btn.clicked.connect(lambda checked, i=index: self.main.set_page(i))
            layout.addWidget(btn)

        layout.addStretch()
