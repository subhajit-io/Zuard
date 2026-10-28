import os
import re
import shutil
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Query, Header
from fastapi.responses import JSONResponse

from vault.brand_vault import BrandVault
from vault.project_manager import MultiProjectManager
from workers.orchestrator import StaticAuditOrchestrator
from synthesizer.delta_synthesizer import DeltaSynthesizer
from synthesizer.models import (
    AuditRequest,
    AuditResponse,
    ReviewActionRequest,
    SubmissionCreateRequest,
    SubmissionDecisionRequest
)
from vault.submissions_db import SubmissionsDatabase
from .telemetry import GovernanceTelemetry
import config as config

router = APIRouter(prefix="/api")

# Multi-project manager, submissions DB, and telemetry
project_manager = MultiProjectManager()
submissions_db = SubmissionsDatabase(config.DB_PATH)
telemetry = GovernanceTelemetry()

def check_reviewer_role(x_zuard_role: Optional[str] = None, role_param: Optional[str] = None):
    """Enforces that administrative and governance actions require Central Reviewer authority."""
    role = x_zuard_role or role_param
    if role and role.strip().lower() == "creator":
        raise HTTPException(
            status_code=403,
            detail="Permission Denied: Central Reviewer authority required for this operation. Creators do not have administrative or decision permissions."
        )


@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Zuard Static RAG Pipeline",
        "version": "1.0.0",
        "privacy_mode": "Local Edge" if config.LOCAL_PRIVACY_MODE or not config.GEMINI_API_KEY else f"Cloud Gemini ({config.GEMINI_MODEL})",
        "multi_project_enabled": True
    }

@router.get("/projects")
def list_projects():
    """Returns all project workspaces with their metadata and statistics."""
    return project_manager.list_projects()

@router.post("/projects")
async def create_project(
    project_id: str = Form(...),
    name: str = Form(...),
    description: Optional[str] = Form(""),
    persona: Optional[str] = Form("Standard Corporate"),
    guidelines_file: Optional[UploadFile] = File(None),
    x_zuard_role: Optional[str] = Header(None)
):
    check_reviewer_role(x_zuard_role)
    """Creates a new isolated project brand workspace with its own guidelines and static workers."""
    temp_file_path = None
    if guidelines_file:
        temp_dir = config.BASE_DIR / ".tmp_guidelines"
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_file_path = temp_dir / guidelines_file.filename
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(guidelines_file.file, buffer)

    res = project_manager.create_project(
        project_id=project_id,
        name=name,
        description=description or "",
        persona=persona or "",
        guideline_file=temp_file_path
    )
    return res

@router.get("/vault")
def get_vault_data(
    project_id: str = "default",
    x_zuard_role: Optional[str] = Header(None)
):
    """Returns the Brand Vault for a specific project workspace. Restricted to Central Reviewers."""
    check_reviewer_role(x_zuard_role)
    clean_id = project_id if isinstance(project_id, str) else "default"
    vault = project_manager.get_vault(clean_id)
    return {
        "project_id": project_id,
        "summary": vault.get_vault_summary(),
        "approved_facts": vault.facts_db.get_all_facts(),
        "terminology_rules": vault.get_terms(),
        "color_palette": vault.get_palette(),
        "visual_rules": vault.get_visual_config()
    }

@router.post("/clear-vault")
def clear_vault_data(project_id: str = Form("default"), x_zuard_role: Optional[str] = Header(None)):
    check_reviewer_role(x_zuard_role)
    """Wipes all brand guidelines, facts, terminology, and colors for a workspace."""
    vault = project_manager.get_vault(project_id)
    orch = project_manager.get_orchestrator(project_id)
    result = vault.clear_all_guidelines()
    if orch:
        orch.re_instruct_workers()
    return result

@router.post("/upload-guidelines")
async def upload_guidelines(
    file: UploadFile = File(...),
    project_id: str = Form("default"),
    x_zuard_role: Optional[str] = Header(None)
):
    check_reviewer_role(x_zuard_role)
    """
    Dynamically ingests a Brand Guidelines PDF or document into a specific project workspace,
    extracts rules/facts/colors, updates that project's Branched RAG,
    and re-instructs that project's 4 static workers in real-time.
    """
    vault = project_manager.get_vault(project_id)
    orch = project_manager.get_orchestrator(project_id)

    temp_dir = config.BASE_DIR / ".tmp_guidelines"
    temp_dir.mkdir(parents=True, exist_ok=True)
    file_path = temp_dir / file.filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    result = vault.ingest_new_guideline_document(file_path, orchestrator=orch)
    result["project_id"] = project_id
    return result

@router.post("/audit-content", response_model=AuditResponse)
async def audit_content(req: AuditRequest):
    project_id = req.project_id or "default"
    orchestrator = project_manager.get_orchestrator(project_id)
    synthesizer = project_manager.get_synthesizer(project_id)

    # Auto-derive document title from content if omitted or empty
    doc_title = (req.document_title or "").strip()
    if not doc_title or doc_title.lower() in ["untitled_draft", "untitled draft", "draft", ""]:
        lines = [ln.strip() for ln in req.content_text.splitlines() if ln.strip()]
        if lines:
            first_line = re.sub(r'^[#*>\s]+', '', lines[0]).strip()
            doc_title = (first_line[:47] + "...") if len(first_line) > 50 else (first_line or "Draft Copy")
        else:
            doc_title = "Draft Copy"
    req.document_title = doc_title

    # Convert color_pairs format if present
    c_pairs = None
    if req.color_pairs:
        c_pairs = [(p[0], p[1]) for p in req.color_pairs if len(p) >= 2]

    # Resolve image path if specified
    img_path = None
    if req.image_filename:
        possible_path = Path(req.image_filename)
        if not possible_path.is_absolute():
            possible_path = config.BASE_DIR / req.image_filename
        if possible_path.exists():
            img_path = possible_path

    # Step 1: Run 4 parallel static workers against this project's rules in ~2ms
    static_result = await orchestrator.run_parallel_audit(
        draft_text=req.content_text,
        image_path=img_path,
        color_pairs=c_pairs,
        alt_texts=req.alt_texts
    )

    # Step 2: Delta-Only synthesis (minimal token payload + project RAG citations)
    audit_resp = synthesizer.synthesize(
        document_title=req.document_title,
        original_text=req.content_text,
        static_audit_result=static_result,
        privacy_mode_override=req.privacy_mode,
        project_id=project_id
    )

    # Step 3: Record telemetry
    telemetry.record_audit(audit_resp.model_dump())

    return audit_resp

@router.post("/audit-upload")
async def audit_upload(
    file: UploadFile = File(...),
    project_id: Optional[str] = Form("default"),
    document_title: Optional[str] = Form(None),
    privacy_mode: Optional[bool] = Form(False)
):
    p_id = project_id or "default"
    vault = project_manager.get_vault(p_id)
    orchestrator = project_manager.get_orchestrator(p_id)
    synthesizer = project_manager.get_synthesizer(p_id)

    title = document_title or file.filename
    temp_dir = config.BASE_DIR / ".tmp_uploads"
    temp_dir.mkdir(parents=True, exist_ok=True)
    file_path = temp_dir / file.filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    content_text = ""
    image_path = None

    suffix = file_path.suffix.lower()
    if suffix in [".txt", ".md", ".html", ".htm", ".json", ".csv"]:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content_text = f.read()
    elif suffix == ".pdf":
        chunks = vault.indexer.parse_pdf_file(file_path)
        content_text = "\n\n".join([c["content"] for c in chunks])
    elif suffix in [".png", ".jpg", ".jpeg", ".webp"]:
        image_path = file_path
        content_text = f"Uploaded visual banner: {file.filename}"
    else:
        raise HTTPException(status_code=400, detail="Unsupported file format.")

    static_result = await orchestrator.run_parallel_audit(
        draft_text=content_text,
        image_path=image_path
    )

    audit_resp = synthesizer.synthesize(
        document_title=title,
        original_text=content_text,
        static_audit_result=static_result,
        privacy_mode_override=privacy_mode,
        project_id=p_id
    )

    telemetry.record_audit(audit_resp.model_dump())
    return audit_resp

@router.post("/review-action")
def review_action(req: ReviewActionRequest, x_zuard_role: Optional[str] = Header(None)):
    if req.action.upper() == "OVERRIDE":
        check_reviewer_role(x_zuard_role, req.reviewer_role)
    telemetry.record_action(req.model_dump())
    return {
        "status": "SUCCESS",
        "project_id": req.project_id,
        "flag_id": req.flag_id,
        "recorded_action": req.action,
        "role": req.reviewer_role,
        "message": f"Action {req.action} recorded for flag {req.flag_id} in project {req.project_id}."
    }

@router.get("/analytics")
def get_analytics():
    return telemetry.get_insights()

@router.post("/analytics/clear")
def clear_analytics(x_zuard_role: Optional[str] = Header(None)):
    check_reviewer_role(x_zuard_role)
    telemetry.clear()
    return {"status": "SUCCESS", "message": "Telemetry metrics cleared"}

# =========================================================================
# Two-Sided Architecture: Creator <-> Central Reviewer Submissions
# =========================================================================

@router.get("/submissions")
def list_submissions(
    project_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50)
):
    """List submissions for Creator tracking or Central Reviewer governance queue."""
    return submissions_db.list_submissions(project_id=project_id, status=status, limit=limit)

@router.post("/submissions")
async def create_submission(req: SubmissionCreateRequest):
    """
    Creator submits a draft and its pre-screen audit results to the Central Reviewer.
    """
    p_id = req.project_id or "default"

    # Auto-derive document title from content if omitted or empty
    doc_title = (req.title or "").strip()
    if not doc_title or doc_title.lower() in ["untitled_draft", "untitled draft", "draft", "untitled campaign", ""]:
        lines = [ln.strip() for ln in req.content_text.splitlines() if ln.strip()]
        if lines:
            first_line = re.sub(r'^[#*>\s]+', '', lines[0]).strip()
            doc_title = (first_line[:47] + "...") if len(first_line) > 50 else (first_line or "Draft Copy")
        else:
            doc_title = "Draft Copy"
    req.title = doc_title

    creator = (req.creator_name or "").strip()
    if not creator:
        req.creator_name = "Content Creator"

    # If audit_data was not supplied, we can run a quick audit
    audit_data = req.audit_data
    comp_score = req.compliance_score
    viol_count = req.violations_count

    if not audit_data:
        try:
            orchestrator = project_manager.get_orchestrator(p_id)
            synthesizer = project_manager.get_synthesizer(p_id)
            static_res = await orchestrator.run_parallel_audit(draft_text=req.content_text)
            audit_resp = synthesizer.synthesize(
                document_title=req.title,
                original_text=req.content_text,
                static_audit_result=static_res,
                project_id=p_id
            )
            audit_data = audit_resp.model_dump()
            comp_score = float(audit_resp.compliance_score)
            viol_count = int(audit_resp.total_violations_count)
        except Exception as e:
            audit_data = {"error": str(e)}

    sub = submissions_db.create_submission(
        project_id=p_id,
        title=req.title,
        content_text=req.content_text,
        creator_name=req.creator_name or "Creator",
        notes=req.notes or "",
        compliance_score=comp_score or 0.0,
        violations_count=viol_count or 0,
        audit_data=audit_data,
        status="PENDING_REVIEW"
    )

    # Record in telemetry
    telemetry.record_action({
        "action": "SUBMIT_FOR_REVIEW",
        "project_id": p_id,
        "submission_id": sub["id"],
        "reviewer_role": "Creator",
        "creator_name": req.creator_name
    })

    return sub

@router.get("/submissions/{sub_id}")
def get_submission(sub_id: str):
    """Retrieve full details of a single submission for inspection."""
    sub = submissions_db.get_submission(sub_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found.")
    return sub

@router.post("/submissions/{sub_id}/decision")
def make_submission_decision(sub_id: str, req: SubmissionDecisionRequest, x_zuard_role: Optional[str] = Header(None)):
    check_reviewer_role(x_zuard_role)
    """
    Central Reviewer (Admin) records an official decision:
    - APPROVE
    - REQUEST_CHANGES
    - OVERRIDE
    """
    sub = submissions_db.get_submission(sub_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found.")

    updated = submissions_db.record_decision(
        sub_id=sub_id,
        action=req.action,
        reviewer_name=req.reviewer_name or "Central Reviewer",
        feedback_notes=req.feedback_notes or "",
        justification=req.justification or ""
    )

    # Record in telemetry
    telemetry.record_action({
        "action": f"DECISION_{req.action.upper()}",
        "project_id": sub.get("project_id", "default"),
        "submission_id": sub_id,
        "reviewer_role": "Central Reviewer",
        "notes": req.feedback_notes or req.justification
    })

    return {
        "status": "SUCCESS",
        "submission": updated,
        "message": f"Submission {sub_id} marked as {updated.get('status')} by {req.reviewer_name}"
    }

@router.delete("/submissions/{sub_id}")
def delete_submission(sub_id: str, x_zuard_role: Optional[str] = Header(None)):
    check_reviewer_role(x_zuard_role)
    """Delete a submission."""
    success = submissions_db.delete_submission(sub_id)
    if not success:
        raise HTTPException(status_code=404, detail="Submission not found.")
    return {"status": "SUCCESS", "message": f"Submission {sub_id} deleted."}

@router.get("/submissions-stats")
def get_submission_stats(project_id: Optional[str] = Query(None)):
    """Returns counts for Pending, Approved, and Changes Requested."""
    return submissions_db.get_stats(project_id=project_id)

@router.delete("/projects/{project_id}")
def delete_workspace(project_id: str, x_zuard_role: Optional[str] = Header(None)):
    check_reviewer_role(x_zuard_role)
    success = project_manager.delete_project(project_id)
    if not success:
        raise HTTPException(status_code=404, detail="Workspace not found.")
    return {"status": "SUCCESS", "message": f"Workspace '{project_id}' deleted."}
