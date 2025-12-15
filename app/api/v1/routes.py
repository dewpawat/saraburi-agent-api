from fastapi import APIRouter
from .hie import router as hie_router
from .stroke import router as stroke_router
from .rti import router as rti_router
from .epidem import router as epidem_router
from .monitor import router as monitor_router

router = APIRouter()

router.include_router(hie_router, prefix="/hie", tags=["HIE"])
router.include_router(stroke_router, prefix="/stroke", tags=["Stroke"])
router.include_router(rti_router, prefix="/rti", tags=["RTI"])
router.include_router(epidem_router, prefix="/epidem", tags=["Epidem"])
router.include_router(monitor_router, prefix="/monitor", tags=["Monitor"])
 