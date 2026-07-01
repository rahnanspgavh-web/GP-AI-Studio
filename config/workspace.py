"""Configuration constants for the workspace manager."""

from __future__ import annotations

from pathlib import Path

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
