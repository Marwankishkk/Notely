from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    RESEND_API_KEY: str
    OPENAI_API_KEY: str
    ENVIRONMENT: str = "development"
    FRONTEND_URL: str = "http://localhost:3000"
    # Comma-separated list. Falls back to FRONTEND_URL if empty.
    CORS_ORIGINS: str = ""
    REDIS_URL: str = "redis://localhost:6379/0"
    # Cookie auth: use "none" when frontend and API are on different sites (needs HTTPS).
    # Use "lax" when same-site (e.g. Next.js proxy to the API).
    COOKIE_SAMESITE: str = "lax"
    COOKIE_SECURE: bool | None = None
    COOKIE_DOMAIN: str | None = None

    class Config:
        env_file = ".env"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    @property
    def cookie_secure(self) -> bool:
        if self.COOKIE_SECURE is not None:
            return self.COOKIE_SECURE
        return self.is_production

    @property
    def cors_origins(self) -> list[str]:
        if self.CORS_ORIGINS.strip():
            return [
                origin.strip().rstrip("/")
                for origin in self.CORS_ORIGINS.split(",")
                if origin.strip()
            ]
        return [self.FRONTEND_URL.rstrip("/")]


settings = Settings()
