import os
from dataclasses import dataclass, field
from typing import Literal, Optional


@dataclass
class Settings:
    """Application settings loaded from environment variables."""

    app_mode: Literal["local", "staging", "production"] = field(
        default_factory=lambda: os.getenv("APP_MODE", "local").lower()
    )
    azure_key_vault_name: Optional[str] = field(
        default_factory=lambda: os.getenv("AZURE_KEY_VAULT_NAME")
    )


def load_key_vault_secrets() -> None:
    """Populate environment variables from Azure Key Vault secrets."""
    key_vault_name = os.getenv("AZURE_KEY_VAULT_NAME")
    if not key_vault_name:
        return

    from azure.identity import DefaultAzureCredential
    from azure.keyvault.secrets import SecretClient

    credential = DefaultAzureCredential()
    client = SecretClient(
        vault_url=f"https://{key_vault_name}.vault.azure.net", credential=credential
    )
    for secret in client.list_properties_of_secrets():
        value = client.get_secret(secret.name).value
        if value is not None:
            os.environ.setdefault(secret.name, value)
