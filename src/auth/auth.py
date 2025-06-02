from __future__ import annotations

from fastapi import Request

from adapters.repository import AbstractUserRepository
from auth.keycloak_client import keycloak_client
from models import User


async def login(request: Request, access_token: str, user_repository: AbstractUserRepository):
    userinfo = await keycloak_client.a_userinfo(access_token)
    user = await user_repository.get(userinfo["sub"])
    if not user:
        user = User(
            userinfo["sub"],
            userinfo["email"]
        )
        await user_repository.save(user)
    request.session["user"] = user.to_dict()


def logout(request: Request):
    request.scope.pop("user", None)
    request.session.clear()


def authenticate(request: Request) -> bool:
    if request.session is None:
        return False
    user = request.session.get("user")
    if user is None:
        return False

    request.scope["user"] = User(**user)

    return True
