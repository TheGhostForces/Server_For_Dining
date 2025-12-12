from datetime import datetime, date
from sqlalchemy import ForeignKey, Enum, Date, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from Server_For_Dining.database.enums import StatusOrder


class Model(DeclarativeBase):
    pass


class StudentsOrm(Model):
    __tablename__ = "Students"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_id_card: Mapped[str] = mapped_column(nullable=False)
    full_name: Mapped[str] = mapped_column(nullable=False)
    date_start: Mapped[date] = mapped_column(Date, nullable=False)
    date_end: Mapped[date] = mapped_column(Date, nullable=False)
    free_food: Mapped[bool] = mapped_column(nullable=False)
    rating: Mapped[int] = mapped_column(default=0, nullable=False)
    # возможно, стоит добавить название группы студента
    email: Mapped[str] = mapped_column(nullable=False)
    role: Mapped[str] = mapped_column(nullable=False)

    institution_id: Mapped[int] = mapped_column(ForeignKey("EducationInstitution.id"), nullable=False)

    institution: Mapped["EducationInstitutionOrm"] = relationship("EducationInstitutionOrm", back_populates="students")
    temporary_codes: Mapped[list["TemporaryCodeOrm"]] = relationship("TemporaryCodeOrm", back_populates="student")
    shopping_carts: Mapped[list["ShoppingCartOrm"]] = relationship("ShoppingCartOrm", back_populates="student")
    orders: Mapped[list["OrderOrm"]] = relationship("OrderOrm", back_populates="student")
    history: Mapped[list["HistoryOrm"]] = relationship("HistoryOrm", back_populates="student")
    qr_code: Mapped["StudentQRCodeOrm"] = relationship("StudentQRCodeOrm", back_populates="student",uselist=False)

class TemporaryCodeOrm(Model):
    __tablename__ = "TemporaryCode"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code_hash: Mapped[str] = mapped_column(nullable=False)
    attempts: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    expires_at: Mapped[datetime] = mapped_column(nullable=False)
    used_at: Mapped[datetime] = mapped_column(nullable=True)

    student_id: Mapped[int] = mapped_column(ForeignKey("Students.id"), nullable=False)
    student: Mapped["StudentsOrm"] = relationship("StudentsOrm", back_populates="temporary_codes")

class StudentQRCodeOrm(Model):
    __tablename__ = "StudentQRCode"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    QR_code_url: Mapped[str] = mapped_column(nullable=False)

    student_id: Mapped[int] = mapped_column(ForeignKey("Students.id"), nullable=False,unique=True)

    student: Mapped["StudentsOrm"] = relationship("StudentsOrm", back_populates="qr_code")

class EducationInstitutionOrm(Model):
    __tablename__ = "EducationInstitution"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(nullable=False)
    # адрес

    students: Mapped[list["StudentsOrm"]] = relationship("StudentsOrm", back_populates="institution")
    dishes: Mapped[list["DishesOrm"]] = relationship("DishesOrm", back_populates="institution")

class DishesOrm(Model):
    __tablename__ = "Dishes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    dish_name: Mapped[str] = mapped_column(nullable=False)
    category: Mapped[str] = mapped_column(nullable=False)
    # Вес
    # Пищевые ценности
    fixed_price: Mapped[int] = mapped_column(nullable=False)
    img_url: Mapped[str] = mapped_column(nullable=True)

    institution_id: Mapped[int] = mapped_column(ForeignKey("EducationInstitution.id"), nullable=False)

    institution: Mapped["EducationInstitutionOrm"] = relationship("EducationInstitutionOrm", back_populates="dishes")
    order_items: Mapped[list["OrderDishOrm"]] = relationship("OrderDishOrm", back_populates="dish")
    schedules: Mapped[list["ScheduleDishesOrm"]] = relationship("ScheduleDishesOrm", back_populates="dish")
    history_schedules: Mapped[list["HistoryScheduleOrm"]] = relationship(
        "HistoryScheduleOrm",
        back_populates="dish",
        cascade="all, delete-orphan"
    )

class ScheduleDishesOrm(Model):
    __tablename__ = "ScheduleDishes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)

    dish_id: Mapped[int] = mapped_column(ForeignKey("Dishes.id"), nullable=False)

    dish: Mapped["DishesOrm"] = relationship("DishesOrm", back_populates="schedules")
    cart_items: Mapped[list["ShoppingCartDishesOrm"]] = relationship("ShoppingCartDishesOrm", back_populates="schedule_dish")

    __table_args__ = (
        UniqueConstraint('dish_id', 'date', name='uq_dish_date'),
    )

class ShoppingCartOrm(Model):
    __tablename__ = "ShoppingCart"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    updated_at: Mapped[datetime] = mapped_column(nullable=True)

    student_id: Mapped[int] = mapped_column(ForeignKey("Students.id"), nullable=False)
    student: Mapped["StudentsOrm"] = relationship("StudentsOrm", back_populates="shopping_carts")
    cart_dishes: Mapped[list["ShoppingCartDishesOrm"]] = relationship("ShoppingCartDishesOrm", back_populates="shopping_cart")

class ShoppingCartDishesOrm(Model):
    __tablename__ = "ShoppingCartDishes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    cart_quantity: Mapped[int] = mapped_column(nullable=False)

    shoppingcart_id: Mapped[int] = mapped_column(ForeignKey("ShoppingCart.id"), nullable=False)
    schedule_dish_id: Mapped[int] = mapped_column(ForeignKey("ScheduleDishes.id"), nullable=False)

    shopping_cart: Mapped["ShoppingCartOrm"] = relationship("ShoppingCartOrm", back_populates="cart_dishes")
    schedule_dish: Mapped["ScheduleDishesOrm"] = relationship("ScheduleDishesOrm", back_populates="cart_items")

class OrderOrm(Model):
    __tablename__ = "Order"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_status: Mapped[StatusOrder] = mapped_column(Enum(StatusOrder),nullable=False)
    updated_at: Mapped[datetime] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False)

    student_id: Mapped[int] = mapped_column(ForeignKey("Students.id"), nullable=False)
    student: Mapped["StudentsOrm"] = relationship("StudentsOrm", back_populates="orders")
    order_dishes: Mapped[list["OrderDishOrm"]] = relationship("OrderDishOrm", back_populates="order")
    history: Mapped["HistoryOrm"] = relationship("HistoryOrm", back_populates="order")

class OrderDishOrm(Model):
    __tablename__ = "OrderDish"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    cart_quantity: Mapped[int] = mapped_column(nullable=False)

    order_id: Mapped[int] = mapped_column(ForeignKey("Order.id"), nullable=False)
    dish_id: Mapped[int] = mapped_column(ForeignKey("Dishes.id"), nullable=False)

    order: Mapped["OrderOrm"] = relationship("OrderOrm", back_populates="order_dishes")
    dish: Mapped["DishesOrm"] = relationship("DishesOrm", back_populates="order_items")

class HistoryOrm(Model):
    __tablename__ = "History"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    order_id: Mapped[int] = mapped_column(ForeignKey("Order.id"), nullable=False)
    student_id: Mapped[int] = mapped_column(ForeignKey("Students.id"), nullable=False)
    order: Mapped["OrderOrm"] = relationship("OrderOrm", back_populates="history")
    student: Mapped["StudentsOrm"] = relationship("StudentsOrm", back_populates="history")

class HistoryScheduleOrm(Model):
    __tablename__ = "HistorySchedule"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    total_quantity: Mapped[int] = mapped_column(nullable=False)

    dish_id: Mapped[int] = mapped_column(ForeignKey("Dishes.id"), nullable=False)

    dish: Mapped["DishesOrm"] = relationship("DishesOrm", back_populates="history_schedules")