import enum

class StatusOrder(enum.Enum):
    IN_PROGRESS = "in_progress"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

class CategoryForDishes(enum.Enum):
    First = "Первое"
    Second = "Второе"
    Drink = "Напитки"
    Dessert = "Десерт"
    # будет больше