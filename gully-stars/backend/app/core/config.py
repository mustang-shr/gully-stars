from pydantic_settings import BaseSettings
from typing import List, Union
import json


class Settings(BaseSettings):
    APP_NAME: str = "Gully Stars"
    APP_ENV: str = "development"
    DEBUG: bool = True

    SECRET_KEY: str = "dev-secret-key-change-in-production-must-be-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days

    DATABASE_URL: str = "postgresql+asyncpg://gullyuser:gullypass@localhost:5432/gullydb"

    BACKEND_CORS_ORIGINS: Union[List[str], str] = ["http://localhost:5173", "http://localhost:3000"]

    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE_MB: int = 10

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

    def get_cors_origins(self) -> List[str]:
        if isinstance(self.BACKEND_CORS_ORIGINS, str):
            try:
                return json.loads(self.BACKEND_CORS_ORIGINS)
            except Exception:
                return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",")]
        return self.BACKEND_CORS_ORIGINS


settings = Settings()
