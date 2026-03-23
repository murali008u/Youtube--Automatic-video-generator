import urllib.parse
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "YouTube Automation System"
    DATABASE_PASSWORD: str
    
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "mistral"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def DATABASE_URL(self) -> str:
        encoded_password = urllib.parse.quote_plus(self.DATABASE_PASSWORD)
        # Change the localhost or port number if needed
        return f"postgresql://postgres:{encoded_password}@localhost:5433/youtube_automation"

settings = Settings()
