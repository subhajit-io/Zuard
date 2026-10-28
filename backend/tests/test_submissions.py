import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Add backend directory
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

import config
from vault.submissions_db import SubmissionsDatabase

def test_submissions_workflow():
    db = SubmissionsDatabase(config.DB_PATH)
    
    # 1. List submissions (seeds should exist)
    subs = db.list_submissions()
    print(f"Total initial submissions: {len(subs)}")
    assert len(subs) >= 3, "Expected at least 3 seeded submissions"
    
    # 2. Check stats
    stats = db.get_stats()
    print(f"Initial stats: {stats}")
    assert stats["total"] >= 3
    
    # 3. Create submission (Creator)
    created = db.create_submission(
        project_id="zuard-enterprise",
        title="Creator Spring Launch Campaign",
        content_text="Check out our guaranteed best AI system.",
        creator_name="Jordan (Creator Studio)",
        notes="Urgent review needed for Friday release",
        compliance_score=55.0,
        violations_count=2,
        audit_data={"flags": [{"issue": "Unsubstantiated claim 'guaranteed best'"}]}
    )
    print(f"Created submission: {created['id']} - status: {created['status']}")
    assert created["status"] == "PENDING_REVIEW"
    sub_id = created["id"]
    
    # 4. Record decision (Central Reviewer)
    decided = db.record_decision(
        sub_id=sub_id,
        action="REQUEST_CHANGES",
        reviewer_name="Elena Vance (Governance Lead)",
        feedback_notes="Please replace 'guaranteed best' with approved metric F-104."
    )
    print(f"Decided submission: {decided['id']} - status: {decided['status']}")
    assert decided["status"] == "CHANGES_REQUESTED"
    assert decided["reviewer_decision"]["reviewer_name"] == "Elena Vance (Governance Lead)"
    
    # 5. Overriding submission
    overridden = db.record_decision(
        sub_id=sub_id,
        action="OVERRIDE",
        reviewer_name="Legal Counsel",
        justification="Executive exception authorized under Q2 Memo."
    )
    assert overridden["status"] == "OVERRIDDEN"
    print(f"Overridden submission: {overridden['id']} - status: {overridden['status']}")
    
    # 6. Approve submission
    approved = db.record_decision(
        sub_id=sub_id,
        action="APPROVE",
        reviewer_name="Chief Brand Officer",
        feedback_notes="All revisions verified. Approved."
    )
    assert approved["status"] == "APPROVED"
    print(f"Approved submission: {approved['id']} - status: {approved['status']}")
    
    print("\n✓ ALL SUBMISSIONS DATABASE TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_submissions_workflow()
