from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from modules.project_manager.project_manager import (
    ProjectAlreadyExistsError,
    ProjectManager,
    ProjectValidationError,
)
from modules.project_manager.workspace_manager import WorkspaceManager
from modules.shared.logger import get_logger


class ProjectManagerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.project_root = Path(self.temp_dir.name)
        self.workspace_path = self.project_root / "workspace"
        self.workspace_path.mkdir(parents=True, exist_ok=True)
        self.workspace_config_path = self.project_root / "workspace.json"
        self.workspace_config_path.write_text(
            json.dumps(
                {
                    "workspace_path": str(self.workspace_path.resolve()),
                    "creation_date": "2026-07-01T00:00:00Z",
                    "gp_ai_studio_version": "0.1.0",
                }
            ),
            encoding="utf-8",
        )
        self.workspace_manager = WorkspaceManager(
            workspace_config_path=self.workspace_config_path,
            logger=get_logger("project-manager-tests"),
        )
        self.manager = ProjectManager(
            workspace_manager=self.workspace_manager,
            logger=get_logger("project-manager-tests"),
        )

    def test_create_project_initializes_structure_and_metadata(self) -> None:
        metadata = self.manager.create_project("My Project", category="Spiritual")

        project_dir = self.workspace_path / "My Project"
        self.assertTrue(project_dir.is_dir())
        self.assertEqual(metadata["project_name"], "My Project")
        self.assertEqual(metadata["category"], "Spiritual")

        for folder_name in self.manager.required_folders:
            self.assertTrue((project_dir / folder_name).is_dir(), folder_name)

        self.assertTrue((project_dir / "project.json").is_file())
        self.assertTrue((project_dir / "progress.json").is_file())
        self.assertTrue((project_dir / "settings.json").is_file())

    def test_validate_project_repairs_missing_folders_and_files(self) -> None:
        self.manager.create_project("Repair Test")
        project_dir = self.workspace_path / "Repair Test"

        (project_dir / "01_Research").rmdir()
        (project_dir / "settings.json").unlink()
        (project_dir / "11_Logs").mkdir(parents=True, exist_ok=True)

        metadata = self.manager.validate_project("Repair Test")

        self.assertTrue((project_dir / "01_Research").is_dir())
        self.assertTrue((project_dir / "settings.json").is_file())
        self.assertEqual(metadata["project_name"], "Repair Test")

    def test_create_project_refuses_to_overwrite_existing_project(self) -> None:
        self.manager.create_project("Existing")

        with self.assertRaises(ProjectAlreadyExistsError):
            self.manager.create_project("Existing")

    def test_validate_project_raises_for_invalid_project_path(self) -> None:
        project_path = self.workspace_path / "Broken"
        project_path.write_text("not a directory", encoding="utf-8")

        with self.assertRaises(ProjectValidationError):
            self.manager.validate_project("Broken")


if __name__ == "__main__":
    unittest.main()
