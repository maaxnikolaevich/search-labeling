from __future__ import annotations

import uuid
from datetime import datetime

from adapters.analytics_adapter import ElasticsearchClient
from adapters.repository import AbstractMarkupSessionRepository
from adapters.search_adapter import SearchConnectorClient
from models import (
    MarkupResult,
    MarkupSession,
    RateError,
    SearchCase,
    User,
)


async def get_new_cases(
    analytics_adapter: ElasticsearchClient,
    search_adapter: SearchConnectorClient,
    limit: int = 2,
):
    top_cerebro_queries = await analytics_adapter.get_cerebro_top_search_queries(limit)
    search_cases: list[SearchCase] = []

    for search_query in top_cerebro_queries:
        results = await search_adapter.search(search_query.query)
        search_case = SearchCase(
            id=uuid.uuid4().hex,
            query=search_query,
            time_generated=datetime.now(),
            results=results,
        )
        search_cases.append(search_case)
    print("Загрузка кейсов... Запрошено ", len(search_cases), " кейсов")
    return search_cases


async def rate_search(
    session_id: str,
    is_relevant: bool | None,
    position: int | None,
    search_result_id: str,
    session_repo: AbstractMarkupSessionRepository,
):
    """Сохраняет результат оценки"""
    session = await session_repo.get(session_id)

    if not session:
        raise RateError("Сессия не найдена")

    result = MarkupResult(
        search_result_id=search_result_id,
        is_relevant=is_relevant,
        reranked_position=position,
    )

    session.add_result(result)
    await session_repo.save(session)


async def complete_session(session_id: str, session_repo: AbstractMarkupSessionRepository):
    """Завершает сессию разметки"""
    session = await session_repo.get(session_id)

    if not session:
        raise RateError("Сессия не найдена")

    session.complete()

    await session_repo.save(session)


async def start_markup_session(session: MarkupSession, session_repository: AbstractMarkupSessionRepository):
    session.start()
    await session_repository.save(session)


async def assign_cases_to_user(
    cases: list[SearchCase],
    user: User,
    session_repository: AbstractMarkupSessionRepository,
):
    new_batch = [MarkupSession.create(user, case) for case in cases]
    await session_repository.save_all(new_batch)
