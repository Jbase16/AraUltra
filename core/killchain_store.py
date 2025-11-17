class KillchainStore:
    """
    Tracks the MITRE Kill Chain phases triggered by discovered findings.
    Simple and extensible store used by TaskRouter and the UI.
    """

    def __init__(self):
        self.phases = set()

    def add_phase(self, phase: str):
        self.phases.add(phase)

    def get_phases(self):
        return sorted(list(self.phases))


# Singleton
killchain_store = KillchainStore()