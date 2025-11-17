# core/scan_orchestrator.py
# High-level orchestrator that runs tool scans, recon phases, and correlation.

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

from core.scanner_engine import ScannerEngine
from core.runner import PhaseRunner
from core.issues_store import issues_store
from core.killchain_store import killchain_store
from core.findings import findings_store


LogCallback = Callable[[str], None]


@dataclass
class ScanContext:
    target: str
    findings: List[dict]
    issues: List[dict]
    killchain_edges: List[dict]
    phase_results: Dict[str, List[dict]]
    logs: List[str]


class ScanOrchestrator:
    """Wrapper that sequences the end-to-end pipeline for a target."""

    def __init__(self, log_fn: Optional[LogCallback] = None):
        self.log = log_fn or (lambda msg: None)
        self.scanner = ScannerEngine()

    async def run(self, target: str) -> ScanContext:
        logs: List[str] = []

        async for line in self.scanner.scan(target):
            logs.append(line)
            self.log(line)

        phase_runner = PhaseRunner(target, lambda msg: self._log(msg, logs))
        phase_results = await phase_runner.run_all_phases()

        findings = self.scanner.get_last_results()
        issues = issues_store.get_all()
        edges = killchain_store.get_all()

        return ScanContext(
            target=target,
            findings=findings,
            issues=issues,
            killchain_edges=edges,
            phase_results=phase_results,
            logs=logs,
        )

    def run_sync(self, target: str) -> ScanContext:
        """Convenience wrapper to run orchestrator in a synchronous context."""
        return asyncio.run(self.run(target))

    def _log(self, msg: str, logs: List[str]):
        logs.append(msg)
        self.log(msg)
