import hashlib
from datetime import timedelta, datetime, date
from fastapi import HTTPException
from sqlalchemy import select, update, delete, func, and_, extract
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import selectinload, joinedload
from database.db import new_session
from database.enums import StatusOrder
from database.models import StudentsOrm, TemporaryCodeOrm, DishesOrm, ShoppingCartOrm, ShoppingCartDishesOrm, OrderOrm, \
    OrderDishOrm, StudentQRCodeOrm, ScheduleDishesOrm, EducationInstitutionOrm, HistoryScheduleOrm
from schemas import DishAdd, Date, DishRequest, DishToBasket


class StudentRepository:
    @classmethod
    async def get_student(cls, student_id: int = None, student_card_id: str = None):
        async with new_session() as session:
            query = select(StudentsOrm)
            if student_id is not None:
                query = query.where(StudentsOrm.id == student_id)
            if student_card_id is not None:
                query = query.where(StudentsOrm.student_id_card == student_card_id)
            result = await session.execute(query)
            return result.scalar_one_or_none()

class TemporaryCodeRepository:
    @classmethod
    async def set_temporary_code(cls, student_card_id: str, code: str):
        async with new_session() as session:
            stmt = select(StudentsOrm).where(StudentsOrm.student_id_card == student_card_id)
            result = await session.execute(stmt)
            student = result.scalar_one_or_none()

            if not student:
                raise ValueError(f"Студент с card_id {student_card_id} не найден")

            code_hash = hashlib.sha256(code.encode()).hexdigest()

            now = datetime.now()
            expires_at = now + timedelta(minutes=10)

            temporary_code = TemporaryCodeOrm(
                code_hash=code_hash,
                attempts=0,
                created_at=now,
                expires_at=expires_at,
                used_at=None,
                student_id=student.id
            )

            session.add(temporary_code)
            await session.flush()
            await session.commit()

            return temporary_code.id


    @classmethod
    async def get_temporary_code(cls, student_id: int, temporary_code_id: int):
        async with new_session() as session:
            stmt = select(TemporaryCodeOrm).where(
                TemporaryCodeOrm.id == temporary_code_id,
                TemporaryCodeOrm.student_id == student_id
            )

            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    @classmethod
    async def increment_attempts(cls, student_id: int, temporary_code_id: int):
        async with new_session() as session:
            stmt = update(TemporaryCodeOrm).where(
                TemporaryCodeOrm.id == temporary_code_id,
                TemporaryCodeOrm.student_id == student_id
            ).values(attempts=TemporaryCodeOrm.attempts + 1)
            await session.execute(stmt)
            await session.commit()

    @classmethod
    async def mark_code_as_used(cls, student_id: int, temporary_code_id: int):
        async with new_session() as session:
            stmt = update(TemporaryCodeOrm).where(
                TemporaryCodeOrm.id == temporary_code_id,
                TemporaryCodeOrm.student_id == student_id
            ).values(used_at=datetime.now())
            await session.execute(stmt)
            await session.commit()

class QRCodeRepository:
    @classmethod
    async def get_qrcode(cls, qrcode_id: int = None, student_id: int = None):
        async with new_session() as session:
            query = select(StudentQRCodeOrm)
            if qrcode_id is not None:
                query = query.where(StudentQRCodeOrm.id == qrcode_id)
            if student_id is not None:
                query = query.where(StudentQRCodeOrm.student_id == student_id)
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @classmethod
    async def set_qrcode(cls, qrcode_url: str):
        async with new_session() as session:
            pass

class InstitutionRepository:
    @classmethod
    async def get_institutions(cls):
        async with new_session() as session:
            query = select(EducationInstitutionOrm)
            result = await session.execute(query)
            return result.scalars().all()

class DishesRepository:
    @classmethod
    async def get_dish(cls, dish_id: int = None, institution_id: int = None, dish_name: str = None):
        async with new_session() as session:
            query = select(DishesOrm)
            if dish_id is not None:
                query = query.where(DishesOrm.id == dish_id)
            if institution_id is not None:
                query = query.where(DishesOrm.institution_id == institution_id)
            if dish_name is not None:
                query = query.where(DishesOrm.dish_name == dish_name)
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @classmethod
    async def get_dishes(cls,
                         dish_id: int = None,
                         institution_id: int = None,
                         dish_name: str = None,
                         category: str = None
):
        async with new_session() as session:
            query = select(DishesOrm)
            if dish_id is not None:
                query = query.where(DishesOrm.id == dish_id)
            if institution_id is not None:
                query = query.where(DishesOrm.institution_id == institution_id)
            if dish_name is not None:
                query = query.where(DishesOrm.dish_name == dish_name)
            if category is not None:
                query = query.where(DishesOrm.category == category)
            result = await session.execute(query)
            return result.scalars().all()

    @classmethod
    async def get_dishes_on_next_day(cls, institution_id: int, next_day: date):
        async with new_session() as session:
            query = (
                select(ScheduleDishesOrm)
                .join(DishesOrm)
                .where(
                    ScheduleDishesOrm.date == next_day,
                    DishesOrm.institution_id == institution_id
                )
                .options(joinedload(ScheduleDishesOrm.dish))
            )

            result = await session.execute(query)
            items = result.scalars().all()

            formatted_result = []
            for item in items:
                formatted_result.append({
                    "id": item.id,
                    "dish_id": item.dish_id,
                    "institution_id": item.dish.institution_id,
                    "dish_name": item.dish.dish_name,
                    "category": item.dish.category,
                    "quantity": item.quantity,
                    "fixed_price": item.dish.fixed_price,
                    "img_url": item.dish.img_url,
                })
            return formatted_result

    @classmethod
    async def get_fixed_dishes_by_date(cls, institution_id: int, day: date):
        async with new_session() as session:
            query = (
                select(HistoryScheduleOrm)
                .join(DishesOrm)
                .where(
                    HistoryScheduleOrm.date == day,
                    DishesOrm.institution_id == institution_id
                )
                .options(joinedload(HistoryScheduleOrm.dish))
            )

            result = await session.execute(query)
            items = result.scalars().all()

            if not items:
                raise HTTPException(
                    status_code=404,
                    detail=f"Schedule not found for {day}"
                )

            formatted_result = []
            for item in items:
                formatted_result.append({
                    "id": item.id,
                    "dish_id": item.dish_id,
                    "institution_id": item.dish.institution_id,
                    "dish_name": item.dish.dish_name,
                    "category": item.dish.category,
                    "quantity": item.total_quantity,
                    "fixed_price": item.dish.fixed_price,
                    "img_url": item.dish.img_url,
                })
            return formatted_result


    @classmethod
    async def create_one_dish(cls, data: DishAdd):
        async with new_session() as session:
            dish_dict = data.model_dump()

            dish = DishesOrm(**dish_dict)
            session.add(dish)
            await session.flush()
            await session.commit()
            return dish.id

    @classmethod
    async def set_dishes_on_day(cls, institution_id: int, data: DishRequest, day: Date):
        async with new_session() as session:
            target_date = date(day.year, day.month, day.day)

            dish_ids = [item.dish_id for item in data.items]

            existing_dishes = await session.execute(
                select(DishesOrm.id).where(
                    DishesOrm.id.in_(dish_ids),
                    DishesOrm.institution_id == institution_id
                )
            )
            existing_dish_ids = {dish_id for (dish_id,) in existing_dishes}

            invalid_dish_ids = set(dish_ids) - existing_dish_ids
            if invalid_dish_ids:
                raise HTTPException(
                    status_code=400,
                    detail=f"Incorrect dish for institution"
                )

            for item in data.items:
                existing_schedule = await session.execute(
                    select(ScheduleDishesOrm).where(
                        ScheduleDishesOrm.dish_id == item.dish_id,
                        ScheduleDishesOrm.date == target_date
                    )
                )
                existing_schedule = existing_schedule.scalar_one_or_none()

                if existing_schedule:
                    existing_schedule.quantity = item.cart_quantity
                else:
                    schedule_dish = ScheduleDishesOrm(
                        date=target_date,
                        dish_id=item.dish_id,
                        quantity=item.cart_quantity
                    )
                    session.add(schedule_dish)

            await session.commit()

    @classmethod
    async def change_remaining_by_id(cls, dish_id: int, quantity: int):
        async with new_session() as session:
            stmt = update(DishesOrm).where(
                DishesOrm.id == dish_id
            ).values(quantity=quantity)
            await session.execute(stmt)
            await session.commit()

class StudentBasketRepository:
    @classmethod
    async def get_basket_by_student_id(cls, student_id: int):
        async with new_session() as session:
            query = select(ShoppingCartOrm).where(ShoppingCartOrm.student_id == student_id)
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @classmethod
    async def create_student_basket(cls, student_id: int):
        async with new_session() as session:
            query = ShoppingCartOrm(student_id=student_id)
            session.add(query)
            await session.flush()
            await session.commit()
            return query.id

class BasketDishesRepository:
    @classmethod
    async def get_basket(cls, basket_id: int = None, student_id: int = None):
        async with new_session() as session:
            query = select(ShoppingCartOrm)
            if basket_id is not None:
                query = query.where(ShoppingCartOrm.id == basket_id)
            if student_id is not None:
                query = query.where(ShoppingCartOrm.student_id == student_id)
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @classmethod
    async def get_dishes(cls, id_basket: int = None, shoppingcart_id: int = None, schedule_dish_id: int = None):
        async with new_session() as session:
            query = select(ShoppingCartDishesOrm).options(
                selectinload(ShoppingCartDishesOrm.schedule_dish).selectinload(ScheduleDishesOrm.dish)
            )
            if id_basket is not None:
                query = query.where(ShoppingCartDishesOrm.id == id_basket)
            if shoppingcart_id is not None:
                query = query.where(ShoppingCartDishesOrm.shoppingcart_id == shoppingcart_id)
            if schedule_dish_id is not None:
                query = query.where(ShoppingCartDishesOrm.schedule_dish_id == schedule_dish_id)

            result = await session.execute(query)
            cart_items = result.scalars().all()

            return [
                {
                    "id": item.id,
                    "dish_id": item.schedule_dish.dish_id,
                    "schedule_dish_id": item.schedule_dish_id,
                    "date": item.schedule_dish.date,
                    "quantity": item.cart_quantity,
                    "dish_name": item.schedule_dish.dish.dish_name,
                    "institution_id": item.schedule_dish.dish.institution_id,
                    "category": item.schedule_dish.dish.category,
                    "fixed_price": item.schedule_dish.dish.fixed_price,
                    "total_price": item.cart_quantity * item.schedule_dish.dish.fixed_price,
                    "img_url": item.schedule_dish.dish.img_url,
                    "schedule_quantity": item.schedule_dish.quantity,
                }
                for item in cart_items
            ]

    @classmethod
    async def add_dish_to_basket(cls, student_id: int, data: DishToBasket):
        async with new_session() as session:
            schedule_query = select(ScheduleDishesOrm).options(
                selectinload(ScheduleDishesOrm.dish)
            ).join(
                ScheduleDishesOrm.dish
            ).where(
                and_(
                    ScheduleDishesOrm.dish_id == data.dish_id,
                    ScheduleDishesOrm.date == date.today() + timedelta(days=1)
                )
            )
            schedule_result = await session.execute(schedule_query)
            schedule_dish = schedule_result.scalar_one_or_none()

            if not schedule_dish:
                raise HTTPException(status_code=404, detail="No schedule found for this dish")

            dish_price = schedule_dish.dish.fixed_price

            query = select(ShoppingCartOrm).where(ShoppingCartOrm.student_id == student_id)
            result = await session.execute(query)
            shopping_cart = result.scalar_one_or_none()

            if not shopping_cart:
                shopping_cart = ShoppingCartOrm(student_id=student_id)
                session.add(shopping_cart)
                await session.flush()

            query = select(
                func.sum(ShoppingCartDishesOrm.cart_quantity),
                func.sum(ShoppingCartDishesOrm.cart_quantity * DishesOrm.fixed_price)
            ).select_from(ShoppingCartDishesOrm).join(
                ShoppingCartDishesOrm.schedule_dish
            ).join(
                ScheduleDishesOrm.dish
            ).where(
                ShoppingCartDishesOrm.shoppingcart_id == shopping_cart.id
            )
            result = await session.execute(query)
            total_info = result.first()
            total_dishes = total_info[0] or 0
            total_amount = total_info[1] or 0

            if total_dishes + data.cart_quantity > 5:
                raise HTTPException(status_code=400, detail="Too many dishes")

            new_item_amount = dish_price * data.cart_quantity
            if total_amount + new_item_amount > 1000:
                raise HTTPException(
                    status_code=400,
                    detail=f"Total order amount exceeds 1000. Current: {total_amount}, adding: {new_item_amount}"
                )

            query = select(ShoppingCartDishesOrm).where(
                and_(
                    ShoppingCartDishesOrm.shoppingcart_id == shopping_cart.id,
                    ShoppingCartDishesOrm.schedule_dish_id == schedule_dish.id
                )
            )
            result = await session.execute(query)
            existing_item = result.scalar_one_or_none()

            if existing_item:
                new_quantity = existing_item.cart_quantity + data.cart_quantity

                if total_dishes + data.cart_quantity > 5:
                    raise HTTPException(status_code=400, detail="Too many dishes")
                if total_amount + new_item_amount > 1000:
                    raise HTTPException(status_code=400, detail="Total order amount exceeds 1000")

                existing_item.cart_quantity = new_quantity
                dish_basket_id = existing_item.id
            else:
                dish_basket = ShoppingCartDishesOrm(
                    shoppingcart_id=shopping_cart.id,
                    schedule_dish_id=schedule_dish.id,
                    cart_quantity=data.cart_quantity
                )
                session.add(dish_basket)
                dish_basket_id = dish_basket.id

            stmt = update(
                ShoppingCartOrm
            ).where(
                ShoppingCartOrm.student_id == student_id
            ).values(updated_at=datetime.now())
            await session.execute(stmt)

            await session.commit()

    @classmethod
    async def delete_dish_from_basket(cls, student_id: int, dish_id: int):
        async with new_session() as session:
            query = select(ShoppingCartOrm).where(ShoppingCartOrm.student_id == student_id)
            result = await session.execute(query)
            shopping_cart = result.scalar_one_or_none()

            if not shopping_cart:
                raise HTTPException(status_code=404, detail="Basket not found")

            query = select(ShoppingCartDishesOrm).options(
                selectinload(ShoppingCartDishesOrm.schedule_dish)
            ).where(
                and_(
                    ShoppingCartDishesOrm.shoppingcart_id == shopping_cart.id,
                    ShoppingCartDishesOrm.schedule_dish.has(ScheduleDishesOrm.dish_id == dish_id)
                )
            )
            result = await session.execute(query)
            cart_item = result.scalar_one_or_none()

            if not cart_item:
                raise HTTPException(status_code=404, detail="Dish not found in basket")

            stmt = delete(
                ShoppingCartDishesOrm
            ).where(
                and_(
                    ShoppingCartDishesOrm.shoppingcart_id == shopping_cart.id,
                    ShoppingCartDishesOrm.schedule_dish.has(ScheduleDishesOrm.dish_id == dish_id)
                )
            )

            result = await session.execute(stmt)

            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Dish not found in basket")

            # Обновляем время изменения корзины
            stmt = update(
                ShoppingCartOrm
            ).where(
                ShoppingCartOrm.student_id == student_id
            ).values(updated_at=datetime.now())

            await session.execute(stmt)
            await session.commit()

    @classmethod
    async def change_quantity(cls, student_id: int, data: DishToBasket):
        async with new_session() as session:
            schedule_query = select(ScheduleDishesOrm).options(
                selectinload(ScheduleDishesOrm.dish)
            ).join(
                ScheduleDishesOrm.dish
            ).where(
                and_(
                    ScheduleDishesOrm.dish_id == data.dish_id,
                    ScheduleDishesOrm.date == date.today() + timedelta(days=1)
                )
            )
            schedule_result = await session.execute(schedule_query)
            schedule_dish = schedule_result.scalar_one_or_none()

            if not schedule_dish:
                raise HTTPException(status_code=404, detail="No schedule found for this dish")

            dish_price = schedule_dish.dish.fixed_price

            query = select(ShoppingCartOrm).where(ShoppingCartOrm.student_id == student_id)
            result = await session.execute(query)
            shopping_cart = result.scalar_one_or_none()

            if not shopping_cart:
                raise HTTPException(status_code=404, detail="Cart not found")

            query = select(ShoppingCartDishesOrm).where(
                and_(
                    ShoppingCartDishesOrm.shoppingcart_id == shopping_cart.id,
                    ShoppingCartDishesOrm.schedule_dish.has(ScheduleDishesOrm.dish_id == data.dish_id)
                )
            )
            result = await session.execute(query)
            cart_item = result.scalar_one_or_none()

            if not cart_item:
                raise HTTPException(status_code=404, detail="Dish not found in cart")

            query = select(
                func.sum(ShoppingCartDishesOrm.cart_quantity),
                func.sum(ShoppingCartDishesOrm.cart_quantity * DishesOrm.fixed_price)
            ).select_from(ShoppingCartDishesOrm).join(
                ShoppingCartDishesOrm.schedule_dish
            ).join(
                ScheduleDishesOrm.dish
            ).where(
                and_(
                    ShoppingCartDishesOrm.shoppingcart_id == shopping_cart.id,
                    ShoppingCartDishesOrm.schedule_dish.has(ScheduleDishesOrm.dish_id != data.dish_id)
                )
            )
            result = await session.execute(query)
            other_dishes_info = result.first()
            other_dishes_total = other_dishes_info[0] or 0
            other_dishes_amount = other_dishes_info[1] or 0

            if other_dishes_total + data.cart_quantity > 5:
                raise HTTPException(status_code=400, detail="Too many dishes")

            new_item_amount = dish_price * data.cart_quantity
            if other_dishes_amount + new_item_amount > 1000:
                raise HTTPException(
                    status_code=400,
                    detail=f"Total order amount exceeds 1000. Current: {other_dishes_amount}, new item: {new_item_amount}"
                )

            if data.cart_quantity == 0:
                stmt = delete(
                    ShoppingCartDishesOrm
                ).where(
                    and_(
                        ShoppingCartDishesOrm.shoppingcart_id == shopping_cart.id,
                        ShoppingCartDishesOrm.schedule_dish.has(ScheduleDishesOrm.dish_id == data.dish_id)
                    )
                )
                await session.execute(stmt)
            else:
                stmt = update(
                    ShoppingCartDishesOrm
                ).where(
                    and_(
                        ShoppingCartDishesOrm.shoppingcart_id == shopping_cart.id,
                        ShoppingCartDishesOrm.schedule_dish.has(ScheduleDishesOrm.dish_id == data.dish_id)
                    )
                ).values(cart_quantity=data.cart_quantity)

                await session.execute(stmt)

            stmt = update(
                ShoppingCartOrm
            ).where(
                ShoppingCartOrm.student_id == student_id
            ).values(updated_at=datetime.now())

            await session.execute(stmt)
            await session.commit()

    @classmethod
    async def clear_all_baskets(cls):
        async with new_session() as session:
            query = delete(ShoppingCartDishesOrm)
            await session.execute(query)
            await session.commit()

class OrdersRepository:
    @classmethod
    async def create_order(cls, student_id: int):
        async with new_session() as session:
            query = select(OrderOrm).where(
                OrderOrm.student_id == student_id
            ).where(
                OrderOrm.order_status == StatusOrder.IN_PROGRESS
            )
            result = await session.execute(query)
            order = result.scalar_one_or_none()
            if order:
                raise HTTPException(status_code=400, detail="Order already exists")

            cart_query = select(ShoppingCartOrm).where(
                ShoppingCartOrm.student_id == student_id
            )
            cart_result = await session.execute(cart_query)
            shopping_cart = cart_result.scalar_one_or_none()

            if not shopping_cart:
                raise HTTPException(status_code=404, detail="Shopping cart not found")

            stmt = select(ShoppingCartDishesOrm).options(
                selectinload(ShoppingCartDishesOrm.schedule_dish)
            ).where(
                ShoppingCartDishesOrm.shoppingcart_id == shopping_cart.id
            )
            result = await session.execute(stmt)
            cart_items = result.scalars().all()

            if not cart_items:
                raise HTTPException(status_code=400, detail="Cart is empty")

            order_dish_data = []
            schedule_updates = {}
            cart_updates = {}
            items_to_remove = []

            for cart_item in cart_items:
                if cart_item.schedule_dish.date != date.today() + timedelta(days=1):
                    items_to_remove.append(cart_item.id)
                    continue

                available_quantity = cart_item.schedule_dish.quantity
                requested_quantity = cart_item.cart_quantity

                if available_quantity <= 0:
                    items_to_remove.append(cart_item.id)
                    continue

                if requested_quantity > available_quantity:
                    cart_updates[cart_item.id] = available_quantity
                    continue

                order_dish_data.append({
                    'cart_quantity': requested_quantity,
                    'dish_id': cart_item.schedule_dish.dish_id,
                    'order_id': None,
                })

                schedule_dish_id = cart_item.schedule_dish.id
                schedule_updates[schedule_dish_id] = schedule_updates.get(schedule_dish_id, 0) + requested_quantity

            if cart_updates or items_to_remove:
                for cart_item_id, new_quantity in cart_updates.items():
                    stmt = update(ShoppingCartDishesOrm).where(
                        ShoppingCartDishesOrm.id == cart_item_id
                    ).values(cart_quantity=new_quantity)
                    await session.execute(stmt)

                if items_to_remove:
                    stmt = delete(ShoppingCartDishesOrm).where(
                        ShoppingCartDishesOrm.id.in_(items_to_remove)
                    )
                    await session.execute(stmt)

                update_cart_stmt = update(ShoppingCartOrm).where(
                    ShoppingCartOrm.id == shopping_cart.id
                ).values(updated_at=datetime.now())
                await session.execute(update_cart_stmt)

                await session.commit()

                error_message = "Cart updated due to insufficient availability: "
                if cart_updates:
                    error_message += f"quantities adjusted for {len(cart_updates)} items. "
                if items_to_remove:
                    error_message += f"removed {len(items_to_remove)} unavailable items."

                raise HTTPException(
                    status_code=400,
                    detail=error_message.strip()
                )

            if not order_dish_data:
                raise HTTPException(
                    status_code=400,
                    detail="No available dishes found in cart for tomorrow's order"
                )

            order = OrderOrm(
                student_id=student_id,
                order_status=StatusOrder.IN_PROGRESS,
                created_at=datetime.now(),
            )
            session.add(order)
            await session.flush()

            for dish_data in order_dish_data:
                dish_data['order_id'] = order.id

            stmt = insert(OrderDishOrm).values(order_dish_data)
            await session.execute(stmt)

            for schedule_dish_id, quantity_to_subtract in schedule_updates.items():
                stmt = update(ScheduleDishesOrm).where(
                    and_(
                        ScheduleDishesOrm.id == schedule_dish_id,
                        ScheduleDishesOrm.quantity >= quantity_to_subtract
                    )
                ).values(quantity=ScheduleDishesOrm.quantity - quantity_to_subtract)

                result = await session.execute(stmt)

                if result.rowcount == 0:
                    await session.rollback()
                    raise HTTPException(
                        status_code=400,
                        detail=f"Not enough dishes available for schedule dish {schedule_dish_id}"
                    )

            delete_stmt = delete(ShoppingCartDishesOrm).where(
                ShoppingCartDishesOrm.shoppingcart_id == shopping_cart.id
            )
            await session.execute(delete_stmt)

            update_cart_stmt = update(ShoppingCartOrm).where(
                ShoppingCartOrm.id == shopping_cart.id
            ).values(updated_at=datetime.now())
            await session.execute(update_cart_stmt)

            await session.commit()

            return {
                "order_id": order.id,
                "added_items": len(order_dish_data),
            }

    @classmethod
    async def get_dishes(cls, order_id: int = None, student_id: int = None, dish_id: int = None):
        async with new_session() as session:
            if student_id is not None:
                student = await session.get(StudentsOrm, student_id)
                if not student:
                    raise HTTPException(status_code=404, detail="Student not found")

            query = select(OrderDishOrm).options(
                selectinload(OrderDishOrm.dish),
                selectinload(OrderDishOrm.order)
            )

            query = query.join(OrderDishOrm.order).where(OrderOrm.order_status == StatusOrder.IN_PROGRESS)

            if order_id is not None:
                query = query.where(OrderDishOrm.order_id == order_id)
            if student_id is not None:
                query = query.where(OrderOrm.student_id == student_id)
            if dish_id is not None:
                query = query.where(OrderDishOrm.dish_id == dish_id)

            result = await session.execute(query)
            order_items = result.scalars().all()

            return [
                {
                    "id": item.id,
                    "dish_id": item.dish_id,
                    "order_id": item.order_id,
                    "quantity": item.cart_quantity,
                    "dish_name": item.dish.dish_name,
                    "institution_id": item.dish.institution_id,
                    "category": item.dish.category,
                    "fixed_price": item.dish.fixed_price,
                    "total_price": item.cart_quantity * item.dish.fixed_price,
                    "img_url": item.dish.img_url,
                    "created_at": item.order.created_at,
                }
                for item in order_items
            ]

    @classmethod
    async def complete_order(cls, student_id: int):
        async with (new_session() as session):
            if student_id is not None:
                student = await session.get(StudentsOrm, student_id)
                if not student:
                    raise HTTPException(status_code=404, detail="Student not found")

            query = update(
                OrderOrm
            ).where(
                OrderOrm.student_id == student_id
            ).where(
                OrderOrm.order_status == StatusOrder.IN_PROGRESS
            ).values(
                order_status=StatusOrder.COMPLETED,
                updated_at=datetime.now(),
            )
            await session.execute(query)
            await session.commit()

    @classmethod
    async def undo_order(cls, student_id: int):
        async with new_session() as session:
            # 1. Получаем заказ и его блюда
            query = (
                select(OrderOrm, OrderDishOrm)
                .join(OrderDishOrm, OrderOrm.id == OrderDishOrm.order_id)
                .where(
                    OrderOrm.student_id == student_id,
                    OrderOrm.order_status == StatusOrder.IN_PROGRESS
                )
            )
            result = await session.execute(query)
            order_data = result.all()

            if not order_data:
                raise ValueError("No order in progress found for this student")

            order = order_data[0].OrderOrm
            today = date.today() + timedelta(days=1)

            # 2. Подготовка данных для обновления ScheduleDishesOrm
            schedule_updates = []
            for row in order_data:
                order_dish = row.OrderDishOrm
                schedule_updates.append({
                    'dish_id': order_dish.dish_id,
                    'date': today,
                    'quantity': order_dish.cart_quantity
                })

            # 3. Пакетное обновление ScheduleDishesOrm
            for update_data in schedule_updates:
                stmt = insert(ScheduleDishesOrm).values(**update_data)

                # Для PostgreSQL
                stmt = stmt.on_conflict_do_update(
                    constraint='uq_dish_date',
                    set_=dict(quantity=ScheduleDishesOrm.quantity + update_data['quantity'])
                )

                await session.execute(stmt)

            # 4. Обновляем статус заказа
            query_update = (
                update(OrderOrm)
                .where(OrderOrm.id == order.id)
                .values(
                    order_status=StatusOrder.CANCELLED,
                    updated_at=datetime.now()
                )
            )
            await session.execute(query_update)
            await session.commit()

    @classmethod
    async def get_all_ordered_dishes(cls, institution_id: int, day: date):
        async with new_session() as session:
            schedule_quantity_subquery = (
                select(func.coalesce(func.sum(ScheduleDishesOrm.quantity), 0))
                .where(ScheduleDishesOrm.dish_id == HistoryScheduleOrm.dish_id)
                .where(ScheduleDishesOrm.date == day)
                .scalar_subquery()
            )

            query = (
                select(
                    HistoryScheduleOrm,
                    (HistoryScheduleOrm.total_quantity - schedule_quantity_subquery).label("available_quantity")
                )
                .join(DishesOrm)
                .where(
                    HistoryScheduleOrm.date == day,
                    DishesOrm.institution_id == institution_id
                )
                .options(joinedload(HistoryScheduleOrm.dish))
            )

            result = await session.execute(query)
            items = result.all()

            if not items:
                raise HTTPException(
                    status_code=404,
                    detail=f"Schedule not found"
                )

            formatted_result = []
            for item in items:
                history_schedule = item[0]
                available_quantity = item[1]

                final_quantity = max(available_quantity, 0)

                formatted_result.append({
                    "id": history_schedule.id,
                    "dish_id": history_schedule.dish_id,
                    "institution_id": history_schedule.dish.institution_id,
                    "dish_name": history_schedule.dish.dish_name,
                    "category": history_schedule.dish.category,
                    "total_quantity": history_schedule.total_quantity,
                    "remains_quantity": history_schedule.total_quantity - final_quantity,
                    "ordered_quantity": final_quantity,
                    "fixed_price": history_schedule.dish.fixed_price,
                    "date": day,
                    "img_url": history_schedule.dish.img_url,
                })
            return formatted_result

class HistoryRepository:
    @classmethod
    async def get_history_for_month(cls, student_id: int, month: int = None, year: int = None):
        async with new_session() as session:
            if month is None or year is None:
                current_date = datetime.now()
                year = current_date.year
                month = current_date.month

            query = select(OrderOrm).where(
                OrderOrm.student_id == student_id
            ).where(
                and_(
                    extract('year', OrderOrm.updated_at) == year,
                    extract('month', OrderOrm.updated_at) == month,
                )
            ).options(
            selectinload(OrderOrm.order_dishes).options(
                selectinload(OrderDishOrm.dish)
            ),
        )
            result = await session.execute(query)
            order_items = result.scalars().all()

        return [
            {
                "order_id": order.id,
                "dishes": [
                    {
                        "dish_id": order_dish.dish.id,
                        "quantity": order_dish.cart_quantity,
                        "dish_name": order_dish.dish.dish_name,
                        "fixed_price": order_dish.dish.fixed_price,
                        "total_price": order_dish.cart_quantity * order_dish.dish.fixed_price,
                        "date": order.updated_at.date(),
                    }
                    for order_dish in order.order_dishes
                ]
            }
            for order in order_items
        ]