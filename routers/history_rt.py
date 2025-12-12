from fastapi import APIRouter, Depends
from Server_For_Dining.database.repository import HistoryRepository
from Server_For_Dining.schemas import UniversalOrderHistory
from Server_For_Dining.security.auth import require_role

router = APIRouter(
    prefix="/history",
    tags=["Эндпоинты для истории заказов"],
)

@router.get("/history", response_model=UniversalOrderHistory, tags=["Студент"])
async def get_history(
        month: int = None,
        year: int = None,
        student = Depends(require_role("student"))
):
    history = await HistoryRepository.get_history_for_month(student.id, month, year)
    return {"Ok": True, "history": history}