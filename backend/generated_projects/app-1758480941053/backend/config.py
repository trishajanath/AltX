# config.py
# Application configuration and settings

from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    """
    Application settings are managed here.
    Using pydantic-settings allows for easy management of environment variables.
    """
    PROJECT_NAME: str = "Portfolio API"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # CORS (Cross-Origin Resource Sharing) settings
    # This list should be updated with the production frontend URL.
    # For development, we allow the default Vite React development server.
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000", # Common alternative for React dev servers
    ]

    class Config:
        # This allows pydantic to read settings from a .env file if it exists
        case_sensitive = True

# Instantiate the settings object that will be used throughout the application
settings = Settings()