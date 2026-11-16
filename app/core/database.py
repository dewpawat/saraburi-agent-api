import logging

from sqlalchemy import event
from sqlalchemy.exc import DisconnectionError
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine.url import URL
from app.core.config import settings

logger = logging.getLogger("saraburi_agent.database")

if settings.is_postgresql:
    DATABASE_URL = URL.create(
        drivername="postgresql+asyncpg",
        username=settings.DB_USER,
        password=settings.DB_PASS,
        host=settings.DB_HOST,
        port=settings.db_port,
        database=settings.DB_NAME,
    )
    CONNECT_ARGS = {
        # asyncpg waits 60 s by default; use the same 10 s limit as the MySQL driver
        "timeout": 10,
        "server_settings": {
            "application_name": "saraburi-agent-api",
            # The agent only reads: make every transaction read-only on the server side,
            # so even a DB user with write rights cannot change hospital data through it.
            "default_transaction_read_only": "on",
        }
    }
else:
    # MySQL / MariaDB: same settings as v1.2.0
    DATABASE_URL = URL.create(
        drivername="mysql+aiomysql",
        username=settings.DB_USER,
        password=settings.DB_PASS,
        host=settings.DB_HOST,
        port=settings.db_port,
        database=settings.DB_NAME,
        query={"charset": "utf8mb4"}
    )
    CONNECT_ARGS = {}

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args=CONNECT_ARGS,
    # Health check is done by the "checkout" listener below instead of pool_pre_ping.
    # pool_pre_ping only reconnects on errors the driver reports as a disconnect; under
    # uvloop a socket the server already closed raises a plain RuntimeError
    # ("unable to perform operation on <TCPTransport closed=True ...>; the handler is closed"),
    # which pool_pre_ping lets through and the request fails.
    pool_pre_ping=False,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
)


@event.listens_for(engine.sync_engine, "checkout")
def _ping_on_checkout(dbapi_connection, connection_record, connection_proxy):
    """
    Ping every connection taken from the pool. Any failure (2013 Lost connection,
    TCPTransport closed, ...) raises DisconnectionError, which makes SQLAlchemy drop the
    dead connection and open a new one (up to 3 attempts) before the query runs.
    """
    try:
        engine.dialect.do_ping(dbapi_connection)
    except Exception as exc:
        raise DisconnectionError(f"Ping failed: {type(exc).__name__}: {exc}") from exc


@event.listens_for(engine.sync_engine, "invalidate")
def _log_invalidate(dbapi_connection, connection_record, exception):
    # One line per dropped connection, so `docker compose logs` shows how often the
    # hospital network / MySQL server cuts idle connections.
    reason = f"{type(exception).__name__}: {exception}" if exception else "no exception"
    logger.warning(f"DB connection dropped and will be reopened ({reason})")


async_session_factory = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db():
    async with async_session_factory() as session:
        yield session
