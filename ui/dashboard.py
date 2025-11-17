from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QListWidget,
    QFrame,
    QHBoxLayout
)
from PyQt6.QtCore import Qt
from datetime import datetime


class DashboardPanel(QWidget):
    """
    High-level overview and recent activity feed.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        title = QLabel("Dashboard")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        main_layout.addWidget(title)

        subtitle = QLabel("High-level view of active scans, new findings, and system status.")
        subtitle.setStyleSheet("color: #aaaaaa;")
        main_layout.addWidget(subtitle)

        # Cards container
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(12)

        self.status_card = self._build_card("System Status", "Idle")
        self.scan_card = self._build_card("Active Scans", "0")
        self.findings_card = self._build_card("Total Findings", "0")

        cards_layout.addWidget(self.status_card)
        cards_layout.addWidget(self.scan_card)
        cards_layout.addWidget(self.findings_card)

        main_layout.addLayout(cards_layout)

        # Recent events
        events_label = QLabel("Recent Activity")
        events_label.setStyleSheet("margin-top: 12px; font-weight: bold;")
        main_layout.addWidget(events_label)

        self.events_list = QListWidget()
        self.events_list.setStyleSheet("background-color: #181818; border: 1px solid #333333;")
        main_layout.addWidget(self.events_list)

        self.setLayout(main_layout)

    def _build_card(self, title: str, value: str) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(4)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 12px; color: #bbbbbb;")

        value_label = QLabel(value)
        value_label.setStyleSheet("font-size: 22px; font-weight: bold;")

        layout.addWidget(title_label)
        layout.addWidget(value_label)
        layout.addStretch(1)

        card.setLayout(layout)
        card.value_label = value_label  # store for updates
        return card

    def add_recent_event(self, text: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.events_list.insertItem(0, f"[{timestamp}] {text}")
        # keep it from growing unbounded
        if self.events_list.count() > 200:
            self.events_list.takeItem(self.events_list.count() - 1)

    def set_system_status(self, text: str):
        self.status_card.value_label.setText(text)

    def set_active_scans(self, count: int):
        self.scan_card.value_label.setText(str(count))

    def set_total_findings(self, count: int):
        self.findings_card.value_label.setText(str(count))