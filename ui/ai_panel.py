from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton
)
from PyQt6.QtCore import Qt


class AIPanel(QWidget):
    """
    Freeform AI interaction panel.
    Right now this is UI-only and can later be wired into AIEngine.chat-style calls.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(10)

        title = QLabel("AI Panel")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        main_layout.addWidget(title)

        subtitle = QLabel("Ask the analysis engine questions or request summaries.")
        subtitle.setStyleSheet("color: #aaaaaa;")
        main_layout.addWidget(subtitle)

        self.input_box = QPlainTextEdit()
        self.input_box.setPlaceholderText("Ask AraUltra something about the target, evidence, or findings...")
        main_layout.addWidget(self.input_box, stretch=1)

        self.btn_ask = QPushButton("Ask AI")
        self.btn_ask.clicked.connect(self.on_ask)
        main_layout.addWidget(self.btn_ask)

        self.output_box = QPlainTextEdit()
        self.output_box.setReadOnly(True)
        self.output_box.setPlaceholderText("AI responses will appear here.")
        main_layout.addWidget(self.output_box, stretch=2)

        self.setLayout(main_layout)

    def on_ask(self):
        prompt = self.input_box.toPlainText().strip()
        if not prompt:
            self.output_box.appendPlainText("[system] No prompt provided.")
            return

        # Placeholder behavior for now; backend wiring can be added later.
        self.output_box.appendPlainText(f"[you] {prompt}\n")
        self.output_box.appendPlainText("[ai] Interactive chat integration not wired yet into AIEngine.\n")
        self.input_box.clear()