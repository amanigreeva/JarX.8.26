"""
tests/test_training_manager.py

Comprehensive tests for the JarX-8.26 AI Training Manager.
Tests hardware detection, job lifecycle, checkpoint management, and edge cases.
"""

import json
import os
import sys
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestHardwareDetection(unittest.TestCase):
    """Test local hardware detection."""

    def test_detect_hardware_returns_dict(self):
        from services.training.hardware import detect_hardware
        info = detect_hardware()
        self.assertIsInstance(info, dict)
        self.assertIn("cpu", info)
        self.assertIn("ram_total_gb", info)
        self.assertIn("gpu_available", info)

    def test_detect_hardware_cpu_info(self):
        from services.training.hardware import detect_hardware
        info = detect_hardware()
        self.assertIsInstance(info["cpu"], str)
        self.assertGreater(len(info["cpu"]), 0)

    def test_detect_hardware_ram_positive(self):
        from services.training.hardware import detect_hardware
        info = detect_hardware()
        self.assertGreater(info["ram_total_gb"], 0)


class TestTrainingModels(unittest.TestCase):
    """Test Pydantic models and enums."""

    def test_training_status_values(self):
        from services.training.models import TrainingJobStatus
        self.assertEqual(TrainingJobStatus.CREATED.value, "CREATED")
        self.assertEqual(TrainingJobStatus.RUNNING.value, "RUNNING")
        self.assertEqual(TrainingJobStatus.COMPLETED.value, "COMPLETED")
        self.assertEqual(TrainingJobStatus.FAILED.value, "FAILED")

    def test_training_mode_values(self):
        from services.training.models import TrainingMode
        self.assertEqual(TrainingMode.LOCAL.value, "local")
        self.assertEqual(TrainingMode.REMOTE.value, "remote")

    def test_training_config_defaults(self):
        from services.training.models import TrainingConfig
        config = TrainingConfig(
            model_path="test_model",
            dataset_path="test_data",
            epochs=5,
        )
        self.assertEqual(config.epochs, 5)
        self.assertEqual(config.batch_size, 32)
        self.assertEqual(config.learning_rate, 0.001)
        self.assertFalse(config.mixed_precision)
        self.assertEqual(config.checkpoint_interval, 1)


class TestTrainingManager(unittest.TestCase):
    """Test TrainingManager job lifecycle."""

    def setUp(self):
        """Create a temporary data directory for testing."""
        self.test_dir = tempfile.mkdtemp(prefix="jarx_training_test_")

    def tearDown(self):
        """Clean up test directory."""
        try:
            shutil.rmtree(self.test_dir, ignore_errors=True)
        except Exception:
            pass

    def test_create_job(self):
        """Test creating a training job."""
        from services.training.manager import TrainingManager

        with patch('services.training.manager.DATA_DIR', self.test_dir):
            manager = TrainingManager()
            result = manager.create_job(
                name="test_job",
                mode="local",
                config={
                    "model_path": "models/test",
                    "dataset_path": "data/test.csv",
                    "epochs": 5,
                    "batch_size": 16,
                }
            )

            self.assertIsNotNone(result)
            self.assertIsNotNone(result.job_id)
            self.assertEqual(result.name, "test_job")
            self.assertEqual(result.mode.value, "local")
            self.assertIsNotNone(result.status)

    def test_list_jobs_empty(self):
        """Test listing jobs when none exist."""
        from services.training.manager import TrainingManager

        with patch('services.training.manager.DATA_DIR', self.test_dir):
            manager = TrainingManager()
            jobs = manager.list_jobs()
            self.assertIsInstance(jobs, list)

    def test_get_nonexistent_job(self):
        """Test getting a job that doesn't exist."""
        from services.training.manager import TrainingManager

        with patch('services.training.manager.DATA_DIR', self.test_dir):
            manager = TrainingManager()
            result = manager.get_job("nonexistent_id")
            self.assertIsNone(result)

    def test_create_and_retrieve_job(self):
        """Test creating and then retrieving a job."""
        from services.training.manager import TrainingManager

        with patch('services.training.manager.DATA_DIR', self.test_dir):
            manager = TrainingManager()
            created = manager.create_job(
                name="retrieve_test",
                mode="local",
                config={
                    "model_path": "models/bert",
                    "dataset_path": "data/train.csv",
                    "epochs": 10,
                }
            )

            job_id = created.job_id
            retrieved = manager.get_job(job_id)
            self.assertIsNotNone(retrieved)
            self.assertEqual(retrieved.name, "retrieve_test")


class TestRemoteEngine(unittest.TestCase):
    """Test remote engine stubs."""

    def test_remote_not_configured(self):
        """Remote engine should indicate it's not configured."""
        from services.training.remote_engine import RemoteTrainingEngine
        engine = RemoteTrainingEngine()
        result = engine.check_connection("localhost", 8443)
        self.assertFalse(result)


class TestAgentTools(unittest.TestCase):
    """Test agent tool wrappers."""

    def test_detect_hardware_tool(self):
        """Test DetectHardwareTool returns valid JSON."""
        from src.agent_tools.training_tools import DetectHardwareTool
        tool = DetectHardwareTool()
        result = tool.execute("")
        parsed = json.loads(result)
        self.assertIn("cpu", parsed)

    def test_list_training_jobs_tool(self):
        """Test ListTrainingJobsTool returns valid JSON."""
        from src.agent_tools.training_tools import ListTrainingJobsTool
        tool = ListTrainingJobsTool()
        result = tool.execute("")
        parsed = json.loads(result)
        self.assertIsInstance(parsed, (list, dict))


class TestToolRegistration(unittest.TestCase):
    """Test that training tools are properly registered."""

    def test_tools_in_handlers(self):
        """Training tools should be in TOOL_HANDLERS."""
        from src.agent_tools import TOOL_HANDLERS
        training_tools = [
            "create_training_job", "start_training", "stop_training",
            "get_training_status", "list_training_jobs", "get_training_logs",
            "get_training_metrics", "detect_hardware",
        ]
        for tool in training_tools:
            self.assertIn(tool, TOOL_HANDLERS, f"{tool} not found in TOOL_HANDLERS")

    def test_tools_in_tags(self):
        """Training tools should be in TOOL_TAGS."""
        from src.agent_tools import TOOL_TAGS
        training_tools = [
            "create_training_job", "start_training", "stop_training",
            "get_training_status", "list_training_jobs", "get_training_logs",
            "get_training_metrics", "detect_hardware",
        ]
        for tool in training_tools:
            self.assertIn(tool, TOOL_TAGS, f"{tool} not found in TOOL_TAGS")


if __name__ == "__main__":
    unittest.main()
