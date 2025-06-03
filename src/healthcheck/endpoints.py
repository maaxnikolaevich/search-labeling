from fastapi import APIRouter
from fastapi.responses import UJSONResponse

router = APIRouter(prefix="/healthcheck", tags=["Health check"])


@router.get("/")
async def healthcheck():
    return UJSONResponse(content={"success": True, "msg": "App available"})
