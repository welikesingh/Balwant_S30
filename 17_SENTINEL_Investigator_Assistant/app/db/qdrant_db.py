"""Read-only access to the existing Qdrant collection (sentinel_corpus2).

Collection facts (verified live): 850 points, 3072-dim vectors, cosine distance,
keyword payload indexes on document_type, source_document and regulator_theme.
This module never creates, deletes or writes to the collection.
"""
import logging
from typing import Any

from qdrant_client import QdrantClient, models

from app.db.errors import DatabaseUnavailable

logger = logging.getLogger(__name__)

PAYLOAD_FIELDS = ["source_document", "title", "document_type", "chunk_number", "chunk_count",
                  "topic", "regulator_theme", "split", "text"]


class QdrantStore:
    def __init__(self, url: str, api_key: str, collection: str, timeout: int = 30):
        self.collection = collection
        self._client = QdrantClient(url=url, api_key=api_key, timeout=timeout)

    def close(self) -> None:
        self._client.close()

    def search(self, vector: list[float], top_k: int = 5,
               document_types: list[str] | None = None) -> list[dict[str, Any]]:
        """Nearest chunks by cosine similarity, optionally restricted to some document types."""
        query_filter = None
        if document_types:
            query_filter = models.Filter(must=[models.FieldCondition(
                key="document_type", match=models.MatchAny(any=document_types))])
        try:
            points = self._client.query_points(
                self.collection, query=vector, limit=top_k,
                query_filter=query_filter, with_payload=PAYLOAD_FIELDS,
            ).points
        except Exception as exc:  # qdrant-client raises several transport-specific types
            raise DatabaseUnavailable(f"Qdrant search failed: {type(exc).__name__}") from exc

        results = []
        for rank, point in enumerate(points, start=1):
            payload = point.payload or {}
            results.append({
                "rank": rank,
                "point_id": str(point.id),
                "score": round(point.score, 4),
                **{field: payload.get(field) for field in PAYLOAD_FIELDS},
            })
        return results

    def collection_info(self) -> dict[str, Any]:
        try:
            info = self._client.get_collection(self.collection)
        except Exception as exc:
            raise DatabaseUnavailable(f"Qdrant unavailable: {type(exc).__name__}") from exc
        vectors = info.config.params.vectors
        return {"collection": self.collection, "points": info.points_count,
                "vector_size": vectors.size, "distance": str(vectors.distance.value)}
