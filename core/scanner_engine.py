# core/scanner_engine.py — macOS-compatible active scanner engine
from __future__ import annotations

import asyncio
from urllib.parse import urlparse
from typing import AsyncGenerator, Dict, List

from core.findings import findings_store
from core.evidence import evidence_store
from core import raw_classifier
from core.vuln_rules import apply_rules
from core.issues_store import issues_store
from core.killchain_store import killchain_store
from core.runner import PhaseRunner
from core.tools import TOOLS, get_tool_command, get_installed_tools


class ScannerEngine:
    """Runs supported scanning tools on macOS (no unsupported tool errors)."""

    MAX_CONCURRENT_TOOLS = 2

    TOOLS: Dict[str, Dict[str, object]] = {
        "nmap": {
            "cmd": ["nmap", "-sV", "-T4", "{target}"],
        },
        "whatweb": {
            "cmd": ["whatweb", "--log-json=-", "{target}"],
        },
        "wafw00f": {
            "cmd": ["wafw00f", "{target}", "-f", "json"],
        },
    }

    # Placeholder “weaponization” block (non-operational on macOS)
    WEAPONIZATION = {
        "placeholder": {
            "description": "Simulated exploitation logic — disabled for macOS safety.",
            "enabled": True,
        }
    }

    def __init__(self):
        self._last_results: List[dict] = []
        self._fingerprint_cache: set[str] = set()
        self._installed_meta: Dict[str, Dict[str, object]] = {}
        self._recon_edges: List[dict] = []
        self._recon_edge_keys: set[tuple] = set()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    async def scan(self, target: str, selected_tools: List[str] | None = None) -> AsyncGenerator[str, None]:
        """
        Async generator that yields log-style strings while the supported tools run.
        Each tool's raw output is saved to the evidence store and parsed into findings.
        """
        installed = self._detect_installed()
        self._installed_meta = installed
        self._last_results = []
        self._fingerprint_cache = set()
        self._recon_edges = []
        self._recon_edge_keys = set()

        selected_clean = [t for t in (selected_tools or []) if t in TOOLS]
        tools_to_run = list(installed.keys())
        missing: List[str] = []
        if selected_clean:
            tools_to_run = [t for t in selected_clean if t in installed]
            missing = [t for t in selected_clean if t not in installed]
        if selected_clean:
            yield f"[scanner] Selected tools: {', '.join(selected_clean)}"
        if missing:
            yield f"[scanner] Skipping (not installed): {', '.join(missing)}"

        if not tools_to_run:
            yield "[scanner] No supported tools available in PATH. Skipping tool phase."
            return
        else:
            yield f"Installed tools: {', '.join(tools_to_run)}"
            queue: asyncio.Queue[str] = asyncio.Queue()
            running: Dict[str, asyncio.Task[List[dict]]] = {}
            pending = list(tools_to_run)
            results_map: Dict[str, List[dict] | Exception] = {}

            while pending and len(running) < self.MAX_CONCURRENT_TOOLS:
                tool = pending.pop(0)
                running[tool] = asyncio.create_task(self._run_tool_task(tool, target, queue))
                await queue.put(f"[scanner] Started {tool} (batch launch)")

            while running:
                done, _ = await asyncio.wait(list(running.values()), timeout=0.2)
                while not queue.empty():
                    yield queue.get_nowait()
                for finished in done:
                    tool_name = next((name for name, t in running.items() if t is finished), None)
                    if tool_name:
                        try:
                            results_map[tool_name] = finished.result()
                        except Exception as exc:  # pragma: no cover
                            results_map[tool_name] = exc
                            await queue.put(f"[{tool_name}] task error: {exc}")
                        del running[tool_name]
                        if pending:
                            next_tool = pending.pop(0)
                            running[next_tool] = asyncio.create_task(self._run_tool_task(next_tool, target, queue))
                            await queue.put(f"[scanner] Started {next_tool} (batch launch)")
                if not done:
                    await asyncio.sleep(0.05)
            while not queue.empty():
                yield queue.get_nowait()

            for tool in tools_to_run:
                result = results_map.get(tool)
                if result is None:
                    continue
                if isinstance(result, Exception):
                    yield f"[{tool}] task error: {result}"
                    continue
                normalized = self._normalize_findings(result)
                if normalized:
                    findings_store.bulk_add(normalized)
                    self._last_results.extend(normalized)
                    yield f"[scanner] Recorded {len(normalized)} finding(s) from {tool}."
                    self._refresh_enrichment()

        phase_logs: List[str] = []
        phase_runner = PhaseRunner(target, phase_logs.append)
        phase_results = await phase_runner.run_all_phases()
        for msg in phase_logs:
            yield msg

        for phase_name, phase_findings in phase_results.items():
            normalized_phase = self._normalize_findings(phase_findings)
            if not normalized_phase:
                continue
            findings_store.bulk_add(normalized_phase)
            self._last_results.extend(normalized_phase)
            yield f"[phase] {phase_name} produced {len(normalized_phase)} finding(s)."
            recon_edges = self._build_recon_edges(normalized_phase)
            if recon_edges:
                self._record_recon_edges(recon_edges)
            self._refresh_enrichment()

        issues_count, edge_count = self._refresh_enrichment()
        yield f"[rules] {issues_count} correlated issue(s)."
        yield f"[killchain] {edge_count} relationship edge(s) generated."
        yield "[scanner] Scan run complete."

    async def run_all(self, target: str):
        """
        Compatibility helper: run the scan generator and return aggregated findings.
        """
        async for _ in self.scan(target):
            # Discard streamed lines – this helper mirrors the old API surface.
            pass
        return list(self._last_results)

    # ----------------------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------------------
    def _detect_installed(self) -> Dict[str, Dict[str, object]]:
        return get_installed_tools()

    def _normalize_findings(self, items: List[dict] | None) -> List[dict]:
        normalized: List[dict] = []
        if not items:
            return normalized

        for item in items:
            entry = dict(item)
            entry.setdefault("message", entry.get("proof", ""))
            entry.setdefault("tags", [])
            entry.setdefault("families", [])
            entry.setdefault("metadata", {})
            severity = str(entry.get("severity", "INFO")).upper()
            entry["severity"] = severity
            original_target = entry.get("target") or entry.get("asset") or "unknown"
            asset = self._normalize_asset(original_target)
            entry.setdefault("metadata", {})
            entry["metadata"].setdefault("original_target", original_target)
            entry["asset"] = asset
            entry["target"] = asset
            fingerprint = entry.setdefault(
                "fingerprint",
                f"{entry.get('tool', 'scanner')}:{asset}:{entry.get('type', 'generic')}:{severity}"
            )
            if fingerprint in self._fingerprint_cache:
                continue
            self._fingerprint_cache.add(fingerprint)
            normalized.append(entry)
        return normalized

    def get_last_results(self) -> List[dict]:
        """Return the findings produced by the most recent scan."""
        return list(self._last_results)

    def _build_recon_edges(self, findings: List[dict]) -> List[dict]:
        edges: List[dict] = []
        for item in findings:
            families = item.get("families", [])
            recon_families = [fam for fam in families if fam.startswith("recon-phase")]
            if not recon_families:
                continue
            metadata = item.get("metadata") or {}
            variant = metadata.get("variant") or "behavior"
            for fam in recon_families:
                edges.append({
                    "source": item.get("asset", "unknown"),
                    "target": f"{fam}:{variant}",
                    "label": item.get("type"),
                    "severity": item.get("severity"),
                    "tags": item.get("tags", []),
                    "signal": item.get("message"),
                    "families": families,
                    "edge_type": "behavioral-signal",
                })
        return edges

    def _record_recon_edges(self, edges: List[dict]):
        for edge in edges:
            key = self._edge_signature(edge)
            if key in self._recon_edge_keys:
                continue
            self._recon_edge_keys.add(key)
            self._recon_edges.append(edge)

    def _edge_signature(self, edge: dict) -> tuple:
        return (
            edge.get("source"),
            edge.get("target"),
            edge.get("label"),
            edge.get("edge_type"),
            edge.get("severity"),
        )

    def _refresh_enrichment(self) -> tuple[int, int]:
        if self._last_results:
            enriched, _, killchain_edges = apply_rules(self._last_results)
        else:
            enriched, killchain_edges = [], []

        issues_store.replace_all(enriched)
        combined_edges = list(killchain_edges) + list(self._recon_edges)
        killchain_store.replace_all(combined_edges)
        return len(enriched), len(combined_edges)

    async def _run_tool_task(self, tool: str, target: str, queue: asyncio.Queue[str]) -> List[dict]:
        meta_override = self._installed_meta.get(tool)
        cmd = get_tool_command(tool, target, meta_override)
        await queue.put(f"--- Running {tool} ---")
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
        except FileNotFoundError:
            msg = f"[{tool}] NOT INSTALLED or not in PATH."
            evidence_store.save_text(f"{tool}_error", target, msg)
            await queue.put(msg)
            return []
        except Exception as exc:
            msg = f"[{tool}] failed to start: {exc}"
            evidence_store.save_text(f"{tool}_error", target, msg)
            await queue.put(msg)
            return []

        output_lines: List[str] = []
        assert proc.stdout is not None
        while True:
            line = await proc.stdout.readline()
            if not line:
                break
            text = line.decode("utf-8", errors="ignore").rstrip()
            if not text:
                continue
            output_lines.append(text)
            await queue.put(f"[{tool}] {text}")

        exit_code = await proc.wait()
        await queue.put(f"[{tool}] Exit code: {exit_code}")

        output_text = "\n".join(output_lines)
        evidence_store.save_text(tool, target, output_text)

        try:
            return raw_classifier.classify(tool, target, output_text)
        except Exception as exc:
            err = f"[{tool}] classifier error: {exc}"
            evidence_store.save_text(f"{tool}_classifier_error", target, err)
            await queue.put(err)
            return []

    def _normalize_asset(self, target: str) -> str:
        parsed = urlparse(target)
        host = parsed.hostname or target
        if host.startswith("www."):
            host = host[4:]
        return host
