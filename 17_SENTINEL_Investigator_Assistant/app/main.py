"""FastAPI entry point.

    uv run uvicorn app.main:app --reload
    Swagger UI: http://127.0.0.1:8000/docs
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.config import get_settings
from app.db.neo4j_db import Neo4jGraph
from app.db.qdrant_db import QdrantStore
from app.db.supabase_db import SupabaseRepository
from app.services.investigation import InvestigationService
from app.services.llm_service import GeminiExplainer
from app.services.policy_retriever import GeminiEmbedder, PolicyRetriever


def build_service() -> InvestigationService:
    """Wire the real database clients and the LLM into the orchestrator."""
    s = get_settings()
    if s.llm_provider.lower() != "gemini":
        raise ValueError(f"LLM_PROVIDER={s.llm_provider!r} is not supported; use 'gemini'")

    store = QdrantStore(s.qdrant_url, s.qdrant_api_key.get_secret_value(), s.qdrant_collection)
    embedder = GeminiEmbedder(s.gemini_api_key.get_secret_value(), s.embedding_model,
                              s.embedding_dim, s.embedding_query_task)
    return InvestigationService(
        transactions=SupabaseRepository(s.supabase_db_url.get_secret_value()),
        graph=Neo4jGraph(s.neo4j_uri, s.neo4j_user, s.neo4j_password.get_secret_value(),
                         lookback_days=s.graph_lookback_days, label_splits=s.graph_label_splits,
                         max_records=s.graph_max_records),
        policies=PolicyRetriever(embedder, store, s.policy_document_types),
        llm=GeminiExplainer(s.llm_key, s.llm_model, s.llm_temperature, s.llm_timeout_seconds,
                            fallback_models=s.llm_fallback_models),
        top_k=s.policy_top_k,
        model_info={"llm": s.llm_model, "embedding": s.embedding_model,
                    "qdrant_collection": s.qdrant_collection},
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.basicConfig(level=get_settings().log_level,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    # Tests may inject a fake service before startup.
    if not hasattr(app.state, "service"):
        app.state.service = build_service()
    yield
    service = app.state.service
    for closer in (getattr(service.graph, "close", None),
                   getattr(getattr(service.policies, "store", None), "close", None)):
        if closer:
            closer()


app = FastAPI(
    title="SENTINEL Fraud Investigator Assistant",
    description="Hybrid Graph RAG over Supabase (transactions), Neo4j (relationships) and "
                "Qdrant (policies) with a grounded Gemini explanation.",
    version="0.1.0",
    lifespan=lifespan,
)
app.include_router(router)
