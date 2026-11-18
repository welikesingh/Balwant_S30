"""Semantic policy retrieval: build a query, embed it with Gemini Embedding 2, search Qdrant.

Embedding settings must match how sentinel_corpus2 was built
(QUADRANTDB_EMBEDDING/sentinel_qdrant_human_written.ipynb):
  model gemini-embedding-2, output_dimensionality 3072, task type RETRIEVAL_DOCUMENT
  for chunks, so queries use RETRIEVAL_QUERY. Chunks were embedded as raw text
  (title + chunk), so the query is plain natural language with no extra preprocessing.
"""
import logging
from typing import Any

from google import genai
from google.genai import types

from app.db.errors import DatabaseUnavailable
from app.db.qdrant_db import QdrantStore
from app.services.reason_codes import REASON_CODE_CATALOG

logger = logging.getLogger(__name__)


class GeminiEmbedder:
    def __init__(self, api_key: str, model: str, dimension: int, task_type: str):
        self._client = genai.Client(api_key=api_key)
        self.model = model
        self.dimension = dimension
        self.task_type = task_type

    def embed_query(self, text: str) -> list[float]:
        try:
            result = self._client.models.embed_content(
                model=self.model, contents=text,
                config=types.EmbedContentConfig(task_type=self.task_type,
                                                output_dimensionality=self.dimension))
        except Exception as exc:
            raise DatabaseUnavailable(f"Gemini embedding failed: {type(exc).__name__}") from exc
        vector = result.embeddings[0].values
        if len(vector) != self.dimension:
            raise DatabaseUnavailable(f"Embedding has {len(vector)} dims, expected {self.dimension}")
        return vector


def build_policy_query(transaction: dict[str, Any], supported: dict[str, dict[str, str]]) -> str:
    """Turn transaction facts and supported reason codes into one natural-language question.

    The corpus is organised by topic (device change, night activity, shared devices, ...),
    so naming the topics of the supported codes steers retrieval toward the right guidance.
    """
    topics = []
    for code in supported:
        topic = REASON_CODE_CATALOG[code]["topic"]
        if topic not in topics:
            topics.append(topic)

    signals = "; ".join(entry["description"].lower() for entry in supported.values())
    payment = (f"a {transaction.get('payment_channel', '')} payment of INR "
               f"{transaction.get('transaction_amount')} to a merchant in category {transaction.get('merchant_category', '')}")
    if not signals:
        return (f"What should a fraud investigator verify for {payment} "
                f"when no specific risk signal is present?")
    return (f"What should a fraud investigator check and record for {payment} "
            f"with these risk signals: {signals}? Relevant topics: {', '.join(topics)}.")


class PolicyRetriever:
    def __init__(self, embedder: GeminiEmbedder, store: QdrantStore,
                 document_types: list[str] | None = None):
        self.embedder = embedder
        self.store = store
        self.document_types = document_types

    def search_policy(self, query: str, top_k: int = 5,
                      document_types: list[str] | None = None) -> list[dict[str, Any]]:
        """Top-k policy chunks with document name, chunk number, score and text."""
        vector = self.embedder.embed_query(query)
        types_filter = self.document_types if document_types is None else document_types
        return self.store.search(vector, top_k=top_k, document_types=types_filter or None)
