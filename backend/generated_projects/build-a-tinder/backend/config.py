```python
import os
from pydantic_settings import BaseSettings
from typing import List

# Determine the base directory of the project
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Utilizes pydantic-settings for robust type validation.
    """
    APP_NAME: str = "TinderClone API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # CORS (Cross-Origin Resource Sharing) settings
    # This configuration is crucial for allowing frontend applications
    # hosted on different domains to interact with the API.
    CORS_ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",  # React default dev server
        "http://localhost:3000",  # Another common dev port
    ]

    class Config:
        # Specifies the .env file to load environment variables from.
        # This allows for easy configuration management across different environments
        # (development, staging, production) without hardcoding values.
        env_file = os.path.join(BASE_DIR, ".env")
        env_file_encoding = 'utf-8'

# Instantiate settings to be imported and used across the application
settings = Settings()

```