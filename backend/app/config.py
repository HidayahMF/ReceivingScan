from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_env: str = "development"
    app_secret: str = "local-development-only"
    public_origin: str = "http://localhost:5173"
    storage_path: str = "/var/lib/receiving-ai"
    max_upload_bytes: int = 10 * 1024 * 1024
    allowed_image_types: str = "image/jpeg,image/png,image/webp,application/pdf"
    redis_url: str = "redis://redis:6379/0"
    sqlserver_host: str | None = None
    sqlserver_port: int = 1433
    sqlserver_database: str | None = None
    sqlserver_user: str | None = None
    sqlserver_password: str | None = None
    sqlserver_encrypt: bool = True
    mysql_po_host: str | None = None
    mysql_po_port: int = 3306
    mysql_po_database: str | None = None
    mysql_po_readonly_user: str | None = None
    mysql_po_password: str | None = None
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str | None = None
    enable_local_vlm: bool = False
    ollama_timeout_seconds: int = 60
    ollama_max_retries: int = 2
    tesseract_cmd: str | None = None
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

@lru_cache
def get_settings() -> Settings:
    return Settings()
