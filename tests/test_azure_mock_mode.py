import os

import pytest

from app.backend.prepdocslib.strategy import SearchInfo
from tests.mocks import MockAzureCredential, MockSearchClient


@pytest.mark.asyncio
async def test_search_uses_mock_client():
    assert os.getenv("AZURE_TEST_MODE") == "mock"
    search_info = SearchInfo(
        endpoint="https://example.search.windows.net",
        credential=MockAzureCredential(),
        index_name="test-index",
    )
    async with search_info.create_search_client() as client:
        assert isinstance(client, MockSearchClient)
        results = []
        search_results = await client.search("interest rates")
        async for page in search_results:
            async for doc in page:
                results.append(doc)
    assert results and results[0]["sourcefile"] == "Financial Market Analysis Report 2023.pdf"
