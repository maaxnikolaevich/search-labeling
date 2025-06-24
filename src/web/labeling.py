from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends, Path, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
from starlette import status

from adapters import queries
from models import MarkupResult, MarkupSession, SearchResult
from services.labeling import (
    complete_session,
    load_new_cases,
    rate_search,
    skip_session,
    start_new_markup_session,
)
from web.deps import (
    DBSessionDep,
    check_auth,
    get_current_user,
    get_elasticsearch_client,
    get_search_cases_repo,
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


def _to_result_items(search_results: list[SearchResult], markup_results: list[MarkupResult]) -> list[dict]:
    items = []
    markups_map = {mr.search_result_id: mr for mr in markup_results}

    for result in search_results:
        data = asdict(result)
        if markups_map.get(result.id):
            data["is_relevant"] = markups_map[result.id].is_relevant
        items.append(data)

    return items


@router.get("/thankyou", response_class=HTMLResponse, name="thankyou")
async def thankyou(
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


@router.post("/search-cases/{currentSessionId}/missed")
async def skip_session_handler(
    request: Request,
    current_session_id: str = Path(alias="currentSessionId"),
    session_repository=Depends(get_session_repo),
):
    await skip_session(current_session_id, session_repository)
    return RedirectResponse(url=request.url_for("rate"), status_code=status.HTTP_302_FOUND)


@router.get("/", response_class=HTMLResponse, name="rate")
async def index(
    request: Request,
    db_session: DBSessionDep,
    templates=Depends(get_templates),
    user=Depends(get_current_user),
    analytics_adapter=Depends(get_elasticsearch_client),
    search_adapter=Depends(get_search_connector_client),
    session_repository=Depends(get_session_repo),
    search_cases_repo=Depends(get_search_cases_repo),
):
    unfinished_session: MarkupSession | None = await session_repository.find_by_user_id(user.oidc_id, started=True)
    if unfinished_session:
        unfinished_session.start()

        search_results = _to_result_items(unfinished_session.search_case.results, unfinished_session.results)

        content = {
            "request": request,
            "search_case": unfinished_session.search_case,
            "user": unfinished_session.user,
            "session": unfinished_session,
            "search_results": search_results,
        }

        await session_repository.save(unfinished_session)

        if request.headers.get("hx-request") == "true":
            return templates.TemplateResponse("rate_card.html", content)
        else:
            return templates.TemplateResponse("page.html", content)

    search_case = await queries.get_active_case(db_session=db_session, user_id=user.oidc_id)
    if not search_case:
        # Подгружаем если в бд пусто или не осталось не показанных для текущего пользователя
        await load_new_cases(
            analytics_adapter=analytics_adapter,
            search_adapter=search_adapter,
            cases_repo=search_cases_repo,
            db_session=db_session,
            cases_count=20,
            results_limit_per_case=10,
        )
        return RedirectResponse(url=request.url_for("rate"), status_code=status.HTTP_302_FOUND)

    await start_new_markup_session(user, search_case, session_repository)

    return RedirectResponse(url=request.url_for("rate"), status_code=status.HTTP_302_FOUND)


@router.post("/results", name="rate_result")
async def rate_search_result(
    data: CreateResultSchema,
    request: Request,
    session_repository=Depends(get_session_repo),
    templates=Depends(get_templates),
):
    session, result = await rate_search(
        data.search_session_id,
        data.is_relevant,
        data.position,
        data.search_result_id,
        session_repository,
    )

    results_map = {result.id: result for result in session.search_case.results}
    result_item = asdict(results_map[data.search_result_id])
    result_item["is_relevant"] = result.is_relevant

    context = {"request": request, "result": result_item, "session": session}
    return templates.TemplateResponse("result_item.html", context)
