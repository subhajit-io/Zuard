import asyncio
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from vault.brand_vault import BrandVault
from .worker_lexical import LexicalStyleWorker
from .worker_facts import FactVerificationWorker
from .worker_visual import VisualAuditWorker
from .worker_wcag import WCAGAccessibilityWorker

class StaticAuditOrchestrator:
    def __init__(self, vault: BrandVault):
        self.vault = vault
        self.re_instruct_workers()

    def re_instruct_workers(self):
        """Dynamically re-instructs all 4 static workers with updated vault rules in real-time."""
        self.worker1 = LexicalStyleWorker(self.vault)
        self.worker2 = FactVerificationWorker(self.vault)
        self.worker3 = VisualAuditWorker(self.vault)
        self.worker4 = WCAGAccessibilityWorker(self.vault)

    async def run_parallel_audit(
        self,
        draft_text: str = "",
        image_path: Optional[Path] = None,
        color_pairs: Optional[List[Tuple[str, str]]] = None,
        alt_texts: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        start_time = time.perf_counter()

        loop = asyncio.get_running_loop()

        # Run the 4 workers concurrently using asyncio.gather
        tasks = [
            loop.run_in_executor(None, self.worker1.analyze, draft_text),
            loop.run_in_executor(None, self.worker2.analyze, draft_text),
            loop.run_in_executor(None, self._run_visual_worker, image_path),
            loop.run_in_executor(None, self.worker4.analyze, color_pairs, alt_texts)
        ]

        results = await asyncio.gather(*tasks)

        res_lexical, res_facts, res_visual, res_wcag = results

        all_flags = []
        all_flags.extend(res_lexical.get("flags", []))
        all_flags.extend(res_facts.get("flags", []))
        all_flags.extend(res_visual.get("flags", []))
        all_flags.extend(res_wcag.get("flags", []))

        total_exec_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # Dimension breakdown
        dimension_counts = {
            "tone": 0,
            "terminology": 0,
            "facts": 0,
            "claims": 0,
            "visual": 0,
            "accessibility": 0
        }
        for f in all_flags:
            dim = f.get("dimension", "general")
            if dim in dimension_counts:
                dimension_counts[dim] += 1
            else:
                dimension_counts[dim] = 1

        # Calculate preliminary deterministic compliance score (100 - penalties)
        critical_count = sum(1 for f in all_flags if f.get("severity") == "CRITICAL")
        warning_count = sum(1 for f in all_flags if f.get("severity") == "WARNING")
        penalty = (critical_count * 20) + (warning_count * 8)
        compliance_score = max(0, min(100, 100 - penalty))

        return {
            "total_execution_ms": total_exec_ms,
            "total_flags": len(all_flags),
            "compliance_score": compliance_score,
            "status": "APPROVED" if len(all_flags) == 0 else ("CHANGES_REQUESTED" if critical_count > 0 else "WARNINGS_DETECTED"),
            "dimension_breakdown": dimension_counts,
            "worker_timings": {
                "worker_1_lexical_ms": res_lexical.get("execution_ms", 0),
                "worker_2_facts_ms": res_facts.get("execution_ms", 0),
                "worker_3_visual_ms": res_visual.get("execution_ms", 0),
                "worker_4_wcag_ms": res_wcag.get("execution_ms", 0),
            },
            "metrics": {
                "readability": res_lexical.get("metrics", {}),
                "visual_dominant_colors": res_visual.get("dominant_colors", []),
                "contrast_checks": res_wcag.get("contrast_evaluations", [])
            },
            "flags": all_flags
        }

    def _run_visual_worker(self, image_path: Optional[Path]) -> Dict[str, Any]:
        if image_path and image_path.exists():
            return self.worker3.analyze_image(image_path)
        return {
            "worker": "Static Worker #3 (Visual Audit)",
            "execution_ms": 0.0,
            "flags": [],
            "dominant_colors": []
        }
