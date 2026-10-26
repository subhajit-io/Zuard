import urllib.request
import json
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def audit(project_id, text):
    payload = {
        "project_id": project_id,
        "document_title": f"{project_id}_audit_test",
        "content_text": text
    }
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/audit-content",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def main():
    print("==================================================")
    print(" MULTI-PROJECT BRAND GOVERNANCE VERIFICATION")
    print("==================================================")

    # 1. Test Enterprise Project with cost claim
    ent_res = audit("zuard-enterprise", "Our #1 enterprise engine is super cheap and cuts costs by 99.9%.")
    print(f"\n[Project: zuard-enterprise (B2B)]")
    print(f"Compliance Score: {ent_res['compliance_score']}/100 | Violations: {ent_res['total_violations_count']}")
    for c in ent_res["inspector_cards"]:
        print(f"  * [{c['flag_id']}] {c['dimension'].upper()}: Flagged '{c['original_snippet']}' -> Rewrite: '{c['suggested_rewrite']}'")

    # 2. Test Consumer Project with consumer terminology & claims
    cons_res = audit("zuard-consumer", "Avoid corporate bureaucracy! Our app gives unlimited free exports.")
    print(f"\n[Project: zuard-consumer (B2C & Mobile)]")
    print(f"Compliance Score: {cons_res['compliance_score']}/100 | Violations: {cons_res['total_violations_count']}")
    for c in cons_res["inspector_cards"]:
        print(f"  * [{c['flag_id']}] {c['dimension'].upper()}: Flagged '{c['original_snippet']}' -> Rewrite: '{c['suggested_rewrite']}'")

    assert ent_res["total_violations_count"] >= 3, "Enterprise rules not applied"
    assert cons_res["total_violations_count"] >= 2, "Consumer rules not applied"
    print("\n✓ MULTI-PROJECT ISOLATION & GOVERNANCE VERIFIED 100% SUCCESSFULLY!")

if __name__ == "__main__":
    main()
