from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from database.db import create_tables
from database.triggers import create_triggers
from routers.auth_rt import router as auth_rt
from routers.institution_rt import router as institution_rt
from routers.dishes_rt import router as dishes_rt
from routers.dish_to_basket_rt import router as dish_to_basket_rt
from routers.order_rt import router as order_rt
from routers.history_rt import router as history_rt


async def lifespan(app: FastAPI):
    await create_tables()
    print("База создана")
    await create_triggers()
    print("Триггеры созданы")
    yield
    print("Выключение")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_rt)
app.include_router(dishes_rt)
app.include_router(institution_rt)
app.include_router(dish_to_basket_rt)
app.include_router(order_rt)
app.include_router(history_rt)


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True, host="0.0.0.0", port=8000)