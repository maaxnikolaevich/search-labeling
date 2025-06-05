from __future__ import annotations

from fastapi import Request

from adapters.repository import AbstractUserRepository
from auth.keycloak_client import keycloak_client
from models import User


async def _login_user(oidc_id: str, email: str, user_repository: AbstractUserRepository) -> User:
    user = await user_repository.get(oidc_id)
    if not user:
        user = User(oidc_id, email)
        await user_repository.save(user)
    return user


async def login(request: Request, access_token: str, user_repository: AbstractUserRepository):
    userinfo = await keycloak_client.a_userinfo(access_token)
    user = await _login_user(userinfo["sub"], userinfo["email"], user_repository)
    request.session["user"] = user.to_dict()


def logout(request: Request):
    request.scope.pop("user", None)
    request.session.clear()


async def authenticate(request: Request, user_repository: AbstractUserRepository) -> bool:
    if request.session is None:
        return False
    user = request.session.get("user")
    if user is None:
        return False

    user = await _login_user(user["oidc_id"], user["email"], user_repository)

    request.scope["user"] = user.to_dict()

    return True
