from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio.session import AsyncSession

from adapters import queries
from adapters.analytics_adapter import ElasticsearchClient
from adapters.repository import AbstractMarkupSessionRepository, AbstractSearchCaseRepository
from adapters.search_adapter import SearchConnectorClient
from models import (
    MarkupResult,
    MarkupSession,
    RateError,
    SearchCase,
    User,
)


async def _load_new_cases(
    analytics_adapter: ElasticsearchClient,
    search_adapter: SearchConnectorClient,
    cases_count: int,
    results_count: int,
    excluded_queries: list[str] | None = None,
):
    top_cerebro_queries = await analytics_adapter.get_cerebro_top_search_queries(cases_count, excluded_queries)
    search_cases: list[SearchCase] = []

    for search_query in top_cerebro_queries:
        results = await search_adapter.search(search_query.query, results_count)
        search_case = SearchCase(
            id=uuid.uuid4().hex,
            query=search_query,
            time_generated=datetime.now(),
            results=results,
        )
        search_cases.append(search_case)
    print("Загрузка кейсов... Запрошено ", len(search_cases), " кейсов")
    return search_cases


async def load_new_cases(
    analytics_adapter: ElasticsearchClient,
    search_adapter: SearchConnectorClient,
    cases_repo: AbstractSearchCaseRepository,
    db_session: AsyncSession,
    cases_count: int,
    results_limit_per_case: int,
):
    loaded_queries = await queries.get_search_queries(db_session)
    search_cases = await _load_new_cases(
        analytics_adapter=analytics_adapter,
        search_adapter=search_adapter,
        cases_count=cases_count,
        results_count=results_limit_per_case,
        excluded_queries=loaded_queries or None,
    )
    await cases_repo.save_all(search_cases)
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


async def start_markup_session(
    user: User, search_case: SearchCase, session_repository: AbstractMarkupSessionRepository
):
    session = MarkupSession.create(user, search_case)
    session.start()
    await session_repository.save(session)


async def assign_cases_to_user(
    cases: list[SearchCase],
    user: User,
    session_repository: AbstractMarkupSessionRepository,
):
    new_batch = [MarkupSession.create(user, case) for case in cases]
    await session_repository.save_all(new_batch)
