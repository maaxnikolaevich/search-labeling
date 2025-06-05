from __future__ import annotations

import functools
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.ext.asyncio.engine import create_async_engine
from starlette import status
from starlette.exceptions import HTTPException
from starlette.requests import Request

from adapters.analytics_adapter import ElasticsearchClient
from adapters.orm import start_mappers
from adapters.repository import MarkupSessionRepository, UserRepository
from adapters.search_adapter import SearchConnectorClient
from auth.auth import authenticate
from models import User

base_path = Path(__file__).resolve().parent


def get_templates():
    return Jinja2Templates(directory=str(base_path / "templates"))


class UserNotFoundError(Exception):
    pass


POSTGRES_POOL_MIN_SIZE = int(os.getenv("POSTGRES_POOL_MIN_SIZE") or 5)
DB_URL = (
    f"postgresql+asyncpg://{os.getenv('POSTGRES_DB_USER') or ''}:"
    f"{os.getenv('POSTGRES_DB_PASSWORD') or ''}@{os.getenv('POSTGRES_DB_HOST') or ''}"
    f":{os.getenv('POSTGRES_DB_PORT') or '5432'}/{os.getenv('POSTGRES_DB_NAME') or ''}"
)

alchemy_async_engine = create_async_engine(
    DB_URL,
    echo=False,
    pool_size=POSTGRES_POOL_MIN_SIZE,
    max_overflow=int(os.getenv("POSTGRES_POOL_MAX_SIZE") or 10) - POSTGRES_POOL_MIN_SIZE,
    pool_recycle=600,
    pool_pre_ping=True,
)

asyncsession = async_sessionmaker(bind=alchemy_async_engine, autoflush=False)
start_mappers()


@asynccontextmanager
async def db_session():
    session = asyncsession()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def get_db_session():
    async with db_session() as session:
        yield session


DBSessionDep = Annotated[AsyncSession, Depends(get_db_session)]


def get_session_repo(session: DBSessionDep) -> MarkupSessionRepository:
    return MarkupSessionRepository(session)


def get_user_repo(session: DBSessionDep) -> UserRepository:
    return UserRepository(session)


async def get_current_user(request: Request, user_repo: UserRepository = Depends(get_user_repo)) -> User:
    user_info = request.scope.get("user")

    if not user_info:
        raise UserNotFoundError

    user = await user_repo.get(user_info["oidc_id"])

    if not user:
        raise UserNotFoundError

    return user


async def check_auth(request: Request, db_session_: DBSessionDep, user_repository=Depends(get_user_repo)):
    login_path = request.url_for("preview")

    is_auth = await authenticate(request, user_repository)
    await db_session_.commit()

    if not is_auth:
        if request.headers.get("HX-Request") == "true":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                headers={"HX-Redirect": str(login_path)},
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_307_TEMPORARY_REDIRECT,
                headers={"Location": str(login_path)},
            )


@functools.cache
def get_elasticsearch_client() -> ElasticsearchClient:
    url = os.getenv("ELASTICSEARCH_URL") or ""
    login = os.getenv("ELASTICSEARCH_LOGIN") or ""
    password = os.getenv("ELASTICSEARCH_PASSWORD") or ""
    return ElasticsearchClient(url, login, password)


@functools.cache
def get_search_connector_client() -> SearchConnectorClient:
    url = os.getenv("SEARCH_CONNECTOR_URL") or ""
    api_key = os.getenv("SEARCH_CONNECTOR_API_KEY") or ""
    return SearchConnectorClient(url, api_key)
