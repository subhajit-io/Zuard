from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class GuidelineUploadResponse(BaseModel):
    status: Literal["success", "error", "partial"]
    filename: str
    document_name: str
    pages_processed: int
    chunks_indexed: int
    duplicates_skipped: int = 0
    collection: str = "brand_guidelines"
    message: str

class ReviewIssue(BaseModel):
    type: str = Field(..., description="Category of issue, e.g. Unsupported Claim, Inconsistent Brand Tone, Incorrect Terminology")
    severity: Literal["high", "medium", "low"] = Field("medium", description="Severity level")
    explanation: str = Field(..., description="Why this content violates approved brand guidelines")
    guideline_reference: str = Field(..., description="Citation to approved guidelines, e.g. 'Brand Guidelines, page 3 (Section 1.2)'")
    suggestion: str = Field(..., description="Actionable replacement or remediation recommendation")

class ReviewResponse(BaseModel):
    status: Literal["compliant", "needs_revision", "insufficient_evidence"]
    issues: List[ReviewIssue] = Field(default_factory=list)
    summary: str
    retrieved_guidelines_count: int = 0
    retrieved_references: List[str] = Field(default_factory=list)

class TextReviewRequest(BaseModel):
    content_text: str = Field(..., min_length=1, description="Marketing copy or digital content to review")
    project_id: Optional[str] = Field("zuard-enterprise", description="Isolated project workspace ID")
    document_title: Optional[str] = Field(None, description="Optional title or headline of the collateral")
