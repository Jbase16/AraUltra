# ui/ai_panel.py
# AI Analyst panel – uses Ollama via core.ai_engine

from __future__ import annotations

import json

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QPlainTextEdit, QLineEdit, QLabel
)
from PyQt6.QtCore import QThread, pyqtSignal

from core.ai_engine import ai_engine


class AIWorker(QThread):
    result_ready = pyqtSignal(str)

    def __init__(self, mode: str, question: str | None = None):
        super().__init__()
        self.mode = mode
        self.question = question

    def run(self):
        if self.mode == "summary":
            text = ai_engine.summarize_findings()
        elif self.mode == "report":
            text = ai_engine.generate_report()
        elif self.mode == "question" and self.question:
            text = ai_engine.answer_custom_question(self.question)
        else:
            text = "Invalid AI mode."
        self.result_ready.emit(text)


class AIPanel(QWidget):
    def __init__(self):
        super().__init__()

        self.worker: AIWorker | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        # Top controls
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self.btn_summary = QPushButton("Analyze Findings")
        self.btn_summary.clicked.connect(self.run_summary)

        self.btn_report = QPushButton("Generate Report Draft")
        self.btn_report.clicked.connect(self.run_report)

        self.btn_reasoning = QPushButton("Reasoning Snapshot")
        self.btn_reasoning.clicked.connect(self.show_reasoning)

        btn_row.addWidget(self.btn_summary)
        btn_row.addWidget(self.btn_report)
        btn_row.addWidget(self.btn_reasoning)
        btn_row.addStretch()

        layout.addLayout(btn_row)

        # Custom question row
        q_row = QHBoxLayout()
        q_row.setSpacing(8)

        q_label = QLabel("Ask AI:")
        self.q_input = QLineEdit()
        self.q_input.setPlaceholderText("e.g. 'Which issues should I triage first and why?'")
        self.q_button = QPushButton("Ask")
        self.q_button.clicked.connect(self.run_question)

        q_row.addWidget(q_label)
        q_row.addWidget(self.q_input)
        q_row.addWidget(self.q_button)

        layout.addLayout(q_row)

        # Output display
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet("QPlainTextEdit { background-color: #1e1e1e; }")
        layout.addWidget(self.output, stretch=1)

    def _append(self, text: str):
        self.output.appendPlainText(text)
        sb = self.output.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _run_worker(self, mode: str, question: str | None = None):
        if self.worker and self.worker.isRunning():
            self._append("[AI] Already running a task. Please wait.")
            return

        self._append(f"[AI] Starting {mode} request...")
        self.worker = AIWorker(mode, question)
        self.worker.result_ready.connect(self.on_result_ready)
        self.worker.start()

    def run_summary(self):
        self._run_worker("summary")

    def run_report(self):
        self._run_worker("report")

    def run_question(self):
        q = self.q_input.text().strip()
        if not q:
            self._append("[AI] Please enter a question first.")
            return
        self.q_input.clear()
        self._run_worker("question", q)

    def on_result_ready(self, text: str):
        self._append("\n[AI RESULT]\n")
        self._append(text)

    def show_reasoning(self):
        snapshot = ai_engine.reasoning_snapshot()
        formatted = json.dumps(snapshot, indent=2)
        self._append("\n[REASONING SNAPSHOT]\n")
        self._append(formatted)
