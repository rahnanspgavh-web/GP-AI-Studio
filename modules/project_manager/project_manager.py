"""Production-quality project management for GP AI Studio.

This module provides an object-oriented interface for creating, validating,
repairing, archiving, restoring, duplicating, and backing up projects. It uses
pathlib for all filesystem operations and integrates with the workspace manager
for resolving the configured workspace root.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from modules.project_manager.workspace_manager import WorkspaceManager
from modules.shared.logger import get_logger


class ProjectError(RuntimeError):
    """Base exception for project management failures."""


class ProjectAlreadyExistsError(ProjectError):
    """Raised when a project already exists and would be overwritten."""


class ProjectValidationError(ProjectError):
    """Raised when a project path or structure is invalid."""


class ProjectManager:
    """Manage GP AI Studio projects within the configured workspace.

    The manager creates the full folder tree for a project, writes the required
    metadata files, validates and repairs existing projects, and supports
    archival and backup workflows without overwriting existing data.
    """

    def __init__(
        self,
        *,
        workspace_manager: WorkspaceManager | None = None,
        logger: Any | None = None,
    ) -> None:
        """Initialize the project manager.

        Args:
            workspace_manager: Optional workspace manager instance. A default
                manager is created when omitted.
            logger: Optional logger instance for diagnostics.
        """

        self.workspace_manager = workspace_manager or WorkspaceManager()
        self.logger = logger or get_logger("project-manager")
        self.required_folders: tuple[str, ...] = (
            "00_Project",
            "01_Research",
            "02_Scripts",
            "02_Scripts/Tamil",
            "02_Scripts/English",
            "02_Scripts/Hindi",
            "03_Prompts",
            "04_Images",
            "05_Videos",
            "06_Audio",
            "07_Subtitles",
            "08_Final",
            "09_Website",
            "10_YouTube",
            "11_Logs",
            "12_Backups",
        )

    def create_project(self, project_name: str, *, category: str = "General") -> dict[str, Any]:
        """Create a new project directory and initialize its metadata files.

        Args:
            project_name: Human-readable project name.
            category: Project category stored in metadata.

        Returns:
            A dictionary containing the generated metadata.

        Raises:
            ProjectValidationError: If the project name is invalid.
            ProjectAlreadyExistsError: If the target project already exists.
        """

        normalized_name = self._normalize_project_name(project_name)
        project_path = self._resolve_project_path(normalized_name)

        if project_path.exists():
            raise ProjectAlreadyExistsError(f"Project '{normalized_name}' already exists.")

        if project_path.parent != self._workspace_root:
            raise ProjectValidationError(
                f"Project path '{project_path}' is outside the configured workspace."
            )

        project_path.mkdir(parents=True, exist_ok=False)
        self._create_project_structure(project_path)

        metadata = self._build_project_metadata(project_name=normalized_name, category=category, workspace_path=self._workspace_root)
        self._write_json_file(project_path / "project.json", metadata)
        self._write_json_file(project_path / "progress.json", self._build_progress_payload())
        self._write_json_file(project_path / "settings.json", self._build_settings_payload())
        self._write_log(project_path, f"Project Created: {normalized_name}")

        self.logger.info("Created project '%s' at %s", normalized_name, project_path)
        return metadata

    def open_project(self, project_name: str) -> dict[str, Any]:
        """Open and validate an existing project.

        Args:
            project_name: Name of the project to open.

        Returns:
            The validated project metadata.

        Raises:
            ProjectValidationError: If the project does not exist or is invalid.
        """

        metadata = self.validate_project(project_name)
        self._write_log(self._resolve_project_path(project_name), f"Project Loaded: {project_name}")
        self.logger.info("Loaded project '%s'", project_name)
        return metadata

    def rename_project(self, project_name: str, new_project_name: str) -> dict[str, Any]:
        """Rename an existing project and update its metadata.

        Args:
            project_name: Current project name.
            new_project_name: New project name.

        Returns:
            Updated project metadata.

        Raises:
            ProjectValidationError: If the project is missing or invalid.
            ProjectAlreadyExistsError: If the target name already exists.
        """

        source_name = self._normalize_project_name(project_name)
        target_name = self._normalize_project_name(new_project_name)
        source_path = self._resolve_project_path(source_name)
        target_path = self._resolve_project_path(target_name)

        if not source_path.exists():
            raise ProjectValidationError(f"Project '{source_name}' was not found.")
        if target_path.exists():
            raise ProjectAlreadyExistsError(f"Project '{target_name}' already exists.")

        source_path.rename(target_path)
        metadata = self._load_project_metadata(target_path)
        metadata["project_name"] = target_name
        metadata["last_modified_date"] = self._utc_timestamp()
        self._write_json_file(target_path / "project.json", metadata)
        self._write_log(target_path, f"Project Updated: Renamed to {target_name}")
        self.logger.info("Renamed project '%s' to '%s'", source_name, target_name)
        return metadata

    def delete_project(self, project_name: str) -> None:
        """Delete a project directory and all of its contents.

        Args:
            project_name: Name of the project to delete.

        Raises:
            ProjectValidationError: If the project is missing or invalid.
        """

        normalized_name = self._normalize_project_name(project_name)
        project_path = self._resolve_project_path(normalized_name)

        if not project_path.exists():
            raise ProjectValidationError(f"Project '{normalized_name}' was not found.")
        if not project_path.is_dir():
            raise ProjectValidationError(f"Project path '{project_path}' is not a directory.")

        self._remove_tree(project_path)
        self._write_log(self._workspace_root / "01_Projects", f"Project Deleted: {normalized_name}")
        self.logger.info("Deleted project '%s'", normalized_name)

    def archive_project(self, project_name: str) -> Path:
        """Archive a project into the workspace backups folder.

        Args:
            project_name: Name of the project to archive.

        Returns:
            Path to the archived project directory.

        Raises:
            ProjectValidationError: If the project is missing or invalid.
            ProjectAlreadyExistsError: If the archive destination already exists.
        """

        normalized_name = self._normalize_project_name(project_name)
        project_path = self._resolve_project_path(normalized_name)
        backups_dir = self._workspace_root / "12_Backups"
        backups_dir.mkdir(parents=True, exist_ok=True)

        if not project_path.exists():
            raise ProjectValidationError(f"Project '{normalized_name}' was not found.")
        if not project_path.is_dir():
            raise ProjectValidationError(f"Project path '{project_path}' is not a directory.")

        archive_path = backups_dir / f"{normalized_name}_archived_{self._timestamp()}"
        if archive_path.exists():
            raise ProjectAlreadyExistsError(f"Archive target '{archive_path}' already exists.")

        project_path.rename(archive_path)
        self._write_log(archive_path, f"Backup Created: Archived {normalized_name}")
        self.logger.info("Archived project '%s' to %s", normalized_name, archive_path)
        return archive_path

    def restore_project(self, project_name: str) -> dict[str, Any]:
        """Restore an archived project back into the workspace root.

        Args:
            project_name: Name of the project to restore.

        Returns:
            Project metadata after restoration.

        Raises:
            ProjectValidationError: If no archived project is found.
            ProjectAlreadyExistsError: If the restored project already exists.
        """

        normalized_name = self._normalize_project_name(project_name)
        backup_dir = self._workspace_root / "12_Backups"
        target_path = self._resolve_project_path(normalized_name)

        if target_path.exists():
            raise ProjectAlreadyExistsError(f"Project '{normalized_name}' already exists in the workspace.")

        archived_candidates = [
            candidate
            for candidate in backup_dir.iterdir()
            if candidate.is_dir() and candidate.name.startswith(f"{normalized_name}_archived_")
        ] if backup_dir.exists() else []
        if not archived_candidates:
            raise ProjectValidationError(f"No archived project '{normalized_name}' was found.")

        archived_path = sorted(archived_candidates, key=lambda path: path.name)[-1]
        archived_path.rename(target_path)
        self._write_log(target_path, f"Project Updated: Restored {normalized_name}")
        self.logger.info("Restored project '%s' from %s", normalized_name, archived_path)
        return self._load_project_metadata(target_path)

    def duplicate_project(self, project_name: str, new_project_name: str) -> dict[str, Any]:
        """Create a duplicate of an existing project under a new name.

        Args:
            project_name: Source project name.
            new_project_name: Destination project name.

        Returns:
            Metadata of the duplicated project.

        Raises:
            ProjectValidationError: If the source project does not exist or is invalid.
            ProjectAlreadyExistsError: If the target project already exists.
        """

        source_name = self._normalize_project_name(project_name)
        target_name = self._normalize_project_name(new_project_name)
        source_path = self._resolve_project_path(source_name)
        target_path = self._resolve_project_path(target_name)

        if not source_path.exists():
            raise ProjectValidationError(f"Project '{source_name}' was not found.")
        if target_path.exists():
            raise ProjectAlreadyExistsError(f"Project '{target_name}' already exists.")

        self._copy_tree(source_path, target_path)
        metadata = self._load_project_metadata(target_path)
        metadata["project_name"] = target_name
        metadata["project_id"] = self._project_id(target_name)
        metadata["created_date"] = self._utc_timestamp()
        metadata["last_modified_date"] = metadata["created_date"]
        self._write_json_file(target_path / "project.json", metadata)
        self._write_log(target_path, f"Project Updated: Duplicated from {source_name}")
        self.logger.info("Duplicated project '%s' to '%s'", source_name, target_name)
        return metadata

    def validate_project(self, project_name: str) -> dict[str, Any]:
        """Validate and repair a project if needed.

        Args:
            project_name: Name of the project to validate.

        Returns:
            Project metadata after validation.

        Raises:
            ProjectValidationError: If the project path is missing or invalid.
        """

        normalized_name = self._normalize_project_name(project_name)
        project_path = self._resolve_project_path(normalized_name)

        if not project_path.exists():
            raise ProjectValidationError(f"Project '{normalized_name}' was not found.")
        if not project_path.is_dir():
            raise ProjectValidationError(f"Project path '{project_path}' is not a directory.")

        self._create_project_structure(project_path)
        metadata = self._ensure_project_files(project_path, normalized_name)
        self._write_log(project_path, f"Project Updated: Validated {normalized_name}")
        self.logger.info("Validated project '%s'", normalized_name)
        return metadata

    def repair_project(self, project_name: str) -> dict[str, Any]:
        """Repair missing folders and JSON files for an existing project.

        Args:
            project_name: Name of the project to repair.

        Returns:
            Repaired project metadata.

        Raises:
            ProjectValidationError: If the project path is missing or invalid.
        """

        return self.validate_project(project_name)

    def backup_project(self, project_name: str) -> Path:
        """Create a backup copy of a project inside the backups folder.

        Args:
            project_name: Name of the project to back up.

        Returns:
            Path to the backup copy.

        Raises:
            ProjectValidationError: If the project is missing or invalid.
            ProjectAlreadyExistsError: If the backup target already exists.
        """

        normalized_name = self._normalize_project_name(project_name)
        source_path = self._resolve_project_path(normalized_name)
        backups_dir = self._workspace_root / "12_Backups"
        backups_dir.mkdir(parents=True, exist_ok=True)

        if not source_path.exists():
            raise ProjectValidationError(f"Project '{normalized_name}' was not found.")
        if not source_path.is_dir():
            raise ProjectValidationError(f"Project path '{source_path}' is not a directory.")

        backup_path = backups_dir / f"{normalized_name}_backup_{self._timestamp()}"
        if backup_path.exists():
            raise ProjectAlreadyExistsError(f"Backup target '{backup_path}' already exists.")

        self._copy_tree(source_path, backup_path)
        self._write_log(backup_path, f"Backup Created: {normalized_name}")
        self.logger.info("Backed up project '%s' to %s", normalized_name, backup_path)
        return backup_path

    @property
    def workspace_root(self) -> Path:
        """Return the resolved workspace root path."""

        self._workspace_root = self._workspace_root if hasattr(self, "_workspace_root") else self._get_workspace_path()
        return self._workspace_root

    def _workspace_path(self) -> Path:
        """Resolve the configured workspace path from the workspace manager."""

        return self._get_workspace_path()

    def _get_workspace_path(self) -> Path:
        """Load the workspace configuration and return the resolved workspace root."""

        configuration = self.workspace_manager.ensure_workspace()
        workspace_path = Path(configuration["workspace_path"]).expanduser()
        try:
            resolved_path = workspace_path.resolve(strict=False)
        except OSError as exc:  # pragma: no cover - defensive guard
            raise ProjectValidationError(f"Unable to resolve workspace path '{workspace_path}': {exc}") from exc

        if not resolved_path.exists():
            raise ProjectValidationError(f"Workspace path '{resolved_path}' does not exist.")
        if not resolved_path.is_dir():
            raise ProjectValidationError(f"Workspace path '{resolved_path}' is not a directory.")
        return resolved_path

    def _resolve_project_path(self, project_name: str) -> Path:
        """Resolve a project path inside the configured workspace."""

        workspace_root = self._get_workspace_path()
        self._workspace_root = workspace_root
        return workspace_root / project_name

    def _normalize_project_name(self, project_name: str) -> str:
        """Validate and normalize a project name."""

        if not isinstance(project_name, str) or not project_name.strip():
            raise ProjectValidationError("A project name is required.")

        normalized_name = project_name.strip()
        if "/" in normalized_name or "\\" in normalized_name or normalized_name in {".", ".."}:
            raise ProjectValidationError("Project names may not contain path separators.")
        return normalized_name

    def _create_project_structure(self, project_path: Path) -> None:
        """Create the complete folder structure expected by a project."""

        for folder_name in self.required_folders:
            folder_path = project_path / folder_name
            folder_path.mkdir(parents=True, exist_ok=True)

    def _build_project_metadata(
        self,
        *,
        project_name: str,
        category: str,
        workspace_path: Path,
    ) -> dict[str, Any]:
        """Build the initial metadata payload for a new project."""

        timestamp = self._utc_timestamp()
        return {
            "project_id": self._project_id(project_name),
            "project_name": project_name,
            "category": category,
            "created_date": timestamp,
            "last_modified_date": timestamp,
            "workspace_path": str(workspace_path.resolve(strict=False)),
            "project_version": "1.0.0",
            "status": "Active",
            "current_module": "Project Manager",
        }

    def _build_progress_payload(self) -> dict[str, Any]:
        """Create the default progress tracking payload."""

        timestamp = self._utc_timestamp()
        items = {
            "Research": {"status": "not_started", "updated_at": timestamp},
            "Scripts": {"status": "not_started", "updated_at": timestamp},
            "Prompts": {"status": "not_started", "updated_at": timestamp},
            "Images": {"status": "not_started", "updated_at": timestamp},
            "Videos": {"status": "not_started", "updated_at": timestamp},
            "Audio": {"status": "not_started", "updated_at": timestamp},
            "Subtitles": {"status": "not_started", "updated_at": timestamp},
            "Final Video": {"status": "not_started", "updated_at": timestamp},
            "Website": {"status": "not_started", "updated_at": timestamp},
            "YouTube": {"status": "not_started", "updated_at": timestamp},
        }
        return items

    def _build_settings_payload(self) -> dict[str, Any]:
        """Create the default settings payload for a new project."""

        return {
            "default_language": "Tamil",
            "supported_languages": ["Tamil", "English", "Hindi"],
            "video_resolution": "1920x1080",
            "aspect_ratio": "16:9",
            "video_duration": "00:03:00",
            "image_style": "cinematic",
            "voice_style": "neutral",
            "music_style": "ambient",
            "subtitle_style": "clean",
            "output_format": "mp4",
        }

    def _ensure_project_files(self, project_path: Path, project_name: str) -> dict[str, Any]:
        """Ensure that the required JSON files exist and are structurally valid."""

        metadata_path = project_path / "project.json"
        progress_path = project_path / "progress.json"
        settings_path = project_path / "settings.json"

        metadata = self._load_json_file(metadata_path, self._build_project_metadata(project_name=project_name, category="General", workspace_path=self._workspace_root), repair=True)
        if not isinstance(metadata, dict):
            metadata = self._build_project_metadata(project_name=project_name, category="General", workspace_path=self._workspace_root)

        if metadata.get("project_name") != project_name:
            metadata["project_name"] = project_name
            metadata["last_modified_date"] = self._utc_timestamp()

        self._write_json_file(metadata_path, metadata)
        self._write_json_file(progress_path, self._load_json_file(progress_path, self._build_progress_payload(), repair=True))
        self._write_json_file(settings_path, self._load_json_file(settings_path, self._build_settings_payload(), repair=True))
        return metadata

    def _load_project_metadata(self, project_path: Path) -> dict[str, Any]:
        """Load project metadata from project.json, falling back to defaults."""

        metadata_path = project_path / "project.json"
        if not metadata_path.exists():
            metadata = self._build_project_metadata(
                project_name=project_path.name,
                category="General",
                workspace_path=self._workspace_root,
            )
            self._write_json_file(metadata_path, metadata)
            return metadata

        try:
            payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError, ValueError):
            metadata = self._build_project_metadata(
                project_name=project_path.name,
                category="General",
                workspace_path=self._workspace_root,
            )
            self._write_json_file(metadata_path, metadata)
            return metadata

        if not isinstance(payload, dict):
            payload = self._build_project_metadata(
                project_name=project_path.name,
                category="General",
                workspace_path=self._workspace_root,
            )
            self._write_json_file(metadata_path, payload)
            return payload

        if "project_name" not in payload:
            payload["project_name"] = project_path.name
        if "workspace_path" not in payload:
            payload["workspace_path"] = str(self._workspace_root)
        return payload

    def _load_json_file(self, path: Path, default: Any, *, repair: bool) -> Any:
        """Safely read a JSON file, creating it when missing or invalid."""

        if not path.exists():
            if repair:
                self._write_json_file(path, default)
                return default
            raise ProjectValidationError(f"Required JSON file '{path}' is missing.")

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError, ValueError) as exc:
            if repair:
                self._write_json_file(path, default)
                return default
            raise ProjectValidationError(f"JSON file '{path}' is invalid: {exc}") from exc

        return payload

    def _write_json_file(self, path: Path, payload: Any) -> None:
        """Persist a JSON payload to disk with UTF-8 encoding."""

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _write_log(self, project_path: Path, message: str) -> None:
        """Append an event to the project's log file inside 11_Logs."""

        logs_dir = project_path / "11_Logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        log_path = logs_dir / "events.log"
        entry = f"{self._utc_timestamp()} {message}\n"
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(entry)

    def _copy_tree(self, source_path: Path, destination_path: Path) -> None:
        """Copy a project tree to a new location using pathlib operations only."""

        destination_path.mkdir(parents=True, exist_ok=True)
        for item in source_path.iterdir():
            destination_item = destination_path / item.name
            if item.is_dir():
                self._copy_tree(item, destination_item)
            else:
                destination_item.write_bytes(item.read_bytes())

    def _remove_tree(self, path: Path) -> None:
        """Delete a directory tree recursively using pathlib primitives."""

        if path.is_dir():
            for child in sorted(path.iterdir(), key=lambda child: child.name):
                self._remove_tree(child)
            path.rmdir()
        elif path.exists():
            path.unlink()

    def _timestamp(self) -> str:
        """Return a compact timestamp suitable for project names."""

        return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")

    def _utc_timestamp(self) -> str:
        """Return an ISO-8601 timestamp in UTC."""

        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    def _project_id(self, project_name: str) -> str:
        """Generate a stable project identifier from the project name."""

        return f"{project_name.lower().replace(' ', '-')}-{self._timestamp()}"
