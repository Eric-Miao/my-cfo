import os
from dataclasses import dataclass, field


def _csv_env(name: str, default: str) -> list[str]:
    value = os.getenv(name, default)
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    app_name: str = "my-cfo"
    environment: str = "development"
    database_url: str = "sqlite:///./my-cfo.db"
    admin_password_hash: str = "dev-placeholder"
    session_secret: str = "dev-session-secret"
    cors_origins: list[str] = field(
        default_factory=lambda: ["http://localhost:5173"]
    )
    allow_public_docs: bool = True
    deployment_network: str = "lan"
    cookie_secure: bool = False
    fx_provider: str = "frankfurter"
    frankfurter_base_url: str = "https://api.frankfurter.dev/v2"
    official_base_currency: str = "CNY"

    @classmethod
    def from_env(cls) -> "Settings":
        environment = os.getenv("APP_ENV", "development")
        session_secret = os.getenv("SESSION_SECRET", "dev-session-secret")
        admin_password_hash = os.getenv("ADMIN_PASSWORD_HASH", "dev-placeholder")

        settings = cls(
            app_name=os.getenv("APP_NAME", "my-cfo"),
            environment=environment,
            database_url=os.getenv("DATABASE_URL", "sqlite:///./my-cfo.db"),
            admin_password_hash=admin_password_hash,
            session_secret=session_secret,
            cors_origins=_csv_env("CORS_ORIGINS", "http://localhost:5173"),
            allow_public_docs=os.getenv("ALLOW_PUBLIC_DOCS", "true").lower()
            in {"1", "true", "yes"},
            deployment_network=os.getenv("DEPLOYMENT_NETWORK", "lan"),
            cookie_secure=os.getenv("COOKIE_SECURE", "false").lower()
            in {"1", "true", "yes"},
            fx_provider=os.getenv("FX_PROVIDER", "frankfurter"),
            frankfurter_base_url=os.getenv(
                "FRANKFURTER_BASE_URL", "https://api.frankfurter.dev/v2"
            ),
            official_base_currency=os.getenv("OFFICIAL_BASE_CURRENCY", "CNY"),
        )
        settings.validate()
        return settings

    def validate(self) -> None:
        if self.environment == "production":
            if self.session_secret in {"", "change-me", "dev-session-secret"}:
                raise ValueError("SESSION_SECRET must be set for production")
            if self.admin_password_hash in {"", "change-me", "dev-placeholder"}:
                raise ValueError("ADMIN_PASSWORD_HASH must be set for production")
            if self.deployment_network != "lan" and not self.cookie_secure:
                raise ValueError("COOKIE_SECURE must be true outside LAN production")


settings = Settings.from_env()
