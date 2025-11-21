import unittest
from unittest.mock import patch, MagicMock
import json
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock PyQt6
sys.modules["PyQt6"] = MagicMock()
sys.modules["PyQt6.QtCore"] = MagicMock()
sys.modules["PyQt6.QtWidgets"] = MagicMock()

# Mock Store Modules
evidence_store_mock = MagicMock()
sys.modules["core.evidence_store"] = evidence_store_mock
findings_store_mock = MagicMock()
sys.modules["core.findings_store"] = findings_store_mock
killchain_store_mock = MagicMock()
sys.modules["core.killchain_store"] = killchain_store_mock

from core.ai_engine import AIEngine, OllamaClient

class TestAIIntegration(unittest.TestCase):
    
    def setUp(self):
        # Reset singleton
        AIEngine._instance = None

    @patch('urllib.request.urlopen')
    def test_ollama_client_generate(self, mock_urlopen):
        # Mock successful Ollama response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps({
            "response": json.dumps({
                "findings": [
                    {
                        "type": "Open Port",
                        "severity": "LOW",
                        "value": "Port 80 is open",
                        "technical_details": "Nmap scan found port 80/tcp open"
                    }
                ]
            })
        }).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        client = OllamaClient("http://localhost:11434", "llama3:latest")
        response = client.generate("test prompt")
        
        self.assertIn("Port 80 is open", response)

    @patch('core.ai_engine.OllamaClient.check_connection')
    @patch('core.ai_engine.OllamaClient.generate')
    def test_ai_engine_process_output(self, mock_generate, mock_check_conn):
        # Mock connection success
        mock_check_conn.return_value = True
        
        # Mock LLM generation
        mock_generate.return_value = json.dumps({
            "findings": [
                {
                    "type": "Critical Vuln",
                    "severity": "HIGH",
                    "value": "SQL Injection detected",
                    "technical_details": "Payload ' OR 1=1 caused delay"
                }
            ]
        })

        engine = AIEngine.instance()
        
        # Simulate tool output
        result = engine.process_tool_output(
            tool_name="sqlmap",
            stdout="...detected...",
            stderr="",
            rc=0,
            metadata={"target": "example.com"}
        )

        # Verify findings were extracted via LLM
        findings = result['findings']
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]['type'], "Critical Vuln")
        self.assertEqual(findings[0]['severity'], "HIGH")
        self.assertTrue(findings[0]['ai_generated'])

if __name__ == '__main__':
    unittest.main()
