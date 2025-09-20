```python
import os
from typing import List, Union

from pydantic_settings import BaseSettings, SettingsConfigDict

# SECURITY NOTE: This configuration class uses pydantic-settings to load application
# settings from environment variables. This is a security best practice that prevents
# hardcoding sensitive information directly into the codebase.
# In a CI/CD pipeline, these variables would be injected securely.

class Settings(BaseSettings):
    """
    Application settings are loaded from environment variables.
    A .env file is used for local development.
    """
    PROJECT_NAME: str = "E-Commerce Core API"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # CORS (Cross-Origin Resource Sharing) settings
    # This list defines which origins are allowed to communicate with the API.
    # For production, this should be a specific list of frontend domains, not a wildcard "*".
    # Example: ALLOWED_ORIGINS=["https://your-react-app.com"]
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # The model_config tells pydantic-settings to look for a .env file.
    # This is only for local development and the .env file should be in .gitignore.
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8', extra="ignore")

settings = Settings()
```