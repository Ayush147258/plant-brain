"""Embedding service for sentence-transformers model inference."""

import asyncio
import hashlib
import logging
import math
import re
import threading
import time
from typing import Any


from app.config import settings


logger = logging.getLogger(__name__)


class EmbeddingService:
    """Generate normalized text embeddings with lazy model loading."""

    _model: Any | None = None
    _model_name: str = settings.embedding_model
    _lock: threading.Lock = threading.Lock()

    def get_model(self) -> Any:
        """Return the cached embedding model, loading it once in a thread-safe way."""

        if self.__class__._model is None:
            with self.__class__._lock:
                if self.__class__._model is None:
                    from sentence_transformers import SentenceTransformer

                    logger.info("Loading embedding model %s...", self.__class__._model_name)
                    self.__class__._model = SentenceTransformer(self.__class__._model_name)
                    logger.info("Embedding model loaded")
        return self.__class__._model

    def embed_text(self, text: str) -> list[float]:
        """Generate a normalized embedding for a single text string."""

        start_time = time.time()
        try:
            cleaned_text = self._clean_text(text)
            if not cleaned_text:
                logger.info("Empty text received; returning zero vector")
                return self._zero_vector()

            if settings.lightweight_embeddings:
                return self._hash_embedding(cleaned_text)

            model = self.get_model()
            embedding = model.encode(
                [cleaned_text[:5000]],
                normalize_embeddings=True,
                show_progress_bar=False,
            )[0]
            elapsed_ms = (time.time() - start_time) * 1000
            logger.info("Embedded 1 text in %.2f ms", elapsed_ms)
            return self._to_float_list(embedding)
        except Exception:
            elapsed_ms = (time.time() - start_time) * 1000
            logger.exception("Failed to embed text after %.2f ms", elapsed_ms)
            raise

    def embed_batch(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        """Generate normalized embeddings for a batch of text strings."""

        start_time = time.time()
        try:
            logger.info("Embedding batch with %s texts using batch size %s", len(texts), batch_size)
            if not texts:
                logger.info("Empty text batch received; returning empty embedding list")
                return []

            cleaned_texts = [self._clean_text(text)[:5000] for text in texts]
            non_empty_texts = [cleaned_text for cleaned_text in cleaned_texts if cleaned_text]

            if not non_empty_texts:
                logger.info("All batch texts are empty; returning zero vectors")
                return [self._zero_vector() for _ in cleaned_texts]

            if settings.lightweight_embeddings:
                return [self._hash_embedding(text) if text else [0.0] * 384 for text in cleaned_texts]

            model = self.get_model()
            encoded_embeddings = model.encode(
                non_empty_texts,
                batch_size=batch_size,
                normalize_embeddings=True,
                show_progress_bar=False,
            )

            zero_vector = self._zero_vector()
            encoded_index = 0
            embeddings: list[list[float]] = []
            for cleaned_text in cleaned_texts:
                if cleaned_text:
                    embeddings.append(self._to_float_list(encoded_embeddings[encoded_index]))
                    encoded_index += 1
                else:
                    embeddings.append(list(zero_vector))

            elapsed_ms = (time.time() - start_time) * 1000
            logger.info("Embedded %s texts in %.2f ms", len(texts), elapsed_ms)
            return embeddings
        except Exception:
            elapsed_ms = (time.time() - start_time) * 1000
            logger.exception("Failed to embed batch after %.2f ms", elapsed_ms)
            raise

    def get_model_dimension(self) -> int:
        """Return the active embedding dimension."""

        if settings.lightweight_embeddings:
            return 384
        return int(self.get_model().get_sentence_embedding_dimension())

    async def embed_text_async(self, text: str) -> list[float]:
        """Generate a text embedding in the default executor."""

        return await asyncio.get_event_loop().run_in_executor(None, self.embed_text, text)

    async def embed_batch_async(self, texts: list[str]) -> list[list[float]]:
        """Generate batch embeddings in the default executor."""

        return await asyncio.get_event_loop().run_in_executor(None, self.embed_batch, texts)

    @staticmethod
    def _hash_embedding(text: str, dimension: int = 384) -> list[float]:
        """Create a deterministic normalized token-hash vector for offline development."""

        vector = [0.0] * dimension
        for token in re.findall(r"[a-z0-9-]+", text.lower()):
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % dimension
            vector[index] += 1.0 if digest[4] % 2 == 0 else -1.0
        norm = math.sqrt(sum(value * value for value in vector))
        return [value / norm for value in vector] if norm else vector

    @staticmethod
    def _clean_text(text: str) -> str:
        """Normalize text before embedding."""

        return text.strip().replace("\n", " ")

    def _zero_vector(self) -> list[float]:
        """Return a zero vector matching the configured model dimension."""

        return [0.0] * self.get_model_dimension()

    @staticmethod
    def _to_float_list(embedding: Any) -> list[float]:
        """Convert a model embedding object into a plain list of floats."""

        if hasattr(embedding, "tolist"):
            return [float(value) for value in embedding.tolist()]
        return [float(value) for value in embedding]


embedding_service = EmbeddingService()

__all__ = ["EmbeddingService", "embedding_service"]
