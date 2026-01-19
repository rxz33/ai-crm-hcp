from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GROQ_API_KEY: str = ""
    DB_URL: str = "sqlite:///./app.db"

    MODEL_NAME: str = "llama-3.1-8b-instant"

    EXTRACT_MODEL: str = "llama-3.3-70b-versatile"
    TOOL_MODEL: str = "llama-3.1-8b-instant"

    class Config:
        env_file = ".env"

settings = Settings()
