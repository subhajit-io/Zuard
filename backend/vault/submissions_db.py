import sqlite3
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

class SubmissionsDatabase:
    """
    SQLite-backed persistence for two-sided Creator <-> Central Reviewer workflow.
    Stores creator drafts, compliance audit snapshots, reviewer decisions, and revision logs.
    """
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS submissions (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content_text TEXT NOT NULL,
                    creator_name TEXT NOT NULL,
                    notes TEXT,
                    status TEXT NOT NULL DEFAULT 'PENDING_REVIEW',
                    compliance_score REAL DEFAULT 0,
                    violations_count INTEGER DEFAULT 0,
                    audit_data TEXT,
                    reviewer_decision TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_submissions_project ON submissions(project_id);
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_submissions_status ON submissions(status);
            """)
            conn.commit()
        self._seed_sample_submissions()

    def _seed_sample_submissions(self):
        """Seed initial realistic creator submissions if the table is currently empty."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as cnt FROM submissions")
            if cursor.fetchone()["cnt"] == 0:
                now_iso = datetime.utcnow().isoformat() + "Z"
                samples = [
                    (
                        "SUB-2026-A109",
                        "zuard-enterprise",
                        "Q4 Global Launch Headline & Copy",
                        "Our #1 AI platform is super cheap and guaranteed to save you 99% on costs. Using our revolutionary miracle engine you'll crush your competition.",
                        "Alex Rivera (Content Team Alpha)",
                        "High priority launch copy for tomorrow's press briefing. Need compliance sign-off.",
                        "PENDING_REVIEW",
                        45.0,
                        5,
                        json.dumps({
                            "summary": "Flagged 5 violations: banned terms ('super cheap', 'crush'), unsubstantiated claim ('save you 99%'), superlative ('#1 AI platform')."
                        }),
                        None,
                        now_iso,
                        now_iso
                    ),
                    (
                        "SUB-2026-B214",
                        "zuard-enterprise",
                        "Enterprise FinTech Ledger Brief",
                        "The Zuard Enterprise Platform delivers 70% faster review cycles. Our legacy sync pipeline reduces errors across banking ledgers.",
                        "Morgan Lee (FinTech Solutions)",
                        "Whitepaper executive abstract. Requesting fast-track review.",
                        "PENDING_REVIEW",
                        68.0,
                        2,
                        json.dumps({
                            "summary": "Flagged 2 items: claim '70% faster' requires empirical citation #F-104; terminology 'legacy sync pipeline' is outdated."
                        }),
                        None,
                        now_iso,
                        now_iso
                    ),
                    (
                        "SUB-2026-C330",
                        "zuard-enterprise",
                        "Sustainability & Infrastructure Whitepaper",
                        "Zuard's governance engine pre-screens drafts in 2.5 seconds, demonstrating a verified 42% average operational cost reduction (Study ID #F-104).",
                        "Sarah Chen (Corporate Communications)",
                        "Ready for publication. Clean pre-screen report attached.",
                        "APPROVED",
                        98.0,
                        0,
                        json.dumps({
                            "summary": "All 4 static workers passed with 0 violations. Verified facts match FactsDB #F-104."
                        }),
                        json.dumps({
                            "action": "APPROVE",
                            "status": "APPROVED",
                            "reviewer_name": "Chief Brand Officer",
                            "feedback_notes": "Perfect compliance with Enterprise guidelines. Approved for immediate release.",
                            "decided_at": now_iso
                        }),
                        now_iso,
                        now_iso
                    )
                ]
                cursor.executemany("""
                    INSERT INTO submissions (
                        id, project_id, title, content_text, creator_name,
                        notes, status, compliance_score, violations_count,
                        audit_data, reviewer_decision, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, samples)
                conn.commit()

    def create_submission(
        self,
        project_id: str,
        title: str,
        content_text: str,
        creator_name: str = "Creator",
        notes: str = "",
        compliance_score: float = 0.0,
        violations_count: int = 0,
        audit_data: Optional[Dict[str, Any]] = None,
        status: str = "PENDING_REVIEW"
    ) -> Dict[str, Any]:
        sub_id = f"SUB-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        now_iso = datetime.utcnow().isoformat() + "Z"
        audit_json = json.dumps(audit_data) if audit_data else "{}"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO submissions (
                    id, project_id, title, content_text, creator_name,
                    notes, status, compliance_score, violations_count,
                    audit_data, reviewer_decision, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?)
            """, (
                sub_id, project_id, title, content_text, creator_name,
                notes, status, compliance_score, violations_count,
                audit_json, now_iso, now_iso
            ))
            conn.commit()

        return self.get_submission(sub_id)

    def list_submissions(
        self,
        project_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        query = "SELECT * FROM submissions"
        conditions = []
        params = []

        if project_id and project_id != "all":
            conditions.append("project_id = ?")
            params.append(project_id)
        if status and status != "all":
            conditions.append("status = ?")
            params.append(status)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            results = []
            for row in rows:
                item = dict(row)
                if item.get("audit_data"):
                    try:
                        item["audit_data"] = json.loads(item["audit_data"])
                    except Exception:
                        pass
                if item.get("reviewer_decision"):
                    try:
                        item["reviewer_decision"] = json.loads(item["reviewer_decision"])
                    except Exception:
                        pass
                results.append(item)
            return results

    def get_submission(self, sub_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM submissions WHERE id = ?", (sub_id,))
            row = cursor.fetchone()
            if not row:
                return None
            item = dict(row)
            if item.get("audit_data"):
                try:
                    item["audit_data"] = json.loads(item["audit_data"])
                except Exception:
                    pass
            if item.get("reviewer_decision"):
                try:
                    item["reviewer_decision"] = json.loads(item["reviewer_decision"])
                except Exception:
                    pass
            return item

    def record_decision(
        self,
        sub_id: str,
        action: str, # 'APPROVE', 'REQUEST_CHANGES', 'OVERRIDE'
        reviewer_name: str = "Central Reviewer",
        feedback_notes: str = "",
        justification: str = ""
    ) -> Optional[Dict[str, Any]]:
        status_map = {
            "APPROVE": "APPROVED",
            "REQUEST_CHANGES": "CHANGES_REQUESTED",
            "OVERRIDE": "OVERRIDDEN"
        }
        new_status = status_map.get(action.upper(), "PENDING_REVIEW")
        now_iso = datetime.utcnow().isoformat() + "Z"

        decision_data = {
            "action": action.upper(),
            "status": new_status,
            "reviewer_name": reviewer_name,
            "feedback_notes": feedback_notes,
            "justification": justification,
            "decided_at": now_iso
        }

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE submissions
                SET status = ?, reviewer_decision = ?, updated_at = ?
                WHERE id = ?
            """, (new_status, json.dumps(decision_data), now_iso, sub_id))
            conn.commit()

        return self.get_submission(sub_id)

    def delete_submission(self, sub_id: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM submissions WHERE id = ?", (sub_id,))
            conn.commit()
            return cursor.rowcount > 0

    def get_stats(self, project_id: Optional[str] = None) -> Dict[str, int]:
        query = "SELECT status, COUNT(*) as count FROM submissions"
        params = []
        if project_id and project_id != "all":
            query += " WHERE project_id = ?"
            params.append(project_id)
        query += " GROUP BY status"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            stats = {
                "total": 0,
                "pending": 0,
                "approved": 0,
                "changes_requested": 0,
                "overridden": 0
            }
            for row in rows:
                st = row["status"].upper()
                c = row["count"]
                stats["total"] += c
                if st == "PENDING_REVIEW":
                    stats["pending"] += c
                elif st == "APPROVED":
                    stats["approved"] += c
                elif st == "CHANGES_REQUESTED":
                    stats["changes_requested"] += c
                elif st == "OVERRIDDEN":
                    stats["overridden"] += c
            return stats
