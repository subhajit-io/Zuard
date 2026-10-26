from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class InspectorCard(BaseModel):
    flag_id: str
    dimension: str # tone, terminology, facts, claims, visual, accessibility
    severity: str # CRITICAL, WARNING, INFO
    original_snippet: str
    context_sentence: Optional[str] = ""
    issue_explanation: str
    suggested_rewrite: str
    cited_source: str # e.g. "Approved Fact Sheet ID #F-104 & Brand Guide p.12, Sec 3.1"
    ai_disclosure: str # e.g. "Verified by Static Worker #2 + Rewritten by Gemini 2.5 Flash"
    confidence_score: float = 1.0
    allowed_actions: List[str] = ["ACCEPT", "EDIT", "OVERRIDE"]
    status: str = "PENDING" # PENDING, ACCEPTED, EDITED, OVERRIDDEN
    override_reason: Optional[str] = None

class AuditRequest(BaseModel):
    project_id: Optional[str] = "zuard-enterprise"
    document_title: str = "Untitled_Draft"
    content_text: str
    image_filename: Optional[str] = None
    color_pairs: Optional[List[List[str]]] = None # [["#FFFFFF", "#FF0055"]]
    alt_texts: Optional[List[Dict[str, str]]] = None # [{"alt": "...", "asset_name": "banner"}]
    privacy_mode: Optional[bool] = False # True = 100% local edge offline mode

class ReviewActionRequest(BaseModel):
    project_id: Optional[str] = "zuard-enterprise"
    flag_id: str
    action: str # ACCEPT, EDIT, OVERRIDE
    edited_text: Optional[str] = None
    override_justification: Optional[str] = None
    reviewer_role: str = "Creator" # Creator, Reviewer, Manager

class AuditResponse(BaseModel):
    project_id: str = "zuard-enterprise"
    document_title: str
    status: str # DRAFT, IN_REVIEW, CHANGES_REQUESTED, APPROVED
    compliance_score: int # 0 to 100
    execution_time_ms: float
    privacy_mode: str # "Cloud (Gemini 2.5 Flash)" or "Confidential Local Mode"
    flagged_draft_markup: str
    original_text: str
    suggested_full_rewrite: str
    total_violations_count: int
    dimension_breakdown: Dict[str, int]
    inspector_cards: List[InspectorCard]
    metrics: Dict[str, Any]
    worker_latencies_ms: Dict[str, float]
