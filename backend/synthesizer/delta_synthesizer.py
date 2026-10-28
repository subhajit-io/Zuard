import os
import re
import json
import time
from typing import List, Dict, Any, Optional
from vault.brand_vault import BrandVault
from .models import InspectorCard, AuditResponse
import config as config

class DeltaSynthesizer:
    """
    Delta-Only Synthesizer Engine.
    Processes only the flagged snippets ('deltas') detected by the 4 static workers,
    queries Branched RAG for missing guideline citations, and performs a single-pass
    Gemini LLM synthesis to generate context-aware, intent-preserving rewrites and
    explanations.
    
    Includes automatic graceful fallback to deterministic local edge rule-based
    synthesis when offline or running in confidential local privacy mode.
    """
    def __init__(self, vault: BrandVault):
        self.vault = vault
        self._client = None
        self._init_client()

    def _init_client(self):
        api_key = getattr(config, "GEMINI_API_KEY", "")
        privacy_mode = getattr(config, "LOCAL_PRIVACY_MODE", False)
        if api_key and not privacy_mode:
            try:
                from google import genai
                self._client = genai.Client(api_key=api_key)
            except Exception as e:
                print(f"[DeltaSynthesizer] Notice: Cloud client init deferred ({e})")
                self._client = None
        else:
            self._client = None

    def _call_gemini_delta_synthesis(
        self,
        original_text: str,
        inspector_cards: List[InspectorCard]
    ) -> Optional[Dict[str, Any]]:
        deltas = []
        for card in inspector_cards:
            deltas.append({
                "flag_id": card.flag_id,
                "dimension": card.dimension,
                "severity": card.severity,
                "snippet": card.original_snippet,
                "issue": card.issue_explanation,
                "citation": card.cited_source,
                "baseline_suggestion": card.suggested_rewrite
            })

        system_instruction = (
            "You are Zuard's Delta Synthesizer AI powered by Google Gemini. "
            "You receive content flagged with brand governance violations ('deltas') along with retrieved official citations. "
            "Your mission: Provide brand-compliant, natural, intent-preserving replacements and explanations, "
            "and synthesize a cohesive, compliant rewrite of the full text.\n\n"
            "STRICT GUIDELINES:\n"
            "1. Adhere strictly to the cited guidelines and approved facts.\n"
            "2. Preserve original marketing intent without hyperbole or prohibited terms.\n"
            "3. Output MUST be strictly valid JSON matching the schema below without markdown backticks."
        )

        prompt = f"""{system_instruction}

ORIGINAL DRAFT:
\"\"\"{original_text}\"\"\"

FLAGGED DELTAS & RETRIEVED CITATIONS:
{json.dumps(deltas, indent=2)}

EXPECTED JSON SCHEMA:
{{
  "rewrites": [
    {{
      "flag_id": "FLAG-01",
      "suggested_rewrite": "Compliant, natural replacement for this specific snippet",
      "issue_explanation": "Concise, professional explanation referencing the guideline"
    }}
  ],
  "suggested_full_rewrite": "Complete, cohesive rewrite of the original text with all violations naturally resolved."
}}
"""
        preferred_model = getattr(config, "GEMINI_MODEL", "gemini-3.8-flash")
        models_to_try = [
            preferred_model,
            "gemini-3.8-flash",
            "gemini-flash-latest",
            "gemini-2.5-flash"
        ]
        # Deduplicate while preserving order
        unique_models = list(dict.fromkeys(models_to_try))

        last_error = None
        for model in unique_models:
            try:
                response = self._client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config={"response_mime_type": "application/json"}
                )
                raw_text = response.text.strip()
                if raw_text.startswith("```"):
                    raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
                    raw_text = re.sub(r"\s*```$", "", raw_text)
                return json.loads(raw_text)
            except Exception as e:
                last_error = e
                continue

        if last_error:
            raise last_error
        return None

    def synthesize(
        self,
        document_title: str,
        original_text: str,
        static_audit_result: Dict[str, Any],
        privacy_mode_override: Optional[bool] = None,
        project_id: str = "default"
    ) -> AuditResponse:
        flags = static_audit_result.get("flags", [])
        privacy_mode_active = (
            privacy_mode_override 
            if privacy_mode_override is not None 
            else config.LOCAL_PRIVACY_MODE
        )
        api_key = config.GEMINI_API_KEY
        use_cloud_llm = bool(api_key and not privacy_mode_active)

        # Refresh client if key configured dynamically
        if use_cloud_llm and self._client is None:
            self._init_client()

        inspector_cards: List[InspectorCard] = []
        applied_replacements = []

        active_model_name = getattr(config, "GEMINI_MODEL", "gemini-3.8-flash")

        # Step 1: Process each static flag and resolve Branched RAG citations
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

            # Determine baseline deterministic suggestion
            suggested_rewrite = flag.get("suggested_rewrite", "")
            if not suggested_rewrite:
                pref = flag.get("preferred_replacement", "")
                suggested_rewrite = pref if pref else "Refer to official guideline citation."

            # Attribution badge
            if use_cloud_llm:
                disclosure = f"Verified by {worker_source} + Rewritten by {active_model_name}"
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

        # Baseline deterministic full rewrite
        full_rewrite = original_text
        applied_replacements.sort(key=lambda x: len(x[0]), reverse=True)
        for old_snip, new_snip in applied_replacements:
            if old_snip in full_rewrite:
                full_rewrite = re.sub(re.escape(old_snip), new_snip, full_rewrite, flags=re.IGNORECASE)

        # Step 2: Cloud Gemini Delta Synthesis (Single-pass LLM call for all deltas)
        cloud_synthesis_applied = False
        if use_cloud_llm and self._client and inspector_cards:
            try:
                ai_synth = self._call_gemini_delta_synthesis(original_text, inspector_cards)
                if ai_synth:
                    rewrites_map = {item["flag_id"]: item for item in ai_synth.get("rewrites", []) if isinstance(item, dict) and "flag_id" in item}
                    for card in inspector_cards:
                        if card.flag_id in rewrites_map:
                            ai_item = rewrites_map[card.flag_id]
                            if ai_item.get("suggested_rewrite"):
                                card.suggested_rewrite = ai_item["suggested_rewrite"]
                            if ai_item.get("issue_explanation"):
                                card.issue_explanation = ai_item["issue_explanation"]
                    if ai_synth.get("suggested_full_rewrite"):
                        full_rewrite = ai_synth["suggested_full_rewrite"]
                    cloud_synthesis_applied = True
            except Exception as e:
                print(f"[DeltaSynthesizer] Notice: Cloud Gemini call failed, using deterministic RAG analyzer: {e}")

        # Update attribution if cloud synthesis was not applied
        if not cloud_synthesis_applied and not use_cloud_llm:
            for card in inspector_cards:
                worker_source = card.ai_disclosure.split(" + ")[0] if " + " in card.ai_disclosure else "Static Worker"
                card.ai_disclosure = f"{worker_source} + Synthesized by Local Edge Engine"

        # Generate Flagged Draft Markup (Inline annotations like in wireframe)
        markup_text = original_text
        for idx, card in enumerate(inspector_cards):
            if card.original_snippet and card.original_snippet in markup_text:
                tag = f" [FLAG {idx+1}: {card.dimension.upper()} - {card.severity}]"
                markup_text = markup_text.replace(card.original_snippet, f"{card.original_snippet}{tag}", 1)

        # Final mode string
        mode_str = "Confidential Local Edge Mode (Ollama/Offline)" if (privacy_mode_active or not api_key) else f"Google Gemini {active_model_name} Cloud"

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
