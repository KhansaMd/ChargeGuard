from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/.env, found from this file's location so scripts work from any folder
ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_file_encoding="utf-8", extra="ignore")

    paypal_client_id: str
    paypal_secret: str
    paypal_base: str = "https://api-m.sandbox.paypal.com"
    anthropic_api_key: str
    ai_model: str = "claude-haiku-5-5"
    database_url: str = "sqlite:///chargeguard.db"
    frontend_origin: str = "http://localhost:5173"


settings = Settings()

# Guard against stray spaces or quotes pasted into .env
settings.paypal_client_id = settings.paypal_client_id.strip().strip('"').strip("'")
settings.paypal_secret = settings.paypal_secret.strip().strip('"').strip("'")
settings.paypal_base = settings.paypal_base.strip().rstrip("/")
