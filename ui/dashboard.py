# ui/dashboard.py
# High-level overview dashboard for AraUltra

from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QFrame
)
from PyQt6.QtCore import Qt

from core.findings import findings_store
from core.issues_store import issues_store
from core.risk import risk_engine

class StatCard(QFrame):
    def __init__(self, title: str, value: str):
        super().__init__()
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("QFrame { background-color: #252526; border-radius: 8px; }")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("color: #a0a0a0; font-size: 12px;")
        value_lbl = QLabel(value)
        value_lbl.setStyleSheet("color: #ffffff; font-size: 24px; font-weight: bold;")

        layout.addWidget(title_lbl)
        layout.addWidget(value_lbl)
        layout.addStretch()

        self._value_lbl = value_lbl

    def set_value(self, value: str):
        self._value_lbl.setText(value)


class DashboardView(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        title = QLabel("Overview")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        # Stats row
        stats_row = QHBoxLayout()
        stats_row.setSpacing(16)

        self.card_targets = StatCard("Targets Scanned", "0")
        self.card_findings = StatCard("Total Findings", "0")
        self.card_high = StatCard("High/Critical", "0")

        stats_row.addWidget(self.card_targets)
        stats_row.addWidget(self.card_findings)
        stats_row.addWidget(self.card_high)
        stats_row.addStretch()

        layout.addLayout(stats_row)
        layout.addStretch()

        self.refresh()

    def refresh(self):
        # Simple derived stats from findings_store
        findings = findings_store.get_all()
        total = len(findings)
        high = sum(1 for f in findings if f["severity"] in ("HIGH", "CRITICAL"))
        targets = len({f["target"] for f in findings})

        self.card_targets.set_value(str(targets))
        self.card_findings.set_value(str(total))
        self.card_high.set_value(str(high))

class Dashboard(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        self.status_label = QLabel("Status: Idle")
        self.status_label.setStyleSheet("color: #cccccc; font-size: 14px;")

        self.total_label = QLabel("Total Findings: 0")
        self.high_label = QLabel("High/Critical: 0")
        self.issues_label = QLabel("Correlated Issues: 0")
        self.issues_label.setStyleSheet("color:#ffffff; font-size:16px;")
        self.critical_label = QLabel("Critical Issues: 0 | High Issues: 0")
        self.critical_label.setStyleSheet("color:#ffb347; font-size:14px;")
        self.asset_summary = QLabel("Top Assets:\n—")
        self.asset_summary.setWordWrap(True)
        self.asset_summary.setStyleSheet("color:#dddddd; font-size:13px;")

        for lbl in (self.total_label, self.high_label):
            lbl.setStyleSheet("color: #ffffff; font-size: 22px; font-weight: bold;")

        layout.addWidget(self.status_label)
        layout.addWidget(self.total_label)
        layout.addWidget(self.high_label)

        issue_row = QHBoxLayout()
        issue_row.addWidget(self.issues_label)
        issue_row.addWidget(self.critical_label)
        issue_row.addStretch()
        layout.addLayout(issue_row)

        layout.addWidget(self.asset_summary)
        layout.addStretch()

    def set_scanning(self, scanning: bool):
        if scanning:
            self.status_label.setText("Status: SCANNING…")
            self.status_label.setStyleSheet("color: #ffcc00; font-size: 14px;")
        else:
            self.status_label.setText("Status: Idle")
            self.status_label.setStyleSheet("color: #cccccc; font-size: 14px;")

    def update_metrics(self, findings):
        total = len(findings)
        high = sum(1 for f in findings if f.get("severity") in ("HIGH", "CRITICAL"))

        self.total_label.setText(f"Total Findings: {total}")
        self.high_label.setText(f"High/Critical: {high}")
        issues = issues_store.get_all()
        crit = sum(1 for issue in issues if str(issue.get("severity", "")).upper() == "CRITICAL")
        high_issue = sum(1 for issue in issues if str(issue.get("severity", "")).upper() == "HIGH")
        self.issues_label.setText(f"Correlated Issues: {len(issues)}")
        self.critical_label.setText(f"Critical Issues: {crit} | High Issues: {high_issue}")
        self.asset_summary.setText(self._format_top_assets())

    def _format_top_assets(self, limit: int = 3) -> str:
        scores = risk_engine.get_scores()
        if not scores:
            return "Top Assets:\n—"
        top = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:limit]
        lines = [f"{idx + 1}. {asset} — score {score:.1f}" for idx, (asset, score) in enumerate(top)]
        return "Top Assets:\n" + "\n".join(lines)
