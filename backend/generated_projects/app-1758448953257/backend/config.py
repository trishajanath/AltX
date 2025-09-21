import os
from typing import List
from pydantic_settings import BaseSettings

class AppSettings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Pydantic's BaseSettings provides robust validation and type hints.
    """
    PROJECT_NAME: str = "Task Management API"
    API_PREFIX: str = "/api"
    
    # CORS (Cross-Origin Resource Sharing) settings
    # This allows the frontend hosted on localhost:5173 to communicate with the API.
    # In production, this should be updated to the actual frontend domain.
    CORS_ORIGINS: List[str] = ["http://localhost:5173"]

    class Config:
        # Specifies the file to load environment variables from.
        # Useful for local development.
        env_file = ".env"
        env_file_encoding = "utf-8"

# Instantiate the settings so they can be imported and used throughout the application.
settings = AppSettings()