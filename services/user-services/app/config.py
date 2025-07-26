import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "User Service"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "BreakingTheMonolithWithIEEECSCUET")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    ALGORITHM: str = "HS256"
    DATABASE_URL: str = os.getenv("DATABASE_URL")

settings = Settings()
