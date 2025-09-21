```python
import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Pydantic's BaseSettings provides robust validation and type hints.
    """
    APP_NAME: str = "ShopSphere API"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
    API_V1_PREFIX: str = "/api/v1"
    
    # CORS (Cross-Origin Resource Sharing) settings
    # This configuration is critical for allowing the React frontend
    # (e.g., running on http://localhost:5173) to communicate with the API.
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",  # React default dev server
        "http://localhost:3000",  # Another common frontend dev port
    ]

    class Config:
        # This allows loading settings from a .env file if one exists
        # To use this, create a .env file in the root directory and add variables like:
        # DEBUG=True
        env_file = ".env"
        env_file_encoding = 'utf-8'

# Create a single instance of the settings to be imported across the application
settings = Settings()
```