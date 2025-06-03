from fastapi import APIRouter
from fastapi.responses import UJSONResponse

router = APIRouter(tags=["Health check"])


@router.get("/healthcheck")
async def healthcheck():
    return UJSONResponse(content={"success": True, "msg": "App available"})
