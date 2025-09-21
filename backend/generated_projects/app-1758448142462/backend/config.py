import os
from pydantic_settings import BaseSettings
from typing import List, Union

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Utilizes pydantic-settings for robust configuration management.
    """
    PROJECT_NAME: str = "WFD - What's for Dinner?"
    API_V1_STR: str = "/api/v1"
    
    # CORS (Cross-Origin Resource Sharing) settings.
    # The default value is a list containing the React frontend's local development URL.
    # In a production environment, this should be a space-separated string in an env var.
    # e.g., CORS_ORIGINS="https://your-frontend.com http://localhost:5173"
    CORS_ORIGINS: Union[str, List[str]] = "http://localhost:5173"

    @property
    def cors_origins_list(self) -> List[str]:
        """
        Parses the CORS_ORIGINS string into a list of origins.
        This allows setting multiple origins from a single environment variable.
        """
        if isinstance(self.CORS_ORIGINS, str):
            return [origin.strip() for origin in self.CORS_ORIGINS.split(" ")]
        return self.CORS_ORIGINS

    class Config:
        # This tells pydantic-settings to read settings from a .env file.
        # Create a `.env` file in the root directory to override these settings.
        env_file = ".env"
        env_file_encoding = 'utf-8'

# Instantiate the settings class to be used throughout the application
settings = Settings()