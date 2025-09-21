import os
from pydantic_settings import BaseSettings
from typing import List

# Load environment variables from a .env file if it exists
from dotenv import load_dotenv
load_dotenv()

class Settings(BaseSettings):
    """
    Application configuration settings.
    Uses Pydantic's BaseSettings to automatically load from environment variables.
    """
    PROJECT_NAME: str = "TodoApp API"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"

    # CORS (Cross-Origin Resource Sharing) configuration
    # This allows the frontend hosted on localhost:5173 (default for Vite)
    # to communicate with the backend.
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",  # React (Vite) default
        "http://localhost:3000",  # React (Create React App) default
        "http://localhost:8080",  # Vue default
    ]

    class Config:
        # Pydantic settings configuration
        case_sensitive = True
        # Reads settings from a .env file.
        # env_file = ".env" 

# Instantiate the settings object to be used throughout the application
settings = Settings()