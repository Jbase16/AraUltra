# ui/ai_panel.py
# Interactive AI analyst panel with context view, live feed, and Q&A.

from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTextEdit,
    QLineEdit,
    QPushButton,
)
from PyQt6.QtCore import Qt, pyqtSignal

from core.ai_engine import AIEngine
from core.evidence_store import EvidenceStore
from core.findings_store import findings_store
from core.task_router import TaskRouter


class AIPanel(QWidget):
    """
    Panel that lets the user:
      - See a high-level summary of evidence & findings
      - Watch a live AI commentary feed as tools finish
      - Ask natural-language questions and get analysis
    """

    live_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self.engine = AIEngine.instance()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # ------------------------------------------------------
        # Context / situation overview
        # ------------------------------------------------------
        context_label = QLabel("Current context")
        context_label.setStyleSheet("font-weight: 600;")
        layout.addWidget(context_label)

        self.context_view = QTextEdit()
        self.context_view.setReadOnly(True)
        self.context_view.setPlaceholderText(
            "Recent tool runs, evidence summaries, and extracted findings "
            "will appear here so you can see what the AI is reasoning over."
        )
        layout.addWidget(self.context_view, stretch=2)

        # ------------------------------------------------------
        # Live AI commentary feed
        # ------------------------------------------------------
        live_label = QLabel("Live AI feed")
        live_label.setStyleSheet("font-weight: 600;")
        layout.addWidget(live_label)

        self.live_view = QTextEdit()
        self.live_view.setReadOnly(True)
        self.live_view.setStyleSheet(
            "background: #101010; color: #c0e0ff; font-family: Menlo, monospace; font-size: 11px;"
        )
        self.live_view.setPlaceholderText(
            "Short AI comments about each tool run will stream here in real time."
        )
        layout.addWidget(self.live_view, stretch=2)

        # ------------------------------------------------------
        # Question input
        # ------------------------------------------------------
        q_row = QHBoxLayout()

        q_label = QLabel("Question:")
        q_row.addWidget(q_label)

        self.question_input = QLineEdit()
        self.question_input.setPlaceholderText(
            "e.g., What are the most critical issues for this target?"
        )
        q_row.addWidget(self.question_input, stretch=1)

        self.ask_btn = QPushButton("Ask AI")
        self.ask_btn.clicked.connect(self.on_ask_clicked)
        q_row.addWidget(self.ask_btn)

        layout.addLayout(q_row)

        # ------------------------------------------------------
        # Answer output
        # ------------------------------------------------------
        answer_label = QLabel("AI analysis")
        answer_label.setStyleSheet("font-weight: 600;")
        layout.addWidget(answer_label)

        self.answer_view = QTextEdit()
        self.answer_view.setReadOnly(True)
        self.answer_view.setPlaceholderText(
            "The AI assistant's explanation and guidance will appear here."
        )
        layout.addWidget(self.answer_view, stretch=3)

        # Initial context
        self.refresh_context()

        # Hook store updates so context stays fresh
        EvidenceStore.instance().evidence_changed.connect(self.refresh_context)
        findings_store.findings_changed.connect(self.refresh_context)

        # Connect live feed signal to UI slot
        self.live_signal.connect(self._append_live_ui)

        # Register for live AI events from TaskRouter
        router = TaskRouter.instance()
        router.register_ui_callback("ai_live_comment", self._on_live_comment)

    # ----------------------------------------------------------
    # Context rendering
    # ----------------------------------------------------------
    def refresh_context(self):
        """
        Render a human-readable view of current evidence + findings.
        """
        evidence = EvidenceStore.instance().get_all()
        findings = findings_store.get_all()

        lines = []

        if not evidence and not findings:
            self.context_view.setPlainText(
                "No evidence or findings yet.\n\n"
                "Run some tools from the Scanner tab and the AI will summarize them here."
            )
            return

        if evidence:
            lines.append("=== Evidence ===")
            for eid, entry in sorted(evidence.items()):
                tool = entry.get("tool", "unknown")
                meta = entry.get("metadata", {})
                target = meta.get("target", "?")
                summary = entry.get("summary") or "<no summary yet>"

                lines.append(f"[#{eid}] {tool} on {target}")
                if len(summary) > 400:
                    summary_snip = summary[:400].rstrip() + "..."
                else:
                    summary_snip = summary
                lines.append(f"  Summary: {summary_snip}")
                lines.append("")

        if findings:
            lines.append("=== Findings ===")
            for idx, f in enumerate(findings, start=1):
                tool = f.get("tool", "unknown")
                ftype = f.get("type", "generic")
                sev = f.get("severity", "unknown")
                val = f.get("value", "")

                lines.append(f"[{idx}] ({sev}) {ftype} from {tool}")
                if val:
                    if len(val) > 300:
                        val_snip = val[:300].rstrip() + "..."
                    else:
                        val_snip = val
                    lines.append(f"  {val_snip}")
                lines.append("")

        self.context_view.setPlainText("\n".join(lines))

    # ----------------------------------------------------------
    # Live commentary handler
    # ----------------------------------------------------------
    def _on_live_comment(self, payload: dict):
        tool = payload.get("tool", "tool")
        target = payload.get("target") or "target"
        comment = payload.get("comment") or ""

        line = f"[{tool} → {target}] {comment}"
        self.live_signal.emit(line)

    def _append_live_ui(self, line: str):
        self.live_view.append(line)
        sb = self.live_view.verticalScrollBar()
        sb.setValue(sb.maximum())

    # ----------------------------------------------------------
    # Question handling
    # ----------------------------------------------------------
    def on_ask_clicked(self):
        question = self.question_input.text().strip()
        if not question:
            self.answer_view.setPlainText("Ask a specific question first.")
            return

        self.ask_btn.setEnabled(False)
        self.answer_view.setPlainText("Thinking...")

        try:
            answer = self.engine.chat(question)
            self.answer_view.setPlainText(answer)
        except Exception as e:
            self.answer_view.setPlainText(f"Error while running AI analysis:\n{e}")
        finally:
            self.ask_btn.setEnabled(True)