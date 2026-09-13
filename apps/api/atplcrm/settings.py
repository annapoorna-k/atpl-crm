from functools import lru_cache
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=True)
    app_mode: str = Field("connected", alias="APP_MODE")
    instance_type: str = Field("INTERNATIONAL", alias="INSTANCE_TYPE")
    tenant_key: str = Field("atplcrm-local", alias="TENANT_KEY")
    app_secret: str = Field(alias="APP_SECRET")
    postgres_db: str = Field("atplcrm", alias="POSTGRES_DB")
    postgres_user: str = Field("atplcrm", alias="POSTGRES_USER")
    postgres_password: str = Field(alias="POSTGRES_PASSWORD")
    postgres_host: str = Field("db", alias="POSTGRES_HOST")
    database_url_override: str | None = Field(None, alias="DATABASE_URL")
    redis_url: str = Field("redis://redis:6379/0", alias="REDIS_URL")
    demo_password: str | None = Field(None, alias="DEMO_PASSWORD")
    fx_rates_url: str | None = Field(None, alias="FX_RATES_URL")
    fx_rate_source: str = Field("Configured published source", alias="FX_RATE_SOURCE")
    session_hours: int = 12

    @field_validator("instance_type")
    @classmethod
    def valid_instance(cls, value: str) -> str:
        if value not in {"US", "INTERNATIONAL"}:
            raise ValueError("INSTANCE_TYPE must be US or INTERNATIONAL")
        return value

    @property
    def database_url(self) -> str:
        return self.database_url_override or f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:5432/{self.postgres_db}"

    @property
    def session_cookie(self) -> str:
        return self.tenant_key.replace("-", "_") + "_session"

    @property
    def csrf_cookie(self) -> str:
        return self.tenant_key.replace("-", "_") + "_csrf"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
