```python
import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    """
    Application settings are managed here.
    Pydantic's BaseSettings automatically reads from environment variables.
    """
    PROJECT_NAME: str = "Simple Todo App API"
    API_V1_STR: str = "/api/v1"
    
    # CORS (Cross-Origin Resource Sharing) configuration
    # This setting defines which origins are allowed to communicate with the API.
    # It's crucial for security in web applications.
    # In a production environment, this should be set to the domain of your frontend.
    # For local development, we allow the React default port.
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",  # React default
        "http://localhost:3000",  # Another common frontend port
        "http://127.0.0.1:5173",
    ]

    class Config:
        # This allows pydantic to look for a .env file to load the settings
        # It's good practice to not commit .env files to version control.
        env_file = ".env"
        case_sensitive = True

# Instantiate the settings class
settings = Settings()
```