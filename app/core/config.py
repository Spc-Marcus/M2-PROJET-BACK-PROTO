from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Duobingo API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "sqlite:///./duobingo.db"
    
    # JWT
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Classroom
    CLASSROOM_CODE_LENGTH: int = 6
    
    # Leitner
    LEITNER_BOX_WEIGHTS: list = [50, 25, 15, 7, 3]  # Box 1-5 selection weights
    LEITNER_VALID_QUESTION_COUNTS: list = [5, 10, 15, 20]
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
