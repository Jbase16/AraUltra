from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QListWidget
)
from PyQt6.QtCore import Qt
from datetime import datetime


class IssuesPanel(QWidget):
    """
    High-level issue tracker for aggregating findings into actionable tickets.
    Currently a simple list that can be wired to IssuesStore.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(10)

        title = QLabel("Issues")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        main_layout.addWidget(title)

        subtitle = QLabel("Roll-up of findings into issues requiring remediation.")
        subtitle.setStyleSheet("color: #aaaaaa;")
        main_layout.addWidget(subtitle)

        self.list = QListWidget()
        self.list.setStyleSheet("background-color: #181818; border: 1px solid #333333;")
        main_layout.addWidget(self.list)

        self.setLayout(main_layout)

        self.refresh()

    def refresh(self):
        """
        Called when findings are updated.
        For now, just reflects that a refresh occurred.
        """
        ts = datetime.now().strftime("%H:%M:%S")
        self.list.addItem(f"Issues view refreshed at {ts}")
        # keep list from exploding
        if self.list.count() > 200:
            self.list.takeItem(0)