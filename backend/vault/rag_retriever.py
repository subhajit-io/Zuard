import math
from typing import List, Dict, Any, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class BranchedRAGRetriever:
    def __init__(self):
        self.chunks: List[Dict[str, Any]] = []
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix = None

    def index_chunks(self, chunks: List[Dict[str, Any]]):
        if not chunks:
            return
        self.chunks = chunks
        corpus = [f"{c['section']} {c['content']}" for c in chunks]
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            ngram_range=(1, 2),
            token_pattern=r"(?u)\b\w[\w-]*\w\b|\b\w+\b"
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(corpus)

    def retrieve(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        if not self.chunks or self.vectorizer is None or self.tfidf_matrix is None:
            return []
        
        query_clean = query.strip()
        if not query_clean:
            return []

        query_vec = self.vectorizer.transform([query_clean])
        scores = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        
        # Also compute keyword overlap boost
        query_words = set(query_clean.lower().split())
        results = []
        for idx, score in enumerate(scores):
            chunk = self.chunks[idx]
            chunk_text = f"{chunk['section']} {chunk['content']}".lower()
            overlap = sum(1 for w in query_words if len(w) > 3 and w in chunk_text)
            combined_score = float(score) + (overlap * 0.15)
            
            if combined_score > 0.05:
                results.append({
                    "doc_name": chunk["doc_name"],
                    "page_number": chunk["page_number"],
                    "section": chunk["section"],
                    "content": chunk["content"],
                    "score": round(combined_score, 4)
                })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def format_citation(self, match: Dict[str, Any]) -> str:
        doc = match.get("doc_name", "Brand Guide")
        page = match.get("page_number", 1)
        sec = match.get("section", "Guidelines")
        return f"{doc}, Page {page}, {sec}"
