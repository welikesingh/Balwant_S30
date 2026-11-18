"""Application settings, loaded from environment variables (and a local .env file)."""
from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Supabase PostgreSQL. SecretStr keeps credentials out of logs and reprs.
    supabase_db_url: SecretStr
    supabase_url: str = ""
    supabase_publishable_key: SecretStr = SecretStr("")

    # Neo4j
    neo4j_uri: str = "bolt://localhost:7688"
    neo4j_user: str = "neo4j"
    neo4j_password: SecretStr

    # Qdrant
    qdrant_url: str
    qdrant_api_key: SecretStr
    qdrant_collection: str = "sentinel_corpus2"

    # Gemini Embedding 2. These must match how sentinel_corpus2 was built
    # (QUADRANTDB_EMBEDDING/sentinel_qdrant_human_written.ipynb).
    gemini_api_key: SecretStr
    embedding_model: str = "gemini-embedding-2"
    embedding_dim: int = 3072
    embedding_query_task: str = "RETRIEVAL_QUERY"

    # LLM
    llm_provider: str = "gemini"
    llm_model: str = "gemini-3.8-flash"
    llm_api_key: SecretStr = SecretStr("")
    llm_temperature: float = 0.0
    llm_timeout_seconds: int = 90
    # Tried in order when the primary model is overloaded (503/504).
    llm_fallback_models: list[str] = ["gemini-3.5-flash-lite"]

    # Retrieval behaviour
    policy_top_k: int = 5
    # Investigator notes and chargeback narratives describe other customers' cases,
    # so policy retrieval uses the policy-style documents by default.
    policy_document_types: list[str] = ["playbooks", "regulatory_exercises", "guidelines", "rba_guides"]
    graph_lookback_days: int = 90
    # Only labels from these splits may appear as historical graph evidence.
    graph_label_splits: list[str] = ["warmup", "train"]
    graph_max_records: int = 25

    log_level: str = "INFO"

    @property
    def llm_key(self) -> str:
        """LLM key, falling back to the Gemini embedding key when LLM_API_KEY is empty."""
        return self.llm_api_key.get_secret_value() or self.gemini_api_key.get_secret_value()


@lru_cache
def get_settings() -> Settings:
    return Settings()
