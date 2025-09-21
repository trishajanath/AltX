```python
import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    """
    Application settings management.
    Reads configuration from environment variables.
    """
    APP_NAME: str = "Quick Delivery API"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")

    # CORS settings
    # This list of origins is allowed to make cross-origin requests.
    # The default value is set for a standard React development server.
    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        # This allows Pydantic to read from a .env file if you create one
        # For this project, we are using defaults, but this is a best practice.
        env_file = ".env"
        env_file_encoding = 'utf-8'

# Instantiate the settings object to be imported by other modules
settings = Settings()
```