"""Configuration constants for the workspace manager."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

GP_AI_STUDIO_VERSION: str = "0.1.0"
DEFAULT_WORKSPACE_SUBDIRECTORIES: tuple[str, ...] = (
    "01_Projects",
    "02_Assets",
    "03_Exports",
    "04_Backups",
    "05_Templates",
    "06_Downloads",
    "07_Logs",
    "08_Cache",
)

DEFAULT_WORKSPACE_CONFIG_FILENAME: str = "workspace.json"


def get_default_workspace_config_path(project_root: Path) -> Path:
    """Return the default workspace configuration path for the project root."""

    return project_root / DEFAULT_WORKSPACE_CONFIG_FILENAME


class WorkspaceConfig:
    """Read workspace configuration and expose standard workspace folders."""

    def __init__(self, *, project_root: Path | None = None, workspace_config_path: Path | None = None) -> None:
        """Initialize the workspace configuration helper."""

        self.project_root = Path(project_root).expanduser() if project_root is not None else Path(__file__).resolve().parents[1]
        self.workspace_config_path = (
            Path(workspace_config_path).expanduser()
            if workspace_config_path is not None
            else get_default_workspace_config_path(self.project_root)
        )

    def get_workspace(self) -> Path:
        """Return the configured workspace directory after validation."""

        workspace_path = self._read_workspace_path()
        if not workspace_path.exists():
            raise FileNotFoundError(f"Workspace path '{workspace_path}' does not exist.")
        if not workspace_path.is_dir():
            raise NotADirectoryError(f"Workspace path '{workspace_path}' is not a directory.")
        return workspace_path

    def get_projects_folder(self) -> Path:
        """Return the projects folder inside the workspace."""

        return self.get_workspace() / "01_Projects"

    def get_logs_folder(self) -> Path:
        """Return the logs folder inside the workspace."""

        return self.get_workspace() / "07_Logs"

    def get_backups_folder(self) -> Path:
        """Return the backups folder inside the workspace."""

        return self.get_workspace() / "04_Backups"

    def _read_workspace_path(self) -> Path:
        """Read and resolve the configured workspace path from disk."""

        if not self.workspace_config_path.exists():
            raise FileNotFoundError(f"Workspace configuration does not exist at {self.workspace_config_path}.")

        with self.workspace_config_path.open("r", encoding="utf-8") as handle:
            payload: Any = json.load(handle)

        if not isinstance(payload, dict):
            raise ValueError("Workspace configuration must be a JSON object.")

        workspace_path_value = payload.get("workspace_path")
        if not isinstance(workspace_path_value, str) or not workspace_path_value.strip():
            raise ValueError("Workspace configuration must define a non-empty workspace_path.")

        workspace_path = Path(workspace_path_value).expanduser()
        try:
            return workspace_path.resolve(strict=False)
        except OSError as exc:
            raise ValueError(f"Unable to resolve workspace path '{workspace_path}': {exc}") from exc
