try:
    from PyQt6.QtCore import QObject, pyqtSignal
except ImportError:
    class QObject:
        def __init__(self): pass
    class pyqtSignal:
        def __init__(self, *args): pass
        def emit(self, *args): pass


class IssuesStore(QObject):
    """
    Tracks issues detected by AraUltra. Issues are higher-level
    concerns derived from findings or killchain data.
    """

    try:
        issues_changed = pyqtSignal()
    except NameError:
        issues_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._issues = []
        if not hasattr(self, 'issues_changed'):
            self.issues_changed = pyqtSignal()

    def add_issue(self, issue: dict):
        self._issues.append(issue)
        if hasattr(self.issues_changed, 'emit'):
            self.issues_changed.emit()

    def get_all(self):
        return list(self._issues)

    def clear(self):
        self._issues = []
        if hasattr(self.issues_changed, 'emit'):
            self.issues_changed.emit()


issues_store = IssuesStore()