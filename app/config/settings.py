"""Application configuration utilities.

Provides helpers to load secrets from Azure Key Vault and a Pydantic
``Settings`` class that sources sensitive values from Key Vault when running
in staging or production environments.
"""
from __future__ import annotations

import os
from functools import lru_cache

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from pydantic import BaseSettings, Field, model_validator


@lru_cache
def _secret_client() -> SecretClient:
    """Create (and cache) a SecretClient for the configured Key Vault."""
    vault_url = os.environ.get("KEY_VAULT_URL")
    if not vault_url:
        raise ValueError("KEY_VAULT_URL environment variable is not set")
    credential = DefaultAzureCredential()
    return SecretClient(vault_url=vault_url, credential=credential)


def get_secret(name: str) -> str:
    """Retrieve a secret value from Azure Key Vault."""
    return _secret_client().get_secret(name).value


class Settings(BaseSettings):
    """Application settings loaded from environment or Azure Key Vault."""

    environment: str = Field(default="local", alias="ENVIRONMENT")
    azure_openai_key: str | None = Field(default=None, alias="AZURE_OPENAI_KEY")
    azure_search_key: str | None = Field(default=None, alias="AZURE_SEARCH_KEY")

    _secret_fields = {
        "azure_openai_key": "AZURE-OPENAI-KEY",
        "azure_search_key": "AZURE-SEARCH-KEY",
    }

    @model_validator(mode="after")
    def load_key_vault_secrets(self) -> Settings:
        """Populate secret fields from Key Vault in staging/production."""
        if self.environment.lower() in {"staging", "production"}:
            for field, secret_name in self._secret_fields.items():
                if getattr(self, field) in (None, ""):
                    setattr(self, field, get_secret(secret_name))
        return self


__all__ = ["Settings", "get_secret"]
