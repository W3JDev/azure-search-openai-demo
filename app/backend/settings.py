from __future__ import annotations

import os
from typing import Literal

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    app_mode: Literal["local", "staging", "production"] = "local"


def load_key_vault_secrets() -> None:
    """Populate environment variables from Azure Key Vault.

    Expected environment variables:
    - ``AZURE_KEY_VAULT_ENDPOINT`` or ``AZURE_KEY_VAULT_NAME`` to locate the vault.
    - ``KEY_VAULT_SECRETS``: comma separated list of secret names to fetch.
    """

    key_vault_url = os.getenv("AZURE_KEY_VAULT_ENDPOINT")
    if not key_vault_url:
        name = os.getenv("AZURE_KEY_VAULT_NAME")
        if not name:
            return
        key_vault_url = f"https://{name}.vault.azure.net"

    secret_names = [s.strip() for s in os.getenv("KEY_VAULT_SECRETS", "").split(",") if s.strip()]
    if not secret_names:
        return

    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=key_vault_url, credential=credential)

    for secret_name in secret_names:
        try:
            os.environ[secret_name] = client.get_secret(secret_name).value
        except Exception:
            # Ignore failures to fetch individual secrets to avoid breaking startup.
            pass


def load_env_if_local() -> Settings:
    """Load environment configuration based on application mode."""

    # Load .env early so APP_MODE can be read from there during local development.
    load_dotenv()
    mode = os.getenv("APP_MODE", "local")

    if mode in {"staging", "production"}:
        load_key_vault_secrets()

    return Settings()
