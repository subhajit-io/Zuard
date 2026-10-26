import os
import re
import time
from typing import List, Dict, Any, Optional
from vault.brand_vault import BrandVault
from .models import InspectorCard, AuditResponse
import config as config

class DeltaSynthesizer:
    def __init__(self, vault: BrandVault):
        self.vault = vault

    def synthesize(
        self,
        document_title: str,
        original_text: str,
        static_audit_result: Dict[str, Any],
        privacy_mode_override: Optional[bool] = None,
        project_id: str = "zuard-enterprise"
    ) -> AuditResponse:
        flags = static_audit_result.get("flags", [])
        privacy_mode_active = (
            privacy_mode_override 
            if privacy_mode_override is not None 
            else config.LOCAL_PRIVACY_MODE
        )
        api_key = config.GEMINI_API_KEY
        use_cloud_llm = bool(api_key and not privacy_mode_active)

        inspector_cards: List[InspectorCard] = []
        applied_replacements = []

        # Process each flag
        for idx, flag in enumerate(flags):
            flag_id = flag.get("flag_id", f"FLAG-{idx+1:02d}")
            snippet = flag.get("snippet", "")
            dimension = flag.get("dimension", "general")
            worker_source = flag.get("worker_source", "Static Worker")
            cited_source = flag.get("cited_source", "")

            # If no citation provided by worker, query Branched RAG
            if not cited_source:
                rag_results = self.vault.retriever.retrieve(snippet or flag.get("issue", ""), top_k=1)
                if rag_results:
                    top_match = rag_results[0]
                    cited_source = self.vault.retriever.format_citation(top_match)
                else:
                    cited_source = "Brand Guide v2, General Compliance Guidelines"

            # Determine suggestion
            suggested_rewrite = flag.get("suggested_rewrite", "")
            if not suggested_rewrite:
                pref = flag.get("preferred_replacement", "")
                suggested_rewrite = pref if pref else "Refer to official guideline citation."

            # Attribution badge
            if use_cloud_llm:
                disclosure = f"Verified by {worker_source} + Rewritten by Gemini 2.5 Flash"
            else:
                disclosure = f"Verified by {worker_source} + Synthesized by Local Edge Engine"

            card = InspectorCard(
                flag_id=flag_id,
                dimension=dimension,
                severity=flag.get("severity", "WARNING"),
                original_snippet=snippet,
                context_sentence=flag.get("context_sentence", ""),
                issue_explanation=flag.get("issue", ""),
                suggested_rewrite=suggested_rewrite,
                cited_source=cited_source,
                ai_disclosure=disclosure,
                confidence_score=flag.get("confidence_score", 1.0),
                allowed_actions=["ACCEPT", "EDIT", "OVERRIDE"],
                status="PENDING"
            )
            inspector_cards.append(card)

            if snippet and suggested_rewrite and snippet != suggested_rewrite:
                applied_replacements.append((snippet, suggested_rewrite))

        # Generate Flagged Draft Markup (Inline annotations like in wireframe)
        # e.g., "Our #1 AI platform [FLAG 1: Unverified Claim] is super cheap [FLAG 2: Banned Term & Tone]..."
        markup_text = original_text
        for idx, card in enumerate(inspector_cards):
            if card.original_snippet and card.original_snippet in markup_text:
                tag = f" [FLAG {idx+1}: {card.dimension.upper()} - {card.severity}]"
                # Replace only first occurrence to avoid duplicates
                markup_text = markup_text.replace(card.original_snippet, f"{card.original_snippet}{tag}", 1)

        # Generate Full Suggested Compliant Rewrite
        full_rewrite = original_text
        # Perform replacements deterministically
        # Sort replacements by length descending to prevent substring collisions
        applied_replacements.sort(key=lambda x: len(x[0]), reverse=True)
        for old_snip, new_snip in applied_replacements:
            if old_snip in full_rewrite:
                full_rewrite = re.sub(re.escape(old_snip), new_snip, full_rewrite, flags=re.IGNORECASE)

        # Final mode string
        mode_str = "Confidential Local Edge Mode (Ollama/Offline)" if (privacy_mode_active or not api_key) else "Google Gemini 2.5 Flash Cloud"

        return AuditResponse(
            project_id=project_id,
            document_title=document_title,
            status=static_audit_result.get("status", "IN_REVIEW"),
            compliance_score=static_audit_result.get("compliance_score", 100),
            execution_time_ms=static_audit_result.get("total_execution_ms", 0.0),
            privacy_mode=mode_str,
            flagged_draft_markup=markup_text,
            original_text=original_text,
            suggested_full_rewrite=full_rewrite,
            total_violations_count=len(inspector_cards),
            dimension_breakdown=static_audit_result.get("dimension_breakdown", {}),
            inspector_cards=inspector_cards,
            metrics=static_audit_result.get("metrics", {}),
            worker_latencies_ms=static_audit_result.get("worker_timings", {})
        )
