from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QListWidget
)
from PyQt6.QtCore import Qt
from datetime import datetime


class KillchainPanel(QWidget):
    """
    Simple visualization of the attack kill chain stages.
    For now this is a conceptual view that can later be wired into KillchainStore.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(10)

        title = QLabel("Killchain")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        main_layout.addWidget(title)

        subtitle = QLabel("Attack progression mapped against standard kill chain phases.")
        subtitle.setStyleSheet("color: #aaaaaa;")
        main_layout.addWidget(subtitle)

        self.list = QListWidget()
        self.list.setStyleSheet("background-color: #181818; border: 1px solid #333333;")
        main_layout.addWidget(self.list)

        self.setLayout(main_layout)

        self.refresh()

    def refresh(self):
        """
        Called when new findings are available.
        For now, just updates a timestamp and shows generic phases.
        """
        self.list.clear()

        phases = [
            "Reconnaissance",
            "Weaponization",
            "Delivery",
            "Exploitation",
            "Installation",
            "Command & Control",
            "Actions on Objectives"
        ]

        ts = datetime.now().strftime("%H:%M:%S")

        for phase in phases:
            self.list.addItem(f"{phase}  •  updated {ts}")