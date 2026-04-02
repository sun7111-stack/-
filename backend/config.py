"""应用配置"""
from pathlib import Path

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # 数据库
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "carbon_platform"

    # JWT
    JWT_SECRET_KEY: str = "carbon-platform-super-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 10080  # 7天

    # 应用
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    APP_DEBUG: bool = True

    # CORS
    CORS_ORIGINS: str = "http://localhost,http://127.0.0.1,http://localhost:5500,http://127.0.0.1:5500"

    # AI Model
    DASHSCOPE_API_KEY: str = ""

    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = str(Path(__file__).resolve().with_name(".env"))
        env_file_encoding = "utf-8"


settings = Settings()
