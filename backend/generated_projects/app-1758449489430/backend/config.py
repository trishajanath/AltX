import os
from pydantic_settings import BaseSettings
from typing import List, Union

class Settings(BaseSettings):
    """
    Application configuration settings loaded from environment variables.
    Utilizes pydantic-settings for robust, typed configuration management.
    """
    PROJECT_NAME: str = "College EventHub API"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True
    
    # CORS (Cross-Origin Resource Sharing) settings
    # This allows the frontend hosted on localhost:5173 to communicate with the backend.
    # In a production environment, this should be updated to the frontend's domain.
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000", # Common for React as well
    ]

    class Config:
        # Specifies the file to load environment variables from.
        # This is useful for local development.
        env_file = ".env"
        env_file_encoding = 'utf-8'

# Instantiate the settings object that will be used throughout the application.
settings = Settings()