import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv
from openai import AzureOpenAI

try:  # pragma: no cover - optional dependency
    from azure.identity import DefaultAzureCredential, get_bearer_token_provider
except Exception:  # pragma: no cover - azure packages may be absent
    DefaultAzureCredential = None  # type: ignore[assignment]
    get_bearer_token_provider = None  # type: ignore[assignment]

try:  # pragma: no cover - optional dependency
    from azure.keyvault.secrets import SecretClient
except Exception:  # pragma: no cover - azure packages may be absent
    SecretClient = None  # type: ignore[assignment]

try:  # pragma: no cover - optional dependency
    from azure.storage.blob import BlobServiceClient
except Exception:  # pragma: no cover - azure packages may be absent
    BlobServiceClient = None  # type: ignore[assignment]

try:  # pragma: no cover - optional dependency
    from azure.ai.textanalytics import TextAnalyticsClient
except Exception:  # pragma: no cover - azure packages may be absent
    TextAnalyticsClient = None  # type: ignore[assignment]

try:  # pragma: no cover - optional dependency
    from azure.core.credentials import AzureKeyCredential
except Exception:  # pragma: no cover - azure packages may be absent
    AzureKeyCredential = None  # type: ignore[assignment]

try:  # pragma: no cover - optional dependency
    from azure.ai.vision import VisionClient, VisionServiceOptions
except Exception:  # pragma: no cover - vision package may be absent
    VisionClient = None  # type: ignore[assignment]
    VisionServiceOptions = None  # type: ignore[assignment]

APP_MODE = os.getenv("APP_MODE", "local").lower()

if APP_MODE == "local":
    load_dotenv()


@lru_cache
def _get_default_credential() -> Optional[DefaultAzureCredential]:  # pragma: no cover - simple accessor
    if APP_MODE == "azure" and DefaultAzureCredential is not None:
        return DefaultAzureCredential()
    return None


@lru_cache
def get_secret_client() -> Optional[SecretClient]:
    if APP_MODE == "azure" and SecretClient is not None:
        url = os.environ.get("AZURE_KEY_VAULT_URL")
        if url:
            credential = _get_default_credential()
            if credential:
                return SecretClient(vault_url=url, credential=credential)
    return None


def get_secret(name: str) -> Optional[str]:
    client = get_secret_client()
    if client is not None:
        try:
            return client.get_secret(name).value
        except Exception:
            return None
    return os.getenv(name)


@lru_cache
def get_blob_service_client() -> Any:
    if APP_MODE == "azure" and BlobServiceClient is not None:
        url = os.environ.get("AZURE_STORAGE_BLOB_ACCOUNT_URL") or os.environ.get("AZURE_BLOB_SERVICE_URL")
        if url:
            credential = _get_default_credential()
            if credential:
                return BlobServiceClient(account_url=url, credential=credential)
    path = Path(os.environ.get("LOCAL_BLOB_STORAGE_PATH", "./data"))
    path.mkdir(parents=True, exist_ok=True)
    return path


@lru_cache
def get_text_analytics_client() -> Optional[TextAnalyticsClient]:
    endpoint = os.environ.get("AZURE_LANGUAGE_ENDPOINT")
    if not endpoint or TextAnalyticsClient is None:
        return None
    if APP_MODE == "azure":
        credential = _get_default_credential()
    else:
        key = os.environ.get("AZURE_LANGUAGE_KEY")
        credential = AzureKeyCredential(key) if key and AzureKeyCredential else None
    if credential is None:
        return None
    return TextAnalyticsClient(endpoint=endpoint, credential=credential)


@lru_cache
def get_vision_client() -> Optional[VisionClient]:
    endpoint = os.environ.get("AZURE_VISION_ENDPOINT")
    if not endpoint or VisionClient is None:
        return None
    if APP_MODE == "azure":
        credential = _get_default_credential()
    else:
        key = os.environ.get("AZURE_VISION_KEY")
        credential = AzureKeyCredential(key) if key and AzureKeyCredential else None
    if credential is None or VisionServiceOptions is None:
        return None
    options = VisionServiceOptions(endpoint, credential)
    return VisionClient(options)


@lru_cache
def get_openai_client() -> Optional[AzureOpenAI]:
    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    if not endpoint:
        return None
    api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    if APP_MODE == "azure":
        credential = _get_default_credential()
        if credential is None or get_bearer_token_provider is None:
            return None
        token_provider = get_bearer_token_provider(credential, "https://cognitiveservices.azure.com/.default")
        return AzureOpenAI(
            azure_endpoint=endpoint,
            azure_ad_token_provider=token_provider,
            api_version=api_version,
        )
    key = os.environ.get("AZURE_OPENAI_KEY")
    if not key:
        return None
    return AzureOpenAI(
        azure_endpoint=endpoint,
        api_key=key,
        api_version=api_version,
    )


def probe() -> dict[str, bool]:
    """Attempt minimal calls to verify configured services are reachable."""
    results: dict[str, bool] = {}

    client = get_secret_client()
    if client is not None:
        try:
            next(client.list_properties_of_secrets(), None)
            results["key_vault"] = True
        except Exception:
            results["key_vault"] = False
    else:
        results["key_vault"] = False

    blob_client = get_blob_service_client()
    if isinstance(blob_client, Path):
        results["blob_storage"] = blob_client.exists()
    elif blob_client is not None:
        try:
            blob_client.get_service_properties()
            results["blob_storage"] = True
        except Exception:
            results["blob_storage"] = False
    else:
        results["blob_storage"] = False

    ta_client = get_text_analytics_client()
    if ta_client is not None:
        try:
            ta_client.analyze_sentiment(["probe"])
            results["text_analytics"] = True
        except Exception:
            results["text_analytics"] = False
    else:
        results["text_analytics"] = False

    vision_client = get_vision_client()
    if vision_client is not None:
        try:
            probe_fn = getattr(vision_client, "get_account_info", None)
            if probe_fn:
                probe_fn()
            results["vision"] = True
        except Exception:
            results["vision"] = False
    else:
        results["vision"] = False

    openai_client = get_openai_client()
    if openai_client is not None:
        try:
            openai_client.models.list()
            results["openai"] = True
        except Exception:
            results["openai"] = False
    else:
        results["openai"] = False

    return results


__all__ = [
    "get_secret_client",
    "get_secret",
    "get_blob_service_client",
    "get_text_analytics_client",
    "get_vision_client",
    "get_openai_client",
    "probe",
]
