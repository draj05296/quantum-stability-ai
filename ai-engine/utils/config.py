"""
Application configuration.

Values can be overridden via environment variables (or a local .env file)
prefixed with AI_ENGINE_, e.g. AI_ENGINE_ALLOWED_ORIGINS=["https://example.com"].
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="AI_ENGINE_")

    APP_NAME: str = "QSFI AI Engine"
    APP_VERSION: str = "0.1.0"

    # Origins allowed to call this API. The React app runs under Vite, whose
    # default dev port is 5173.
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # Vite auto-increments the port when 5173 is already taken (5174, 5175, ...),
    # which happens often in local dev - this regex covers that whole range so
    # CORS doesn't need to be reconfigured every time.
    ALLOWED_ORIGIN_REGEX: str = r"^http://(localhost|127\.0\.0\.1):51[7-9]\d$"

    # Relative to the ai-engine/ working directory.
    UPLOAD_DIR: str = "uploads"
    PROCESSED_DIR: str = "processed"

    ALLOWED_UPLOAD_EXTENSIONS: tuple[str, ...] = (".csv",)
    MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB


settings = Settings()
