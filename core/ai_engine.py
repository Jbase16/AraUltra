# core/ai_engine.py
# Ollama-based AI assistant for analysis and reporting (defensive / descriptive only)

from __future__ import annotations

import json
from typing import List, Dict, Any, Optional

import requests

from core.findings import findings_store
from core.reasoning import reasoning_engine

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2:3b"  # adjust if you use another model


class AIEngine:
    def __init__(self, base_url: str = OLLAMA_URL, model: str = MODEL_NAME):
        self.base_url = base_url
        self.model = model

    def _generate(self, prompt: str, temperature: float = 0.2, max_tokens: int = 1024) -> str:
        """
        Call Ollama /api/generate with a prompt.
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        try:
            resp = requests.post(self.base_url, json=payload, timeout=180)
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "").strip() or "AI returned an empty response."
        except Exception as e:
            return f"AI ERROR: {e}"

    def summarize_findings(self) -> str:
        """
        Provide a high-level, defensive, bug-bounty-style summary of all findings.
        No exploit payloads, only descriptions, risk context, and mitigation.
        """
        all_findings = findings_store.get_all()
        reasoning_data = reasoning_engine.analyze()
        if not all_findings and not reasoning_data.get("issues"):
            return "No findings available for analysis."

        findings_json = json.dumps(all_findings, indent=2)
        reasoning_json = json.dumps(reasoning_data, indent=2)
        prompt = f"""
        You are a senior application security engineer.

        You are given a list of reconnaissance findings from a security scanner.
        Your job is to:

        1. Group the findings by vulnerability TYPE and SEVERITY.
        2. Explain, in high-level terms, what each issue means in the context of web security.
        3. Describe realistic risk and impact in a bug bounty context.
        4. Suggest defensive mitigations and hardening steps.
        5. DO NOT provide exploit code, payloads, or step-by-step attack instructions.
           Focus purely on description, risk, and remediation.

        Findings (JSON):
        {findings_json}

        Reasoning context (attack paths, recommendations, correlated issues):
        {reasoning_json}
        """

        return self._generate(prompt)

    def generate_report(self) -> str:
        """
        Generate a full bug-bounty-style report (markdown-like text).
        Again: descriptive, defensive, no exploit payloads.
        """
        all_findings = findings_store.get_all()
        reasoning_data = reasoning_engine.analyze()
        if not all_findings and not reasoning_data.get("issues"):
            return "# AraUltra Report\n\nNo findings to report."

        findings_json = json.dumps(all_findings, indent=2)
        reasoning_json = json.dumps(reasoning_data, indent=2)
        prompt = f"""
        You are a security engineer writing a professional bug bounty report.

        You will receive a list of structured findings from a recon engine.
        Produce a single markdown-style report that includes:

        - Executive Summary
        - Scope (targets)
        - Methodology (recon tools, passive analysis)
        - Detailed Findings:
          - Title
          - Severity
          - A short description of the issue class
          - Observed evidence (from the findings)
          - Impact (business and technical)
          - Likelihood
          - Remediation Recommendations
        - Overall Risk & Hardening Recommendations

        Very important rules:
        - DO NOT include any exploit payloads or step-by-step exploit chains.
        - DO NOT show concrete injection strings, shell commands, or weaponized content.
        - You may talk about classes of issues (e.g. SQL injection, XSS) at a high-level only.
        - Focus on helping defenders understand and fix issues.

        Findings (JSON):
        {findings_json}

        Reasoning context (attack paths, degraded paths, recommended phases, correlated issues):
        {reasoning_json}
        """

        return self._generate(prompt, max_tokens=2048)

    def answer_custom_question(self, question: str) -> str:
        """
        Allow the user to ask a question in the context of current findings.
        """
        all_findings = findings_store.get_all()
        findings_json = json.dumps(all_findings, indent=2)
        reasoning_json = json.dumps(reasoning_engine.analyze(), indent=2)

        prompt = f"""
        You are a senior security engineer.

        The user will ask a question about a target or set of findings.
        You may reference the existing findings when useful.

        Constraints:
        - Answer in a concise, practical way.
        - Focus on risk, triage, and defense.
        - DO NOT provide exploit payloads or exploit automation.
        - It is okay to explain web security concepts, but avoid weaponized detail.

        Current findings (JSON, may be empty):
        {findings_json}

        Correlation/reasoning context:
        {reasoning_json}

        User question:
        {question}
        """

        return self._generate(prompt, max_tokens=1024)

    def reasoning_snapshot(self) -> Dict[str, object]:
        """Expose structured reasoning data for UI layers."""
        return reasoning_engine.analyze()


# global instance
ai_engine = AIEngine()
