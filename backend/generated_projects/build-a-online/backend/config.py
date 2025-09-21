```python
import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    """
    Application configuration settings.
    Uses Pydantic's BaseSettings to automatically load from environment variables.
    """
    # Application metadata
    PROJECT_NAME: str = "Clothify Marketplace API"
    API_V1_STR: str = "/api/v1"
    VERSION: str = "0.1.0"
    DESCRIPTION: str = "API for an online marketplace for clothes."

    # CORS (Cross-Origin Resource Sharing) settings
    # This allows the React frontend running on localhost:5173 to communicate with the API
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    class Config:
        # The .env file will be used to load environment variables
        case_sensitive = True
        env_file = ".env"

# Instantiate the settings object that will be used throughout the application
settings = Settings()
```