"""
Phase 11 Logic Verification Tests

Tests the implementation of Phase 11 tools and confirmation flows.
Verifies compliance with:
- LAW 1 (Human Sovereignty / Confirmation)
- LAW 4 (Tool-only execution)
- LAW 15 (Secret Isolation)
"""

import unittest
import tempfile
import shutil
import os
from pathlib import Path
from uuid import uuid4

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.tool_registry import ToolRegistry
from tools.tool_executor import ToolExecutor
from orchestrator.orchestrator import Orchestrator
from orchestrator.task_queue import TaskSource

# Import tools
from tools.system.resource_monitor_tool import make_resource_monitor_tool, resource_monitor_impl
from tools.file.file_read_tool import make_file_read_tool, file_read_impl
from tools.file.file_write_tool import make_file_write_tool, file_write_impl
from tools.file.file_list_tool import make_directory_list_tool, directory_list_impl
from tools.automation_tools import make_trigger_automation_tool

class TestPhase11Tools(unittest.TestCase):
    def setUp(self):
        self.registry = ToolRegistry()
        self.executor = ToolExecutor()
        self.temp_dir = tempfile.mkdtemp()
        
        # Register implementations
        self.executor.register("resource_monitor", resource_monitor_impl)
        self.executor.register("file_read", file_read_impl)
        self.executor.register("file_write", file_write_impl)
        self.executor.register("directory_list", directory_list_impl)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_tool_registration(self):
        """Verify all new tools can be registered correctly."""
        tools = [
            make_resource_monitor_tool(),
            make_file_read_tool(),
            make_file_write_tool(),
            make_directory_list_tool(),
            make_trigger_automation_tool(),
        ]
        
        for tool in tools:
            self.registry.register(tool)
            self.assertTrue(self.registry.exists(tool.name))
            
        # Verify categories
        self.assertEqual(self.registry.get("resource_monitor").category, "system")
        self.assertEqual(self.registry.get("file_write").category, "file")
        self.assertEqual(self.registry.get("trigger_automation").category, "automation")

    def test_confirmation_requirement(self):
        """Verify LAW 1: Certain tools must require confirmation."""
        # Write tool requires confirmation
        write_tool = make_file_write_tool()
        self.assertTrue(write_tool.requires_confirmation)
        
        # Read tool does not
        read_tool = make_file_read_tool()
        self.assertFalse(read_tool.requires_confirmation)
        
        # Trigger automation requires confirmation
        trigger = make_trigger_automation_tool()
        self.assertTrue(trigger.requires_confirmation)

    def test_file_security_law15(self):
        """Verify LAW 15: Secret isolation (blocked patterns)."""
        # Test blocking secrets in file_read
        result = file_read_impl({"path": "/opt/siya/.env"})
        self.assertEqual(result["status"], "error")
        self.assertIn("blocked pattern", result["message"])
        
        # Test blocking secrets in file_write
        result = file_write_impl({"path": "/opt/siya/secrets.txt", "content": "fail"})
        self.assertEqual(result["status"], "error")
        self.assertIn("blocked pattern", result["message"])
        
        # Test directory restriction
        result = file_read_impl({"path": "/etc/shadow"})
        self.assertEqual(result["status"], "error")
        self.assertIn("allowed directories", result["message"])

    def test_directory_list(self):
        """Verify directory listing."""
        # Create some test files
        Path(self.temp_dir).joinpath("file1.txt").touch()
        Path(self.temp_dir).joinpath("file2.txt").touch()
        os.makedirs(Path(self.temp_dir).joinpath("subdir"))
        
        # Mock ALLOWED_BASE_DIRS for this test
        import tools.file.file_list_tool as flt
        original_dirs = flt.ALLOWED_BASE_DIRS
        flt.ALLOWED_BASE_DIRS = [self.temp_dir]
        
        try:
            result = directory_list_impl({"path": self.temp_dir})
            self.assertEqual(result["status"], "ok")
            names = [e["name"] for e in result["entries"]]
            self.assertIn("file1.txt", names)
            self.assertIn("file2.txt", names)
            self.assertIn("subdir", names)
        finally:
            flt.ALLOWED_BASE_DIRS = original_dirs

    def test_orchestrator_confirmation_flow(self):
        """Verify specific Phase 11 Orchestrator confirmation flow logic."""
        # Setup orchestrator with mock MCP
        class MockMCP:
            def get_tool_registry(self):
                reg = ToolRegistry()
                reg.register(make_file_write_tool())
                return reg
                
            def validate_and_authorize(self, request):
                class AuthResult:
                    def __init__(self, authorized, requires_confirmation):
                        self.authorized = authorized
                        self.requires_confirmation = requires_confirmation
                        self.error_code = None
                        self.error_message = None
                
                # Check based on request
                return AuthResult(True, request.get("requires_confirmation", False))

        orch = Orchestrator(mcp=MockMCP(), tool_executor=self.executor)
        orch.start()
        
        # create a tool request that requires confirmation
        tool_req = {
            "type": "tool_request",
            "request_id": str(uuid4()),
            "tool_name": "file_write",
            "arguments": {"path": str(Path(self.temp_dir) / "test.txt"), "content": "hello"},
            "requires_confirmation": True
        }
        
        # Manually inject pending request since we're testing flow logic
        task_id = uuid4()
        # Mock internal state to simulate a pending task with this request
        # (This is a bit invasive but necessary for unit testing internal flow without full system spinup)
        # However, improved way: Use orchestrator.submit_task and mocking intent parsing to produce this request.
        # But for unit test simplicity, we will test the confirm_execution mechanics directly if we can't easily inject.
        
        # Let's rely on `_pending_confirmations` manipulation which we added
        orch._pending_confirmations[task_id] = {
            "tool_request": tool_req,
            "task": None, # Mock
            "step_id": "step_1",
            "tool_name": "file_write",
            "arguments": tool_req["arguments"],
            "message": "Confirm?"
        }
        
        # Mock ALLOWED_WRITE_DIRS
        import tools.file.file_write_tool as fwt
        original_dirs = fwt.ALLOWED_WRITE_DIRS
        fwt.ALLOWED_WRITE_DIRS = [self.temp_dir]
        
        try:
            # Confirm execution
            result = orch.confirm_execution(task_id)
            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["confirmed"], True)
            
            # Verify file written
            with open(Path(self.temp_dir) / "test.txt", "r") as f:
                content = f.read()
            self.assertEqual(content, "hello")
            
        finally:
            fwt.ALLOWED_WRITE_DIRS = original_dirs
            orch.stop()

if __name__ == "__main__":
    unittest.main()
