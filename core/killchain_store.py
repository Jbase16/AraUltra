# core/killchain_store.py — killchain edge storage

from __future__ import annotations

from PyQt6.QtCore import QObject, pyqtSignal
import threading
from typing import List


class KillChainStore(QObject):
    edges_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._lock = threading.Lock()
        self._edges: List[dict] = []

    def add(self, edge: dict):
        with self._lock:
            self._edges.append(edge)
        self.edges_changed.emit()

    def bulk_add(self, edges: List[dict]):
        if not edges:
            return
        with self._lock:
            self._edges.extend(edges)
        self.edges_changed.emit()

    def replace_all(self, edges: List[dict]):
        with self._lock:
            self._edges = list(edges)
        self.edges_changed.emit()

    def clear(self):
        with self._lock:
            self._edges.clear()
        self.edges_changed.emit()

    def get_all(self) -> List[dict]:
        with self._lock:
            return list(self._edges)

    def get_by_asset(self, asset: str) -> List[dict]:
        with self._lock:
            return [edge for edge in self._edges if edge.get("source") == asset or edge.get("target") == asset]


killchain_store = KillChainStore()
