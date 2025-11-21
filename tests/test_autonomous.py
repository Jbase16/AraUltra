import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import json
import sys
import os
import asyncio

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock PyQt6
sys.modules["PyQt6"] = MagicMock()
sys.modules["PyQt6.QtCore"] = MagicMock()
sys.modules["PyQt6.QtWidgets"] = MagicMock()

# Mock Store Modules
sys.modules["core.evidence_store"] = MagicMock()
sys.modules["core.findings_store"] = MagicMock()
sys.modules["core.killchain_store"] = MagicMock()
sys.modules["core.issues_store"] = MagicMock()

from core.ai_engine import AIEngine
from core.scan_orchestrator import ScanOrchestrator
from core.task_router import TaskRouter

class TestAutonomousActions(unittest.IsolatedAsyncioTestCase):
    
    def setUp(self):
        AIEngine._instance = None
        TaskRouter._instance = None

    @patch('core.ai_engine.OllamaClient')
    @patch('core.scanner_engine.ScannerEngine._run_tool_task')
    async def test_autonomous_loop(self, mock_run_tool, MockOllamaClient):
        # Setup Mock AI Client
        mock_client = MockOllamaClient.return_value
        mock_client.check_connection.return_value = True
        
        # Mock AI response with Next Steps
        mock_client.generate.return_value = json.dumps({
            "findings": [{"type": "Open Port", "severity": "LOW", "value": "Port 80 open"}],
            "next_steps": [
                {
                    "tool": "nikto",
                    "args": ["-h", "example.com"],
                    "reason": "Found web server"
                }
            ]
        })

        # Setup Orchestrator
        orchestrator = ScanOrchestrator()
        
        # Mock initial scan tool execution
        # We need to simulate the scanner yielding logs and calling TaskRouter
        async def mock_scan_generator(target):
            yield "[scanner] Started nmap"
            # Simulate tool output processing
            TaskRouter.instance().handle_tool_output(
                "nmap", "output", "", 0, {"target": target}
            )
            yield "[scanner] Finished nmap"
            
            # Wait a bit for async callbacks to propagate
            await asyncio.sleep(0.1)

        # Patch the scanner.scan method to use our generator
        # But we also need the real queueing logic to work.
        # So we should probably use the real scanner but mock the subprocess part.
        
        # Let's try a different approach: Test the Orchestrator callback directly.
        
        # 1. Trigger the callback manually
        payload = {
            "next_steps": [
                {"tool": "nikto", "args": ["-h", "example.com"], "reason": "Found web server"}
            ]
        }
        
        # Mock the scanner's queue_task method
        orchestrator.scanner.queue_task = MagicMock()
        orchestrator.current_target = "example.com"
        
        # Fire the event
        orchestrator._handle_autonomous_actions(payload)
        
        # Assert queue_task was called
        orchestrator.scanner.queue_task.assert_called_with("nikto", ["-h", "example.com"])

if __name__ == '__main__':
    unittest.main()
