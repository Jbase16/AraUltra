from typing import Dict, Any, Union

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem
)
from PyQt6.QtCore import Qt


class FindingsPanel(QWidget):
    """
    Displays structured findings extracted by the AI from evidence.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(10)

        title = QLabel("Findings")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        main_layout.addWidget(title)

        subtitle = QLabel("AI-correlated vulnerabilities and observations.")
        subtitle.setStyleSheet("color: #aaaaaa;")
        main_layout.addWidget(subtitle)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([
            "Title",
            "Severity",
            "Tool",
            "Location",
            "Details"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        main_layout.addWidget(self.table)

        self.setLayout(main_layout)

    def add_finding(self, finding: Union[Dict[str, Any], str]):
        """
        Add a single finding row. Accepts either a dict or a plain string.
        Expected dict keys (if present):
          - title
          - severity
          - tool
          - location
          - description
        """
        row = self.table.rowCount()
        self.table.insertRow(row)

        if isinstance(finding, dict):
            title = finding.get("title") or finding.get("name") or "Finding"
            severity = finding.get("severity") or "info"
            tool = finding.get("tool") or "unknown"
            location = finding.get("location") or finding.get("target") or ""
            desc = finding.get("description") or finding.get("details") or ""
        else:
            title = str(finding)
            severity = "info"
            tool = "unknown"
            location = ""
            desc = str(finding)

        self.table.setItem(row, 0, QTableWidgetItem(title))
        self.table.setItem(row, 1, QTableWidgetItem(severity))
        self.table.setItem(row, 2, QTableWidgetItem(tool))
        self.table.setItem(row, 3, QTableWidgetItem(location))
        self.table.setItem(row, 4, QTableWidgetItem(desc))