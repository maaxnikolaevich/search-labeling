from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
)
from sqlalchemy.orm import registry, relationship, sessionmaker

import models

metadata = MetaData()
mapper_registry = registry()

# Таблица для SearchQuery
search_query_table = Table(
    "search_queries",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("query", String),
    Column("usage_frequency", Integer),
)

# Таблица для SearchResult
search_result_table = Table(
    "search_results",
    metadata,
    Column("id", String, primary_key=True),
    Column("title", String),
    Column("product_code", String),
    Column("category", String),
    Column("position", Integer),
)

# Ассоциативная таблица для связи SearchCase и SearchResult
search_case_result_table = Table(
    "search_case_results",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("search_case_id", String, ForeignKey("search_cases.id")),
    Column("search_result_id", String, ForeignKey("search_results.id")),
)

# Таблица для SearchCase
search_case_table = Table(
    "search_cases",
    metadata,
    Column("id", String, primary_key=True),
    Column("query_id", String, ForeignKey("search_queries.id")),
    Column("time_generated", DateTime, default=datetime.now),
    Column("is_active", Boolean, default=True),
)


# Таблица для MarkupSession
markup_session_table = Table(
    "markup_sessions",
    metadata,
    Column("id", String, primary_key=True),
    Column("search_case_id", String, ForeignKey("search_cases.id")),
    Column("user_id", String, ForeignKey("users.oidc_id")),
    Column("started_at", DateTime, nullable=True),
    Column("completed_at", DateTime, nullable=True),
)

# Таблица для MarkupResult
markup_result_table = Table(
    "markup_results",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("search_result_id", String, ForeignKey("search_results.id")),
    Column("markup_session_id", String, ForeignKey("markup_sessions.id")),
    Column("reranked_position", Integer, nullable=True),
    Column("is_relevant", Boolean, nullable=True),
)


# Таблица для User
user_table = Table(
    "users",
    metadata,
    Column("oidc_id", String, primary_key=True),
    Column("email", String),
    Column("given_name", String),
    Column("family_name", String),
    Column("completed_count", Integer, default=0),
    Column("last_completed", DateTime, nullable=True),
    Column("daily_quota", Integer, default=10),
)


# Маппинг классов
def start_mappers():
    mapper_registry.map_imperatively(models.SearchQuery, search_query_table)
    search_results_mapper = mapper_registry.map_imperatively(models.SearchResult, search_result_table)
    mapper_registry.map_imperatively(models.User, user_table)
    mapper_registry.map_imperatively(models.MarkupResult, markup_result_table)

    mapper_registry.map_imperatively(
        models.SearchCase,
        search_case_table,
        properties={
            "query": relationship(models.SearchQuery, lazy="joined", uselist=False),
            "results": relationship(
                search_results_mapper,
                secondary=search_case_result_table,
                lazy="joined",
                collection_class=list,
            ),
        },
    )

    mapper_registry.map_imperatively(
        models.MarkupSession,
        markup_session_table,
        properties={
            "search_case": relationship(models.SearchCase, lazy="joined", uselist=False),
            "user": relationship(models.User, lazy="joined", uselist=False),
            "results": relationship(models.MarkupResult, lazy="joined", collection_class=list),
        },
    )


if __name__ == "__main__":
    # Создаем движок и таблицы
    engine = create_engine("sqlite:///rate_our_search_db.sqlite")
    metadata.create_all(engine)
    start_mappers()
    Session = sessionmaker(bind=engine)
