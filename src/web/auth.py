from __future__ import annotations

import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from starlette import status
from starlette.responses import HTMLResponse, RedirectResponse

from adapters.repository import AbstractUserRepository
from auth.auth import login, logout
from auth.keycloak_client import keycloak_client
from web.deps import get_templates, get_user_repo

router = APIRouter()


@router.get("/preview", response_class=HTMLResponse, name="preview")
async def preview(
    request: Request,
    templates=Depends(get_templates),
):
    return templates.TemplateResponse(name="auth.html", context={"request": request})


@router.post("/users/logout", name="logout")
async def logout_handler(request: Request):
    logout(request)
    return RedirectResponse(request.url_for("preview"), status_code=status.HTTP_302_FOUND)


@router.post("/users/auth", name="auth")
async def auth(request: Request):
    redirect_uri = request.url_for("login_keycloak")
    try:
        kk_url = await keycloak_client.a_auth_url(
            redirect_uri=str(redirect_uri),
            scope="openid email profile",
            state=secrets.token_urlsafe(32),
        )

        return RedirectResponse(url=kk_url, status_code=status.HTTP_302_FOUND)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось обратиться к Keycloak. {e}",
        ) from e


@router.get("/callback/keycloak", name="login_keycloak")
async def login_keycloak(
    request: Request,
    user_repository: Annotated[AbstractUserRepository, Depends(get_user_repo)],
):
    code = request.query_params.get("code")

    if not code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Код авторизации не найден.")

    try:
        token = await keycloak_client.a_token(
            grant_type="authorization_code",
            code=code,
            redirect_uri=str(request.url_for("login_keycloak")),
        )

        if not (token and token.get("access_token")):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Не удалось получить необходимые токены из Keycloak.",
            )

        await login(request, token["access_token"], user_repository)

        return RedirectResponse(request.url_for("rate"))

    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера при входе в Keycloak.",
        ) from e
