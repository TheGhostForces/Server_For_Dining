from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import date, datetime


class Student(BaseModel):
    pass

class Token(BaseModel):
    access_token: str
    token_type: str

class DishAdd(BaseModel):
    dish_name: str
    category: str
    fixed_price: int
    institution_id: int
    img_url: Optional[str] = None

class Dish(DishAdd):
    id: int

class Orders(Dish):
    order_id: int
    total_price: int
    created_at: datetime
    dish_id: int
    quantity: int

class Dishes(Dish):
    dish_id: int
    quantity: int

class DishesBasket(Dishes):
    total_price: int
    schedule_quantity: int
    date: date
    schedule_dish_id: int

class Institution(BaseModel):
    id: int
    name: str

class Order(BaseModel):
    order_id: int
    added_items: int

class DishHistory(BaseModel):
    dish_id: int
    quantity: int
    dish_name: str
    fixed_price: int
    total_price: int
    date: date

class OrderHistory(BaseModel):
    order_id: int
    dishes: List[DishHistory]

class DishToBasket(BaseModel):
    dish_id: int
    cart_quantity: int = Field(..., gt=0, description="Количество должно быть больше 0")

class DishRequest(BaseModel):
    items: List[DishToBasket]

class Universal(BaseModel):
    Ok: bool = True

class InstitutionsUniversal(Universal):
    Institutions: List[Institution]

class OrderSchema(Universal):
    Order: Order

class OrdersSchema(Universal):
    Orders: List[Orders]

class DishListBasket(Universal):
    dishes: List[DishesBasket]

class UniversalWithID(Universal):
    id: int

class UniversalOrderHistory(Universal):
    history: List[OrderHistory]

class UniversalStudent(Universal):
    student_id: int
    tmp_code_id: int

class UniversalDish(Universal):
    dish: Dish

class UniversalListDish(Universal):
    dishes: List[Dish]

class UniversalDishes(Universal):
    dishes: List[Dishes]