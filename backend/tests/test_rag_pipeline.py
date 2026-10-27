import os
import sys
import unittest
from pathlib import Path
from io import BytesIO
from PIL import Image

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import config as config
from fastapi.testclient import TestClient
from api.app import app
from rag import (
    GeminiEmbedder,
    DocumentProcessor,
    ChromaService,
    AIContentReviewer,
)

class TestMultimodalRAGPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.test_chroma_dir = config.BASE_DIR / "vault" / ".test_chroma"
        cls.chroma_service = ChromaService(
            persist_dir=cls.test_chroma_dir,
            collection_name="test_brand_guidelines"
        )
        cls.chroma_service.reset_collection()
        cls.doc_processor = DocumentProcessor(chunk_size=400, chunk_overlap=50)
        cls.reviewer = AIContentReviewer(chroma_service=cls.chroma_service)

    @classmethod
    def tearDownClass(cls):
        try:
            import shutil
            if cls.test_chroma_dir.exists():
                shutil.rmtree(cls.test_chroma_dir, ignore_errors=True)
        except Exception:
            pass

    def test_01_document_processing_text_and_pdf(self):
        """Phase 1 & 2: Test PyMuPDF and LangChain text splitting with metadata."""
        sample_txt = config.SAMPLE_DATA_DIR / "brand_guidelines.txt"
        self.assertTrue(sample_txt.exists(), "brand_guidelines.txt sample file should exist")

        chunks = self.doc_processor.process_file(sample_txt)
        self.assertGreater(len(chunks), 5, "Should create multiple chunks from guidelines")
        
        first_chunk = chunks[0]
        self.assertIn("chunk_id", first_chunk)
        self.assertIn("text", first_chunk)
        self.assertIn("metadata", first_chunk)
        self.assertEqual(first_chunk["metadata"]["doc_name"], "brand_guidelines.txt")
        self.assertIn("page_number", first_chunk["metadata"])
        self.assertIn("content_hash", first_chunk["metadata"])
        print(f"✓ DocumentProcessor processed {len(chunks)} chunks with LangChain & page metadata.")

    def test_02_chroma_indexing_and_deduplication(self):
        """Phase 2: Test storing chunks and embeddings into ChromaDB with deduplication."""
        sample_txt = config.SAMPLE_DATA_DIR / "brand_guidelines.txt"
        chunks = self.doc_processor.process_file(sample_txt)

        # First indexing run
        res1 = self.chroma_service.index_chunks(chunks)
        self.assertEqual(res1["indexed"], len(chunks))
        self.assertEqual(res1["duplicates_skipped"], 0)

        # Duplicate indexing run should skip all existing chunks
        res2 = self.chroma_service.index_chunks(chunks)
        self.assertEqual(res2["indexed"], 0)
        self.assertEqual(res2["duplicates_skipped"], len(chunks))
        print(f"✓ ChromaDB indexed {res1['indexed']} chunks and prevented {res2['duplicates_skipped']} duplicates.")

    def test_03_rag_retrieval(self):
        """Phase 3: Test similarity search retrieving approved guideline chunks."""
        query = "super cheap pricing tier and cut-rate discounts"
        retrieved = self.chroma_service.retrieve(query, top_k=3)

        self.assertGreater(len(retrieved), 0, "Should retrieve at least one guideline chunk")
        top_match = retrieved[0]
        self.assertIn("citation", top_match)
        self.assertIn("content", top_match)
        self.assertGreater(top_match["score"], 0.0)
        
        # Check that pricing-related section was retrieved
        all_text = " ".join([m["content"] for m in retrieved]).lower()
        self.assertTrue(
            "super cheap" in all_text or "cost-effective" in all_text or "pricing" in all_text,
            "Retrieved chunks should include pricing guideline context"
        )
        print(f"✓ RAG Retrieval retrieved {len(retrieved)} relevant chunks. Top citation: {top_match['citation']}")

    def test_04_api_guideline_upload_endpoint(self):
        """Phase 2: Test POST /api/guidelines/upload API endpoint with TXT."""
        sample_txt = config.SAMPLE_DATA_DIR / "brand_guidelines.txt"
        with open(sample_txt, "rb") as f:
            file_bytes = f.read()

        import time
        unique_name = f"brand_policy_{int(time.time()*1000)}.txt"
        response = self.client.post(
            "/api/guidelines/upload",
            files={"file": (unique_name, BytesIO(file_bytes), "text/plain")},
            data={"project_id": "zuard-enterprise"}
        )

        self.assertEqual(response.status_code, 200, f"Upload API failed: {response.text}")
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["filename"], unique_name)
        self.assertGreater(data["pages_processed"], 0)
        self.assertGreater(data["chunks_indexed"], 0)
        print(f"✓ POST /api/guidelines/upload succeeded: {data['chunks_indexed']} chunks indexed.")


    def test_05_api_review_text_with_violations(self):
        """Phase 4: Test POST /api/review/text detecting unsupported claims and tone violations."""
        flagged_copy = (
            "Our #1 revolutionary AI tool offers super cheap monthly subscriptions "
            "and delivers a 99% cost reduction guaranteed!"
        )

        response = self.client.post(
            "/api/review/text",
            json={"content_text": flagged_copy, "project_id": "zuard-enterprise"}
        )

        self.assertEqual(response.status_code, 200, f"Review API failed: {response.text}")
        data = response.json()
        self.assertEqual(data["status"], "needs_revision")
        self.assertGreater(len(data["issues"]), 0, "Should detect violations")

        # Verify structured issue properties
        issue_types = [i["type"] for i in data["issues"]]
        self.assertTrue(
            any("Unsupported Claim" in t or "Brand Tone" in t or "Policy Violation" in t for t in issue_types),
            f"Expected issue types not found in: {issue_types}"
        )

        for issue in data["issues"]:
            self.assertIn("type", issue)
            self.assertIn("severity", issue)
            self.assertIn("explanation", issue)
            self.assertIn("guideline_reference", issue)
            self.assertIn("suggestion", issue)

        print(f"✓ POST /api/review/text correctly flagged {len(data['issues'])} issues with citations.")

    def test_06_api_review_text_compliant(self):
        """Phase 4: Test POST /api/review/text on fully compliant marketing text."""
        compliant_copy = (
            "Our cost-effective platform is designed to achieve an average 42% operational "
            "cost reduction across enterprise deployments (Study ID #F-104)."
        )

        response = self.client.post(
            "/api/review/text",
            json={"content_text": compliant_copy, "project_id": "zuard-enterprise"}
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "compliant")
        self.assertEqual(len(data["issues"]), 0)
        print("✓ POST /api/review/text validated compliant text with 0 violations.")

    def test_07_api_review_upload_image(self):
        """Phase 5: Test POST /api/review/upload with visual image banner."""
        # Create a test banner in memory
        img = Image.new("RGB", (800, 400), color=(14, 22, 40))
        img_bytes = BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        response = self.client.post(
            "/api/review/upload",
            files={"file": ("marketing_banner.png", img_bytes, "image/png")},
            data={"project_id": "zuard-enterprise"}
        )

        self.assertEqual(response.status_code, 200, f"Multimodal upload failed: {response.text}")
        data = response.json()
        self.assertIn(data["status"], ["compliant", "needs_revision"])
        self.assertIn("summary", data)
        print(f"✓ POST /api/review/upload successfully audited visual banner: status='{data['status']}'.")

    def test_08_error_handling_invalid_files_and_empty_input(self):
        """Phase 6: Test input validation and error responses."""
        # 1. Invalid file extension for guideline upload
        bad_file = BytesIO(b"malicious content")
        resp1 = self.client.post(
            "/api/guidelines/upload",
            files={"file": ("hack.exe", bad_file, "application/octet-stream")},
            data={"project_id": "zuard-enterprise"}
        )
        self.assertEqual(resp1.status_code, 400)
        self.assertIn("Unsupported file format", resp1.json()["detail"])

        # 2. Empty text review
        resp2 = self.client.post(
            "/api/review/text",
            json={"content_text": "   "}
        )
        self.assertEqual(resp2.status_code, 400)

        # 3. Empty file upload
        empty_file = BytesIO(b"")
        resp3 = self.client.post(
            "/api/guidelines/upload",
            files={"file": ("empty.txt", empty_file, "text/plain")}
        )
        self.assertEqual(resp3.status_code, 400)
        print("✓ Error handling verified: 400 Bad Request returned on invalid formats & empty inputs.")

    def test_09_insufficient_evidence_when_guidelines_missing(self):
        """Phase 4: Return 'insufficient_evidence' if no guidelines are in the vector DB."""
        isolated_chroma_dir = config.BASE_DIR / "vault" / ".empty_chroma"
        empty_chroma = ChromaService(persist_dir=isolated_chroma_dir, collection_name="empty_coll")
        empty_chroma.reset_collection()
        empty_reviewer = AIContentReviewer(chroma_service=empty_chroma)

        result = empty_reviewer.review_text("Our brand is the greatest.")
        self.assertEqual(result.status, "insufficient_evidence")
        self.assertEqual(len(result.issues), 0)
        self.assertIn("No approved brand guidelines found", result.summary)

        try:
            import shutil
            if isolated_chroma_dir.exists():
                shutil.rmtree(isolated_chroma_dir, ignore_errors=True)
        except Exception:
            pass
        print("✓ Insufficient evidence verification confirmed: returns 'insufficient_evidence' without hallucinating.")

if __name__ == "__main__":
    unittest.main()
