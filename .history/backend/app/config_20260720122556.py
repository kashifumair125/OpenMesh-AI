"""OpenMesh AI - Central Configuration (Minimal)"""

from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str = "OpenMesh AI"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://openmesh:openmesh@localhost:5432/openmesh",
        env="DATABASE_URL"
    )
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    DEFAULT_MODEL_PROVIDER: str = Field(default="ollama", env="DEFAULT_MODEL_PROVIDER")
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434", env="OLLAMA_BASE_URL")
    OLLAMA_MODEL: str = Field(default="phi3:3.8b", env="OLLAMA_MODEL")
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    ANTHROPIC_MODEL: str = Field(default="claude-3-haiku-20240307", env="ANTHROPIC_MODEL")
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    OPENAI_MODEL: str = Field(default="gpt-3.5-turbo", env="OPENAI_MODEL")
    GOOGLE_API_KEY: Optional[str] = Field(default=None, env="GOOGLE_API_KEY")
    GEMINI_MODEL: str = Field(default="gemini-1.5-flash", env="GEMINI_MODEL")
    MAX_COST_PER_REQUEST: float = Field(default=1.0, env="MAX_COST_PER_REQUEST")
    SANDBOX_ENABLED: bool = Field(default=True, env="SANDBOX_ENABLED")
    DOCKER_HOST: str = Field(default="unix:///var/run/docker.sock", env="DOCKER_HOST")
    MCP_SERVER_TIMEOUT: int = Field(default=30, env="MCP_SERVER_TIMEOUT")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
