import time
from typing import Dict, Any, List, Optional
from collections import Counter

class GovernanceTelemetry:
    def __init__(self):
        self.audit_history: List[Dict[str, Any]] = []
        self.overrides: List[Dict[str, Any]] = []
        self.approvals: List[Dict[str, Any]] = []

    def record_audit(self, audit_response: Dict[str, Any]):
        entry = {
            "timestamp": time.time(),
            "document_title": audit_response.get("document_title", "Untitled"),
            "compliance_score": audit_response.get("compliance_score", 100),
            "execution_ms": audit_response.get("execution_time_ms", 0),
            "violations_count": audit_response.get("total_violations_count", 0),
            "dimension_breakdown": audit_response.get("dimension_breakdown", {}),
            "flag_ids": [c["flag_id"] for c in audit_response.get("inspector_cards", []) if isinstance(c, dict) and "flag_id" in c]
        }
        self.audit_history.append(entry)

    def record_action(self, action_data: Dict[str, Any]):
        action_type = action_data.get("action", "").upper()
        if action_type == "OVERRIDE":
            self.overrides.append({
                "timestamp": time.time(),
                "flag_id": action_data.get("flag_id"),
                "justification": action_data.get("override_justification", ""),
                "role": action_data.get("reviewer_role", "Creator")
            })
        elif action_type == "ACCEPT":
            self.approvals.append({
                "timestamp": time.time(),
                "flag_id": action_data.get("flag_id"),
                "role": action_data.get("reviewer_role", "Creator")
            })

    def clear(self):
        self.audit_history.clear()
        self.overrides.clear()
        self.approvals.clear()

    def get_insights(self) -> Dict[str, Any]:
        total_audits = len(self.audit_history)
        if total_audits == 0:
            avg_score = None
            avg_exec_ms = None
            dim_totals = {}
            total_violations = 0
        else:
            avg_score = round(sum(a["compliance_score"] for a in self.audit_history) / total_audits, 1)
            avg_exec_ms = round(sum(a["execution_ms"] for a in self.audit_history) / total_audits, 2)
            
            dim_totals = Counter()
            for a in self.audit_history:
                for dim, cnt in a.get("dimension_breakdown", {}).items():
                    if cnt and cnt > 0:
                        dim_totals[dim] += cnt
            total_violations = sum(a.get("violations_count", 0) for a in self.audit_history)

        # Identify Ambiguity Hotspots (rules with repeated overrides)
        override_counts = Counter(o["flag_id"] for o in self.overrides if o.get("flag_id"))
        ambiguity_hotspots = [
            {"rule_id": rule_id, "override_count": cnt, "alert": "Unclear Guidelines - Needs Revision"}
            for rule_id, cnt in override_counts.most_common(5)
        ]

        return {
            "total_audits_recorded": total_audits,
            "total_documents_screened": total_audits,
            "average_compliance_score": avg_score,
            "average_latency_ms": avg_exec_ms,
            "average_precheck_latency_ms": avg_exec_ms,
            "total_violations_detected": total_violations,
            "total_human_overrides": len(self.overrides),
            "total_accepted_rewrites": len(self.approvals),
            "violations_by_dimension": dict(dim_totals),
            "actions_recorded": {
                "overrides": len(self.overrides),
                "approvals": len(self.approvals)
            },
            "ambiguity_hotspots": ambiguity_hotspots,
            "recent_audits": self.audit_history[-10:]
        }
