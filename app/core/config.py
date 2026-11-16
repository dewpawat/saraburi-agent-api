from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # extra="ignore": unknown keys in .env (e.g. TZ) must never stop the agent from starting
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str
    APP_ENV: str
    APP_PORT: int
    APP_VERSION: str = "1.2.0"

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

    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASS: str
    DB_NAME: str

    # Connection pool, per Uvicorn worker (docker-compose runs 2 workers).
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 5
    DB_POOL_RECYCLE: int = 1800

    @property
    def docs_enabled(self) -> bool:
        return self.APP_ENV.strip().lower() != "production"


settings = Settings()
