from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App settings
    app_name: str = "Video Downloader API"
    debug: bool = False

    # Cloudflare R2 settings
    r2_account_id: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_bucket_name: str = "video-downloads"
    r2_public_url: str = ""  # Custom domain or R2.dev URL

    # Storage settings
    storage_provider: str = "local"  # "local", "r2", or "gcs"
    local_storage_path: str = "/tmp/video-downloads"
    use_r2_storage: bool = False  # Set to True when R2 is configured (deprecated, use storage_provider)

    # Google Cloud Storage settings
    gcs_bucket_name: str = ""
    gcs_project_id: str = ""  # Optional, auto-detected from environment

    # Task settings
    task_timeout_seconds: int = 300  # 5 minutes
    max_concurrent_tasks: int = 5

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
