# core/task_router.py
# Central event bus connecting tools, AI engine, and UI panels.

try:
    from PyQt6.QtCore import QObject, pyqtSignal
except ImportError:
    class QObject:
        def __init__(self): pass
    class pyqtSignal:
        def __init__(self, *args): pass
        def emit(self, *args): pass

import threading
from typing import Dict, Any

from .ai_engine import AIEngine
from .findings_store import findings_store
from .killchain_store import killchain_store


class TaskRouter(QObject):
    """
    Central event bus for routing messages between Scanner, AI, and UI.
    """
    # Signals
    log_message = pyqtSignal(str)
    scan_started = pyqtSignal(str)
    scan_finished = pyqtSignal()
    findings_update = pyqtSignal(dict)
    ai_commentary = pyqtSignal(str)

    _instance = None

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # -------------------------------------------------------
    # Initialization
    # -------------------------------------------------------
    def __init__(self):
        super().__init__()
        self._lock = threading.Lock()
        # Ensure signals exist if QObject init didn't set them (dummy mode)
        for sig in ['log_message', 'scan_started', 'scan_finished', 'findings_update', 'ai_commentary']:
            if not hasattr(self, sig):
                setattr(self, sig, pyqtSignal())

        self.ai = AIEngine.instance()

        # Lazy-loaded to avoid circular imports
        from core.evidence_store import EvidenceStore
        self.evidence = EvidenceStore.instance()

        # UI callbacks registry
        self._ui_callbacks = {}

    def emit_log(self, message: str):
        if hasattr(self.log_message, 'emit'):
            self.log_message.emit(message)

    def emit_scan_start(self, target: str):
        if hasattr(self.scan_started, 'emit'):
            self.scan_started.emit(target)

    def emit_scan_finish(self):
        if hasattr(self.scan_finished, 'emit'):
            self.scan_finished.emit()

    def emit_findings_update(self, data: Dict[str, Any]):
        if hasattr(self.findings_update, 'emit'):
            self.findings_update.emit(data)

    def emit_ai_commentary(self, text: str):
        if hasattr(self.ai_commentary, 'emit'):
            self.ai_commentary.emit(text)

    # -------------------------------------------------------
    # UI callback registration
    # -------------------------------------------------------
    def register_ui_callback(self, event_type: str, func):
        """
        UI files register for updates (e.g., findings_update, evidence_update,
        ai_live_comment, etc.)
        """
        if event_type not in self._ui_callbacks:
            self._ui_callbacks[event_type] = []
        self._ui_callbacks[event_type].append(func)

    def emit_ui_event(self, event_type: str, payload: dict):
        """
        Fires callbacks inside UI.
        """
        if event_type in self._ui_callbacks:
            for cb in self._ui_callbacks[event_type]:
                cb(payload)

    # -------------------------------------------------------
    # Primary tool output handler
    # -------------------------------------------------------
    def handle_tool_output(
        self,
        tool_name: str,
        stdout: str,
        stderr: str,
        rc: int,
        metadata: dict,
    ):
        """
        Called by ExecutionEngine via tool_callback_factory.
        Runs AI analysis and updates stores + UI panels.
        """

        result = self.ai.process_tool_output(
            tool_name=tool_name,
            stdout=stdout,
            stderr=stderr,
            rc=rc,
            metadata=metadata,
        )

        # Update dashboard & findings viewers
        self.emit_ui_event("evidence_update", {
            "tool": tool_name,
            "summary": result["summary"],
            "evidence_id": result["evidence_id"],
        })

        self.emit_ui_event("findings_update", {
            "tool": tool_name,
            "findings": result["findings"],
            "next_steps": result.get("next_steps", []),
            "killchain_phases": result["killchain_phases"],
        })

        # Live AI commentary stream
        live_comment = result.get("live_comment")
        if live_comment:
            self.emit_ui_event("ai_live_comment", {
                "tool": tool_name,
                "target": metadata.get("target") if metadata else None,
                "comment": live_comment,
            })