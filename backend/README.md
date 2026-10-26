# Zuard Backend Engine

The core deterministic pre-check (~2ms, 0 LLM cost) + Branched Multimodal RAG + Delta-Only Synthesizer engine.

## Architecture

```
backend/
├── api/
│   ├── app.py          # FastAPI application & static mounting
│   ├── routes.py       # REST API endpoints (/api/projects, /api/vault, /api/audit-content, etc.)
│   └── telemetry.py    # Compliance score and violation statistics
├── vault/
│   ├── brand_vault.py      # Unified 4-branch Brand Vault coordinator
│   ├── project_manager.py  # Multi-tenant workspace isolation manager
│   ├── facts_db.py         # SQLite verified metrics repository
│   ├── pdf_indexer.py      # Hierarchical PyMuPDF/pypdf document chunker
│   ├── rag_retriever.py    # Hybrid semantic TF-IDF + keyword citation retriever
│   ├── rule_extractor.py   # Dynamic rule, fact, and palette extractor
│   ├── sample_data/        # Default starter facts, terms, and palettes
│   └── projects/           # Isolated project workspaces with dedicated SQLite DBs
├── workers/
│   ├── orchestrator.py     # asyncio.gather concurrent parallel worker orchestrator
│   ├── worker_lexical.py   # Static Worker #1: Terminology & Textstat tone scanner
│   ├── worker_facts.py     # Static Worker #2: SQLite metric contradiction checker
│   ├── worker_visual.py    # Static Worker #3: OpenCV/PIL K-Means dominant color & CIELAB ΔE
│   └── worker_wcag.py      # Static Worker #4: Mathematical WCAG 2.1 relative luminance & contrast
├── synthesizer/
│   ├── delta_synthesizer.py# Minimal delta payload synthesizer generating Inspector Cards
│   └── models.py           # Pydantic data models
├── tests/                  # Integration & unit test suites
├── config.py               # Environment configuration and thresholds
├── run.py                  # CLI runner (--serve, --test, --audit)
└── test_pipeline.py        # Complete 6-dimension pipeline verification
```

## Quick Start

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Start Backend Server
```bash
python run.py --serve
```
Access the Swagger documentation at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

### 3. Run Pipeline Tests
```bash
python test_pipeline.py
python tests/test_complex_realworld_fintech.py
python tests/test_multi_project.py
```
