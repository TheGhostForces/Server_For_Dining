import os
from dotenv import load_dotenv


load_dotenv()


engine = os.getenv("ENGINE")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
USER_FOR_SENDER = os.getenv("USER_FOR_SENDER")
PASSWORD_FOR_SENDER = os.getenv("PASSWORD_FOR_SENDER")