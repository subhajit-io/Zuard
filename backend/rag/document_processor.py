import re
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Union
from langchain_text_splitters import RecursiveCharacterTextSplitter

class DocumentProcessor:
    """
    Extracts text from brand guideline documents (PDF, TXT, MD) using PyMuPDF,
    preserves page numbers and section headers, and splits text into semantic chunks
    using LangChain's RecursiveCharacterTextSplitter.
    """

    def __init__(self, chunk_size: int = 600, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n=== PAGE", "\nSection ", "\n\n", "\n", ". ", " ", ""]
        )

    def process_file(self, file_path: Union[str, Path]) -> List[Dict[str, Any]]:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        suffix = path.suffix.lower()
        if suffix == ".pdf":
            return self._process_pdf(path)
        elif suffix in [".txt", ".md"]:
            return self._process_text(path)
        else:
            raise ValueError(f"Unsupported file format '{suffix}'. Allowed: PDF, TXT, MD.")

    def _process_pdf(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extracts text page by page using PyMuPDF and chunks with LangChain."""
        import pymupdf
        doc_name = file_path.name
        chunks: List[Dict[str, Any]] = []

        doc = pymupdf.open(str(file_path))
        try:
            total_pages = len(doc)
            for page_idx in range(total_pages):
                page = doc[page_idx]
                page_num = page_idx + 1
                page_text = page.get_text("text") or ""
                page_text = page_text.strip()

                if not page_text:
                    continue

                page_chunks = self._chunk_page_text(doc_name, page_num, page_text)
                chunks.extend(page_chunks)
        finally:
            doc.close()

        return chunks

    def _process_text(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parses TXT/MD files, preserving page markers (=== PAGE X ===) if present."""
        doc_name = file_path.name
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            raw_text = f.read()

        chunks: List[Dict[str, Any]] = []
        page_splits = re.split(r"===\s*PAGE\s+(\d+)\s*===", raw_text, flags=re.IGNORECASE)

        if len(page_splits) > 1:
            for i in range(1, len(page_splits), 2):
                page_num = int(page_splits[i])
                page_content = page_splits[i + 1].strip()
                chunks.extend(self._chunk_page_text(doc_name, page_num, page_content))
        else:
            chunks.extend(self._chunk_page_text(doc_name, 1, raw_text.strip()))

        return chunks

    def _chunk_page_text(self, doc_name: str, page_num: int, text: str) -> List[Dict[str, Any]]:
        """Splits page text using LangChain and enriches with metadata and unique hash."""
        split_texts = self.splitter.split_text(text)
        results: List[Dict[str, Any]] = []

        # Find any section header in text
        current_section = "General Guidelines"
        sec_match = re.search(r"(Section\s+[\d\.]+\s*:[^\n]+)", text, re.IGNORECASE)
        if sec_match:
            current_section = sec_match.group(1).strip()

        for idx, chunk_text in enumerate(split_texts):
            clean_chunk = chunk_text.strip()
            if not clean_chunk:
                continue

            # Check if this specific chunk contains its own section header
            inner_sec = re.search(r"(Section\s+[\d\.]+\s*:[^\n]+)", clean_chunk, re.IGNORECASE)
            section_label = inner_sec.group(1).strip() if inner_sec else current_section

            # Generate deterministic hash for deduplication
            content_hash = hashlib.sha256(f"{doc_name}:{page_num}:{clean_chunk}".encode("utf-8")).hexdigest()
            chunk_id = f"{doc_name}_p{page_num}_c{idx}_{content_hash[:8]}"

            results.append({
                "chunk_id": chunk_id,
                "text": clean_chunk,
                "metadata": {
                    "doc_name": doc_name,
                    "page_number": int(page_num),
                    "section": section_label,
                    "chunk_index": idx,
                    "content_hash": content_hash,
                }
            })

        return results
