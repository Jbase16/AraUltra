import sys
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QStackedWidget
)
from PyQt6.QtCore import Qt

from .sidebar import Sidebar
from .dashboard import DashboardPanel
from .scanner import ScannerPanel
from .findings_view import FindingsPanel
from .killchain_view import KillchainPanel
from .issues_panel import IssuesPanel
from .ai_panel import AIPanel
from .report_viewer import ReportViewer

from .theme import apply_theme
from core.task_router import TaskRouter


class MainWindow(QMainWindow):
    """
    The primary UI container.
    Controls:
      - Sidebar navigation
      - Stack of panels
      - Live updates from TaskRouter
    """

    def __init__(self):
        super().__init__()

        self.setWindowTitle("AraUltra — Autonomous Reconnaissance Assistant")
        self.resize(1400, 900)

        apply_theme(self)

        central_widget = QWidget()
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Sidebar
        self.sidebar = Sidebar()
        self.sidebar.setFixedWidth(220)

        # Stacked view
        self.stack = QStackedWidget()

        # Panels
        self.dashboard_panel = DashboardPanel()
        self.scanner_panel = ScannerPanel()
        self.findings_panel = FindingsPanel()
        self.killchain_panel = KillchainPanel()
        self.issues_panel = IssuesPanel()
        self.ai_panel = AIPanel()
        self.report_panel = ReportViewer()

        # Add to stack
        self.stack.addWidget(self.dashboard_panel)   # index 0
        self.stack.addWidget(self.scanner_panel)     # index 1
        self.stack.addWidget(self.findings_panel)    # index 2
        self.stack.addWidget(self.killchain_panel)   # index 3
        self.stack.addWidget(self.issues_panel)      # index 4
        self.stack.addWidget(self.ai_panel)          # index 5
        self.stack.addWidget(self.report_panel)      # index 6

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.stack)

        # Sidebar navigation
        self.sidebar.navigate.connect(self.switch_panel)

        # TaskRouter callbacks
        router = TaskRouter.instance()
        router.register_ui_callback("evidence_update", self.on_evidence_update)
        router.register_ui_callback("findings_update", self.on_findings_update)

        # Status label in status bar
        self.status_label = QLabel("Ready.")
        self.status_label.setStyleSheet("padding: 6px; color: #bbb;")
        self.statusBar().addPermanentWidget(self.status_label)

    def switch_panel(self, index: int):
        self.stack.setCurrentIndex(index)
        names = [
            "Dashboard", "Scanner", "Findings",
            "Killchain", "Issues", "AI Panel", "Report Viewer"
        ]
        if 0 <= index < len(names):
            self.status_label.setText(f"Viewing: {names[index]}")
        else:
            self.status_label.setText("")

    def on_evidence_update(self, payload):
        tool = payload.get("tool")
        summary = payload.get("summary")

        self.scanner_panel.append_log(f"[{tool}] Evidence added:\n{summary}\n")
        self.sidebar.flash_section("Findings")
        self.dashboard_panel.add_recent_event(f"New evidence from {tool}")
        self.status_label.setText(f"New evidence received from {tool}")

    def on_findings_update(self, payload):
        tool = payload.get("tool")
        findings = payload.get("findings")

        for f in findings:
            self.findings_panel.add_finding(f)

        self.killchain_panel.refresh()
        self.issues_panel.refresh()
        self.dashboard_panel.add_recent_event(
            f"{len(findings)} new findings from {tool}"
        )
        self.status_label.setText(f"Findings updated from {tool}")