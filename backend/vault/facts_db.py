import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

class FactsDatabase:
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
                CREATE TABLE IF NOT EXISTS approved_facts (
                    fact_id TEXT PRIMARY KEY,
                    category TEXT NOT NULL,
                    metric_key TEXT NOT NULL,
                    approved_claim TEXT NOT NULL,
                    approved_value TEXT NOT NULL,
                    unit TEXT,
                    source_doc TEXT NOT NULL,
                    page_number INTEGER NOT NULL,
                    section TEXT NOT NULL,
                    verified_date TEXT NOT NULL,
                    notes TEXT
                );
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_facts_metric ON approved_facts(metric_key);
            """)
            conn.commit()

    def load_seed_data(self, json_path: Path) -> int:
        if not json_path.exists():
            return 0
        with open(json_path, "r", encoding="utf-8") as f:
            facts = json.load(f)
        
        count = 0
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for fact in facts:
                cursor.execute("""
                    INSERT OR REPLACE INTO approved_facts (
                        fact_id, category, metric_key, approved_claim,
                        approved_value, unit, source_doc, page_number,
                        section, verified_date, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    fact["fact_id"],
                    fact.get("category", "general"),
                    fact.get("metric_key", "metric"),
                    fact["approved_claim"],
                    fact["approved_value"],
                    fact.get("unit", ""),
                    fact["source_doc"],
                    int(fact.get("page_number", 1)),
                    fact.get("section", ""),
                    fact.get("verified_date", ""),
                    fact.get("notes", "")
                ))
                count += 1
            conn.commit()
        return count

    def get_all_facts(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM approved_facts ORDER BY fact_id ASC")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_fact_by_id(self, fact_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM approved_facts WHERE fact_id = ?", (fact_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def find_facts_by_metric(self, metric_key: str) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM approved_facts WHERE metric_key LIKE ?", (f"%{metric_key}%",))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def search_facts(self, query: str) -> List[Dict[str, Any]]:
        query_tokens = [t.strip().lower() for t in query.split() if len(t.strip()) > 2]
        if not query_tokens:
            return self.get_all_facts()
        
        all_facts = self.get_all_facts()
        scored_facts = []
        for fact in all_facts:
            haystack = f"{fact['fact_id']} {fact['category']} {fact['metric_key']} {fact['approved_claim']} {fact['approved_value']} {fact['notes']}".lower()
            score = sum(1 for token in query_tokens if token in haystack)
            if score > 0:
                scored_facts.append((score, fact))
        
        scored_facts.sort(key=lambda x: x[0], reverse=True)
        return [f[1] for f in scored_facts]
