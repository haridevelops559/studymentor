"""
Application configuration.

Reads from environment variables (or a local .env file). Falls back to an
in-memory data store by default so the API is runnable out of the box with
zero external services -- handy for local dev, demos, and CI.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "StudyMentor API"
    api_prefix: str = "/api"

    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db_name: str = "studymentor"

    # When True (default), the app uses an in-memory async store instead of
    # MongoDB, so `uvicorn app.main:app --reload` works immediately without
    # any external dependency. Flip to False + provide MONGO_URI for a real
    # deployment.
    use_in_memory_db: bool = True

    cors_origins: list[str] = ["http://localhost:3000"]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
