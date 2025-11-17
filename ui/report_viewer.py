# ui/report_viewer.py
# Bug bounty style report generator / viewer

from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton,
    QSplitter, QPlainTextEdit, QTextBrowser
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from core.ai_engine import ai_engine
from core.reporting import create_report_bundle


class ReportWorker(QThread):
    report_ready = pyqtSignal(str)

    def run(self):
        text = ai_engine.generate_report()
        self.report_ready.emit(text)


class ReportViewer(QWidget):
    def __init__(self):
        super().__init__()

        self.worker: ReportWorker | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        self.btn_generate = QPushButton("Generate Report from Findings")
        self.btn_generate.clicked.connect(self.generate_report)
        layout.addWidget(self.btn_generate)

        self.btn_bundle = QPushButton("Export Report Bundle")
        self.btn_bundle.clicked.connect(self.export_bundle)
        layout.addWidget(self.btn_bundle)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter, stretch=1)

        # Raw markdown/text view
        self.raw_view = QPlainTextEdit()
        self.raw_view.setReadOnly(True)
        self.raw_view.setStyleSheet("QPlainTextEdit { background-color: #1e1e1e; }")

        # Rendered preview
        self.html_view = QTextBrowser()
        self.html_view.setOpenExternalLinks(True)

        splitter.addWidget(self.raw_view)
        splitter.addWidget(self.html_view)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)

    def generate_report(self):
        if self.worker and self.worker.isRunning():
            self.raw_view.appendPlainText("[Report] Already generating...")
            return

        self.raw_view.appendPlainText("[Report] Generating report...")
        self.worker = ReportWorker()
        self.worker.report_ready.connect(self.on_report_ready)
        self.worker.start()

    def on_report_ready(self, text: str):
        self.raw_view.appendPlainText("\n[Report Generated]\n")
        self.raw_view.appendPlainText(text)

        # Quick-and-dirty markdown-ish to HTML
        html = (
            "<html><body style='background-color:#1e1e1e; color:#ffffff; font-family:Menlo,monospace;'>"
            + text.replace("\n", "<br>")
            + "</body></html>"
        )
        self.html_view.setHtml(html)

    def export_bundle(self):
        self.raw_view.appendPlainText("[Report] Exporting bundle...")
        bundle = create_report_bundle()
        self.raw_view.appendPlainText(
            f"[Report] Bundle created at {bundle.folder}\n - {bundle.markdown_path}\n - {bundle.json_path}\n"
        )
