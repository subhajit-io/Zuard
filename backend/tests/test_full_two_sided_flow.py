import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from api.app import app

def test_full_flow():
    client = TestClient(app)
    
    # 1. Health check
    health = client.get("/api/health")
    assert health.status_code == 200, f"Health check failed: {health.text}"
    print("✓ GET /api/health passed")
    
    # 2. Frontend index.html served
    index = client.get("/")
    assert index.status_code == 200, f"Frontend index failed: {index.text[:100]}"
    assert "Two-Sided Role Mode Segmented Toggle" in index.text
    assert "btnRoleCreator" in index.text
    assert "btnRoleReviewer" in index.text
    print("✓ GET / (Two-Sided UI loaded) passed")
    
    # 3. List initial submissions
    subs_res = client.get("/api/submissions")
    assert subs_res.status_code == 200
    subs = subs_res.json()
    print(f"✓ GET /api/submissions returned {len(subs)} submissions")
    
    # 4. Creator submits a draft
    submit_payload = {
        "project_id": "zuard-enterprise",
        "title": "Black Friday Mega Deal Campaign",
        "content_text": "Buy our ultra cheap AI system now. Guaranteed 100% ROI.",
        "creator_name": "Jordan (Growth Team)",
        "notes": "Targeting European fintech clients",
        "compliance_score": 45.0,
        "violations_count": 3,
        "audit_data": {
            "compliance_score": 45,
            "total_violations_count": 3
        }
    }
    created_res = client.post("/api/submissions", json=submit_payload)
    assert created_res.status_code == 200, f"Create submission failed: {created_res.text}"
    created_sub = created_res.json()
    sub_id = created_sub["id"]
    assert created_sub["status"] == "PENDING_REVIEW"
    print(f"✓ Creator POST /api/submissions passed: {sub_id} [Status: {created_sub['status']}]")
    
    # 5. Reviewer inspects submission stats
    stats_res = client.get("/api/submissions-stats")
    assert stats_res.status_code == 200
    stats = stats_res.json()
    print(f"✓ Central Reviewer GET /api/submissions-stats: {stats}")
    assert stats["pending"] >= 1
    
    # 6. Central Reviewer requests changes
    decision_payload = {
        "action": "REQUEST_CHANGES",
        "reviewer_name": "Chief Governance Officer",
        "feedback_notes": "Please remove 'Guaranteed 100% ROI' and replace with verified Fact #F-104."
    }
    dec_res = client.post(f"/api/submissions/{sub_id}/decision", json=decision_payload)
    assert dec_res.status_code == 200
    dec_data = dec_res.json()
    assert dec_data["submission"]["status"] == "CHANGES_REQUESTED"
    print(f"✓ Central Reviewer Decision [REQUEST_CHANGES] passed on {sub_id}")
    
    # 7. Central Reviewer overrides or approves
    approve_payload = {
        "action": "APPROVE",
        "reviewer_name": "Chief Governance Officer",
        "feedback_notes": "Revisions satisfied. Approved for distribution."
    }
    appr_res = client.post(f"/api/submissions/{sub_id}/decision", json=approve_payload)
    assert appr_res.status_code == 200
    appr_data = appr_res.json()
    assert appr_data["submission"]["status"] == "APPROVED"
    print(f"✓ Central Reviewer Decision [APPROVE] passed on {sub_id}")
    
    print("\n✓ ALL TWO-SIDED ARCHITECTURE INTEGRATION TESTS PASSED!")

if __name__ == "__main__":
    test_full_flow()

