# ui/findings_view.py
# Findings list + panel implementations

from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPlainTextEdit, QSplitter
)
from PyQt6.QtCore import Qt

from core.findings import findings_store

class FindingsView(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        splitter = QSplitter(Qt.Orientation.Vertical)
        layout.addWidget(splitter)

        # Table of findings
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "Severity", "Type", "Target", "Tool"])
        self.table.setSortingEnabled(True)
        self.table.itemSelectionChanged.connect(self.on_selection_changed)

        # Detail / evidence
        self.details = QPlainTextEdit()
        self.details.setReadOnly(True)
        self.details.setStyleSheet("QPlainTextEdit { background-color: #1e1e1e; }")

        splitter.addWidget(self.table)
        splitter.addWidget(self.details)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        findings_store.findings_changed.connect(self.refresh)
        self.refresh()

    def refresh(self):
        data = findings_store.get_all()
        self.table.setRowCount(len(data))
        for row, f in enumerate(data):
            self.table.setItem(row, 0, QTableWidgetItem(str(f["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(f["severity"]))
            self.table.setItem(row, 2, QTableWidgetItem(f["type"]))
            self.table.setItem(row, 3, QTableWidgetItem(f["target"]))
            self.table.setItem(row, 4, QTableWidgetItem(f["tool"]))
        if data:
            self.table.selectRow(0)

    def on_selection_changed(self):
        selected = self.table.selectedItems()
        if not selected:
            self.details.setPlainText("")
            return

        row = selected[0].row()
        fid = int(self.table.item(row, 0).text())
        all_f = findings_store.get_all()
        match = next((f for f in all_f if f["id"] == fid), None)
        if not match:
            self.details.setPlainText("")
            return

        text = (
            f"ID: {match['id']}\n"
            f"Target: {match['target']}\n"
            f"Tool: {match['tool']}\n"
            f"Type: {match['type']}\n"
            f"Severity: {match['severity']}\n"
            f"Pattern: {match['pattern']}\n"
            f"Timestamp: {match['timestamp']}\n\n"
            f"Evidence:\n{match['evidence']}\n"
        )
        self.details.setPlainText(text)

class FindingsPanel(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Target", "Type", "Severity", "Tool", "Message", "Timestamp"])
        layout.addWidget(self.table)

        findings_store.findings_changed.connect(self.reload_table)
        self.reload_table()

    def reload_table(self):
        findings = findings_store.get_all()
        self.table.setRowCount(len(findings))

        for row, f in enumerate(findings):
            self.table.setItem(row, 0, QTableWidgetItem(f.get("target", "")))
            self.table.setItem(row, 1, QTableWidgetItem(f.get("type", "")))
            self.table.setItem(row, 2, QTableWidgetItem(f.get("severity", "")))
            self.table.setItem(row, 3, QTableWidgetItem(f.get("tool", "")))
            self.table.setItem(row, 4, QTableWidgetItem(f.get("message", "")))
            self.table.setItem(row, 5, QTableWidgetItem(f.get("timestamp", "")))

        self.table.resizeColumnsToContents()
