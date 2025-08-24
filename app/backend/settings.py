from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    tenant_id: str | None = Field(default=None, env="AZURE_TENANT_ID")
    client_id: str | None = Field(default=None, env="AZURE_CLIENT_ID")
    api_base_url: str | None = Field(default=None, env="API_BASE_URL")
    storage_endpoint: str | None = Field(default=None, env="AZURE_STORAGE_ENDPOINT")


settings = Settings()
