# Zuard — Real-Time Brand Governance & Pre-Screening Engine

> **Sub-5ms Deterministic Pre-Check (~0 LLM Cost) • Branched Multimodal RAG • Zero-Hallucination Synthesizer • Multi-Tenant / Multi-Project Isolation**

---

## 🌟 Overview

**Zuard** is a real-time brand governance and pre-screening platform designed for enterprises and high-velocity marketing organizations. It enforces brand guidelines, legal requirements, factual claims, and accessibility compliance across all marketing collateral, digital copy, and visual banners before publication.

Unlike traditional LLM wrappers that cost thousands of dollars and introduce 5–15 second latencies, Zuard utilizes a **two-stage architecture**:
1. **4 Concurrent Deterministic Static Workers (~2–4ms, $0 LLM cost)** execute first, checking 90%+ of mechanical compliance rules locally.
2. **Delta-Only Synthesizer with Branched RAG Citations** processes only the flagged snippets, drastically reducing token usage while citing exact page numbers, section headers, and third-party study IDs with zero hallucinations.

---

## 📁 Repository Structure

The project is cleanly separated into `frontend`, `backend`, and `docs`:

```
zuard/
├── frontend/                        # Web client portal
│   ├── index.html                   # Modern dark-mode dashboard UI
│   ├── styles.css                   # Glassmorphic UI design system
│   ├── app.js                       # Interactive controller & REST API client
│   ├── package.json                 # Web server scripts
│   └── README.md                    # Frontend documentation
│
├── backend/                         # Core Python FastAPI governance engine
│   ├── api/
│   │   ├── app.py                   # FastAPI application & static mount
│   │   ├── routes.py                # REST API endpoints
│   │   └── telemetry.py             # Compliance audit telemetry
│   ├── vault/
│   │   ├── brand_vault.py           # Unified 4-branch Brand Vault coordinator
│   │   ├── project_manager.py       # Multi-project workspace isolation
│   │   ├── facts_db.py              # SQLite facts & verified claims repository
│   │   ├── pdf_indexer.py           # PyMuPDF/pypdf document hierarchy chunker
│   │   ├── rag_retriever.py         # Hybrid semantic TF-IDF + keyword retriever
│   │   ├── rule_extractor.py        # Dynamic rule, fact, and palette extractor
│   │   ├── sample_data/             # Seed facts, terms, and palettes
│   │   └── projects/                # Isolated project workspaces
│   ├── workers/
│   │   ├── orchestrator.py          # asyncio.gather concurrent parallel worker executor
│   │   ├── worker_lexical.py        # Worker #1: Terminology & Textstat tone scanner
│   │   ├── worker_facts.py          # Worker #2: SQLite metric contradiction checker
│   │   ├── worker_visual.py         # Worker #3: OpenCV/PIL K-Means dominant color & CIELAB ΔE
│   │   └── worker_wcag.py           # Worker #4: Mathematical WCAG 2.1 contrast math
│   ├── synthesizer/
│   │   ├── delta_synthesizer.py     # Minimal delta payload synthesizer generating Inspector Cards
│   │   └── models.py                # Pydantic data schemas
│   ├── tests/
│   │   ├── test_complex_realworld_fintech.py # 6-Dimension FinTech integration test
│   │   ├── test_dynamic_adaptation.py        # Dynamic guideline ingestion test
│   │   └── test_multi_project.py             # Cross-project isolation test
│   ├── config.py                    # Environment thresholds and settings
│   ├── run.py                       # Backend server & CLI runner
│   ├── test_pipeline.py             # Full pipeline test suite
│   ├── requirements.txt             # Python dependencies
│   ├── Dockerfile                   # Backend Docker container specification
│   └── README.md                    # Backend documentation
│
├── docs/                            # Architectural design documents
│   ├── Zuard_Round1_Plan.pdf        # Architecture blueprint
│   └── extracted_plan_text.txt      # Text transcript of blueprint
│
├── docker-compose.yml               # Multi-container orchestration
├── run.py                           # Root developer convenience runner
├── .gitignore                       # Production Git ignore patterns
└── README.md                        # Master repository documentation
```

---

## ⚡ Quick Start

### 1. Installation
Clone the repository and install backend dependencies:
```bash
git clone https://github.com/subhajit-io/zuard.git
cd zuard/backend
pip install -r requirements.txt
```

### 2. Start the Server
Run the unified server from the repository root:
```bash
python run.py --serve
```
- **Web Portal:** Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.
- **REST API Docs (Swagger):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 3. Run Test Suites
```bash
# Main 6-dimension pipeline verification
python run.py --test

# Complex 6-dimension FinTech regulatory test
python backend/tests/test_complex_realworld_fintech.py

# Multi-project governance isolation test
python backend/tests/test_multi_project.py

# Dynamic guideline learning & worker re-instruction test
python backend/tests/test_dynamic_adaptation.py
```

### 4. Run via Docker Compose
```bash
docker-compose up --build
```
- Backend runs on `http://127.0.0.1:8000`
- Frontend runs on `http://127.0.0.1:3000`

---

## 🛡️ Six Governance Dimensions

| Dimension | Worker | Method | Latency |
| :--- | :--- | :--- | :--- |
| **1. Tone & Reading Ease** | Static Worker #1 | Flesch-Kincaid & Gunning Fog via `textstat` | < 1ms |
| **2. Terminology & Slang** | Static Worker #1 | Subspan-aware compiled regex dictionary | < 1ms |
| **3. Claims & Superlatives**| Static Worker #2 | Boundary-aware superlative pattern engine | < 1ms |
| **4. Fact Verification** | Static Worker #2 | Dynamic query against project SQLite database | 1–2ms |
| **5. Visual Harmony** | Static Worker #3 | OpenCV K-Means clustering & CIELAB $\Delta E$ (CIE76) | 2–3ms |
| **6. Accessibility** | Static Worker #4 | WCAG 2.1 relative luminance math ($4.5:1$ AA, $7:1$ AAA) | < 1ms |

---

## 🏢 Multi-Project Isolation

A single organization often has multiple brands, products, or divisions with conflicting guidelines. Zuard isolates each project:
- **Dedicated SQLite Databases**: Stores audited metrics per project (`project_facts.db`).
- **Dedicated Branched RAG Indexes**: Isolated vector representations of project guideline documents.
- **Dynamic Ingestion**: Ingesting a new guideline PDF automatically extracts rules and re-instructs the 4 static workers in real-time.

---

## 📜 License

Apache License 2.0. Built by [subhajit-io](https://github.com/subhajit-io).
