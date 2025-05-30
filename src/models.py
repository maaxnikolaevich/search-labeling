from __future__ import annotations

import dataclasses
import uuid
from datetime import datetime


class RateError(Exception):
    pass


class UserHasReachedDailyQuota(Exception):
    pass


@dataclasses.dataclass(unsafe_hash=True)
class SearchResult:
    id: str
    title: str
    product_code: str
    category: str
    position: int


@dataclasses.dataclass(unsafe_hash=True)
class SearchQuery:
    query: str
    usage_frequency: int


class SearchCase:
    def __init__(
        self,
        id: str,
        query: SearchQuery,
        results: list[SearchResult],
        time_generated: datetime,
        is_active: bool = True,
    ):
        self.id = id
        self.query = query
        self.results = results
        self.time_generated = time_generated
        self.is_active = is_active

    def deactivate(self):
        self.is_active = False


@dataclasses.dataclass
class MarkupResult:
    search_result_id: str
    reranked_position: int | None = None
    is_relevant: bool | None = None


class MarkupSession:
    def __init__(
        self,
        id: str,
        user: User,
        search_case: SearchCase,
    ):
        self.id = id
        self.user = user
        self.search_case = search_case
        self.results = list()  # type: list[MarkupResult]
        self.started_at = None  # type: datetime | None
        self.completed_at = None  # type: datetime | None

    def __eq__(self, other):
        if not isinstance(other, MarkupSession):
            return False
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    def start(self):
        if not self.user.can_rate_more():
            raise UserHasReachedDailyQuota
        self.started_at = datetime.now()

    def add_result(self, result: MarkupResult):
        """Добавляет или обновляет оценку результата"""
        existing = next(
            (r for r in self.results if r.search_result_id == result.search_result_id),
            None,
        )
        if existing:
            self.results.remove(existing)
        self.results.append(result)

    def complete(self):
        """Завершает сессию разметки"""
        if len(self.results) != len(self.search_case.results):
            raise RateError("Не все результаты оценены, необходимо дать оценку для каждого результата")
        self.completed_at = datetime.now()
        self.user.last_completed = self.completed_at
        self.user.completed_count += 1

    @classmethod
    def create(cls, user: User, search_case: SearchCase):
        return cls(id=uuid.uuid4().hex, user=user, search_case=search_case)


class User:
    def __init__(self, oidc_id: str, email: str, given_name: str = "", family_name: str = ""):
        self.oidc_id = oidc_id
        self.email = email
        self.completed_count: int = 0
        self.last_completed: datetime | None = None
        self.daily_quota: int = 2

    def __eq__(self, other):
        if not isinstance(other, User):
            return False
        return self.oidc_id == other.oidc_id

    def __hash__(self):
        return hash(self.oidc_id)

    def _refresh_daily_limit(self):
        self.completed_count = 0

    def can_rate_more(self):
        if self.last_completed and ((datetime.now() - self.last_completed).total_seconds() / 3600 > 0.02):
            self._refresh_daily_limit()
        return self.completed_count < self.daily_quota

    def to_dict(self):
        return {"oidc_id": self.oidc_id, "email": self.email}
