"""Workspace management utilities for GP AI Studio."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config.workspace import (
    DEFAULT_WORKSPACE_SUBDIRECTORIES,
    GP_AI_STUDIO_VERSION,
    get_default_workspace_config_path,
)
from modules.shared.logger import get_logger


class WorkspaceConfigurationError(RuntimeError):
    """Raised when a workspace configuration cannot be used safely."""


class WorkspaceManager:
    """Manage the user's workspace directory and configuration file.

    The manager stores the workspace location in a JSON file and ensures the
    required directory structure exists before the application uses it.
    """

    def __init__(self, *, workspace_config_path: Path | None = None, logger: Any | None = None) -> None:
        """Initialize the manager.

        Args:
            workspace_config_path: Optional path to workspace.json.
            logger: Optional logger instance to use for diagnostics.
        """

        self.project_root = Path(__file__).resolve().parents[2]
        self.workspace_config_path = workspace_config_path or get_default_workspace_config_path(self.project_root)
        self.logger = logger or get_logger("workspace-manager")

    def ensure_workspace(self) -> dict[str, Any]:
        """Ensure a valid workspace exists and return its configuration.

        Returns:
            A dictionary containing the workspace path, creation date, and
            application version.

        Raises:
            WorkspaceConfigurationError: If the saved configuration is invalid
                or the workspace cannot be used.
        """

        self.logger.info("Checking workspace configuration at %s", self.workspace_config_path)

        if not self.workspace_config_path.exists():
            self.logger.info("No workspace configuration found; creating a new workspace.")
            return self._create_workspace()

        try:
            configuration = self._load_configuration()
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            raise WorkspaceConfigurationError(
                f"Unable to read workspace configuration at {self.workspace_config_path}: {exc}"
            ) from exc

        self._validate_configuration(configuration)
        workspace_path = self._resolve_workspace_path(configuration)

        if not workspace_path.exists():
            raise WorkspaceConfigurationError(
                f"Workspace path '{workspace_path}' does not exist. Please reconnect the drive or select a new workspace."
            )

        if not workspace_path.is_dir():
            raise WorkspaceConfigurationError(
                f"Workspace path '{workspace_path}' is not a directory."
            )

        self.logger.info("Loaded workspace configuration for %s", workspace_path)
        return configuration

    def _create_workspace(self) -> dict[str, Any]:
        """Prompt for a workspace path and create the directory structure."""

        workspace_path_input = input("Enter a workspace folder path: ").strip()
        if not workspace_path_input:
            raise WorkspaceConfigurationError("A workspace path is required.")

        workspace_path = Path(workspace_path_input).expanduser().resolve()
        workspace_path.mkdir(parents=True, exist_ok=True)

        self._create_subdirectories(workspace_path)

        configuration = self._build_configuration(workspace_path)
        self._write_configuration(configuration)
        self.logger.info("Created workspace at %s", workspace_path)
        return configuration

    def _load_configuration(self) -> dict[str, Any]:
        """Load the workspace configuration from disk."""

        with self.workspace_config_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

        if not isinstance(payload, dict):
            raise WorkspaceConfigurationError("Workspace configuration must be a JSON object.")
        return payload

    def _validate_configuration(self, configuration: dict[str, Any]) -> None:
        """Validate that the configuration contains required keys and values."""

        required_keys = {"workspace_path", "creation_date", "gp_ai_studio_version"}
        missing_keys = sorted(required_keys.difference(configuration.keys()))
        if missing_keys:
            raise WorkspaceConfigurationError(
                f"Workspace configuration is missing required keys: {', '.join(missing_keys)}"
            )

        if not isinstance(configuration["workspace_path"], str) or not configuration["workspace_path"].strip():
            raise WorkspaceConfigurationError("Workspace configuration contains an invalid workspace_path value.")

        if not isinstance(configuration["creation_date"], str) or not configuration["creation_date"].strip():
            raise WorkspaceConfigurationError("Workspace configuration contains an invalid creation_date value.")

        if not isinstance(configuration["gp_ai_studio_version"], str) or not configuration["gp_ai_studio_version"].strip():
            raise WorkspaceConfigurationError("Workspace configuration contains an invalid gp_ai_studio_version value.")

    def _resolve_workspace_path(self, configuration: dict[str, Any]) -> Path:
        """Resolve the workspace path from configuration to a pathlib.Path."""

        workspace_path = Path(configuration["workspace_path"]).expanduser()
        try:
            return workspace_path.resolve(strict=False)
        except OSError as exc:
            raise WorkspaceConfigurationError(f"Unable to resolve workspace path '{workspace_path}': {exc}") from exc

    def _create_subdirectories(self, workspace_path: Path) -> None:
        """Create the required subdirectories inside the workspace."""

        for folder_name in DEFAULT_WORKSPACE_SUBDIRECTORIES:
            directory_path = workspace_path / folder_name
            directory_path.mkdir(parents=True, exist_ok=True)
            self.logger.debug("Ensured directory exists: %s", directory_path)

    def _build_configuration(self, workspace_path: Path) -> dict[str, Any]:
        """Build a workspace configuration payload."""

        return {
            "workspace_path": str(workspace_path.resolve()),
            "creation_date": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "gp_ai_studio_version": GP_AI_STUDIO_VERSION,
        }

    def _write_configuration(self, configuration: dict[str, Any]) -> None:
        """Persist the workspace configuration to disk."""

        self.workspace_config_path.parent.mkdir(parents=True, exist_ok=True)
        self.workspace_config_path.write_text(json.dumps(configuration, indent=2), encoding="utf-8")
