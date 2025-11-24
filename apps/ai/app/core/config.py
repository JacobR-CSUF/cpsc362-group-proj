from pydantic import BaseSettings


class Settings(BaseSettings):
    GEMINI_API_KEY: str

    class Config:
        env_file = ".env"  # /root/apps/ai/.env


settings = Settings()
