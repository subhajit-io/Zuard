import asyncio
import os
import sys
from pathlib import Path

# Add backend and project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Ensure stdout handles utf-8 on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from vault.brand_vault import BrandVault
from workers.orchestrator import StaticAuditOrchestrator
from synthesizer.delta_synthesizer import DeltaSynthesizer
from workers.worker_wcag import calculate_contrast_ratio, calculate_relative_luminance
from workers.worker_visual import hex_to_rgb, rgb_to_cielab, delta_e_cie76

def test_vault_and_rag(vault: BrandVault):
    print("\n--- TEST 1: Brand Vault & Branched RAG Ingestion ---")
    summary = vault.get_vault_summary()
    print("Vault Summary:", summary)
    assert summary["total_approved_facts"] >= 6, "Expected at least 6 approved facts in SQL"
    assert summary["total_terminology_rules"] >= 10, "Expected at least 10 terminology rules"
    assert summary["brand_colors_count"] >= 5, "Expected brand color palette"
    assert summary["indexed_guideline_chunks"] > 0, "Expected indexed chunks in RAG"

    # Test Facts DB query
    fact_104 = vault.facts_db.get_fact_by_id("F-104")
    assert fact_104 is not None, "Fact F-104 missing"
    assert "42%" in fact_104["approved_value"], "Expected 42% cost reduction in F-104"
    print("✓ Facts DB verified: Fact F-104 =", fact_104["approved_claim"])

    # Test Branched RAG Retrieval
    matches = vault.retriever.retrieve("cost reduction metrics and pricing", top_k=2)
    assert len(matches) > 0, "RAG retrieval returned no matches"
    print(f"✓ Branched RAG retrieval returned {len(matches)} matches. Top citation: {matches[0]['doc_name']} (Page {matches[0]['page_number']})")
    print("TEST 1 PASSED!")

def test_wcag_and_color_math():
    print("\n--- TEST 2: Deterministic WCAG Math & CIELAB Delta-E ---")
    # Test Luminance
    l_white = calculate_relative_luminance(255, 255, 255)
    l_black = calculate_relative_luminance(0, 0, 0)
    assert abs(l_white - 1.0) < 1e-4, "Luminance of white must be 1.0"
    assert abs(l_black - 0.0) < 1e-4, "Luminance of black must be 0.0"

    # Test Contrast: Black on White = 21:1
    contrast_max = calculate_contrast_ratio((0, 0, 0), (255, 255, 255))
    assert abs(contrast_max - 21.0) < 0.1, f"Expected 21:1, got {contrast_max}"
    print(f"✓ Black on White contrast: {contrast_max:.1f}:1")

    # Test Contrast: White on #FF0055 (Hot Magenta)
    rgb_magenta = hex_to_rgb("#FF0055")
    contrast_magenta = calculate_contrast_ratio((255, 255, 255), rgb_magenta)
    print(f"✓ White on #FF0055 contrast: {contrast_magenta:.2f}:1 (Must FAIL WCAG 4.5:1)")
    assert contrast_magenta < 4.5, "Expected WCAG AA contrast failure for #FFFFFF on #FF0055"

    # Test CIELAB Delta-E distance
    lab_navy = rgb_to_cielab(*hex_to_rgb("#0F172A"))
    lab_magenta = rgb_to_cielab(*rgb_magenta)
    dE = delta_e_cie76(lab_navy, lab_magenta)
    print(f"✓ CIELAB ΔE between Brand Navy and Prohibited Magenta: {dE:.1f} (Threshold: 12.0)")
    assert dE > 12.0, "Expected ΔE to exceed off-brand threshold"
    print("TEST 2 PASSED!")

async def test_full_pipeline(vault: BrandVault):
    print("\n--- TEST 3: Parallel 4-Worker Pre-Check & Delta-Only Synthesizer ---")
    orchestrator = StaticAuditOrchestrator(vault)
    synthesizer = DeltaSynthesizer(vault)

    # The exact benchmark text from page 10 of the plan:
    # "Our #1 AI platform [FLAG 1] is super cheap [FLAG 2] and cuts costs by 99.9% [FLAG 3]..."
    draft_sample = "Our #1 AI platform is super cheap and cuts costs by 99.9%. It also includes legacy sync."
    
    # Run audit with low contrast pair (#FFFFFF on #FF0055) and missing alt-text
    static_result = await orchestrator.run_parallel_audit(
        draft_text=draft_sample,
        color_pairs=[("#FFFFFF", "#FF0055")],
        alt_texts=[{"alt": "banner", "asset_name": "promo_banner.png"}]
    )

    print(f"✓ Parallel Execution Latency: {static_result['total_execution_ms']} ms")
    print(f"✓ Static Worker Flags Count: {static_result['total_flags']}")
    print("✓ Timings by Worker:", static_result["worker_timings"])
    print("✓ Dimension Breakdown:", static_result["dimension_breakdown"])

    assert static_result["total_flags"] >= 4, "Expected flags across superlatives, terms, facts, and accessibility"
    
    # Delta-Only Synthesis
    audit_resp = synthesizer.synthesize(
        document_title="Q4_Product_Launch_Release.pdf",
        original_text=draft_sample,
        static_audit_result=static_result,
        privacy_mode_override=True # Test local edge offline mode
    )

    print("\n✓ Synthesizer Inspector Cards Generated:")
    for card in audit_resp.inspector_cards:
        print(f"  [{card.flag_id}] ({card.dimension.upper()}) Severity: {card.severity}")
        print(f"    Original Snippet: '{card.original_snippet}'")
        print(f"    Issue: {card.issue_explanation}")
        print(f"    Cited Source: {card.cited_source}")
        print(f"    Suggested Rewrite: '{card.suggested_rewrite}'")
        print(f"    AI Disclosure: {card.ai_disclosure}")
        print("-" * 50)

    print("\n✓ Full Compliant Rewrite Produced:")
    print("ORIGINAL: ", audit_resp.original_text)
    print("REWRITE : ", audit_resp.suggested_full_rewrite)
    
    assert "super cheap" not in audit_resp.suggested_full_rewrite, "Banned term 'super cheap' must be replaced"
    assert "99.9%" not in audit_resp.suggested_full_rewrite, "Contradictory metric 99.9% must be corrected to 42%"

    print("\nTEST 3 PASSED!")

async def main():
    print("==================================================")
    print(" ZUARD — STATIC RAG PIPELINE TEST SUITE")
    print("==================================================")
    vault = BrandVault()
    test_vault_and_rag(vault)
    test_wcag_and_color_math()
    await test_full_pipeline(vault)
    print("\n==================================================")
    print(" ALL TESTS PASSED SUCCESSFULLY! ")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(main())
