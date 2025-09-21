# config.py
# This file manages application settings using Pydantic's BaseSettings.
# It allows for configuration via environment variables, which is a best practice
# for separating configuration from code (a core tenet of 12-Factor Apps).

from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    """
    Application settings class.
    """
    APP_NAME: str = "Student Attendance Tracker API"
    APP_VERSION: str = "1.0.0"

    

# 
🛡️ CORS Settings: A list of allowed origins.
    # It's critical to restrict this to only the domains you trust.
    CORS_ORIGINS: List[AnyHttpUrl] = [
        "http://localhost:5173",  # Default for Vite/React development server
        "http://localhost:3000",  # Common for Create React App
    ]

    class Config:
        # This allows loading settings from a .env file (not included here for simplicity)
        env_file = ".env"
        env_file_encoding = 'utf-8'

# Instantiate the settings object to be used throughout the application
settings = Settings()