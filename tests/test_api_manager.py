from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from modules.api_manager.api_manager import (
    APIConfigurationError,
    APIDisabledProviderError,
    APIManager,
    APIProviderValidationError,
)
from modules.project_manager.workspace_manager import WorkspaceManager
from modules.shared.logger import get_logger


class APIManagerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.project_root = Path(self.temp_dir.name)
        self.api_keys_path = self.project_root / "config" / "api_keys.json"
        self.workspace_config_path = self.project_root / "workspace.json"
        self.workspace_config_path.write_text(
            json.dumps(
                {
                    "workspace_path": str(self.project_root / "workspace"),
                    "creation_date": "2026-07-01T00:00:00Z",
                    "gp_ai_studio_version": "0.1.0",
                }
            ),
            encoding="utf-8",
        )
        self.workspace_manager = WorkspaceManager(
            workspace_config_path=self.workspace_config_path,
            logger=get_logger("api-manager-tests"),
        )

    def test_initialization_creates_default_configuration(self) -> None:
        manager = APIManager(
            api_keys_path=self.api_keys_path,
            workspace_manager=self.workspace_manager,
            logger=get_logger("api-manager-tests"),
        )

        self.assertTrue(self.api_keys_path.exists())
        payload = manager.load_api_keys()
        self.assertTrue(payload["google"]["enabled"])
        self.assertEqual(payload["google"]["default_model"], "gemini-2.5-pro")
        self.assertFalse(payload["claude"]["enabled"])
        self.assertFalse(payload["openai"]["enabled"])

    def test_save_configuration_persists_changes(self) -> None:
        manager = APIManager(
            api_keys_path=self.api_keys_path,
            workspace_manager=self.workspace_manager,
            logger=get_logger("api-manager-tests"),
        )

        manager.enable_provider("claude")
        manager.set_provider("claude", {"api_key": "claude-key", "default_model": "claude-3.5-sonnet"})
        manager.save_api_keys()

        payload = json.loads(self.api_keys_path.read_text(encoding="utf-8"))
        self.assertTrue(payload["claude"]["enabled"])
        self.assertEqual(payload["claude"]["api_key"], "claude-key")
        self.assertEqual(payload["claude"]["default_model"], "claude-3.5-sonnet")

    def test_enable_and_disable_provider(self) -> None:
        manager = APIManager(
            api_keys_path=self.api_keys_path,
            workspace_manager=self.workspace_manager,
            logger=get_logger("api-manager-tests"),
        )

        manager.enable_provider("openai")
        self.assertTrue(manager.get_provider("openai")["enabled"])

        manager.disable_provider("openai")
        self.assertFalse(manager.get_provider("openai")["enabled"])

    def test_validate_provider_requires_key_and_model_when_enabled(self) -> None:
        manager = APIManager(
            api_keys_path=self.api_keys_path,
            workspace_manager=self.workspace_manager,
            logger=get_logger("api-manager-tests"),
        )

        manager.enable_provider("claude")
        with self.assertRaises(APIProviderValidationError):
            manager.validate_provider("claude")

        manager.set_provider("claude", {"api_key": "claude-key", "default_model": "claude-3.5-sonnet"})
        payload = manager.validate_provider("claude")
        self.assertEqual(payload["default_model"], "claude-3.5-sonnet")

    def test_disabled_provider_raises_clear_error(self) -> None:
        manager = APIManager(
            api_keys_path=self.api_keys_path,
            workspace_manager=self.workspace_manager,
            logger=get_logger("api-manager-tests"),
        )

        with self.assertRaises(APIDisabledProviderError):
            manager.validate_provider("openai")

    def test_missing_configuration_is_repaired(self) -> None:
        manager = APIManager(
            api_keys_path=self.api_keys_path,
            workspace_manager=self.workspace_manager,
            logger=get_logger("api-manager-tests"),
        )
        self.api_keys_path.unlink()

        payload = manager.load_api_keys()
        self.assertIn("google", payload)
        self.assertTrue(self.api_keys_path.exists())

    def test_corrupted_configuration_is_repaired(self) -> None:
        self.api_keys_path.parent.mkdir(parents=True, exist_ok=True)
        self.api_keys_path.write_text("{not valid json", encoding="utf-8")

        manager = APIManager(
            api_keys_path=self.api_keys_path,
            workspace_manager=self.workspace_manager,
            logger=get_logger("api-manager-tests"),
        )

        payload = manager.load_api_keys()
        self.assertIn("google", payload)
        self.assertTrue(payload["google"]["enabled"])

    def test_missing_provider_raises_meaningful_error(self) -> None:
        manager = APIManager(
            api_keys_path=self.api_keys_path,
            workspace_manager=self.workspace_manager,
            logger=get_logger("api-manager-tests"),
        )

        with self.assertRaises(APIConfigurationError):
            manager.get_provider("unknown")


if __name__ == "__main__":
    unittest.main()
