from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # 使用 SQLite 作为开发数据库
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./fishlog.db")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    OPEN_METEO_API_URL: str = "https://api.open-meteo.com/v1"
    AMAP_WEB_SERVICE_KEY: Optional[str] = os.getenv("AMAP_WEB_SERVICE_KEY")
    WECHAT_APP_ID: Optional[str] = os.getenv("WECHAT_APP_ID")
    WECHAT_APP_SECRET: Optional[str] = os.getenv("WECHAT_APP_SECRET")
    WECHAT_REDIRECT_URI: Optional[str] = os.getenv("WECHAT_REDIRECT_URI")

    class Config:
        env_file = ".env"

settings = Settings()

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

async def get_db():
    async with async_session() as session:
        yield session
