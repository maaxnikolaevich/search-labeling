from collections.abc import Sequence

from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.future import select

from adapters import orm
from models import SearchCase, SearchQuery


async def get_active_cases(db_session: AsyncSession, user_id: str, limit: int) -> Sequence[SearchCase]:
    """Запрашиваем кейсы, которые еще не назначались в сессии конктретному пользователю"""
    stmt = (
        select(SearchCase)
        .select_from(
            orm.search_case_table.outerjoin(
                orm.markup_session_table,
                (orm.markup_session_table.c.search_case_id == orm.search_case_table.c.id)
                & (orm.markup_session_table.c.user_id == user_id),
            )
        )
        .where(orm.markup_session_table.c.user_id.is_(None))
        .limit(limit)
    )
    return (await db_session.execute(stmt)).unique().scalars().all()


async def get_search_queries(db_session: AsyncSession, limit: int | None = None) -> list[str]:
    stmt = select(SearchQuery).limit(limit)
    return [search_query.query for search_query in (await db_session.execute(stmt)).scalars().all()]
