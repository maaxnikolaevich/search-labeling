from __future__ import annotations

import uuid
from urllib.parse import urljoin

import httpx

from models import SearchResult


class SearchConnectorError(Exception):
    pass


class SearchConnectorClient:
    def __init__(self, url: str, api_key: str):
        self._url = url
        self._headers = {"content-type": "application/json", "x-api-key": api_key}

    async def search(self, query: str) -> list[SearchResult]:
        url = urljoin(self._url, "/api/v2/dev/materials")

        params = {"saleOrganisation": 1000, "query": query, "limit": 5}

        async with httpx.AsyncClient(headers=self._headers) as client:
            response = await client.get(url=url, headers=self._headers, params=params)  # type: ignore

        try:
            response.raise_for_status()
        except httpx.HTTPError as e:
            print(e)
            raise SearchConnectorError from e
        data = response.json()
        items: list[dict] = data["data"]["items"]
        return [
            SearchResult(
                id=uuid.uuid4().hex,
                title=item["productName"],
                product_code=item["materialId"],
                category=item.get("category", ""),
                position=i,
            )
            for i, item in enumerate(items, 1)
        ]
