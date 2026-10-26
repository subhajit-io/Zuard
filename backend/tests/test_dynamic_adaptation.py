import sys
from pathlib import Path

# Add backend directory and project root to path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(backend_dir.parent))

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from vault.brand_vault import BrandVault
from workers.orchestrator import StaticAuditOrchestrator
import asyncio

def run_test():
    vault = BrandVault()
    orchestrator = StaticAuditOrchestrator(vault)

    test_guide = Path(__file__).parent / "_dynamic_sample.txt"
    test_guide.write_text("""=== PAGE 1 ===
Section 1.0: Cloud Infrastructure Guidelines
Terms like "clunky", "slow sync" are strictly forbidden across all corporate materials.
Instead of "cheap deal", use "strategic enterprise investment".
The verified enterprise platform uptime is 99.98% backed by our 24/7 SLA.
Demonstrated 65% cost reduction across all multi-cloud migrations.
Our new brand secondary accent is Electric Purple (#8B5CF6).
""", encoding="utf-8")

    print("--- Dynamic Ingestion Test ---")
    res = vault.ingest_new_guideline_document(test_guide, orchestrator=orchestrator)
    print("Ingestion Result Status:", res["status"])
    print("Chunks Indexed        :", res["new_chunks_indexed"])
    print("New Terminology Rules :", res["new_terminology_rules"])
    print("New Facts Indexed     :", res["new_facts_indexed"])
    print("New Palette Colors    :", res["new_palette_colors"])

    print("\n--- Auditing Draft with Newly Learned Rules ---")
    draft = "Our new deployment replaces that clunky architecture with a cheap deal."
    audit_res = asyncio.run(orchestrator.run_parallel_audit(draft_text=draft))

    print(f"Total Flags Caught: {audit_res['total_flags']}")
    for f in audit_res['flags']:
        print(f"  [{f['flag_id']}] Snippet: '{f['snippet']}' -> Suggested: '{f.get('suggested_rewrite')}'")

    if test_guide.exists():
        test_guide.unlink()

    snippets = [f['snippet'] for f in audit_res['flags']]
    assert "clunky" in snippets, "Dynamic rule learning failed: 'clunky' was not flagged"
    assert "cheap deal" in snippets, "Dynamic rule learning failed: 'cheap deal' was not flagged"
    print("\n✓ DYNAMIC ADAPTATION & WORKER RE-INSTRUCTION VERIFIED 100% SUCCESSFULLY!")

if __name__ == "__main__":
    run_test()
