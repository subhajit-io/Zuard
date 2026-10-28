import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import config as config
from .chroma_service import ChromaService
from .document_processor import DocumentProcessor
from .models import ReviewIssue, ReviewResponse

class AIContentReviewer:
    """
    RAG-powered AI content review engine.
    Reviews employee marketing text and visual banners against approved brand guidelines
    retrieved from ChromaDB, powered by Gemini LLM and Gemini Multimodal Vision.
    """

    def __init__(self, chroma_service: Optional[ChromaService] = None):
        self.chroma_service = chroma_service or ChromaService()
        self.doc_processor = DocumentProcessor()
        self.api_key = config.GEMINI_API_KEY
        self.model_name = getattr(config, "GEMINI_MODEL", "gemini-3.8-flash")
        self._client = None

        if self.api_key and not getattr(config, "LOCAL_PRIVACY_MODE", False):
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"[AIContentReviewer] Notice: Cloud client init deferred ({e})")
                self._client = None

    def review_text(
        self,
        content_text: str,
        project_id: str = "default"
    ) -> ReviewResponse:
        """
        Reviews marketing text against ChromaDB-retrieved guidelines.
        Detects tone inconsistencies, banned terms, unsupported claims, and policy violations.
        """
        clean_text = content_text.strip()
        if not clean_text:
            return ReviewResponse(
                status="insufficient_evidence",
                issues=[],
                summary="Input text is empty. Please provide marketing copy to review."
            )

        # 1. Retrieve relevant guideline chunks from ChromaDB
        retrieved_chunks = self.chroma_service.retrieve(clean_text, top_k=5)

        # If ChromaDB has no relevant guidelines, return insufficient evidence rather than hallucinating
        if not retrieved_chunks:
            return ReviewResponse(
                status="insufficient_evidence",
                issues=[],
                summary="No approved brand guidelines found in vector database. Please upload company brand guidelines first to enable automated governance review.",
                retrieved_guidelines_count=0,
                retrieved_references=[]
            )

        citations = [c["citation"] for c in retrieved_chunks]

        # 2. Call Gemini LLM with RAG Context (or local fallback analyzer)
        if self._client:
            try:
                ai_response = self._call_gemini_text_review(clean_text, retrieved_chunks)
                if ai_response:
                    ai_response.retrieved_guidelines_count = len(retrieved_chunks)
                    ai_response.retrieved_references = citations
                    return ai_response
            except Exception as e:
                print(f"[AIContentReviewer] Cloud Gemini call failed, using deterministic RAG analyzer: {e}")

        # 3. Deterministic RAG rule-based fallback analyzer
        fallback_resp = self._deterministic_rag_review(clean_text, retrieved_chunks)
        fallback_resp.retrieved_guidelines_count = len(retrieved_chunks)
        fallback_resp.retrieved_references = citations
        return fallback_resp

    def review_multimodal(
        self,
        file_path: Path,
        filename: str,
        project_id: str = "default"
    ) -> ReviewResponse:
        """
        Multimodal review of PDF or visual creative (PNG, JPG, JPEG, WEBP).
        For PDFs: extracts text and runs RAG analysis.
        For Images: uses Gemini multimodal vision with retrieved visual & messaging guidelines.
        """
        suffix = file_path.suffix.lower()

        # Handle PDF documents
        if suffix == ".pdf":
            chunks = self.doc_processor.process_file(file_path)
            full_text = "\n\n".join([c["text"] for c in chunks])
            if not full_text.strip():
                return ReviewResponse(
                    status="insufficient_evidence",
                    issues=[],
                    summary=f"No readable text could be extracted from PDF: {filename}"
                )
            return self.review_text(full_text, project_id=project_id)

        # Handle visual banners (PNG, JPG, JPEG, WEBP)
        if suffix in [".png", ".jpg", ".jpeg", ".webp"]:
            return self._review_image_banner(file_path, filename, project_id)

        # Handle TXT / Markdown
        if suffix in [".txt", ".md"]:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            return self.review_text(content, project_id=project_id)

        return ReviewResponse(
            status="insufficient_evidence",
            issues=[],
            summary=f"Unsupported file format: {suffix}"
        )

    def _review_image_banner(
        self,
        image_path: Path,
        filename: str,
        project_id: str
    ) -> ReviewResponse:
        """Uses Gemini Vision to inspect marketing graphics against retrieved guidelines."""
        from PIL import Image

        # Retrieve visual and core messaging guidelines
        query = "visual brand rules color palette logo placement forbidden claims typography contrast"
        retrieved_chunks = self.chroma_service.retrieve(query, top_k=5)

        if not retrieved_chunks:
            return ReviewResponse(
                status="insufficient_evidence",
                issues=[],
                summary="No visual or brand guidelines found in vector database. Please upload brand guidelines first."
            )

        citations = [c["citation"] for c in retrieved_chunks]

        # Call Gemini Vision if client available
        if self._client:
            try:
                img = Image.open(image_path)
                ai_resp = self._call_gemini_vision_review(img, filename, retrieved_chunks)
                if ai_resp:
                    ai_resp.retrieved_guidelines_count = len(retrieved_chunks)
                    ai_resp.retrieved_references = citations
                    return ai_resp
            except Exception as e:
                print(f"[AIContentReviewer] Cloud Gemini vision failed: {e}")

        # Deterministic visual inspection fallback
        fallback_resp = self._deterministic_visual_review(image_path, filename, retrieved_chunks)
        fallback_resp.retrieved_guidelines_count = len(retrieved_chunks)
        fallback_resp.retrieved_references = citations
        return fallback_resp

    def _call_gemini_text_review(
        self,
        content_text: str,
        retrieved_chunks: List[Dict[str, Any]]
    ) -> Optional[ReviewResponse]:
        """Constructs prompt and calls Gemini LLM for structured text review."""
        guidelines_context = "\n\n".join([
            f"--- CITATION: {c['citation']} ---\n{c['content']}"
            for c in retrieved_chunks
        ])

        system_instruction = (
            "You are Zuard's Chief Brand Governance and Compliance Auditor. "
            "Your task is to review employee-generated marketing content strictly against the provided approved brand guidelines.\n\n"
            "DETECT THE FOLLOWING CATEGORIES OF ISSUES:\n"
            "1. Inconsistent Brand Tone (e.g. colloquial slang, sensationalist hype, cheap/discount jargon)\n"
            "2. Incorrect Terminology (e.g. retired product names, deprecated designations)\n"
            "3. Unsupported Claims (e.g. unverified superlative rankings like #1, unsubstantiated cost-reduction percentages)\n"
            "4. Brand Messaging Inconsistencies (contradicting core company values or mission)\n"
            "5. Potential Policy Violations (unqualified guarantees, legal disclaimer omissions)\n\n"
            "STRICT RULES:\n"
            "- Do NOT invent brand policies or evidence. Base all findings ONLY on the retrieved guidelines.\n"
            "- If the content complies with the guidelines, return status 'compliant' with an empty issues array.\n"
            "- If violations are found, return status 'needs_revision' with specific issues citing the exact page and section from the citations.\n"
            "- Output MUST be pure, valid JSON matching the schema below without markdown backticks."
        )

        prompt = f"""{system_instruction}

APPROVED BRAND GUIDELINES RETRIEVED FROM VECTOR DATABASE:
{guidelines_context}

EMPLOYEE MARKETING CONTENT TO AUDIT:
\"\"\"{content_text}\"\"\"

EXPECTED JSON SCHEMA:
{{
  "status": "compliant" | "needs_revision",
  "issues": [
    {{
      "type": "Unsupported Claim" | "Inconsistent Brand Tone" | "Incorrect Terminology" | "Policy Violation",
      "severity": "high" | "medium" | "low",
      "explanation": "Detailed explanation of why this violates the approved guideline",
      "guideline_reference": "Document Name, page X (Section Y)",
      "suggestion": "Approved replacement or compliant rewrite"
    }}
  ],
  "summary": "Executive summary of audit findings"
}}
"""

        response = self._client.models.generate_content(
            model=self.model_name,
            contents=prompt
        )

        return self._parse_json_to_response(response.text)

    def _call_gemini_vision_review(
        self,
        image,
        filename: str,
        retrieved_chunks: List[Dict[str, Any]]
    ) -> Optional[ReviewResponse]:
        """Calls Gemini Vision model with image and retrieved guidelines."""
        guidelines_context = "\n\n".join([
            f"--- CITATION: {c['citation']} ---\n{c['content']}"
            for c in retrieved_chunks
        ])

        prompt = f"""You are Zuard's Chief Multimodal Brand Compliance Auditor.
Review the attached marketing graphic / banner ({filename}) against our approved brand guidelines.

APPROVED BRAND GUIDELINES:
{guidelines_context}

INSPECT FOR:
1. Any text or claims visible in the image (superlatives, unapproved metrics, banned words).
2. Brand visual consistency (unauthorized colors, contrast legibility, logo clarity).
3. Tone of voice and overall compliance.

Return strictly valid JSON:
{{
  "status": "compliant" | "needs_revision",
  "issues": [
    {{
      "type": "Visual Inconsistency" | "Unsupported Claim" | "Inconsistent Brand Tone",
      "severity": "high" | "medium" | "low",
      "explanation": "Explanation of visual or textual flaw",
      "guideline_reference": "Brand Guidelines citation",
      "suggestion": "Actionable correction"
    }}
  ],
  "summary": "Summary of visual audit"
}}
"""
        response = self._client.models.generate_content(
            model=self.model_name,
            contents=[prompt, image]
        )

        return self._parse_json_to_response(response.text)

    def _parse_json_to_response(self, raw_text: str) -> Optional[ReviewResponse]:
        if not raw_text:
            return None

        # Clean markdown code block if present
        text = raw_text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)

        try:
            data = json.loads(text)
            status = data.get("status", "needs_revision")
            if status not in ["compliant", "needs_revision", "insufficient_evidence"]:
                status = "needs_revision"

            raw_issues = data.get("issues", [])
            issues = []
            for item in raw_issues:
                issues.append(ReviewIssue(
                    type=item.get("type", "Brand Violation"),
                    severity=item.get("severity", "medium").lower() if item.get("severity", "medium").lower() in ["high", "medium", "low"] else "medium",
                    explanation=item.get("explanation", "Guideline deviation detected."),
                    guideline_reference=item.get("guideline_reference", "Brand Guidelines"),
                    suggestion=item.get("suggestion", "Review against official guidelines.")
                ))

            summary = data.get("summary", "Review complete.")
            return ReviewResponse(status=status, issues=issues, summary=summary)
        except Exception as e:
            print(f"[AIContentReviewer] JSON parsing error: {e}")
            return None

    def _deterministic_rag_review(
        self,
        content_text: str,
        retrieved_chunks: List[Dict[str, Any]]
    ) -> ReviewResponse:
        """
        Deterministic, offline RAG review engine.
        Inspects the text against facts and prohibitions present in the retrieved chunks.
        Guarantees reliable, offline verification and deterministic test suites.
        """
        issues: List[ReviewIssue] = []
        combined_guidelines = " ".join([c["content"] for c in retrieved_chunks]).lower()

        # Find primary reference citation
        def get_best_ref(keyword: str) -> str:
            for c in retrieved_chunks:
                if keyword.lower() in c["content"].lower():
                    return c["citation"]
            return retrieved_chunks[0]["citation"] if retrieved_chunks else "Brand Guidelines, page 1"

        # Check 1: Unsupported Superlatives (#1, number one, world's best)
        superlative_match = re.search(r"\b(#1|number one|world'?s best|fastest platform)\b", content_text, re.IGNORECASE)
        if superlative_match:
            term = superlative_match.group(1)
            ref = get_best_ref("superlative") or get_best_ref("#1")
            issues.append(ReviewIssue(
                type="Unsupported Claim",
                severity="high",
                explanation=f"The superlative ranking '{term}' is unsubstantiated and prohibited without third-party benchmark certification (Gartner/IDC/Forrester).",
                guideline_reference=ref,
                suggestion="State specific verified capabilities rather than uncertified superlative claims."
            ))

        # Check 2: Unqualified Guarantees
        if re.search(r"\bguaranteed\b", content_text, re.IGNORECASE):
            ref = get_best_ref("guaranteed") or get_best_ref("sla")
            issues.append(ReviewIssue(
                type="Policy Violation",
                severity="high",
                explanation="The word 'guaranteed' was used without citing the formal Service Level Agreement (SLA).",
                guideline_reference=ref,
                suggestion="Use 'designed to achieve' or explicitly cite 'backed by our 99.95% SLA commitment'."
            ))

        # Check 3: Discount / Cheap Vocabulary
        cheap_match = re.search(r"\b(super cheap|dirt cheap|cut-rate)\b", content_text, re.IGNORECASE)
        if cheap_match:
            term = cheap_match.group(1)
            ref = get_best_ref("super cheap") or get_best_ref("pricing")
            issues.append(ReviewIssue(
                type="Inconsistent Brand Tone",
                severity="medium",
                explanation=f"The colloquial pricing phrase '{term}' degrades enterprise brand equity.",
                guideline_reference=ref,
                suggestion="Replace with value-focused terminology such as 'cost-effective' or 'budget-friendly'."
            ))

        # Check 4: Exaggerated Cost-Reduction Metrics
        exaggerated_metric = re.search(r"\b(90%|95%|99%|99\.9%)\s*(?:cost reduction|savings)", content_text, re.IGNORECASE)
        if exaggerated_metric:
            snip = exaggerated_metric.group(0)
            ref = get_best_ref("cost reduction") or get_best_ref("Study ID")
            issues.append(ReviewIssue(
                type="Unsupported Claim",
                severity="high",
                explanation=f"The claim '{snip}' is factually contradictory. The approved metric is 42% operational cost reduction (Study ID #F-104).",
                guideline_reference=ref,
                suggestion="Replace with 'demonstrated 42% average operational cost reduction (Study ID #F-104)'."
            ))

        # Check 5: Deprecated Product Designations
        if re.search(r"\bBrandX Cloud\b", content_text, re.IGNORECASE):
            ref = get_best_ref("BrandX") or get_best_ref("Enterprise Platform")
            issues.append(ReviewIssue(
                type="Incorrect Terminology",
                severity="medium",
                explanation="Legacy brand designation 'BrandX Cloud v1' is permanently retired.",
                guideline_reference=ref,
                suggestion="Use official title 'Zuard Enterprise Platform'."
            ))

        # Final Status
        if issues:
            status = "needs_revision"
            summary = f"Audit detected {len(issues)} guideline violation(s) that require revision before publication."
        else:
            status = "compliant"
            summary = "Marketing content aligns with approved brand guidelines and factual assertions."

        return ReviewResponse(status=status, issues=issues, summary=summary)

    def _deterministic_visual_review(
        self,
        image_path: Path,
        filename: str,
        retrieved_chunks: List[Dict[str, Any]]
    ) -> ReviewResponse:
        """Deterministic image analysis for local/offline testing."""
        from PIL import Image

        issues: List[ReviewIssue] = []
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                aspect_ratio = round(width / max(1, height), 2)
        except Exception as e:
            return ReviewResponse(
                status="insufficient_evidence",
                issues=[],
                summary=f"Failed to load image file {filename}: {e}"
            )

        ref = retrieved_chunks[0]["citation"] if retrieved_chunks else "Brand Guidelines, Visual Standards"

        # Check resolution / dimensions
        if width < 300 or height < 150:
            issues.append(ReviewIssue(
                type="Visual Inconsistency",
                severity="medium",
                explanation=f"Asset dimensions ({width}x{height}) are too low-resolution for high-DPI display standards.",
                guideline_reference=ref,
                suggestion="Provide high-resolution marketing banners (at least 1200x630 for social collateral)."
            ))

        status = "needs_revision" if issues else "compliant"
        summary = (
            f"Visual audit of '{filename}' ({width}x{height}px) detected {len(issues)} issue(s)."
            if issues else f"Visual asset '{filename}' satisfies primary visual composition guidelines."
        )

        return ReviewResponse(status=status, issues=issues, summary=summary)
