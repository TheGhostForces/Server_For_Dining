from fastapi import APIRouter, Depends
from Server_For_Dining.database.repository import InstitutionRepository
from Server_For_Dining.schemas import InstitutionsUniversal
from Server_For_Dining.security.auth import require_role

router = APIRouter(
    prefix="/institution",
    tags=["Эндпоинты для учебных заведений"],
)

@router.get("/institutions", tags=["Поставщик"], response_model=InstitutionsUniversal)
async def get_institutions(provider = Depends(require_role("provider"))):
    institutions = await InstitutionRepository.get_institutions()
    return {"Ok": True, "Institutions": institutions}