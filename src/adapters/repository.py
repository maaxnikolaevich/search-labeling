from __future__ import annotations

import abc

from sqlalchemy import select
from sqlalchemy.ext.asyncio.session import AsyncSession

from adapters import orm
from models import MarkupSession, SearchCase, User


class AbstractUserRepository(abc.ABC):
    @abc.abstractmethod
    async def get(self, oidc_id: str) -> User | None: ...

    @abc.abstractmethod
    async def save(self, user: User): ...


class AbstractSearchCaseRepository(abc.ABC):
    @abc.abstractmethod
    async def get(self, case_id: str) -> SearchCase | None: ...

    @abc.abstractmethod
    async def save_all(self, cases: list[SearchCase]): ...


class AbstractMarkupSessionRepository:
    @abc.abstractmethod
    async def get(self, session_id: str) -> MarkupSession | None: ...

    @abc.abstractmethod
    async def find_by_user_id(
        self, user_id: str, started: bool = False, finished: bool = False
    ) -> MarkupSession | None: ...

    @abc.abstractmethod
    async def save(self, session: MarkupSession): ...

    @abc.abstractmethod
    async def save_all(self, sessions: list[MarkupSession]): ...


class MarkupSessionRepository(AbstractMarkupSessionRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get(self, session_id: str) -> MarkupSession | None:
        return await self._session.get(MarkupSession, session_id)

    async def find_by_user_id(
        self, user_id: str, started: bool = False, finished: bool = False
    ) -> MarkupSession | None:
        stmt = select(MarkupSession).filter_by(user_id=user_id)

        if started:
            stmt = stmt.filter(
                orm.markup_session_table.c.started_at.is_not(None),
                orm.markup_session_table.c.completed_at.is_(None),
            )
        elif finished:
            stmt = stmt.filter(orm.markup_session_table.c.completed_at.is_not(None))

        else:
            stmt = stmt.filter(
                orm.markup_session_table.c.started_at.is_(None),
                orm.markup_session_table.c.completed_at.is_(None),
            )

        return (await self._session.execute(stmt)).scalars().first()

    async def save_all(self, sessions: list[MarkupSession]):
        self._session.add_all(sessions)

    async def save(self, session: MarkupSession):
        self._session.add(session)


class UserRepository(AbstractUserRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, user: User):
        self._session.add(user)

    async def get(self, oidc_id: str) -> User | None:
        return await self._session.get(User, oidc_id)


class SearchCaseRepository(AbstractSearchCaseRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get(self, case_id: str) -> SearchCase | None:
        return await self._session.get(SearchCase, case_id)

    async def save_all(self, cases: list[SearchCase]):
        self._session.add_all(cases)


class FakeUserRepository(AbstractUserRepository):
    def __init__(self):
        self._users = set()  # type: set[User]

    async def get(self, oidc_id: str) -> User | None:
        user = next((user for user in self._users if user.oidc_id == oidc_id), None)
        return user

    async def save(self, user: User) -> User | None:
        self._users.add(user)


class FakeCaseRepository(AbstractSearchCaseRepository):
    def __init__(self):
        self._search_cases = list()  # type: list[SearchCase]

    async def get(self, case_id: str) -> SearchCase | None:
        search_case = next(
            (search_case for search_case in self._search_cases if search_case.id == case_id),
            None,
        )
        return search_case

    async def save_all(self, cases: list[SearchCase]):
        self._search_cases.extend(cases)


class FakeSessionRepository(AbstractMarkupSessionRepository):
    async def save_all(self, sessions: list[MarkupSession]):
        self._sessions.update(sessions)

    def __init__(self):
        self._sessions = set()  # type: set[MarkupSession]

    async def get(self, session_id: str) -> MarkupSession | None:
        user = next((session for session in self._sessions if session.id == session_id), None)
        return user

    async def find_by_user_id(
        self, user_id: str, started: bool = False, finished: bool = False
    ) -> MarkupSession | None:
        if finished:
            return next(
                (session for session in self._sessions if session.user.oidc_id == user_id and session.completed_at),
                None,
            )
        if started:
            return next(
                (
                    session
                    for session in self._sessions
                    if session.user.oidc_id == user_id and session.started_at and not session.completed_at
                ),
                None,
            )
        return next(
            (
                session
                for session in self._sessions
                if session.user.oidc_id == user_id and not session.started_at and not session.completed_at
            ),
            None,
        )

    async def save(self, session: MarkupSession):
        self._sessions.add(session)
