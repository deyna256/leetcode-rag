from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": (".env", "../.env")}

    POSTGRES_URL: str = "postgresql://leetcode:leetcode@localhost:5432/leetcode"
    QDRANT_URL: str = "http://localhost:6333"
    OPENAI_API_KEY: str
    PARSER_BASE_URL: str = "http://localhost:8001"
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    @field_validator("OPENAI_API_KEY")
    @classmethod
    def validate_openai_key(cls, v: str) -> str:
        if not v.startswith("sk-"):
            raise ValueError("OPENAI_API_KEY must start with 'sk-'")
        return v


settings = Settings()  # type: ignore[missing-argument]  # loaded from env
