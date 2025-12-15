from fastapi import APIRouter

router = APIRouter()

@router.get("/ping")
async def epidem_ping():
    return {"epidem": "coming soon"}
