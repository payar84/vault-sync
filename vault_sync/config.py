"""Configuration management for vault-sync."""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class VaultConfig:
    """Holds all configuration needed to connect to HashiCorp Vault."""

    vault_addr: str = field(default_factory=lambda: os.environ.get("VAULT_ADDR", "http://127.0.0.1:8200"))
    vault_token: Optional[str] = field(default_factory=lambda: os.environ.get("VAULT_TOKEN"))
    vault_namespace: Optional[str] = field(default_factory=lambda: os.environ.get("VAULT_NAMESPACE"))
    mount_point: str = "secret"
    env_file: str = ".env"
    secret_path: str = ""

    def validate(self) -> None:
        """Raise ValueError if required fields are missing."""
        if not self.vault_addr:
            raise ValueError("VAULT_ADDR is required but not set.")
        if not self.vault_token:
            raise ValueError(
                "VAULT_TOKEN is required but not set. "
                "Set the VAULT_TOKEN environment variable or pass --token."
            )
        if not self.secret_path:
            raise ValueError("secret_path must be provided.")

    @classmethod
    def from_env(cls, overrides: Optional[dict] = None) -> "VaultConfig":
        """Create a VaultConfig from environment variables with optional overrides."""
        instance = cls()
        if overrides:
            for key, value in overrides.items():
                if hasattr(instance, key) and value is not None:
                    setattr(instance, key, value)
        return instance
