from __future__ import annotations

from fastapi.responses import UJSONResponse
from starlette import status
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response

from models import RateError, UserHasReachedDailyQuota


def setup_user_has_reached_daily_quota_exception_handler(app):
    @app.exception_handler(UserHasReachedDailyQuota)
    async def user_has_reached_daily_quota_exception_handler(
        request: Request, _: UserHasReachedDailyQuota
    ) -> RedirectResponse | Response:
        reached_daily_quota_page = request.url_for("thankyou")
        if request.headers.get("hx-request") == "true":
            return Response(
                status_code=status.HTTP_403_FORBIDDEN, headers={"hx-redirect": str(reached_daily_quota_page)}
            )
        return RedirectResponse(url=reached_daily_quota_page, status_code=status.HTTP_307_TEMPORARY_REDIRECT)


def setup_rate_error_handler(app):
    @app.exception_handler(RateError)
    async def rate_error_handler(_: Request, exc: RateError) -> UJSONResponse:
        content = {
            "error": {
                "message": str(exc),
                "errors": [{"reason": exc.__class__.__name__, "message": str(exc)}],
            }
        }
        return UJSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=content)
