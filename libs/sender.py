import yagmail
from settings import USER_FOR_SENDER, PASSWORD_FOR_SENDER


def send_email(email: str, code: int):
    yag = yagmail.SMTP(
        user=USER_FOR_SENDER,
        password=PASSWORD_FOR_SENDER,
        host='smtp.mail.ru',
        port=465,
        smtp_ssl=True
    )

    yag.send(
        to=email,
        subject=f'Ваш код подтверждения {code}',
    )

    print("✅ Письмо отправлено!")