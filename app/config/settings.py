from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(case_sensitive=False)

    # App mode
    app_mode: str = Field(default="local", env="APP_MODE")

    # OpenAI / Azure OpenAI
    openai_api_key: str | None = Field(default=None, env="OPENAI_API_KEY")
    openai_base_url: str | None = Field(default=None, env="OPENAI_BASE_URL")
    azure_openai_endpoint: str | None = Field(default=None, env="AZURE_OPENAI_ENDPOINT")
    azure_openai_key: str | None = Field(default=None, env="AZURE_OPENAI_KEY")

    # Azure Search
    azure_search_service: str | None = Field(default=None, env="AZURE_SEARCH_SERVICE")
    azure_search_index: str | None = Field(default=None, env="AZURE_SEARCH_INDEX")
    azure_search_key: str | None = Field(default=None, env="AZURE_SEARCH_KEY")

    # Azure Storage
    azure_storage_account: str | None = Field(default=None, env="AZURE_STORAGE_ACCOUNT")
    azure_storage_container: str | None = Field(default=None, env="AZURE_STORAGE_CONTAINER")
    azure_storage_key: str | None = Field(default=None, env="AZURE_STORAGE_KEY")

    # Speech
    azure_speech_service_id: str | None = Field(default=None, env="AZURE_SPEECH_SERVICE_ID")
    azure_speech_service_location: str | None = Field(default=None, env="AZURE_SPEECH_SERVICE_LOCATION")
    azure_speech_key: str | None = Field(default=None, env="AZURE_SPEECH_KEY")

    @property
    def is_azure(self) -> bool:
        """True if running in Azure mode."""
        return self.app_mode.lower() == "azure"

    @property
    def azure_search_endpoint(self) -> str | None:
        if self.azure_search_service:
            return f"https://{self.azure_search_service}.search.windows.net"
        return None


settings = Settings()
