import json
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
      - Mapping findings to killchain
      - Storing structured evidence
    """

    _instance = None

    @staticmethod
    def instance():
        if AIEngine._instance is None:
            AIEngine._instance = AIEngine()
        return AIEngine._instance

    # ---------------------------------------------------------
    # Main AI processing entrypoint
    # ---------------------------------------------------------
    def process_tool_output(self, tool_name: str, stdout: str, stderr: str, rc: int, metadata: Dict):
        """
        Primary handler for all tool outputs.
        Called automatically by TaskRouter.
        """

        # Step 1: store raw evidence
        evidence_id = EvidenceStore.instance(
            tool=tool_name,
            raw_output=stdout,
            metadata=metadata
        )

        # Step 2: generate summary
        summary = self._summarize_output(tool_name, stdout)

        # Step 3: extract findings
        findings = self._extract_findings(tool_name, stdout)

        # Step 4: map killchain phases
        phases = self._infer_killchain_phases(findings)

        # Step 5: update stores
        for f in findings:
            findings_store.add_finding(f)

        for p in phases:
            killchain_store.add_phase(p)

        # Step 6: update evidence with summary/findings
        EvidenceStore.instance().update_evidence(
            evidence_id,
            summary=summary,
            findings=findings
        )

        return {
            "summary": summary,
            "findings": findings,
            "killchain_phases": phases,
            "evidence_id": evidence_id
        }

    # ---------------------------------------------------------
    # AI simulation (replace with real OpenAI / Ollama later)
    # ---------------------------------------------------------
    def _summarize_output(self, tool: str, output: str) -> str:
        if not output.strip():
            return f"No meaningful output from {tool}."

        # Fake summary for now — replace with LLM call later.
        return f"{tool} executed successfully. Output length: {len(output)} characters."

    def _extract_findings(self, tool: str, output: str) -> List[Dict]:
        """
        Very primitive placeholder. Soon: use GPT for extraction.
        """
        findings = []

        if "open" in output.lower():
            findings.append({
                "tool": tool,
                "type": "open_port",
                "value": "Detected reference to 'open' in output.",
                "severity": "medium"
            })

        if "error" in output.lower():
            findings.append({
                "tool": tool,
                "type": "tool_error",
                "value": "Detected errors in output.",
                "severity": "low"
            })

        return findings

    def _infer_killchain_phases(self, findings: List[Dict]) -> List[str]:
        """
        Maps findings to MITRE killchain phases.
        """
        phases = set()

        for f in findings:
            if f["type"] == "open_port":
                phases.add("Reconnaissance")
            if f["type"] == "tool_error":
                phases.add("Resource Development")

        return list(phases)