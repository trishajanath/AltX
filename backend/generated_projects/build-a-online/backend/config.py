import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Application settings management.
    
    Uses pydantic-settings to load configuration from environment variables
    or default values. This provides a single source of truth for configuration.
    """
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8', extra='ignore')

    PROJECT_NAME: str = "MelodyStream API"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # CORS (Cross-Origin Resource Sharing) settings
    # This is a critical security feature for frontend applications.
    # It specifies which origins are allowed to access the API.
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",  # React default
        "http://localhost:3000",  # Another common frontend port
    ]

# Instantiate the settings class.
# This object will be imported and used throughout the application.
settings = Settings()