"""Secure API provider management for GP AI Studio.

This module centralizes access to AI provider configuration and enforces the
application's security and validation rules. It intentionally avoids exposing
API keys through logging or other diagnostics and provides resilient recovery
from missing or corrupted configuration files.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from modules.project_manager.workspace_manager import WorkspaceManager
from modules.shared.logger import get_logger


class APIConfigurationError(RuntimeError):
    """Raised when API configuration cannot be used safely."""


class APIProviderValidationError(APIConfigurationError):
    """Raised when a provider configuration fails validation."""


class APIDisabledProviderError(APIConfigurationError):
    """Raised when an operation targets a disabled provider."""


class APIManager:
    """Manage provider configuration for GP AI Studio.

    The manager is responsible for loading, persisting, validating, enabling,
    disabling, and querying AI provider settings. It uses a provider-agnostic
    schema so new providers can be added without changing the surrounding
    modules.
    """

    def __init__(
        self,
        *,
        api_keys_path: Path | None = None,
        workspace_manager: WorkspaceManager | None = None,
        logger: Any | None = None,
    ) -> None:
        """Initialize the API manager.

        Args:
            api_keys_path: Optional explicit path to the API key configuration.
            workspace_manager: Optional workspace manager used for integration
                and path resolution.
            logger: Optional logger instance; a module logger is created when
                omitted.
        """

        self.workspace_manager = workspace_manager
        self.logger = logger or get_logger("api-manager")
        self.project_root = self._resolve_project_root()
        self.api_keys_path = api_keys_path or self.project_root / "config" / "api_keys.json"
        self._providers: dict[str, dict[str, Any]] = self._default_provider_map()
        self.load_api_keys()

    def load_api_keys(self) -> dict[str, dict[str, Any]]:
        """Load provider configuration from disk.

        Missing or invalid files are repaired automatically using the default
        structure and then saved back to disk.

        Returns:
            The provider configuration dictionary.

        Raises:
            APIConfigurationError: If the configuration cannot be restored.
        """

        try:
            if not self.api_keys_path.exists():
                self.logger.info("API configuration missing at %s; creating defaults", self.api_keys_path)
                self._providers = self._default_provider_map()
                self.save_api_keys()
                return self._providers

            payload = self._read_configuration_file()
            self._providers = self._normalize_configuration(payload)
            self.logger.info("Loaded API configuration for %s providers", len(self._providers))
            return self._providers
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            self.logger.warning("API configuration is invalid; repairing defaults")
            self._providers = self._default_provider_map()
            self.save_api_keys()
            return self._providers

    def save_api_keys(self) -> None:
        """Persist the current provider configuration to disk."""

        self.api_keys_path.parent.mkdir(parents=True, exist_ok=True)
        self.api_keys_path.write_text(json.dumps(self._providers, indent=2), encoding="utf-8")
        self.logger.debug("Saved API configuration to %s", self.api_keys_path)

    def get_provider(self, provider_name: str) -> dict[str, Any]:
        """Return the configuration for a specific provider.

        Args:
            provider_name: Provider identifier such as ``google`` or ``openai``.

        Returns:
            The provider configuration dictionary.

        Raises:
            APIConfigurationError: If the provider is unknown.
        """

        normalized_name = self._normalize_provider_name(provider_name)
        if normalized_name not in self._providers:
            raise APIConfigurationError(f"Unknown provider '{provider_name}'.")

        self.logger.info("Provider loaded: %s", normalized_name)
        return self._providers[normalized_name]

    def set_provider(self, provider_name: str, configuration: Mapping[str, Any]) -> dict[str, Any]:
        """Update the configuration for a provider.

        Args:
            provider_name: Provider identifier.
            configuration: A mapping containing provider values such as
                ``enabled``, ``api_key``, and ``default_model``.

        Returns:
            The updated provider configuration.

        Raises:
            APIConfigurationError: If the provider is unknown or the payload is
                malformed.
        """

        normalized_name = self._normalize_provider_name(provider_name)
        if normalized_name not in self._providers:
            raise APIConfigurationError(f"Unknown provider '{provider_name}'.")

        if not isinstance(configuration, Mapping):
            raise APIConfigurationError("Provider configuration must be a mapping.")

        updated_configuration = dict(self._providers[normalized_name])
        for key, value in configuration.items():
            if key not in {"enabled", "api_key", "default_model"}:
                raise APIConfigurationError(f"Unsupported provider field '{key}'.")
            if key == "enabled" and not isinstance(value, bool):
                raise APIConfigurationError("Provider 'enabled' field must be a boolean.")
            if key in {"api_key", "default_model"} and not isinstance(value, str):
                raise APIConfigurationError(f"Provider field '{key}' must be a string.")
            updated_configuration[key] = value

        self._providers[normalized_name] = updated_configuration
        self.logger.info("Provider configuration updated: %s", normalized_name)
        self.save_api_keys()
        return self._providers[normalized_name]

    def enable_provider(self, provider_name: str) -> dict[str, Any]:
        """Enable a provider and persist the change.

        Args:
            provider_name: Provider identifier.

        Returns:
            The updated provider configuration.
        """

        updated_provider = self.set_provider(provider_name, {"enabled": True})
        self.logger.info("Provider enabled: %s", self._normalize_provider_name(provider_name))
        return updated_provider

    def disable_provider(self, provider_name: str) -> dict[str, Any]:
        """Disable a provider and persist the change.

        Args:
            provider_name: Provider identifier.

        Returns:
            The updated provider configuration.
        """

        updated_provider = self.set_provider(provider_name, {"enabled": False})
        self.logger.info("Provider disabled: %s", self._normalize_provider_name(provider_name))
        return updated_provider

    def validate_provider(self, provider_name: str) -> dict[str, Any]:
        """Validate the configuration for a provider.

        Args:
            provider_name: Provider identifier.

        Returns:
            The validated provider configuration.

        Raises:
            APIDisabledProviderError: If the provider is disabled.
            APIProviderValidationError: If the provider is enabled but its
                configuration is incomplete.
        """

        provider = self.get_provider(provider_name)
        if not provider.get("enabled", False):
            raise APIDisabledProviderError(f"Provider '{provider_name}' is disabled.")

        api_key = str(provider.get("api_key", "")).strip()
        default_model = str(provider.get("default_model", "")).strip()
        if not api_key:
            raise APIProviderValidationError(f"Provider '{provider_name}' requires a non-empty API key.")
        if not default_model:
            raise APIProviderValidationError(f"Provider '{provider_name}' requires a default model.")

        self.logger.info("Validation success: %s", provider_name)
        return provider

    def list_enabled_providers(self) -> list[str]:
        """Return the list of enabled provider names."""

        return [name for name, configuration in self._providers.items() if configuration.get("enabled", False)]

    def get_default_model(self, provider_name: str) -> str:
        """Return the configured default model for a provider.

        Args:
            provider_name: Provider identifier.

        Returns:
            The default model string.
        """

        provider = self.get_provider(provider_name)
        return str(provider.get("default_model", ""))

    def set_default_model(self, provider_name: str, model_name: str) -> dict[str, Any]:
        """Set the default model for a provider.

        Args:
            provider_name: Provider identifier.
            model_name: New default model name.

        Returns:
            The updated provider configuration.

        Raises:
            APIConfigurationError: If the provider is unknown or the model name
                is not a string.
        """

        if not isinstance(model_name, str):
            raise APIConfigurationError("Default model must be a string.")
        return self.set_provider(provider_name, {"default_model": model_name})

    def _read_configuration_file(self) -> dict[str, Any]:
        """Read and parse the API configuration file."""

        with self.api_keys_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

        if not isinstance(payload, dict):
            raise APIConfigurationError("API configuration must be a JSON object.")
        return payload

    def _normalize_configuration(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        """Normalize the loaded configuration into the expected schema."""

        normalized = self._default_provider_map()
        for provider_name, configuration in normalized.items():
            incoming = payload.get(provider_name)
            if incoming is None:
                continue
            if not isinstance(incoming, Mapping):
                raise APIConfigurationError(f"Provider '{provider_name}' configuration must be an object.")

            normalized_provider = dict(configuration)
            for key in ("enabled", "api_key", "default_model"):
                if key in incoming:
                    value = incoming[key]
                    if key == "enabled" and not isinstance(value, bool):
                        raise APIConfigurationError(f"Provider '{provider_name}' has an invalid enabled value.")
                    if key in {"api_key", "default_model"} and not isinstance(value, str):
                        raise APIConfigurationError(f"Provider '{provider_name}' has an invalid {key} value.")
                    normalized_provider[key] = value

            normalized[provider_name] = normalized_provider

        return normalized

    def _default_provider_map(self) -> dict[str, dict[str, Any]]:
        """Return the default provider configuration schema."""

        return {
            "google": {
                "enabled": True,
                "api_key": "",
                "default_model": "gemini-2.5-pro",
            },
            "claude": {
                "enabled": False,
                "api_key": "",
                "default_model": "",
            },
            "openai": {
                "enabled": False,
                "api_key": "",
                "default_model": "",
            },
        }

    def _normalize_provider_name(self, provider_name: str) -> str:
        """Normalize provider names to lower-case identifiers."""

        if not isinstance(provider_name, str) or not provider_name.strip():
            raise APIConfigurationError("Provider name must be a non-empty string.")
        return provider_name.strip().lower()

    def _resolve_project_root(self) -> Path:
        """Resolve the project root used for default configuration paths."""

        if self.workspace_manager is not None:
            workspace_config_path = getattr(self.workspace_manager, "workspace_config_path", None)
            if isinstance(workspace_config_path, Path):
                return workspace_config_path.parent

        return Path(__file__).resolve().parents[2]
