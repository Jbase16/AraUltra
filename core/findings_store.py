from PyQt6.QtCore import QObject, pyqtSignal


class FindingsStore(QObject):
    """
    Stores all structured findings extracted by AIEngine.
    Emits signals so the UI updates automatically.
    """

    findings_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._findings = []

    def add_finding(self, finding: dict):
        self._findings.append(finding)
        self.findings_changed.emit()

    def get_all(self):
        return list(self._findings)

    def clear(self):
        self._findings = []
        self.findings_changed.emit()


# Singleton instance
findings_store = FindingsStore()