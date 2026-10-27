import os
import math
import hashlib
from typing import List, Optional
import config as config

class GeminiEmbedder:
    """
    Consistent embedding service for brand guidelines ingestion and RAG retrieval.
    Uses Google Gemini Embedding API (text-embedding-004) via the modern google.genai SDK.
    Includes a deterministic fallback embedding generator for offline testing or when
    GEMINI_API_KEY is not configured.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        embedding_dim: int = 768
    ):
        self.api_key = api_key if api_key is not None else config.GEMINI_API_KEY
        self.model_name = model_name or getattr(config, "GEMINI_EMBEDDING_MODEL", "text-embedding-004")
        self.embedding_dim = embedding_dim
        self._client = None

        if self.api_key and not getattr(config, "LOCAL_PRIVACY_MODE", False):
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                # Log without exposing sensitive details
                print(f"[GeminiEmbedder] Notice: Initializing in offline fallback mode ({e})")
                self._client = None

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generates embedding vectors for a batch of guideline text chunks."""
        if not texts:
            return []

        if self._client:
            try:
                # Batch processing with Gemini Embedding API
                vectors = []
                batch_size = 16
                for i in range(0, len(texts), batch_size):
                    batch = texts[i : i + batch_size]
                    response = self._client.models.embed_content(
                        model=self.model_name,
                        contents=batch,
                    )
                    for emb in response.embeddings:
                        vectors.append(emb.values)
                return vectors
            except Exception as e:
                print(f"[GeminiEmbedder] Cloud embedding failed, falling back to local deterministic embedding: {e}")

        # Deterministic offline fallback embedding (768-dim normalized vector)
        return [self._deterministic_fallback_embed(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        """Generates an embedding vector for a single query or marketing draft."""
        results = self.embed_documents([text])
        if results:
            return results[0]
        return self._deterministic_fallback_embed(text)

    def _deterministic_fallback_embed(self, text: str) -> List[float]:
        """
        Generates a deterministic, normalized 768-dimensional pseudo-embedding
        derived from character n-grams and token frequencies.
        Guarantees that cosine similarity in ChromaDB works predictably offline.
        """
        vec = [0.0] * self.embedding_dim
        if not text:
            vec[0] = 1.0
            return vec

        tokens = text.lower().split()
        for idx, token in enumerate(tokens):
            # Primary word hash
            h1 = int(hashlib.md5(token.encode('utf-8')).hexdigest(), 16) % self.embedding_dim
            vec[h1] += 1.0 / (1.0 + math.log(idx + 1))

            # Bigram hash for phrase awareness
            if idx > 0:
                bigram = f"{tokens[idx-1]}_{token}"
                h2 = int(hashlib.sha256(bigram.encode('utf-8')).hexdigest(), 16) % self.embedding_dim
                vec[h2] += 1.5

        # L2 Normalize
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0.0:
            vec = [x / norm for x in vec]
        else:
            vec[0] = 1.0

        return vec
