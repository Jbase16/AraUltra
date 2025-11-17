from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QTextEdit,
    QFrame
)
from PyQt6.QtCore import Qt

from core.tools import TOOLS


class ScannerPanel(QWidget):
    """
    Scanner control panel.
    Lets you trigger basic recon workflows and see raw logs.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(10)

        title = QLabel("Scanner")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        main_layout.addWidget(title)

        subtitle = QLabel("Kick off recon tasks and monitor their output.")
        subtitle.setStyleSheet("color: #aaaaaa;")
        main_layout.addWidget(subtitle)

        # Target input card
        target_card = QFrame()
        target_card.setObjectName("Card")
        target_layout = QHBoxLayout()
        target_layout.setContentsMargins(12, 12, 12, 12)
        target_layout.setSpacing(8)

        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("Target (IP or domain)")

        self.btn_nmap = QPushButton("Run Nmap")
        self.btn_nmap.clicked.connect(self.run_nmap)

        self.btn_subfinder = QPushButton("Run Subfinder")
        self.btn_subfinder.clicked.connect(self.run_subfinder)

        target_layout.addWidget(self.target_input)
        target_layout.addWidget(self.btn_nmap)
        target_layout.addWidget(self.btn_subfinder)

        target_card.setLayout(target_layout)
        main_layout.addWidget(target_card)

        # Log area
        log_label = QLabel("Scan Log")
        log_label.setStyleSheet("margin-top: 8px; font-weight: bold;")
        main_layout.addWidget(log_label)

        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setStyleSheet("background-color: #181818; border: 1px solid #333333;")
        main_layout.addWidget(self.log_view, stretch=1)

        self.setLayout(main_layout)

    def append_log(self, text: str):
        """
        Called from MainWindow when TaskRouter emits evidence updates.
        """
        self.log_view.append(text)

    def run_nmap(self):
        target = self.target_input.text().strip()
        if not target:
            self.append_log("[scanner] No target specified for Nmap.")
            return

        self.append_log(f"[scanner] Starting Nmap basic scan on {target}...")
        try:
            TOOLS["nmap"].scan_basic(target)
        except Exception as e:
            self.append_log(f"[scanner] Error running Nmap: {e}")

    def run_subfinder(self):
        target = self.target_input.text().strip()
        if not target:
            self.append_log("[scanner] No domain specified for Subfinder.")
            return

        self.append_log(f"[scanner] Starting Subfinder on {target}...")
        try:
            TOOLS["subfinder"].enumerate(target)
        except Exception as e:
            self.append_log(f"[scanner] Error running Subfinder: {e}")