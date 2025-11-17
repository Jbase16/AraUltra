# main.py — Master window with navigation, autorefresh, and status bar

from __future__ import annotations

import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QStatusBar
)
from PyQt6.QtCore import Qt, pyqtSignal

from ui.dashboard import Dashboard
from ui.scanner import ScannerPanel
from ui.findings_view import FindingsPanel
from ui.killchain_view import KillChainView
from ui.ai_panel import AIPanel
from ui.report_viewer import ReportViewer
from ui.issues_panel import IssuesPanel
from ui.reasoning_panel import ReasoningPanel

from core.findings import findings_store
from core.issues_store import issues_store


class MainWindow(QMainWindow):

    # Global signals that scanner will emit
    scan_started = pyqtSignal(str)
    scan_finished = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self.setWindowTitle("AraUltra Offensive Recon Suite (Mac Edition)")
        self.setMinimumSize(1200, 800)

        container = QWidget()
        layout = QVBoxLayout(container)

        # ------------------------------------------------------------------
        # NAVIGATION BAR
        # ------------------------------------------------------------------
        nav = QHBoxLayout()

        self.btn_dashboard = QPushButton("Dashboard")
        self.btn_scanner = QPushButton("Scanner")
        self.btn_findings = QPushButton("Findings")
        self.btn_issues = QPushButton("Issues")
        self.btn_reasoning = QPushButton("Reasoning")
        self.btn_killchain = QPushButton("Attack Map")
        self.btn_ai = QPushButton("AI Analyst")
        self.btn_report = QPushButton("Report")

        for b in (
            self.btn_dashboard,
            self.btn_scanner,
            self.btn_findings,
            self.btn_issues,
            self.btn_reasoning,
            self.btn_killchain,
            self.btn_ai,
            self.btn_report
        ):
            b.setCheckable(True)
            b.clicked.connect(self._nav_clicked)
            nav.addWidget(b)

        nav.addStretch()
        layout.addLayout(nav)

        # ------------------------------------------------------------------
        # STACKED CENTRAL AREA
        # ------------------------------------------------------------------
        self.stack = QStackedWidget()

        self.dashboard = Dashboard()
        self.scanner = ScannerPanel()
        self.findings = FindingsPanel()
        self.issues = IssuesPanel()
        self.reasoning = ReasoningPanel()
        self.killchain = KillChainView()
        self.ai = AIPanel()
        self.report = ReportViewer()

        self.stack.addWidget(self.dashboard)
        self.stack.addWidget(self.scanner)
        self.stack.addWidget(self.findings)
        self.stack.addWidget(self.issues)
        self.stack.addWidget(self.reasoning)
        self.stack.addWidget(self.killchain)
        self.stack.addWidget(self.ai)
        self.stack.addWidget(self.report)

        layout.addWidget(self.stack, stretch=1)

        # ------------------------------------------------------------------
        # STATUS BAR
        # ------------------------------------------------------------------
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Ready.")

        self.setCentralWidget(container)

        # ------------------------------------------------------------------
        # CONNECT SIGNALS FROM SCANNER AND FINDINGS
        # ------------------------------------------------------------------
        self.scanner.scan_started.connect(self.on_scan_started)
        self.scanner.scan_finished.connect(self.on_scan_finished)

        findings_store.findings_changed.connect(self.refresh_dashboard)
        findings_store.findings_changed.connect(self.refresh_findings)
        issues_store.issues_changed.connect(self.refresh_dashboard)

        # Default tab
        self.btn_dashboard.setChecked(True)

    # ----------------------------------------------------------------------
    # Navigation bar behavior
    # ----------------------------------------------------------------------
    def _nav_clicked(self):
        sender = self.sender()
        tabs = [
            self.btn_dashboard,
            self.btn_scanner,
            self.btn_findings,
            self.btn_issues,
            self.btn_reasoning,
            self.btn_killchain,
            self.btn_ai,
            self.btn_report
        ]
        for i, b in enumerate(tabs):
            if b is sender:
                b.setChecked(True)
                self.stack.setCurrentIndex(i)
            else:
                b.setChecked(False)

    # ----------------------------------------------------------------------
    # Status + scan events
    # ----------------------------------------------------------------------
    def on_scan_started(self, target: str):
        self.status.showMessage(f"Scan started for {target}…")
        self.dashboard.set_scanning(True)

    def on_scan_finished(self, target: str):
        self.status.showMessage(f"Scan finished for {target}. Findings updated.")
        self.dashboard.set_scanning(False)

        self.refresh_dashboard()
        self.refresh_findings()
        self.killchain.rebuild_graph()

    # ----------------------------------------------------------------------
    # Refresh UI panels
    # ----------------------------------------------------------------------
    def refresh_dashboard(self):
        self.dashboard.update_metrics(findings_store.get_all())

    def refresh_findings(self):
        self.findings.reload_table()


def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
