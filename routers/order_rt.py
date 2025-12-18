from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from database.repository import OrdersRepository
from schemas import Universal, OrderSchema, OrdersSchema
from security.auth import require_role

router = APIRouter(
    prefix="/orders",
    tags=["Эндпоинты для заказов"],
)

@router.post("/order", tags=["Студент"], response_model=OrderSchema)
async def create_order(
        student = Depends(require_role("student"))
):
    order = await OrdersRepository.create_order(student.id)
    return {"Ok": True, "Order": order}

@router.delete("/order", tags=["Студент"], response_model=Universal)
async def undo_order(
        student = Depends(require_role("student"))
):
    # if datetime.today().hour >= 16:
    #     raise HTTPException(status_code=400, detail="Not enough time")
    await OrdersRepository.undo_order(student.id)
    return {"Ok": True}

@router.get("/order", tags=["Студент"], response_model=OrdersSchema)
async def get_dishes_in_order(
        student = Depends(require_role("student"))
):
    orders = await OrdersRepository.get_dishes(student_id=student.id)
    return {"Ok": True, "Orders": orders}

@router.get("/student_order", response_model=OrdersSchema, tags=["Оператор раздачи"])
async def get_dishes_in_order_by_student_id(
        student_id: int,
        operator = Depends(require_role("operator"))
):
    orders = await OrdersRepository.get_dishes(student_id=student_id)
    return {"Ok": True, "Orders": orders}

@router.patch("/order", tags=["Оператор раздачи"], response_model=Universal)
async def complete_order_by_student_id(
        student_id: int,
        operator = Depends(require_role("operator"))
):
    await OrdersRepository.complete_order(student_id=student_id)
    return {"Ok": True}

@router.get("/total_quantity", tags=["Поставщик"])
async def get_all_ordered_dishes(
        institution_id: int,
        provider = Depends(require_role("provider"))
):
    dishes = await OrdersRepository.get_all_ordered_dishes(institution_id=institution_id, day=datetime.now().date())
    return {"Ok": True, "dishes": dishes}