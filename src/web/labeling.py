from __future__ import annotations

from fastapi import APIRouter, Depends, Path, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
from starlette import status

from services.labeling import (
    assign_cases_to_user,
    complete_session,
    get_new_cases,
    rate_search,
    start_markup_session,
)
from web.deps import (
    check_auth,
    get_current_user,
    get_elasticsearch_client,
    get_search_connector_client,
    get_session_repo,
    get_templates,
)

router = APIRouter(dependencies=[Depends(check_auth)])


class CreateResultSchema(BaseModel):
    search_result_id: str
    search_session_id: str
    position: int | None = None
    is_relevant: bool | None = None


@router.get("/thankyou", response_class=HTMLResponse, name="thankyou")
async def preview(
    request: Request,
    templates=Depends(get_templates),
):
    return templates.TemplateResponse(name="thankyou.html", context={"request": request})


@router.post("/search-cases/{currentSessionId}")
async def complete_session_handler(
    request: Request,
    current_session_id: str = Path(alias="currentSessionId"),
    session_repository=Depends(get_session_repo),
):
    await complete_session(current_session_id, session_repository)
    return RedirectResponse(url=request.url_for("rate"), status_code=status.HTTP_302_FOUND)


@router.get("/", response_class=HTMLResponse, name="rate")
async def index(
    request: Request,
    templates=Depends(get_templates),
    user=Depends(get_current_user),
    analytics_adapter=Depends(get_elasticsearch_client),
    search_adapter=Depends(get_search_connector_client),
    session_repository=Depends(get_session_repo),
):
    unfinished_session = await session_repository.get_session(user.oidc_id, started=True)

    if unfinished_session:
        return templates.TemplateResponse(
            "labeling.html",
            {
                "request": request,
                "search_case": unfinished_session.search_case,
                "user": unfinished_session.user,
                "session": unfinished_session,
            },
        )

    session = await session_repository.get_session(user.oidc_id)
    if session:
        await start_markup_session(session, session_repository)
        return RedirectResponse(url=request.url_for("rate"), status_code=status.HTTP_302_FOUND)

    cases = await get_new_cases(analytics_adapter, search_adapter, 20)

    await assign_cases_to_user(cases, user, session_repository)

    return RedirectResponse(url=request.url_for("rate"), status_code=status.HTTP_302_FOUND)


@router.post("/results", name="rate_result")
async def rate_search_result(data: CreateResultSchema, session_repository=Depends(get_session_repo)):
    await rate_search(
        data.search_session_id,
        data.is_relevant,
        data.position,
        data.search_result_id,
        session_repository,
    )
