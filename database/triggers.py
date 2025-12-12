from sqlalchemy import text
from database.db import new_session


async def create_triggers():
    async with new_session() as session:
        try:
            commands_trigger_1 = [
                """
                CREATE OR REPLACE FUNCTION move_to_history_schedule()
                RETURNS TRIGGER AS $$
                BEGIN
                    INSERT INTO "HistorySchedule" (total_quantity, date, dish_id)
                    VALUES (NEW.quantity, NEW.date, NEW.dish_id);
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
                """,

                'DROP TRIGGER IF EXISTS schedule_to_history_trigger ON "ScheduleDishes";',

                """
                CREATE TRIGGER schedule_to_history_trigger
                    AFTER INSERT ON "ScheduleDishes"
                    FOR EACH ROW
                    EXECUTE FUNCTION move_to_history_schedule();
                """
            ]

            for command in commands_trigger_1:
                await session.execute(text(command))
                await session.commit()

        except Exception as e:
            await session.rollback()
            print(f"Ошибка при создании триггеров: {e}")
            raise