import re
from pathlib import Path
from typing import List, Dict, Any

class GuidelinesIndexer:
    def __init__(self):
        pass

    def parse_text_file(self, file_path: Path) -> List[Dict[str, Any]]:
        if not file_path.exists():
            return []
        
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            raw_text = f.read()

        doc_name = file_path.name
        chunks = []
        
        # Split by page marker if present
        page_splits = re.split(r"===\s*PAGE\s+(\d+)\s*===", raw_text, flags=re.IGNORECASE)
        
        if len(page_splits) > 1:
            # We have page splits: [preamble, page_num1, page_content1, page_num2, page_content2, ...]
            for i in range(1, len(page_splits), 2):
                page_num = int(page_splits[i])
                page_content = page_splits[i+1].strip()
                chunks.extend(self._chunk_page(doc_name, page_num, page_content))
        else:
            # Single document / no markers
            chunks.extend(self._chunk_page(doc_name, 1, raw_text))

        return chunks

    def parse_pdf_file(self, file_path: Path) -> List[Dict[str, Any]]:
        if not file_path.exists():
            return []
        
        chunks = []
        doc_name = file_path.name
        
        try:
            import pypdf
            reader = pypdf.PdfReader(str(file_path))
            for idx, page in enumerate(reader.pages):
                page_num = idx + 1
                page_text = page.extract_text() or ""
                if page_text.strip():
                    chunks.extend(self._chunk_page(doc_name, page_num, page_text))
        except Exception as e:
            print(f"Error reading PDF {file_path}: {e}")

        return chunks

    def _chunk_page(self, doc_name: str, page_num: int, page_text: str) -> List[Dict[str, Any]]:
        chunks = []
        # Look for section headers: Section X.Y: Title or Header patterns
        section_pattern = re.compile(r"(Section\s+[\d\.]+\s*:[^\n]+)", re.IGNORECASE)
        sections = section_pattern.split(page_text)
        
        if len(sections) > 1:
            current_section = "General Overview"
            for i in range(len(sections)):
                part = sections[i].strip()
                if not part:
                    continue
                if section_pattern.match(part):
                    current_section = part
                else:
                    chunks.append({
                        "chunk_id": f"{doc_name}_p{page_num}_s{len(chunks)+1}",
                        "doc_name": doc_name,
                        "page_number": page_num,
                        "section": current_section,
                        "content": part
                    })
        else:
            # Whole page chunk
            chunks.append({
                "chunk_id": f"{doc_name}_p{page_num}_s1",
                "doc_name": doc_name,
                "page_number": page_num,
                "section": f"Page {page_num}",
                "content": page_text
            })

        return chunks
