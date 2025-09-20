```python
import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    """
    Application settings management.
    Reads settings from environment variables.
    """
    PROJECT_NAME: str = "Build-A-Dating App"
    API_V1_STR: str = "/api/v1"
    
    # CORS (Cross-Origin Resource Sharing) settings
    # This controls which frontend origins are allowed to communicate with the API.
    # The default allows a React app running on localhost:5173.
    # In production, this should be updated to the actual frontend domain.
    CORS_ORIGINS: List[str] = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(',')

    class Config:
        # Pydantic settings configuration
        case_sensitive = True
        # If you have a .env file, this will load it.
        # env_file = ".env"

# Instantiate the settings object to be used throughout the application
settings = Settings()
```