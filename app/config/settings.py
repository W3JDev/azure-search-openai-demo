from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient


@lru_cache
def _get_secret_client() -> SecretClient:
    """Create a cached SecretClient using DefaultAzureCredential."""
    vault_url = os.getenv("KEY_VAULT_URL")
    if not vault_url:
        raise ValueError("KEY_VAULT_URL environment variable is not set")
    credential = DefaultAzureCredential()
    return SecretClient(vault_url=vault_url, credential=credential)


def get_secret(name: str) -> str | None:
    """Retrieve *name* from Azure Key Vault."""
    client = _get_secret_client()
    return client.get_secret(name).value


_SECRET_FIELDS = {
    "azure_openai_key": "AZURE_OPENAI_KEY",
    "azure_search_key": "AZURE_SEARCH_KEY",
}


@dataclass
class Settings:
    """Application settings loaded from environment or Key Vault."""

    environment: str = field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    azure_openai_key: str | None = field(init=False, default=None)
    azure_search_key: str | None = field(init=False, default=None)

    def __post_init__(self) -> None:  # noqa: D401 - simple initializer
        if self.environment.lower() in {"staging", "production"}:
            for attr, secret_name in _SECRET_FIELDS.items():
                setattr(self, attr, get_secret(secret_name))
        else:
            for attr, env_name in _SECRET_FIELDS.items():
                setattr(self, attr, os.getenv(env_name))


@lru_cache
def get_settings() -> Settings:
    """Return a cached instance of Settings."""
    return Settings()
