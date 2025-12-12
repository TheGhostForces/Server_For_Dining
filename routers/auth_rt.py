from datetime import datetime
from fastapi import APIRouter, HTTPException, Response
from Server_For_Dining.database.repository import StudentRepository, TemporaryCodeRepository, StudentBasketRepository
from Server_For_Dining.libs.generator import generate_numeric_code, verify_password
from Server_For_Dining.libs.sender import send_email
from Server_For_Dining.schemas import Token, UniversalStudent
from Server_For_Dining.security.auth import create_access_token


router = APIRouter(
    prefix="/auth",
    tags=["Эндпоинты для авторизации/выхода из аккаунта"],
)

@router.post("/generate", response_model=UniversalStudent)
async def generate_sms_code(student_card_id: str):
    existing_student = await StudentRepository.get_student(student_card_id=student_card_id)
    if not existing_student:
        raise HTTPException(status_code=400, detail="There is no such id")
    if not existing_student.email:
        raise HTTPException(status_code=400, detail="There is no such email")
    code = generate_numeric_code()
    send_email(existing_student.email, code)
    tmp_id = await TemporaryCodeRepository.set_temporary_code(student_card_id, code)
    return {"Ok": True, "student_id": existing_student.id, "tmp_code_id": tmp_id}

@router.post("/confirm", response_model=Token)
async def confirm(student_id: int, temporary_code_id: int, code: str, response: Response = None):
    existing_student = await StudentRepository.get_student(student_id=student_id)
    if not existing_student:
        raise HTTPException(status_code=400, detail="There is no such id")

    tmp_code = await TemporaryCodeRepository.get_temporary_code(student_id, temporary_code_id)
    if not tmp_code:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if tmp_code.expires_at < datetime.now():
        raise HTTPException(status_code=401, detail="Code expired")

    if tmp_code.used_at is not None:
        raise HTTPException(status_code=400, detail="Code already used")

    if tmp_code.student_id != student_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if tmp_code.id != temporary_code_id:
        raise HTTPException(status_code=401, detail="Incorrect code")

    if not verify_password(code, tmp_code.code_hash):
        await TemporaryCodeRepository.increment_attempts(student_id, temporary_code_id)
        raise HTTPException(status_code=401, detail="Incorrect code")

    access_token = create_access_token(
        data={"sub": str(student_id),
              "role": str(existing_student.role),
              },
    )
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        secure=False,
        samesite="lax"
    )

    await TemporaryCodeRepository.mark_code_as_used(student_id, temporary_code_id)
    basket = await StudentBasketRepository.get_basket_by_student_id(student_id)
    if basket is None:
        await StudentBasketRepository.create_student_basket(student_id)

    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Successfully logged out"}
