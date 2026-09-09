"""Central configuration. Everything tunable lives here, nothing is hard-coded elsewhere."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- LLM ---
    llm_provider: str = "anthropic"
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    model_small: str = "claude-haiku-4-5-20251001"
    model_medium: str = "claude-sonnet-5"
    model_large: str = "claude-opus-5"

    # --- tools ---
    tavily_api_key: str = ""

    # --- infrastructure ---
    postgres_dsn: str = "postgresql+psycopg://arp:arp@localhost:5432/arp"
    analytics_dsn: str = "postgresql+psycopg://arp_readonly:arp@localhost:5432/arp"
    redis_url: str = "redis://localhost:6379/0"
    chroma_host: str = "localhost"
    chroma_port: int = 8001

    # --- retrieval ---
    chunk_size: int = 800
    chunk_overlap: int = 120
    dense_top_k: int = 20
    sparse_top_k: int = 20
    rerank_top_k: int = 6
    rrf_k: int = 60

    # --- control loop ---
    confidence_auto_approve: float = 0.85
    confidence_escalate_below: float = 0.60
    max_replan_attempts: int = 2
    critic_disagreement_threshold: float = 0.25


@lru_cache
def get_settings() -> Settings:
    return Settings()
