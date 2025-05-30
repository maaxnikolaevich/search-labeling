from __future__ import annotations

from urllib.parse import urljoin

import httpx

from models import SearchQuery


class ElasticsearchError(Exception):
    pass


class ElasticsearchClient:
    def __init__(self, url: str, login: str, password: str):
        self._url = url
        self._login = login
        self._password = password
        self._auth = (self._login, self._password)
        self._headers = {"content-type": "application/json"}

    async def get_cerebro_top_search_queries(self, size: int = 100) -> list[SearchQuery]:
        """
        Топ популярных запросов в Cerebro
        """
        url = urljoin(self._url, "/cerebro_events/_search")
        aggs_field_name = "data"

        body = {
            "size": 0,
            "query": {
                "bool": {
                    "must": [
                        {"exists": {"field": "event.phrase.keyword"}},
                        {"range": {"event_datetime": {"gte": "now-30d/d", "lte": "now/d"}}},
                    ]
                }
            },
            "aggs": {
                aggs_field_name: {
                    "terms": {
                        "field": "event.phrase.keyword",
                        "size": size,
                        "order": {"_count": "desc"},
                    }
                }
            },
        }

        async with httpx.AsyncClient(auth=self._auth, headers=self._headers) as client:
            response = await client.post(url=url, json=body)

        try:
            response.raise_for_status()
        except httpx.HTTPError as e:
            print(e)
            raise ElasticsearchError from e

        data = response.json()["aggregations"].get(aggs_field_name, {}).get("buckets", [])

        return [SearchQuery(query=item["key"], usage_frequency=item["doc_count"]) for item in data]
