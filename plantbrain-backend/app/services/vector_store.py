"""Persistent ChromaDB vector store for PlantBrain document chunks."""

import asyncio
import logging
from typing import Any

import chromadb

try:
    from chromadb.errors import ChromaError
except Exception:  # pragma: no cover - defensive across ChromaDB releases
    ChromaError = Exception

from app.config import settings


logger = logging.getLogger(__name__)


class VectorStore:
    """Wrapper around a persistent ChromaDB collection for document retrieval."""

    def __init__(self) -> None:
        """Create an uninitialized vector store wrapper."""

        self.client = None
        self.collection = None
        self.collection_name = "plantbrain_documents"

    def initialize(self) -> None:
        """Initialize the persistent ChromaDB client and collection."""

        try:
            logger.info("Initializing ChromaDB persistent client at %s", settings.chroma_persist_dir)
            self.client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(
                "Vector store initialized with collection %s containing %s chunks",
                self.collection_name,
                self.collection.count(),
            )
        except Exception:
            logger.exception("Failed to initialize vector store")
            raise

    async def add_chunks(self, chunks: list[dict], document_id: str) -> int:
        """Embed and upsert document chunks into ChromaDB in small batches."""

        if not chunks:
            logger.info("No chunks provided for document %s", document_id)
            return 0

        self._ensure_initialized()
        logger.info("Adding %s chunks for document %s", len(chunks), document_id)

        try:
            total_added = 0
            for start in range(0, len(chunks), 50):
                batch = chunks[start : start + 50]
                ids = [chunk["chunk_id"] for chunk in batch]
                documents = [chunk["text"] for chunk in batch]
                from app.services.embedding_service import embedding_service

                embeddings = await embedding_service.embed_batch_async(documents)
                metadatas = [self._build_metadata(chunk, document_id) for chunk in batch]

                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self._sync_add, ids, embeddings, documents, metadatas)
                total_added += len(batch)
                logger.info("Added vector batch %s-%s for document %s", start, start + len(batch), document_id)

            logger.info("Added %s total chunks for document %s", total_added, document_id)
            return total_added
        except Exception:
            logger.exception("Failed to add chunks for document %s", document_id)
            raise

    async def search(
        self,
        query: str,
        top_k: int = 5,
        filter_document_id: str | None = None,
    ) -> list[dict]:
        """Search the vector store for chunks most relevant to a query."""

        self._ensure_initialized()
        logger.info("Searching vector store with top_k=%s filter_document_id=%s", top_k, filter_document_id)

        try:
            from app.services.embedding_service import embedding_service

            embedding = await embedding_service.embed_text_async(query)
            where_clause = {"document_id": filter_document_id} if filter_document_id else None
            loop = asyncio.get_event_loop()
            try:
                results = await loop.run_in_executor(
                    None,
                    self._sync_query,
                    embedding,
                    top_k,
                    where_clause,
                )
            except ChromaError:
                logger.warning("ChromaDB query failed; reinitializing vector store and retrying once", exc_info=True)
                self.initialize()
                results = await loop.run_in_executor(
                    None,
                    self._sync_query,
                    embedding,
                    top_k,
                    where_clause,
                )

            matches = self._format_query_results(results)
            matches.sort(key=lambda item: item["distance"])
            logger.info("Vector search returned %s matches", len(matches))
            return matches
        except Exception:
            logger.exception("Failed to search vector store")
            raise

    async def delete_document(self, document_id: str) -> int:
        """Delete all chunks associated with a document id."""

        self._ensure_initialized()
        logger.info("Deleting vector chunks for document %s", document_id)

        try:
            loop = asyncio.get_event_loop()
            deleted_count = await loop.run_in_executor(None, self._sync_delete_document, document_id)
            logger.info("Deleted %s vector chunks for document %s", deleted_count, document_id)
            return deleted_count
        except Exception:
            logger.exception("Failed to delete vector chunks for document %s", document_id)
            raise


    async def health_check(self) -> bool:
        """Return True when the ChromaDB collection is initialized and countable."""

        try:
            self._ensure_initialized()
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.collection.count)
            return True
        except Exception:
            logger.exception("Vector store health check failed")
            return False

    async def get_stats(self) -> dict:
        """Return basic vector store collection statistics."""

        self._ensure_initialized()
        try:
            loop = asyncio.get_event_loop()
            total_chunks = await loop.run_in_executor(None, self.collection.count)
            return {
                "total_chunks": total_chunks,
                "collection_name": self.collection_name,
            }
        except Exception:
            logger.exception("Failed to get vector store stats")
            raise

    def _sync_add(self, ids, embeddings, documents, metadatas) -> None:
        """Synchronously upsert a prepared chunk batch into ChromaDB."""

        self._ensure_initialized()
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

    def _sync_query(self, embedding: list[float], top_k: int, where_clause: dict | None) -> dict:
        """Synchronously query ChromaDB."""

        self._ensure_initialized()
        query_kwargs: dict[str, Any] = {
            "query_embeddings": [embedding],
            "n_results": top_k,
        }
        if where_clause:
            query_kwargs["where"] = where_clause
        return self.collection.query(**query_kwargs)

    def _sync_delete_document(self, document_id: str) -> int:
        """Synchronously delete all vectors for a document and return the count."""

        self._ensure_initialized()
        existing = self.collection.get(where={"document_id": document_id})
        ids = existing.get("ids", []) if existing else []
        if not ids:
            return 0
        self.collection.delete(where={"document_id": document_id})
        return len(ids)

    def _ensure_initialized(self) -> None:
        """Raise a clear error if the vector store has not been initialized."""

        if self.client is None or self.collection is None:
            raise RuntimeError("VectorStore is not initialized. Call initialize() first.")

    @staticmethod
    def _build_metadata(chunk: dict, document_id: str) -> dict:
        """Build Chroma-compatible metadata for a chunk."""

        metadata = {
            "document_id": document_id,
            "chunk_index": chunk["chunk_index"],
            "char_start": chunk["char_start"],
            "char_end": chunk["char_end"],
            **chunk.get("metadata", {}),
        }
        return VectorStore._sanitize_metadata(metadata)

    @staticmethod
    def _sanitize_metadata(metadata: dict) -> dict:
        """Convert metadata values into Chroma-supported scalar values."""

        sanitized: dict[str, str | int | float | bool] = {}
        for key, value in metadata.items():
            if value is None:
                continue
            if isinstance(value, str | int | float | bool):
                sanitized[str(key)] = value
            else:
                sanitized[str(key)] = str(value)
        return sanitized

    @staticmethod
    def _format_query_results(results: dict) -> list[dict]:
        """Convert ChromaDB query output into a flat list of search matches."""

        documents = results.get("documents", [[]])[0] or []
        metadatas = results.get("metadatas", [[]])[0] or []
        distances = results.get("distances", [[]])[0] or []
        ids = results.get("ids", [[]])[0] or []

        matches: list[dict] = []
        for index, document in enumerate(documents):
            matches.append(
                {
                    "text": document,
                    "metadata": metadatas[index] if index < len(metadatas) else {},
                    "distance": distances[index] if index < len(distances) else 0.0,
                    "id": ids[index] if index < len(ids) else "",
                }
            )
        return matches


vector_store = VectorStore()

__all__ = ["VectorStore", "vector_store"]
