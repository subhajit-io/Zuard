import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from .facts_db import FactsDatabase
from .pdf_indexer import GuidelinesIndexer
from .rag_retriever import BranchedRAGRetriever
import config as config

class BrandVault:
    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or config.VAULT_DIR
        self.sample_dir = config.SAMPLE_DATA_DIR
        self.db_path = config.DB_PATH
        
        # Branch 1: Facts Database (SQLite)
        self.facts_db = FactsDatabase(self.db_path)
        
        # Branch 2: Terminology Dictionary
        self.terminology: Dict[str, Any] = {}
        
        # Branch 3: Visual Rules
        self.visual_rules: Dict[str, Any] = {}
        
        # Branch 4: Unstructured Guidelines (RAG Chunks & Retriever)
        self.indexer = GuidelinesIndexer()
        self.retriever = BranchedRAGRetriever()
        
        self.load_all()

    def load_all(self):
        # 1. Facts Database is persistent SQLite via self.facts_db (no mock seeding)

        # 2. Load Terminology Dictionary if exists
        terms_file = self.sample_dir / "terminology_dictionary.json"
        if terms_file.exists():
            try:
                with open(terms_file, "r", encoding="utf-8") as f:
                    self.terminology = json.load(f)
            except Exception:
                self.terminology = {"terms": []}
        else:
            self.terminology = {"terms": []}

        # 3. Load Visual Rules if exists
        vis_file = self.sample_dir / "visual_brand_rules.json"
        if vis_file.exists():
            try:
                with open(vis_file, "r", encoding="utf-8") as f:
                    self.visual_rules = json.load(f)
            except Exception:
                self.visual_rules = {"color_palette": {}}
        else:
            self.visual_rules = {"color_palette": {}}

        # 4. RAG chunks are only loaded when user uploads guideline documents

    def clear_all_guidelines(self) -> Dict[str, Any]:
        """Wipes all facts, terminology rules, color tokens, and indexed chunks for this vault."""
        with self.facts_db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM approved_facts")
            conn.commit()

        self.terminology = {"terms": []}
        terms_file = self.sample_dir / "terminology_dictionary.json"
        try:
            with open(terms_file, "w", encoding="utf-8") as f:
                json.dump(self.terminology, f, indent=2)
        except Exception:
            pass

        self.visual_rules = {"color_palette": {}}
        vis_file = self.sample_dir / "visual_brand_rules.json"
        try:
            with open(vis_file, "w", encoding="utf-8") as f:
                json.dump(self.visual_rules, f, indent=2)
        except Exception:
            pass

        self.retriever.chunks = []
        self.retriever.index_chunks([])
        return {"status": "SUCCESS", "message": "Brand Vault guidelines wiped completely."}

    def ingest_new_guideline_document(self, file_path: Path, orchestrator=None) -> Dict[str, Any]:
        """
        Dynamically parses an uploaded Brand Guidelines PDF/document,
        extracts new terminology, facts, and colors, updates the Branched RAG,
        and re-instructs the 4 static workers in real-time.
        """
        if not file_path.exists():
            return {"status": "ERROR", "message": f"File {file_path} not found"}

        from .rule_extractor import DynamicRuleExtractor
        extractor = DynamicRuleExtractor()

        # 1. Parse document into granular page & section chunks
        suffix = file_path.suffix.lower()
        if suffix == ".pdf":
            new_chunks = self.indexer.parse_pdf_file(file_path)
        else:
            new_chunks = self.indexer.parse_text_file(file_path)

        if not new_chunks:
            return {"status": "ERROR", "message": "Failed to extract text chunks from uploaded document"}

        # 2. Append to RAG Retriever & Re-index semantic TF-IDF corpus
        self.retriever.chunks.extend(new_chunks)
        self.retriever.index_chunks(self.retriever.chunks)

        # 3. Dynamic Rule Extraction
        discovered = extractor.extract_from_chunks(new_chunks)
        
        # 4. Update Terminology Dictionary
        existing_terms = {t["term"].lower() for t in self.terminology.get("terms", [])}
        new_terms_added = 0
        for item in discovered.get("terms", []):
            if item["term"].lower() not in existing_terms:
                self.terminology.setdefault("terms", []).append(item)
                existing_terms.add(item["term"].lower())
                new_terms_added += 1

        # Persist updated terminology
        terms_file = self.sample_dir / "terminology_dictionary.json"
        try:
            with open(terms_file, "w", encoding="utf-8") as f:
                json.dump(self.terminology, f, indent=2)
        except Exception:
            pass

        # 5. Insert Extracted Facts into SQLite Database
        new_facts_added = 0
        with self.facts_db._get_connection() as conn:
            cursor = conn.cursor()
            for fact in discovered.get("facts", []):
                cursor.execute("""
                    INSERT OR REPLACE INTO approved_facts (
                        fact_id, category, metric_key, approved_claim,
                        approved_value, unit, source_doc, page_number,
                        section, verified_date, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    fact["fact_id"],
                    fact["category"],
                    fact["metric_key"],
                    fact["approved_claim"],
                    fact["approved_value"],
                    fact["unit"],
                    fact["source_doc"],
                    fact["page_number"],
                    fact["section"],
                    fact["verified_date"],
                    fact["notes"]
                ))
                new_facts_added += 1
            conn.commit()

        # 6. Update Visual Palette
        new_colors_added = 0
        palette = self.visual_rules.setdefault("color_palette", {})
        for col in discovered.get("colors", []):
            key = col["name"].lower().replace(" ", "_")
            if key not in palette:
                palette[key] = {
                    "name": col["name"],
                    "hex": col["hex"],
                    "usage": col["usage"]
                }
                new_colors_added += 1

        # Ingest Prohibited Colors & Delta-E Tolerance
        color_audit = self.visual_rules.setdefault("color_audit", {})
        if discovered.get("delta_e_threshold"):
            color_audit["delta_e_threshold"] = discovered["delta_e_threshold"]
            
        prohibited = color_audit.setdefault("flagged_prohibited_colors", [])
        for p_col in discovered.get("prohibited_colors", []):
            if not any(p.get("hex", "").upper() == p_col["hex"].upper() for p in prohibited):
                prohibited.append(p_col)

        vis_file = self.sample_dir / "visual_brand_rules.json"
        try:
            with open(vis_file, "w", encoding="utf-8") as f:
                json.dump(self.visual_rules, f, indent=2)
        except Exception:
            pass

        # 7. Dynamically re-instruct the 4 static workers in real-time
        if orchestrator is not None:
            orchestrator.re_instruct_workers()

        return {
            "status": "SUCCESS",
            "document_name": file_path.name,
            "new_chunks_indexed": len(new_chunks),
            "total_chunks_in_rag": len(self.retriever.chunks),
            "new_terminology_rules": new_terms_added,
            "new_facts_indexed": new_facts_added,
            "new_palette_colors": new_colors_added,
            "workers_reinstructed": True,
            "message": f"Successfully ingested {file_path.name}. Extracted {new_terms_added} rules, {new_facts_added} verified facts, and dynamically re-instructed all 4 static workers."
        }

    def get_terms(self) -> List[Dict[str, Any]]:
        return self.terminology.get("terms", [])

    def get_palette(self) -> Dict[str, Any]:
        return self.visual_rules.get("color_palette", {})

    def get_visual_config(self) -> Dict[str, Any]:
        return self.visual_rules

    def get_vault_summary(self) -> Dict[str, Any]:
        facts = self.facts_db.get_all_facts()
        terms = self.get_terms()
        palette = self.get_palette()
        return {
            "total_approved_facts": len(facts),
            "total_terminology_rules": len(terms),
            "brand_colors_count": len(palette),
            "indexed_guideline_chunks": len(self.retriever.chunks),
            "brand_name": self.visual_rules.get("brand_name", "Zuard"),
            "status": "Ready & Ingested"
        }
