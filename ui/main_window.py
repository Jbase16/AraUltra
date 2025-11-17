# ui/main_window.py
# Primary window container for AraUltra dashboard

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QStackedWidget
)
from ui.sidebar import SideBar
from ui.dashboard import DashboardView
from ui.scanner import ScannerView
from ui.findings_view import FindingsView
from ui.ai_panel import AIPanel
from ui.killchain_view import KillChainView
from ui.report_viewer import ReportViewer
from ui.issues_panel import IssuesPanel
from ui.reasoning_panel import ReasoningPanel
from core.issues_store import issues_store

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("AraUltra – Offensive Recon Platform")
        self.setMinimumSize(1400, 900)

        # Main container
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        # Left sidebar
        self.sidebar = SideBar(self)
        layout.addWidget(self.sidebar)

        # Right stacked views
        self.pages = QStackedWidget()
        layout.addWidget(self.pages)

        # Register pages
        self.dashboard = DashboardView()
        self.scanner = ScannerView()
        self.findings = FindingsView()
        self.ai_panel = AIPanel()
        self.issues = IssuesPanel()
        self.reasoning = ReasoningPanel()
        self.killchain = KillChainView()
        self.report_viewer = ReportViewer()

        self.pages.addWidget(self.dashboard)
        self.pages.addWidget(self.scanner)
        self.pages.addWidget(self.findings)
        self.pages.addWidget(self.ai_panel)
        self.pages.addWidget(self.issues)
        self.pages.addWidget(self.reasoning)
        self.pages.addWidget(self.killchain)
        self.pages.addWidget(self.report_viewer)

        self.setCentralWidget(container)
        issues_store.issues_changed.connect(self.dashboard.refresh)

    def set_page(self, index: int):
        self.pages.setCurrentIndex(index)
