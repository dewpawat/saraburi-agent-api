from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine.url import URL
from app.core.config import settings

DATABASE_URL = URL.create(
    drivername="mysql+aiomysql",
    username=settings.DB_USER,
    password=settings.DB_PASS,
    host=settings.DB_HOST,
    port=settings.DB_PORT,
    database=settings.DB_NAME,
    query={"charset": "utf8mb4"}
)

engine = create_async_engine(DATABASE_URL, echo=False)

async_session_factory = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db():
    async with async_session_factory() as session:
        yield session
