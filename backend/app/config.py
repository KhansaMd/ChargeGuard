from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    paypal_client_id: str
    paypal_secret: str
    paypal_base: str = "https://api-m.sandbox.paypal.com"
    anthropic_api_key: str
    ai_model: str = "claude-haiku-5-5"
    database_url: str = "sqlite:///chargeguard.db"
    frontend_origin: str = "http://localhost:5173"


settings = Settings()