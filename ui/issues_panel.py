# ui/issues_panel.py — Displays correlated issues from issues_store

from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QListWidgetItem,
    QLabel, QHBoxLayout, QPushButton, QComboBox
)
from PyQt6.QtCore import Qt

from core.issues_store import issues_store


class IssueCard(QWidget):
    def __init__(self, issue: dict):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(12, 8, 12, 8)
        self.setStyleSheet("background-color:#1e1e1e; border-radius:8px;")

        header = QHBoxLayout()
        title = QLabel(issue.get("title", issue.get("type", "Issue")))
        title.setStyleSheet("font-size:16px; font-weight:bold;")
        severity = issue.get("severity", "INFO").upper()
        sev_label = QLabel(severity)
        sev_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sev_label.setStyleSheet(self._severity_style(severity))

        header.addWidget(title)
        header.addStretch()
        header.addWidget(sev_label)

        layout.addLayout(header)

        subtitle = QLabel(issue.get("target", "unknown target"))
        subtitle.setStyleSheet("color:#cccccc; font-size:12px;")
        layout.addWidget(subtitle)

        message = QLabel(issue.get("description", issue.get("message", "")))
        message.setWordWrap(True)
        message.setStyleSheet("color:#dddddd; font-size:13px;")
        layout.addWidget(message)

        tag_layout = QHBoxLayout()
        for tag in issue.get("tags", []):
            chip = QLabel(tag)
            chip.setStyleSheet("background:#333; padding:2px 6px; border-radius:4px; font-size:11px;")
            tag_layout.addWidget(chip)
        tag_layout.addStretch()
        layout.addLayout(tag_layout)

    def _severity_style(self, severity: str) -> str:
        mapping = {
            "CRITICAL": "background:#c0392b; color:#fff; padding:4px 8px; border-radius:4px;",
            "HIGH": "background:#d35400; color:#fff; padding:4px 8px; border-radius:4px;",
            "MEDIUM": "background:#d68910; color:#fff; padding:4px 8px; border-radius:4px;",
            "LOW": "background:#7f8c8d; color:#fff; padding:4px 8px; border-radius:4px;",
        }
        return mapping.get(severity, "background:#95a5a6; color:#fff; padding:4px 8px; border-radius:4px;")


class IssuesPanel(QWidget):
    def __init__(self):
        super().__init__()

        self.list = QListWidget()
        self.list.setSpacing(8)
        self.list.setStyleSheet("QListWidget{border:none;}")
        self.filter_combo = QComboBox()
        self.filter_combo.addItem("All Severities", None)
        for sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"):
            self.filter_combo.addItem(sev, sev)
        self.filter_combo.currentIndexChanged.connect(self.reload)

        self.asset_combo = QComboBox()
        self.asset_combo.addItem("All Assets", None)
        self.asset_combo.currentIndexChanged.connect(self.reload)


        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel("Correlated Issues")
        title.setStyleSheet("font-size:18px; font-weight:bold;")
        refresh = QPushButton("Refresh")
        refresh.clicked.connect(self.reload)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(QLabel("Severity:"))
        header.addWidget(self.filter_combo)
        header.addWidget(QLabel("Asset:"))
        header.addWidget(self.asset_combo)
        header.addWidget(refresh)
        layout.addLayout(header)

        layout.addWidget(self.list)

        issues_store.issues_changed.connect(self.reload)
        self.reload()

    def reload(self):
        self.list.clear()
        self._populate_asset_filter()
        severity_filter = self.filter_combo.currentData()
        asset_filter = self.asset_combo.currentData()
        for issue in issues_store.get_all():
            sev = str(issue.get("severity", "INFO")).upper()
            if severity_filter and sev != severity_filter:
                continue
            asset = issue.get("target") or issue.get("asset") or "unknown"
            if asset_filter and asset_filter != asset:
                continue
            item = QListWidgetItem()
            widget = IssueCard(issue)
            item.setSizeHint(widget.sizeHint())
            self.list.addItem(item)
            self.list.setItemWidget(item, widget)

    def _populate_asset_filter(self):
        current = self.asset_combo.currentData()
        self.asset_combo.blockSignals(True)
        self.asset_combo.clear()
        self.asset_combo.addItem("All Assets", None)
        assets = sorted({issue.get("target") or issue.get("asset") or "unknown" for issue in issues_store.get_all()})
        for asset in assets:
            self.asset_combo.addItem(asset, asset)
        index = 0
        if current:
            index = self.asset_combo.findData(current)
        if index == -1:
            index = 0
        self.asset_combo.setCurrentIndex(index)
        self.asset_combo.blockSignals(False)
