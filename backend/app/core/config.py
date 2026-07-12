import os
from dataclasses import dataclass, field


def _csv_env(name: str, default: str) -> list[str]:
    value = os.getenv(name, default)
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "my-cfo")
    environment: str = os.getenv("APP_ENV", "development")
    cors_origins: list[str] = field(
        default_factory=lambda: _csv_env("CORS_ORIGINS", "http://localhost:5173")
    )


settings = Settings()
