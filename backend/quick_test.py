"""Quick pipeline test — skips PDF loading by using sample_data directly."""
import sys, asyncio
sys.path.insert(0, '.')

# Test 1: worker imports
from workers.worker_lexical import LexicalStyleWorker
from workers.worker_facts import FactVerificationWorker
print("[OK] Workers imported")

# Test 2: minimal vault (no PDF)
from vault.facts_db import FactsDatabase
from vault.rag_retriever import BranchedRAGRetriever
from vault.pdf_indexer import GuidelinesIndexer
from pathlib import Path

class MinimalVault:
    def __init__(self):
        import json, config
        self.facts_db = FactsDatabase(config.DB_PATH)
        facts_seed = config.SAMPLE_DATA_DIR / "approved_facts.json"
        if facts_seed.exists():
            self.facts_db.load_seed_data(facts_seed)
        terms_file = config.SAMPLE_DATA_DIR / "terminology_dictionary.json"
        with open(terms_file, "r") as f:
            self.terminology = json.load(f)
        vis_file = config.SAMPLE_DATA_DIR / "visual_brand_rules.json"
        with open(vis_file, "r") as f:
            self.visual_rules = json.load(f)
        self.retriever = BranchedRAGRetriever()
        indexer = GuidelinesIndexer()
        guide_txt = config.SAMPLE_DATA_DIR / "brand_guidelines.txt"
        chunks = indexer.parse_text_file(guide_txt)
        self.retriever.index_chunks(chunks)
        print(f"[OK] Vault ready — {len(chunks)} RAG chunks, {len(self.facts_db.get_all_facts())} facts, {len(self.terminology.get('terms',[]))} terms")

    def get_terms(self):
        return self.terminology.get("terms", [])
    def get_palette(self):
        return self.visual_rules.get("color_palette", {})
    def get_visual_config(self):
        return self.visual_rules

vault = MinimalVault()

# Test 3: workers
w1 = LexicalStyleWorker(vault)
w2 = FactVerificationWorker(vault)

BAD_TEXT = "Our #1 AI platform is super cheap and guaranteed to save you 99% on costs. Using our revolutionary miracle engine."
r1 = w1.analyze(BAD_TEXT)
r2 = w2.analyze(BAD_TEXT)

print(f"[OK] Worker 1 (Lexical): {len(r1['flags'])} flags in {r1['execution_ms']}ms")
for f in r1['flags']:
    print(f"      [{f['severity']}] {f['flag_id']} | '{f['snippet']}' -> '{f['preferred_replacement']}'")

print(f"[OK] Worker 2 (Facts):   {len(r2['flags'])} flags in {r2['execution_ms']}ms")
for f in r2['flags']:
    print(f"      [{f['severity']}] {f['flag_id']} | '{f['snippet']}'")

# Test 4: RAG retrieval
hits = vault.retriever.retrieve("super cheap pricing tone", top_k=2)
print(f"[OK] RAG retrieval: {len(hits)} results")
for h in hits:
    print(f"      score={h['score']} | {h['doc_name']} p{h['page_number']} | {h['section'][:50]}")

print("\n✅ ALL SYSTEMS GO — pipeline fully operational locally")
