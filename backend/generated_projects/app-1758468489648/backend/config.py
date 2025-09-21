import os
from pydantic import BaseSettings
from typing import List

# Load environment variables from a .env file if it exists
from dotenv import load_dotenv
load_dotenv()

class Settings(BaseSettings):
    """
    Application configuration settings.
    Pydantic's BaseSettings automatically reads from environment variables.
    """
    APP_NAME: str = "College Event Management API"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "A simple API to manage events for a college campus."
    
    # CORS (Cross-Origin Resource Sharing) settings
    # This list should be updated with your production frontend URL
    CORS_ORIGINS: List[str] = [
        "http://localhost",
        "http://localhost:5173",  # Default for Vite/React development
        "http://localhost:3000",  # Default for Create React App
    ]

    class Config:
        # This allows Pydantic to read settings from a .env file
        env_file = ".env"
        env_file_encoding = "utf-8"

# Create a single instance of the settings to be used across the application
settings = Settings()