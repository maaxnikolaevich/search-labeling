from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from exception_handlers import (
    setup_rate_error_handler,
    setup_user_has_reached_daily_quota_exception_handler,
)
from web.auth import router as auth_router
from web.labeling import router

app = FastAPI()


def setup_exception_handlers(app_: FastAPI):
    setup_user_has_reached_daily_quota_exception_handler(app_)
    setup_rate_error_handler(app_)


app.add_middleware(SessionMiddleware, secret_key="test")
app.mount("/static", StaticFiles(directory="web/static"), name="static")
app.include_router(router)
app.include_router(auth_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
setup_exception_handlers(app)
