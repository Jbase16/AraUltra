# ui/reasoning_panel.py — visualizes reasoning_engine output

from __future__ import annotations

import json

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPlainTextEdit, QPushButton,
    QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt

from core.ai_engine import reasoning_engine
from core.issues_store import issues_store
from core.killchain_store import killchain_store


class ReasoningPanel(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        header = QLabel("Reasoning & Attack Paths")
        header.setStyleSheet("font-size:20px; font-weight:bold;")
        layout.addWidget(header)

        btn_refresh = QPushButton("Refresh Reasoning Snapshot")
        btn_refresh.clicked.connect(self.reload)
        layout.addWidget(btn_refresh)

        self.attack_list = QListWidget()
        self.attack_list.setStyleSheet("QListWidget{background:#1e1e1e; border:none;}")
        layout.addWidget(QLabel("Attack Paths"))
        layout.addWidget(self.attack_list)

        self.recommendations_box = QPlainTextEdit()
        self.recommendations_box.setReadOnly(True)
        self.recommendations_box.setStyleSheet("QPlainTextEdit{background:#101010;}")
        layout.addWidget(QLabel("Recommended Phases"))
        layout.addWidget(self.recommendations_box)

        self.summary_box = QPlainTextEdit()
        self.summary_box.setReadOnly(True)
        self.summary_box.setStyleSheet("QPlainTextEdit{background:#101010;}")
        layout.addWidget(QLabel("Reasoning Snapshot (JSON)"))
        layout.addWidget(self.summary_box, stretch=1)

        issues_store.issues_changed.connect(self.reload)
        killchain_store.edges_changed.connect(self.reload)
        self.reload()

    def reload(self):
        snapshot = reasoning_engine.analyze()
        self._populate_paths(snapshot.get("attack_paths", []))
        self._populate_recommendations(snapshot.get("recommended_phases", []))
        self.summary_box.setPlainText(json.dumps(snapshot, indent=2))

    def _populate_paths(self, paths):
        self.attack_list.clear()
        for path in paths:
            item = QListWidgetItem(" → ".join(path))
            self.attack_list.addItem(item)

    def _populate_recommendations(self, recs):
        if not recs:
            self.recommendations_box.setPlainText("No additional phases recommended.")
        else:
            self.recommendations_box.setPlainText("\n".join(f"• {r}" for r in recs))
