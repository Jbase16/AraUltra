# core/ai_engine.py
# Central analysis engine for AraUltra

from __future__ import annotations

from typing import Dict, List

from core.findings_store import findings_store
from core.killchain_store import killchain_store
from core.evidence_store import EvidenceStore


class AIEngine:
    """
    Central analysis engine.
    Responsible for:
      - Summarizing tool output
      - Extracting findings
      - Mapping findings to killchain phases
      - Updating evidence with structured info
      - Answering natural-language questions about the current state
      - Producing short live commentary per tool run
    """

    _instance = None

    @staticmethod
    def instance():
        if AIEngine._instance is None:
            AIEngine._instance = AIEngine()
        return AIEngine._instance

    # ---------------------------------------------------------
    # Construction
    # ---------------------------------------------------------
    def __init__(self):
        # Placeholder for optional future LLM client
        pass

    # ---------------------------------------------------------
    # Main tool-output pipeline
    # ---------------------------------------------------------
    def process_tool_output(
        self,
        tool_name: str,
        stdout: str,
        stderr: str,
        rc: int,
        metadata: Dict,
    ):
        """
        Primary handler for all tool outputs.
        Called automatically by TaskRouter via tool_callback_factory.
        """

        # Step 1: store raw evidence
        evidence_id = EvidenceStore.instance().add_evidence(
            tool=tool_name,
            raw_output=stdout,
            metadata=metadata,
        )

        # Step 2: generate summary
        summary = self._summarize_output(tool_name, stdout, stderr, rc)

        # Step 3: extract findings
        findings = self._extract_findings(tool_name, stdout, stderr, rc)

        # Step 4: map killchain phases
        phases = self._infer_killchain_phases(findings)

        # Step 5: update global stores
        for f in findings:
            findings_store.add_finding(f)

        for p in phases:
            killchain_store.add_phase(p)

        # Step 6: enrich the evidence entry
        EvidenceStore.instance().update_evidence(
            evidence_id,
            summary=summary,
            findings=findings,
        )

        # Step 7: generate short live commentary for UI
        target = metadata.get("target") if metadata else None
        live_comment = self._live_commentary(
            tool_name=tool_name,
            target=target,
            summary=summary,
            findings=findings,
            phases=phases,
        )

        return {
            "summary": summary,
            "findings": findings,
            "killchain_phases": phases,
            "evidence_id": evidence_id,
            "live_comment": live_comment,
        }

    # ---------------------------------------------------------
    # Local summarization + extraction
    # ---------------------------------------------------------
    def _summarize_output(self, tool: str, stdout: str, stderr: str, rc: int) -> str:
        stdout = (stdout or "").strip()
        stderr = (stderr or "").strip()

        if not stdout and not stderr:
            return f"{tool} produced no output (rc={rc})."

        parts = [f"{tool} completed with exit code {rc}."]

        if stdout:
            parts.append(f"Stdout length: {len(stdout)} characters.")
            if "error" in stdout.lower():
                parts.append("Stdout appears to contain error messages.")
        else:
            parts.append("No stdout captured.")

        if stderr:
            parts.append(f"Stderr length: {len(stderr)} characters.")
        else:
            parts.append("No stderr captured.")

        return " ".join(parts)

    def _extract_findings(
        self,
        tool: str,
        stdout: str,
        stderr: str,
        rc: int,
    ) -> List[Dict]:
        """
        Very primitive placeholder extraction logic.
        Upgrade this later with real parsing or LLM-based extraction.
        """
        findings: List[Dict] = []
        out = f"{stdout}\n{stderr}".lower()

        # Example heuristic: open ports from nmap
        if "open" in out and tool == "nmap":
            findings.append({
                "tool": tool,
                "type": "open_port_indicator",
                "value": "Nmap output includes references to open ports.",
                "severity": "medium",
            })

        # Example heuristic: HTTP tech stack detection
        if tool == "httpx" and ("tech" in out or "technology" in out):
            findings.append({
                "tool": tool,
                "type": "tech_stack",
                "value": "HTTP probing indicates specific technologies in use.",
                "severity": "low",
            })

        # Any explicit "error" mention
        if "error" in out:
            findings.append({
                "tool": tool,
                "type": "tool_error",
                "value": "Tool output appears to contain errors or failed checks.",
                "severity": "low",
            })

        # Non-zero exit code
        if rc != 0:
            findings.append({
                "tool": tool,
                "type": "non_zero_exit",
                "value": f"{tool} exited with non-zero return code {rc}.",
                "severity": "low",
            })

        return findings

    def _infer_killchain_phases(self, findings: List[Dict]) -> List[str]:
        """
        Maps simple finding types to MITRE-style high-level phases.
        """
        phases = set()

        for f in findings:
            ftype = f.get("type")
            if ftype in ("open_port_indicator", "tech_stack"):
                phases.add("Reconnaissance")
            if ftype in ("tool_error", "non_zero_exit"):
                phases.add("Resource Development")

        return sorted(list(phases))

    # ---------------------------------------------------------
    # Live one-line commentary for the AI feed
    # ---------------------------------------------------------
    def _live_commentary(
        self,
        tool_name: str,
        target: str | None,
        summary: str,
        findings: List[Dict],
        phases: List[str],
    ) -> str:
        tgt = target or "target"

        if not findings:
            return f"{tool_name} finished against {tgt}; no concrete issues extracted yet."

        sev_counts: Dict[str, int] = {}
        for f in findings:
            sev = f.get("severity", "unknown")
            sev_counts[sev] = sev_counts.get(sev, 0) + 1

        sev_bits = [f"{count} {sev}" for sev, count in sorted(sev_counts.items())]
        sev_str = ", ".join(sev_bits)

        phase_str = ", ".join(phases) if phases else "no killchain phase yet"

        return (
            f"{tool_name} on {tgt}: {len(findings)} finding(s) "
            f"({sev_str}); currently mapped to {phase_str}."
        )

    # ---------------------------------------------------------
    # Chat-style AI interface
    # ---------------------------------------------------------
    def chat(self, question: str) -> str:
        """
        Answer a natural-language question based on stored evidence & findings.
        Deterministic and local for now, but structured so you can later
        plug in a real LLM.
        """
        question = (question or "").strip()
        evidence = EvidenceStore.instance().get_all()
        findings = findings_store.get_all()
        phases = killchain_store.get_phases()

        if not evidence and not findings:
            return (
                "Right now there is no evidence or findings to reason about.\n\n"
                "Run some tools from the Scanner tab first, then come back and "
                "ask about attack surface, risks, or next steps."
            )

        lines: List[str] = []

        lines.append(f"Question: {question}")
        lines.append("")

        # High-level situation
        lines.append("=== High-level assessment ===")
        lines.append(f"- Total evidence items: {len(evidence)}")
        lines.append(f"- Total findings: {len(findings)}")
        if phases:
            lines.append(f"- Killchain phases observed: {', '.join(phases)}")
        else:
            lines.append("- No specific killchain phases inferred yet.")
        lines.append("")

        # Severity breakdown
        if findings:
            sev_counts = {}
            for f in findings:
                sev = f.get("severity", "unknown")
                sev_counts[sev] = sev_counts.get(sev, 0) + 1

            lines.append("=== Severity overview ===")
            for sev, count in sorted(sev_counts.items(), key=lambda x: x[0]):
                lines.append(f"- {sev}: {count} finding(s)")
            lines.append("")

        # Answer style: pragmatic guidance
        lines.append("=== Reasoned answer ===")

        q_lower = question.lower()

        if any(k in q_lower for k in ("critical", "biggest risk", "most important")):
            high = [f for f in findings if f.get("severity") in ("high", "critical")]
            if high:
                lines.append(
                    "You asked about the most critical issues. The highest-severity "
                    "findings currently recorded are:"
                )
                for f in high[:10]:
                    lines.append(
                        f"- ({f.get('severity')}) {f.get('type')} from {f.get('tool')}: "
                        f"{f.get('value','')}"
                    )
            else:
                lines.append(
                    "There are no findings explicitly marked as high or critical severity yet. "
                    "At this stage it looks more like low-to-medium recon intel than confirmed "
                    "exploitable issues."
                )
        elif any(k in q_lower for k in ("next step", "what should i do", "prioritize")):
            lines.append(
                "Treat the current results as reconnaissance data. Practical next steps:\n"
                "1. Validate that exposed services (open ports, web endpoints) are expected.\n"
                "2. Lock down anything that isn't strictly necessary (firewall or remove).\n"
                "3. Review HTTP tech stack and versions against known CVEs.\n"
                "4. If this is a lab target, chain what you've found into an attack path and "
                "document mitigations."
            )
        elif "recon" in q_lower or "reconnaissance" in q_lower:
            lines.append(
                "From a recon perspective, the tools you've run are mapping services, "
                "subdomains, and HTTP behavior. That data is enough to:\n"
                "- Build an inventory of reachable hosts and apps.\n"
                "- Identify technologies and potential weak points.\n"
                "- Decide where deeper, authenticated testing would add value."
            )
        else:
            # Generic but grounded in data
            lines.append(
                "Based on the current evidence and findings, this looks like an early-stage "
                "reconnaissance snapshot rather than a fully developed attack chain.\n"
            )
            if phases:
                lines.append(
                    "The inferred killchain phases suggest the activity is currently focused on: "
                    + ", ".join(phases)
                    + "."
                )
            if findings:
                lines.append(
                    "Use the Findings tab to drill into individual entries and decide what "
                    "matters in your environment."
                )

        lines.append("")
        lines.append(
            "For more targeted analysis, try questions like:\n"
            "- \"What do these Nmap results imply about exposed services?\"\n"
            "- \"Are there any indicators of misconfiguration in the HTTP stack?\"\n"
            "- \"What should I lock down first on this host?\""
        )

        return "\n".join(lines)