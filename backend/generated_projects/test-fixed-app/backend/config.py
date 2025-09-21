# config.py
# Application configuration and settings management

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    """
    Manages application settings using Pydantic.
    It automatically reads environment variables for configuration.
    """
    
    # Application metadata
    PROJECT_NAME: str = "Todo FastAPI App"
    API_V1_STR: str = "/api"

    # CORS (Cross-Origin Resource Sharing) configuration
    # This is a critical security setting for front-end integrations.
    # It specifies which origins are allowed to access the API.
    # In production, this should be a list of your frontend domains.
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",  # Default for Vite/React development
        "http://localhost:3000",  # Default for Create React App
    ]

    # Model configuration for Pydantic
    model_config = SettingsConfigDict(
        case_sensitive=True,
        # Allows loading settings from a .env file (requires python-dotenv)
        # env_file = ".env" 
    )

# Instantiate the settings object to be used throughout the application
settings = Settings()