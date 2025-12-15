from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str
    APP_ENV: str
    APP_PORT: int

    API_KEY: str
    API_ALLOWED_IP1: str
    API_ALLOWED_IP2: str

    HOSP_CODE: str
    HOSP_CODE9: str
    HOSP_NAME: str

    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASS: str
    DB_NAME: str

    class Config:
        env_file = ".env"

settings = Settings()
