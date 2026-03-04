"""Application settings loaded from environment variables."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PINPAL_")

    # --- Postgres ---
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "pinpal"
    postgres_password: str = "pinpal"
    postgres_db: str = "pinpal"

    # --- MongoDB ---
    mongo_host: str = "localhost"
    mongo_port: int = 27017
    mongo_user: str = "pinpal"
    mongo_password: str = "pinpal"
    mongo_db: str = "pinpal"

    # --- App ---
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")  # "json" or "console"

    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def postgres_dsn_sync(self) -> str:
        """Sync DSN for Alembic migrations."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def mongo_dsn(self) -> str:
        return (
            f"mongodb://{self.mongo_user}:{self.mongo_password}"
            f"@{self.mongo_host}:{self.mongo_port}"
        )
