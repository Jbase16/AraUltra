from PyQt6.QtCore import QObject, pyqtSignal


class IssuesStore(QObject):
    """
    Tracks issues detected by AraUltra. Issues are higher-level
    concerns derived from findings or killchain data.
    """

    issues_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._issues = []

    def add_issue(self, issue: dict):
        self._issues.append(issue)
        self.issues_changed.emit()

    def get_all(self):
        return list(self._issues)

    def clear(self):
        self._issues = []
        self.issues_changed.emit()


issues_store = IssuesStore()