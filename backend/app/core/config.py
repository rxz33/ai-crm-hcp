from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GROQ_API_KEY: str = ""
    DB_URL: str = "sqlite:///./app.db"

    # Groq decommissioned gemma2-9b-it, so use a supported model.
    MODEL_NAME: str = "llama-3.3-70b-versatile"

    class Config:
        env_file = ".env"

settings = Settings()
