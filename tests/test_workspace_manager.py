from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from modules.project_manager.workspace_manager import (
    WorkspaceManager,
    WorkspaceConfigurationError,
)
from modules.shared.logger import get_logger
from config.workspace import DEFAULT_WORKSPACE_SUBDIRECTORIES, GP_AI_STUDIO_VERSION


class WorkspaceManagerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.project_root = Path(self.temp_dir.name)
        self.config_path = self.project_root / "workspace.json"

    def test_creates_workspace_when_configuration_is_missing(self) -> None:
        workspace_path = self.project_root / "workspace"
        manager = WorkspaceManager(
            workspace_config_path=self.config_path,
            logger=get_logger("workspace-manager-tests"),
        )

        with patch("builtins.input", return_value=str(workspace_path)):
            config = manager.ensure_workspace()

        self.assertTrue(self.config_path.exists())
        self.assertEqual(config["workspace_path"], str(workspace_path.resolve()))
        self.assertEqual(config["gp_ai_studio_version"], GP_AI_STUDIO_VERSION)

        for folder_name in DEFAULT_WORKSPACE_SUBDIRECTORIES:
            self.assertTrue((workspace_path / folder_name).is_dir())

    def test_loads_existing_configuration_when_available(self) -> None:
        workspace_path = self.project_root / "workspace"
        workspace_path.mkdir(parents=True, exist_ok=True)
        config_payload = {
            "workspace_path": str(workspace_path.resolve()),
            "creation_date": "2026-07-01T00:00:00Z",
            "gp_ai_studio_version": GP_AI_STUDIO_VERSION,
        }
        self.config_path.write_text(json.dumps(config_payload), encoding="utf-8")

        manager = WorkspaceManager(
            workspace_config_path=self.config_path,
            logger=get_logger("workspace-manager-tests"),
        )

        config = manager.ensure_workspace()

        self.assertEqual(config["workspace_path"], str(workspace_path.resolve()))

    def test_raises_for_invalid_configuration_payload(self) -> None:
        self.config_path.write_text('{"workspace_path": 123}', encoding="utf-8")
        manager = WorkspaceManager(
            workspace_config_path=self.config_path,
            logger=get_logger("workspace-manager-tests"),
        )

        with self.assertRaises(WorkspaceConfigurationError):
            manager.ensure_workspace()


if __name__ == "__main__":
    unittest.main()
