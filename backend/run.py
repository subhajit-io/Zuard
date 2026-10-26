import argparse
import asyncio
import os
import sys
from pathlib import Path

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Ensure current backend directory and parent in path
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(parent_dir))

def start_server():
    import uvicorn
    from api.app import app
    import config as config
    print("\n" + "="*60)
    print(" 🚀 STARTING ZUARD GOVERNANCE SERVER")
    print(f" 📍 Web Portal URL  : http://{config.HOST}:{config.PORT}")
    print(f" 📚 API Docs        : http://{config.HOST}:{config.PORT}/docs")
    print(f" 🛡️  Privacy Mode   : {'Local Edge Offline' if config.LOCAL_PRIVACY_MODE or not config.GEMINI_API_KEY else 'Cloud Gemini 2.5 Flash'}")
    print("="*60 + "\n")
    uvicorn.run("api.app:app", host=config.HOST, port=config.PORT, reload=False)

def run_tests():
    from test_pipeline import main as test_main
    asyncio.run(test_main())

def run_cli_audit(text_input: str, is_file: bool = False):
    from vault.brand_vault import BrandVault
    from workers.orchestrator import StaticAuditOrchestrator
    from synthesizer.delta_synthesizer import DeltaSynthesizer

    vault = BrandVault()
    orchestrator = StaticAuditOrchestrator(vault)
    synthesizer = DeltaSynthesizer(vault)

    content = text_input
    if is_file:
        file_path = Path(text_input)
        if not file_path.exists():
            print(f"Error: File not found: {file_path}")
            return
        content = file_path.read_text(encoding="utf-8", errors="ignore")

    print("\nRunning Deterministic Pre-Check on draft...")
    static_result = asyncio.run(orchestrator.run_parallel_audit(draft_text=content))
    audit_resp = synthesizer.synthesize("CLI_Draft", content, static_result)

    print("\n" + "="*60)
    print(f" AUDIT RESULT: Score {audit_resp.compliance_score}/100 | Status: {audit_resp.status}")
    print(f" Pre-check Latency: {audit_resp.execution_time_ms} ms")
    print(f" Total Violations : {audit_resp.total_violations_count}")
    print("="*60)

    for c in audit_resp.inspector_cards:
        print(f"\n[{c.flag_id}] {c.dimension.upper()} ({c.severity})")
        print(f"  Flagged: \"{c.original_snippet}\"")
        print(f"  Issue  : {c.issue_explanation}")
        print(f"  Source : {c.cited_source}")
        print(f"  Rewrite: \"{c.suggested_rewrite}\"")

    print("\n--- SUGGESTED COMPLIANT REWRITE ---")
    print(audit_resp.suggested_full_rewrite)
    print("="*60 + "\n")

def main():
    parser = argparse.ArgumentParser(description="Zuard Static RAG Pipeline Runner")
    parser.add_argument("--serve", action="store_true", help="Start the FastAPI server and Web Portal")
    parser.add_argument("--test", action="store_true", help="Execute the automated test pipeline")
    parser.add_argument("--audit", type=str, help="Audit a raw text string")
    parser.add_argument("--file", type=str, help="Audit a document file")

    args = parser.parse_args()

    if args.serve:
        start_server()
    elif args.test:
        run_tests()
    elif args.audit:
        run_cli_audit(args.audit)
    elif args.file:
        run_cli_audit(args.file, is_file=True)
    else:
        # Default action: run tests and show banner
        print("Usage:")
        print("  python run.py --serve         # Launch web review portal")
        print("  python run.py --test          # Run automated test suite")
        print("  python run.py --audit 'text'  # Audit text snippet via CLI")
        print("  python run.py --file path.txt # Audit a text or markdown file")
        print("\nExecuting verification tests now...\n")
        run_tests()

if __name__ == "__main__":
    main()
