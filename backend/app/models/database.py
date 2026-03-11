from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool
import os

from ..config import settings

# 数据库路径
DB_PATH = settings.database.sqlite_path
DB_DIR = os.path.dirname(DB_PATH) or "data"

# 确保数据库目录存在
os.makedirs(DB_DIR, exist_ok=True)

# SQLite数据库URL
DATABASE_URL = f"sqlite:///{DB_PATH}"
ASYNC_DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"

# 创建同步引擎（用于Alembic迁移）
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=settings.database.sqlite_echo,
    poolclass=StaticPool,
)

# 创建异步引擎
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=settings.database.sqlite_echo,
)

# 创建Session工厂
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# 创建异步Session工厂
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base类
Base = declarative_base()


def get_db():
    """获取数据库Session（同步）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db():
    """获取数据库Session（异步）"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def init_db():
    """初始化数据库表"""
    Base.metadata.create_all(bind=engine)
