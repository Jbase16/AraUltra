# core/findings.py — central findings store with UI signals

from __future__ import annotations

try:
    from PyQt6.QtCore import QObject, pyqtSignal
except ImportError:
    # Dummy classes for headless mode
    class QObject:
        def __init__(self): pass
    
    class pyqtSignal:
        def __init__(self, *args): pass
        def emit(self, *args): pass

import threading


class FindingsStore(QObject):
    # Only define signal if PyQt6 is available, otherwise it's a dummy attribute
    try:
        findings_changed = pyqtSignal()
    except NameError:
        findings_changed = pyqtSignal() # Uses the dummy class

    def __init__(self):
        super().__init__()
        self._lock = threading.Lock()
        self._findings = []
        # Ensure findings_changed exists even if QObject init doesn't set it
        if not hasattr(self, 'findings_changed'):
             self.findings_changed = pyqtSignal()

    def add(self, item: dict):
        """Add a single finding and notify UI."""
        with self._lock:
            self._findings.append(item)
        if hasattr(self.findings_changed, 'emit'):
            self.findings_changed.emit()

    def bulk_add(self, items: list[dict]):
        """Add multiple findings at once."""
        with self._lock:
            self._findings.extend(items)
        if hasattr(self.findings_changed, 'emit'):
            self.findings_changed.emit()

    def get_all(self):
        """Return a copy of the current findings list."""
        with self._lock:
            return list(self._findings)

    def clear(self):
        """Remove all findings and notify UI."""
        with self._lock:
            self._findings.clear()
        if hasattr(self.findings_changed, 'emit'):
            self.findings_changed.emit()


# Global singleton
findings_store = FindingsStore()