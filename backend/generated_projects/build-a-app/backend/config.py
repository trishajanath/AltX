```python
import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    """
    Application settings management.
    
    Loads configuration from environment variables. This is a best practice
    for separating configuration from code, especially for secrets and
    environment-specific settings.
    """
    APP_NAME: str = "SwiggyClone API"
    API_V1_STR: str = "/api/v1"
    
    # CORS (Cross-Origin Resource Sharing) settings
    # This list defines which origins are allowed to communicate with the API.
    # It's critically important for security in a web application.
    # We are specifically allowing our React frontend development server.
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",  # React default dev server
        "http://localhost:3000",  # Another common dev server port
    ]

    class Config:
        # This allows pydantic to read from a .env file if it exists.
        # Create a .env file in the root directory for local development.
        env_file = ".env"
        env_file_encoding = 'utf-8'

# Instantiate the settings object to be used throughout the application
settings = Settings()
```