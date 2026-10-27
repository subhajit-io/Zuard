import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
import config as config
from .embeddings import GeminiEmbedder

class ChromaService:
    """
    Manages vector storage and similarity retrieval for brand guidelines in ChromaDB.
    Ensures persistent storage, deduplication, and consistent Gemini embeddings.
    """

    def __init__(
        self,
        persist_dir: Optional[Path] = None,
        collection_name: str = "brand_guidelines",
        embedder: Optional[GeminiEmbedder] = None
    ):
        self.persist_dir = persist_dir or getattr(config, "CHROMA_PERSIST_DIR", config.VAULT_DIR / "chroma_db")
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name
        self.embedder = embedder or GeminiEmbedder()

        # Initialize persistent ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={
                "hnsw:space": "cosine",
                "description": "Company-approved brand guidelines vector collection"
            }
        )

    def index_chunks(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Indexes chunks into ChromaDB with embeddings and source metadata.
        Prevents duplicate indexing using deterministic chunk IDs and content hashes.
        """
        if not chunks:
            return {"total_chunks": 0, "indexed": 0, "duplicates_skipped": 0}

        # Check existing IDs in collection to prevent duplicate indexing
        chunk_ids = [c["chunk_id"] for c in chunks]
        existing_data = self.collection.get(ids=chunk_ids)
        existing_ids = set(existing_data.get("ids", []))

        new_chunks = [c for c in chunks if c["chunk_id"] not in existing_ids]
        duplicates_skipped = len(chunks) - len(new_chunks)

        if not new_chunks:
            return {
                "total_chunks": len(chunks),
                "indexed": 0,
                "duplicates_skipped": duplicates_skipped
            }

        # Generate embeddings for new chunks using Gemini Embedding API
        texts = [c["text"] for c in new_chunks]
        embeddings = self.embedder.embed_documents(texts)

        ids = [c["chunk_id"] for c in new_chunks]
        metadatas = [c["metadata"] for c in new_chunks]

        # ChromaDB requires all metadata values to be str, int, float, or bool
        sanitized_metadatas = []
        for m in metadatas:
            clean_m = {}
            for k, v in m.items():
                if isinstance(v, (str, int, float, bool)):
                    clean_m[k] = v
                else:
                    clean_m[k] = str(v)
            sanitized_metadatas.append(clean_m)

        self.collection.add(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=sanitized_metadatas
        )

        return {
            "total_chunks": len(chunks),
            "indexed": len(new_chunks),
            "duplicates_skipped": duplicates_skipped
        }

    def retrieve(self, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        """
        Performs vector similarity search against ChromaDB using the Gemini Embedding API.
        Returns top matching approved guideline chunks with doc_name and page references.
        """
        if not query or not query.strip():
            return []

        count = self.collection.count()
        if count == 0:
            return []

        # Generate embedding for the query using the consistent embedder
        query_vector = self.embedder.embed_query(query.strip())
        k = min(top_k, count)

        res = self.collection.query(
            query_embeddings=[query_vector],
            n_results=k,
            include=["documents", "metadatas", "distances"]
        )

        results: List[Dict[str, Any]] = []
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        dists = res.get("distances", [[]])[0]

        for idx, doc_text in enumerate(docs):
            meta = metas[idx] if idx < len(metas) else {}
            dist = dists[idx] if idx < len(dists) else 0.0

            # Convert distance to normalized similarity score [0.0, 1.0]
            similarity = round(1.0 / (1.0 + max(0.0, float(dist))), 4) if dist is not None else 1.0

            doc_name = meta.get("doc_name", "Brand Guidelines")
            page_num = meta.get("page_number", 1)
            section = meta.get("section", "General")

            citation = f"{doc_name}, page {page_num} ({section})"

            results.append({
                "doc_name": doc_name,
                "page_number": page_num,
                "section": section,
                "citation": citation,
                "content": doc_text,
                "score": similarity,
                "metadata": meta
            })

        return results

    def get_stats(self) -> Dict[str, Any]:
        """Returns collection stats for telemetry and diagnostics."""
        count = self.collection.count()
        return {
            "collection_name": self.collection_name,
            "total_chunks": count,
            "persist_directory": str(self.persist_dir)
        }

    def reset_collection(self):
        """Clears collection for testing."""
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={
                "hnsw:space": "cosine",
                "description": "Company-approved brand guidelines vector collection"
            }
        )

