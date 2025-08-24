import datetime
import logging
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, BinaryIO, Optional

logger = logging.getLogger(__name__)


@dataclass
class OCRLine:
    """Simple representation of a single line of OCR text."""

    text: str
    bounding_polygon: list[float]


class OCRService:
    """Service helper to extract text using Azure Vision Image Analysis.

    The service uploads the supplied file to Azure Blob storage and then
    invokes the Azure AI Vision *Image Analysis* OCR capability.  When the
    environment variable ``APP_MODE`` is set to ``"local"`` the file is stored
    on the local filesystem instead of blob storage.
    """

    def __init__(
        self,
        *,
        vision_endpoint: Optional[str] = None,
        vision_key: Optional[str] = None,
        storage_conn_str: Optional[str] = None,
        container_name: str = "uploads",
        local_dir: Optional[str] = None,
    ) -> None:
        self.vision_endpoint = vision_endpoint or os.getenv("VISION_ENDPOINT")
        self.vision_key = vision_key or os.getenv("VISION_KEY")
        self.storage_conn_str = storage_conn_str or os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        self.container_name = container_name
        self.local_dir = Path(local_dir or os.getenv("LOCAL_STORAGE", "data"))
        self.app_mode = os.getenv("APP_MODE", "cloud").lower()

    async def extract_text(self, file: BinaryIO, filename: str) -> dict[str, Any]:
        """Upload ``file`` and return OCR text with metadata.

        Parameters
        ----------
        file:
            A binary file-like object positioned at the beginning of the data.
        filename:
            Name to use when storing the file in blob storage or locally.
        """

        if self.app_mode == "local":
            stored_path = await self._save_local(file, filename)
            with open(stored_path, "rb") as f:
                image_data = f.read()
            result = await self._analyze_image(image_data=image_data)
            result["path"] = str(stored_path)
            return result

        blob_url = await self._upload_to_blob(file, filename)
        result = await self._analyze_image(image_url=blob_url)
        result["url"] = blob_url
        return result

    async def _upload_to_blob(self, file: BinaryIO, filename: str) -> str:
        """Upload ``file`` to Azure Blob Storage and return the URL."""

        if not self.storage_conn_str:
            raise RuntimeError("AZURE_STORAGE_CONNECTION_STRING is not configured")

        from azure.storage.blob import BlobSasPermissions, generate_blob_sas
        from azure.storage.blob.aio import BlobServiceClient

        service_client = BlobServiceClient.from_connection_string(self.storage_conn_str)
        container = service_client.get_container_client(self.container_name)
        if not await container.exists():
            await container.create_container()

        blob_client = container.get_blob_client(filename)
        await blob_client.upload_blob(file, overwrite=True)

        # Generate a short lived SAS so the Vision service can access the blob
        sas = generate_blob_sas(
            account_name=blob_client.account_name,
            container_name=blob_client.container_name,
            blob_name=blob_client.blob_name,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.datetime.utcnow() + datetime.timedelta(hours=1),
        )
        await service_client.close()
        return f"{blob_client.url}?{sas}"

    async def _save_local(self, file: BinaryIO, filename: str) -> Path:
        """Save the file to ``self.local_dir`` and return the path."""

        self.local_dir.mkdir(parents=True, exist_ok=True)
        path = self.local_dir / filename
        file.seek(0)
        with open(path, "wb") as f:
            f.write(file.read())
        return path

    async def _analyze_image(
        self, *, image_url: Optional[str] = None, image_data: Optional[bytes] = None
    ) -> dict[str, Any]:
        """Run the Azure Vision OCR service on the supplied image."""

        if not self.vision_endpoint or not self.vision_key:
            raise RuntimeError("Vision endpoint/key not configured")

        from azure.ai.vision.imageanalysis.aio import ImageAnalysisClient
        from azure.ai.vision.imageanalysis.models import VisualFeatures
        from azure.core.credentials import AzureKeyCredential

        credential = AzureKeyCredential(self.vision_key)
        client = ImageAnalysisClient(self.vision_endpoint, credential)

        try:
            if image_url:
                analysis = await client.analyze(image_url=image_url, visual_features=[VisualFeatures.READ])
            elif image_data:
                analysis = await client.analyze(image_data=image_data, visual_features=[VisualFeatures.READ])
            else:
                raise ValueError("Either image_url or image_data must be provided")
        finally:
            await client.close()

        lines: list[OCRLine] = []
        text: list[str] = []
        language: Optional[str] = None

        read_result = getattr(analysis, "read", None)
        if read_result:
            if getattr(read_result, "languages", None):
                # languages may be list[DetectedLanguage] with .name or .locale
                lang = read_result.languages[0]
                language = getattr(lang, "locale", None) or getattr(lang, "name", None)

            for block in getattr(read_result, "blocks", []):
                for line in getattr(block, "lines", []):
                    text.append(line.text)
                    lines.append(OCRLine(text=line.text, bounding_polygon=list(line.bounding_polygon)))

        return {
            "language": language,
            "text": "\n".join(text),
            "lines": [asdict(line) for line in lines] if lines else [],
        }
