"""Configuration management for Solarware application."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application configuration from environment variables."""

    # API
    API_TITLE: str = "Solarware API"
    API_DESCRIPTION: str = "Solar prospect discovery and outreach automation"
    API_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Database
    DATABASE_URL: str = "postgresql://solarware:password@localhost:5432/solarware"
    DATABASE_ECHO: bool = False

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # Satellite Providers
    GOOGLE_EARTH_ENGINE_PROJECT: str = ""
    GOOGLE_EARTH_ENGINE_KEY_FILE: str = ""
    SENTINEL_HUB_CLIENT_ID: str = ""
    SENTINEL_HUB_CLIENT_SECRET: str = ""

    # Geocoding
    NOMINATIM_USER_AGENT: str = "solarware/0.1.0"

    # Contact Enrichment
    GOOGLE_MAPS_API_KEY: str = ""
    GOOGLE_SEARCH_API_KEY: str = ""
    GOOGLE_SEARCH_ENGINE_ID: str = ""

    # Solar Analysis
    SOLAR_PANEL_WIDTH_M: float = 1.75  # Standard panel width in meters
    SOLAR_PANEL_HEIGHT_M: float = 1.05  # Standard panel height in meters
    SOLAR_PANEL_RATED_POWER_W: int = 400  # Standard panel power rating
    SYSTEM_EFFICIENCY: float = 0.82  # System efficiency (accounting for inverter, wiring losses)
    
    # Location settings for default solar irradiance
    DEFAULT_COUNTRY: str = "US"
    
    # Email Configuration
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@solarware.local"
    SMTP_FROM_NAME: str = "Solarware"
    
    # Optional: SendGrid configuration
    SENDGRID_API_KEY: str = ""
    
    # Optional: AWS SES configuration
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"

    # Output Paths
    OUTPUT_BASE_PATH: str = "./output"
    MAILING_PACKS_PATH: str = "./output/mailing_packs"
    VISUALIZATIONS_PATH: str = "./output/visualizations"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
