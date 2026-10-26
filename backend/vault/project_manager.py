import json
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from vault.brand_vault import BrandVault
from workers.orchestrator import StaticAuditOrchestrator
from synthesizer.delta_synthesizer import DeltaSynthesizer
import config as config

class MultiProjectManager:
    """
    Manages multi-tenant / multi-project brand governance workspaces.
    Each project maintains isolated brand guidelines, approved facts,
    terminology dictionaries, and re-instructed static workers.
    """

    def __init__(self, projects_root: Optional[Path] = None):
        self.projects_root = projects_root or (config.VAULT_DIR / "projects")
        self.projects_root.mkdir(parents=True, exist_ok=True)
        self._vault_cache: Dict[str, BrandVault] = {}
        self._orchestrator_cache: Dict[str, StaticAuditOrchestrator] = {}
        self._synthesizer_cache: Dict[str, DeltaSynthesizer] = {}

    def list_projects(self) -> List[Dict[str, Any]]:
        projects = []
        for p_dir in self.projects_root.iterdir():
            if p_dir.is_dir():
                meta_file = p_dir / "project_meta.json"
                if meta_file.exists():
                    try:
                        with open(meta_file, "r", encoding="utf-8") as f:
                            meta = json.load(f)
                    except Exception:
                        meta = {"project_id": p_dir.name, "name": p_dir.name.title()}
                else:
                    meta = {
                        "project_id": p_dir.name,
                        "name": p_dir.name.title(),
                        "description": f"Guidelines workspace for {p_dir.name}",
                        "persona": "Standard"
                    }

                # Get summary stats
                vault = self.get_vault(meta["project_id"])
                summary = vault.get_vault_summary()
                meta["stats"] = summary
                projects.append(meta)

        projects.sort(key=lambda x: x["project_id"])
        return projects

    def get_vault(self, project_id: str = "zuard-enterprise") -> BrandVault:
        clean_id = project_id.strip().lower()
        if clean_id not in self._vault_cache:
            p_dir = self.projects_root / clean_id
            if not p_dir.exists():
                # Fallback to default
                clean_id = "zuard-enterprise"
                p_dir = self.projects_root / clean_id
                p_dir.mkdir(parents=True, exist_ok=True)

            # Initialize dedicated BrandVault for this project
            db_path = p_dir / "project_facts.db"
            vault = BrandVault(base_dir=p_dir)
            vault.sample_dir = p_dir
            vault.db_path = db_path
            from vault.facts_db import FactsDatabase
            vault.facts_db = FactsDatabase(db_path)
            vault.load_all()
            self._vault_cache[clean_id] = vault

        return self._vault_cache[clean_id]

    def get_orchestrator(self, project_id: str = "zuard-enterprise") -> StaticAuditOrchestrator:
        clean_id = project_id.strip().lower()
        if clean_id not in self._orchestrator_cache:
            vault = self.get_vault(clean_id)
            self._orchestrator_cache[clean_id] = StaticAuditOrchestrator(vault)
        return self._orchestrator_cache[clean_id]

    def get_synthesizer(self, project_id: str = "zuard-enterprise") -> DeltaSynthesizer:
        clean_id = project_id.strip().lower()
        if clean_id not in self._synthesizer_cache:
            vault = self.get_vault(clean_id)
            self._synthesizer_cache[clean_id] = DeltaSynthesizer(vault)
        return self._synthesizer_cache[clean_id]

    def create_project(
        self,
        project_id: str,
        name: str,
        description: str = "",
        persona: str = "General Corporate",
        guideline_file: Optional[Path] = None
    ) -> Dict[str, Any]:
        clean_id = project_id.strip().lower().replace(" ", "-")
        p_dir = self.projects_root / clean_id
        p_dir.mkdir(parents=True, exist_ok=True)

        meta = {
            "project_id": clean_id,
            "name": name.strip(),
            "description": description.strip(),
            "persona": persona.strip()
        }
        with open(p_dir / "project_meta.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        # Initialize starter files if not present
        if not (p_dir / "approved_facts.json").exists():
            with open(p_dir / "approved_facts.json", "w", encoding="utf-8") as f:
                json.dump([], f)
        if not (p_dir / "terminology_dictionary.json").exists():
            with open(p_dir / "terminology_dictionary.json", "w", encoding="utf-8") as f:
                json.dump({"terms": []}, f)
        if not (p_dir / "visual_brand_rules.json").exists():
            with open(p_dir / "visual_brand_rules.json", "w", encoding="utf-8") as f:
                json.dump({
                    "brand_name": name,
                    "color_palette": {
                        "primary": {"name": "Primary Brand", "hex": "#0F172A", "usage": "Primary elements"},
                        "accent": {"name": "Accent Tone", "hex": "#2563EB", "usage": "Action items"}
                    },
                    "color_audit": {"delta_e_threshold": 12.0}
                }, f, indent=2)

        # Clear cache for this id to re-init fresh
        self._vault_cache.pop(clean_id, None)
        self._orchestrator_cache.pop(clean_id, None)
        self._synthesizer_cache.pop(clean_id, None)

        vault = self.get_vault(clean_id)
        orch = self.get_orchestrator(clean_id)

        # If a guidelines file is provided, ingest it
        ingest_summary = None
        if guideline_file and guideline_file.exists():
            dest = p_dir / guideline_file.name
            shutil.copy(guideline_file, dest)
            ingest_summary = vault.ingest_new_guideline_document(dest, orchestrator=orch)

        return {
            "status": "SUCCESS",
            "project": meta,
            "ingestion": ingest_summary,
            "message": f"Project '{name}' successfully created and isolated."
        }
