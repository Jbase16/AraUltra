# core/issues_store.py — enriched issue storage

from __future__ import annotations

from PyQt6.QtCore import QObject, pyqtSignal
import threading
from typing import List, Dict, Iterable


class IssuesStore(QObject):
    issues_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._lock = threading.Lock()
        self._issues: List[dict] = []

    def add(self, issue: dict):
        with self._lock:
            self._issues.append(issue)
        self.issues_changed.emit()

    def bulk_add(self, issues: List[dict]):
        if not issues:
            return
        with self._lock:
            self._issues.extend(issues)
        self.issues_changed.emit()

    def replace_all(self, issues: List[dict]):
        with self._lock:
            self._issues = list(issues)
        self.issues_changed.emit()

    def clear(self):
        with self._lock:
            self._issues.clear()
        self.issues_changed.emit()

    def get_all(self) -> List[dict]:
        with self._lock:
            return list(self._issues)

    def get_by_asset(self, asset: str) -> List[dict]:
        with self._lock:
            return [issue for issue in self._issues if issue.get("target") == asset or issue.get("asset") == asset]


issues_store = IssuesStore()
