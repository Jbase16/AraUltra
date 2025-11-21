# core/risk.py — simple asset risk scoring engine

from __future__ import annotations

from collections import defaultdict
from typing import Dict

try:
    from PyQt6.QtCore import QObject, pyqtSignal
except ImportError:
    class QObject:
        def __init__(self): pass
    class pyqtSignal:
        def __init__(self, *args): pass
        def emit(self, *args): pass
        def connect(self, *args): pass

from core.issues_store import issues_store


SEVERITY_WEIGHTS = {
    "CRITICAL": 10,
    "HIGH": 6,
    "MEDIUM": 3,
    "LOW": 1,
    "INFO": 0.5,
}


class RiskEngine(QObject):
    try:
        scores_changed = pyqtSignal()
    except NameError:
        scores_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._scores: Dict[str, float] = {}
        if not hasattr(self, 'scores_changed'):
            self.scores_changed = pyqtSignal()
        
        # Only connect if the signal has a connect method (dummy or real)
        if hasattr(issues_store.issues_changed, 'connect'):
            issues_store.issues_changed.connect(self.recalculate)
            
        self.recalculate()

    def recalculate(self):
        raw = issues_store.get_all()
        scores = defaultdict(float)
        for issue in raw:
            asset = issue.get("target") or issue.get("asset") or "unknown"
            severity = str(issue.get("severity", "INFO")).upper()
            weight = SEVERITY_WEIGHTS.get(severity, 0.5)
            scores[asset] += weight
        self._scores = dict(scores)
        if hasattr(self.scores_changed, 'emit'):
            self.scores_changed.emit()

    def get_scores(self) -> Dict[str, float]:
        return dict(self._scores)


risk_engine = RiskEngine()
