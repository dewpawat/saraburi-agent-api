from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# DB_TYPE values accepted in .env -> canonical name
_DB_TYPE_ALIASES = {
    "mysql": "mysql",
    "mariadb": "mysql",
    "postgresql": "postgresql",
    "postgres": "postgresql",
    "pgsql": "postgresql",
}
_DEFAULT_DB_PORT = {"mysql": 3306, "postgresql": 5432}


class Settings(BaseSettings):
    # extra="ignore": unknown keys in .env (e.g. TZ) must never stop the agent from starting
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str
    APP_ENV: str
    APP_PORT: int
    APP_VERSION: str = "1.3.1"

    API_KEY: str
    # Allowed caller IPs. API_ALLOWED_IPS takes a comma-separated list (IPs or CIDR, e.g.
    # "203.157.115.86,203.157.115.88,127.0.0.1"). The older API_ALLOWED_IP1/IP2 still work
    # and are merged with it, so existing .env files need no change.
    API_ALLOWED_IPS: str = ""
    API_ALLOWED_IP1: str = ""
    API_ALLOWED_IP2: str = ""
    # X-Forwarded-For is only trusted when the direct peer is one of these (a reverse proxy
    # in front of the agent). Default: loopback + private LAN ranges.
    TRUSTED_PROXIES: str = "127.0.0.1,::1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16"

    HOSP_CODE: str
    HOSP_CODE9: str
    HOSP_NAME: str

    # Database of the hospital HIS: "mysql" (default, also MariaDB) or "postgresql".
    # .env files from before v1.3.0 have no DB_TYPE and keep using MySQL.
    DB_TYPE: str = "mysql"
    DB_HOST: str
    # Optional since v1.3.0: defaults to 3306 (mysql) / 5432 (postgresql)
    DB_PORT: Optional[int] = None
    DB_USER: str
    DB_PASS: str
    DB_NAME: str

    # Connection pool, per Uvicorn worker (docker-compose runs 2 workers).
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 5
    DB_POOL_RECYCLE: int = 1800

    @field_validator("DB_TYPE", mode="before")
    @classmethod
    def _normalize_db_type(cls, value):
        raw = "" if value is None else str(value).split("#", 1)[0].strip().lower()
        if raw == "":
            return "mysql"
        if raw not in _DB_TYPE_ALIASES:
            raise ValueError(f"DB_TYPE '{value}' is not supported; use 'mysql' or 'postgresql'")
        return _DB_TYPE_ALIASES[raw]

    @field_validator("DB_PORT", mode="before")
    @classmethod
    def _blank_port_is_default(cls, value):
        if value is None or (isinstance(value, str) and value.split("#", 1)[0].strip() == ""):
            return None
        return value

    @property
    def is_postgresql(self) -> bool:
        return self.DB_TYPE == "postgresql"

    @property
    def db_port(self) -> int:
        return self.DB_PORT if self.DB_PORT is not None else _DEFAULT_DB_PORT[self.DB_TYPE]

    @property
    def docs_enabled(self) -> bool:
        return self.APP_ENV.strip().lower() != "production"


settings = Settings()
