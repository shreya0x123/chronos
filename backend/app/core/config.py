from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Chronos"
    DATABASE_URL: str = "sqlite:///chronos.db"

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()
