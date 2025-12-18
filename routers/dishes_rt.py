from datetime import date, timedelta, datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from database.repository import DishesRepository
from schemas import DishAdd, DishRequest, UniversalDish, UniversalDishes, UniversalWithID, Universal, \
    UniversalListDish, DishUpdate
from security.auth import require_role


router = APIRouter(
    prefix="/dishes",
    tags=["Эндпоинты для блюд"],
)

@router.get("/dish", tags=["Админ"], response_model=UniversalDish)
async def get_dish_by_name(
        name: str,
        institution_id: int,
        admin = Depends(require_role("admin"))
):
    cleaned_name = name.strip()
    if not cleaned_name:
        raise HTTPException(status_code=400, detail="Dish name cannot be empty")

    dish = await DishesRepository.get_dish(None, institution_id, cleaned_name)
    if dish is None:
        raise HTTPException(status_code=404, detail="Dish not found")
    return {"Ok": True, "dish": dish}

@router.post("/dish", response_model=UniversalWithID, tags=["Админ"])
async def create_dish(
        dish: DishAdd,
        admin = Depends(require_role("admin"))
):
    existing_dish = await DishesRepository.get_dish(None, None, dish.dish_name.strip())
    if existing_dish:
        if existing_dish.institution_id != dish.institution_id:
            raise HTTPException(
                status_code=409,
                detail=f"Dish with name '{dish.dish_name.strip()}' already exists"
            )
    dish_id = await DishesRepository.create_one_dish(dish)
    return {"Ok":True, "id": dish_id}

@router.delete("/dish", response_model=Universal, tags=["Админ"])
async def delete_dish(
        dish_id: int = None,
        dish_name: str = None,
        institution_id: int = None,
        admin = Depends(require_role("admin"))
):
    if dish_id is None and dish_name is None:
        raise HTTPException(status_code=400, detail="Cannot be deleted without parameters")
    if dish_name and institution_id is None:
        raise HTTPException(status_code=400, detail="Cannot be deleted without institution_id")
    dish = await DishesRepository.get_dish(dish_id, institution_id, dish_name)
    if dish is None:
        raise HTTPException(status_code=404, detail="Dish not found")
    dish = await DishesRepository.delete_dish(dish.id)
    if dish is None:
        raise HTTPException(status_code=400, detail="Dishes cannot be deleted")
    return {"Ok": True}

@router.patch("/dish", response_model=Universal, tags=["Админ"])
async def update_dish(
        data: DishUpdate,
        dish_id: int = None,
        dish_name: str = None,
        institution_id: int = None,
        admin = Depends(require_role("admin"))
):
    if dish_id is None and dish_name is None:
        raise HTTPException(status_code=400, detail="Cannot be deleted without parameters")
    if dish_name and institution_id is None:
        raise HTTPException(status_code=400, detail="Cannot be deleted without institution_id")
    dish = await DishesRepository.get_dish(dish_id, institution_id, dish_name)
    if dish is None:
        raise HTTPException(status_code=404, detail="Dish not found")
    dish = await DishesRepository.update_dish(dish.id, data)
    if dish is None:
        raise HTTPException(status_code=400, detail="Dishes cannot be updated")
    return {"Ok": True}

@router.get("/dishes_tomorrow", tags=["Студент"], response_model=UniversalDishes)
async def get_dishes_tomorrow(
        student = Depends(require_role("student"))
):
    date_tomorrow = date.today() + timedelta(days=1)
    dishes = await DishesRepository.get_dishes_on_next_day(
        institution_id=student.institution_id,
        next_day=date_tomorrow
    )
    # сделать проверку на количество, если количество равно 0, то не отдавать данные
    return {"Ok": True, "dishes": dishes}

@router.get("/date_dishes", tags=["Поставщик"], response_model=UniversalDishes)
async def get_all_dishes_by_date(
        institution_id: int,
        day: str = Query(description="Дата в формате YYYY-MM-DD"),
        provider = Depends(require_role("provider"))
):
    date_obj = datetime.strptime(day, "%Y-%m-%d").date()
    dishes = await DishesRepository.get_fixed_dishes_by_date(institution_id, date_obj)
    return {"Ok": True, "dishes": dishes}

@router.get("/dishes", response_model=UniversalListDish, tags=["Оператор раздачи"])
async def get_all_dishes(
        operator = Depends(require_role("operator"))
):
    dishes = await DishesRepository.get_dishes(None, operator.institution_id)
    if not dishes:
        raise HTTPException(status_code=404, detail="Dishes not found")
    return {"Ok": True, "dishes": dishes}

@router.put("/dishes", response_model=Universal, tags=["Оператор раздачи"])
async def set_dishes_on_day(
        dishes: DishRequest,
        target_date: date,
        operator = Depends(require_role("operator"))
):
    current_day = date.today()
    if target_date <= current_day:
        raise HTTPException(status_code=400, detail="You can not assign past dates")
    if target_date > current_day + timedelta(days=7):
        raise HTTPException(status_code=400, detail="You can only bet for a week.")
    await DishesRepository.set_dishes_on_day(operator.institution_id, dishes, target_date)
    return {"Ok": True}

@router.get("/date_dishes_operator", tags=["Оператор раздачи"])
async def get_dishes_by_date(
        target_date: date,
        operator = Depends(require_role("operator"))
):
    dishes = await DishesRepository.get_fixed_dishes_by_date(operator.institution_id, target_date)
    return {"Ok": True, "dishes": dishes}