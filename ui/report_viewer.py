from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton
)
from PyQt6.QtCore import Qt


class ReportViewer(QWidget):
    """
    Displays generated reports or allows previewing report drafts.
    Currently a simple text viewer with a 'refresh' hook.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(10)

        title = QLabel("Report Viewer")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        main_layout.addWidget(title)

        subtitle = QLabel("Preview and refine engagement reports.")
        subtitle.setStyleSheet("color: #aaaaaa;")
        main_layout.addWidget(subtitle)

        self.refresh_btn = QPushButton("Refresh Report")
        self.refresh_btn.clicked.connect(self.refresh_report)
        main_layout.addWidget(self.refresh_btn)

        self.text = QPlainTextEdit()
        self.text.setReadOnly(True)
        self.text.setPlaceholderText("Generated reports will appear here once reporting is wired into the backend.")
        main_layout.addWidget(self.text, stretch=1)

        self.setLayout(main_layout)

    def refresh_report(self):
        """
        Invoked when the user clicks 'Refresh Report'.
        For now, just drops a stub message. Backend can later load a real report.
        """
        self.text.appendPlainText("[report] Report refresh requested. Backend integration pending.\n")