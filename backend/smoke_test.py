import sys, asyncio
sys.path.insert(0, '.')
import config
from vault.project_manager import MultiProjectManager

pm = MultiProjectManager()
orch = pm.get_orchestrator('default')
synth = pm.get_synthesizer('default')

text = 'Our #1 AI platform is super cheap and guaranteed to save you 99% on costs. Using our revolutionary miracle engine.'

async def run():
    result = await orch.run_parallel_audit(draft_text=text)
    print('Workers OK. Flags:', result['total_flags'], '| Score:', result['compliance_score'], '| Time:', result['total_execution_ms'], 'ms')
    print('Dimension breakdown:', result['dimension_breakdown'])
    resp = synth.synthesize('Test Doc', text, result)
    print('Synthesizer OK. Cards:', resp.total_violations_count)
    for card in resp.inspector_cards:
        print(f'  [{card.severity}] {card.flag_id} | {card.dimension} | snippet: "{card.original_snippet}" | cite: {card.cited_source[:60]}')
    print()
    print('RAG check (query: "super cheap pricing tone"):')
    vault = pm.get_vault('default')
    hits = vault.retriever.retrieve('super cheap pricing tone', top_k=2)
    for h in hits:
        print(f'  doc={h["doc_name"]} page={h["page_number"]} score={h["score"]} sec={h["section"]}')
    print()
    print('ALL GOOD - pipeline fully operational')

asyncio.run(run())
