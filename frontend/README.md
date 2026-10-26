# Zuard Web Portal (Frontend)

The modern, ultra-responsive web portal for **Zuard Real-Time Brand Governance & Pre-Screening**.

## Architecture & Features
- **Project Workspace Switcher**: Live dropdown to switch between isolated company projects (e.g., Enterprise B2B, Consumer Mobile, FinTech Banking).
- **Dynamic New Project Modal**: Create new project brand workspaces with dedicated tone personas, color palettes, and guideline document uploads.
- **Drag-and-Drop Guideline Ingestion**: Ingest PDFs or text guidelines directly into the active project workspace with real-time progress indicators.
- **Side-by-Side Diff & Interactive Highlighter**: Visual inspection comparing original draft vs. suggested zero-hallucination compliance rewrites.
- **Zero-Hallucination Inspector Cards**: Detailed flag cards citing exact page, section, and study IDs, with 1-click "Accept Fix" or "Ignore Flag" buttons.
- **Brand Vault & Visual Identity Explorer**: Inspect approved facts, SQLite audit metrics, terminology dictionaries, and verified hex swatches.
- **Governance Intelligence & Analytics**: Interactive radar charts (Chart.js), violation trends, and exportable JSON/PDF audit reports.

## Running Locally

### Option A: Unified Full-Stack (Recommended)
When running the Zuard backend server, the frontend is automatically mounted and served at:
```bash
http://127.0.0.1:8000
```

### Option B: Standalone Web Server
To run the frontend on a separate port or static host (e.g. port 3000):
```bash
cd frontend
npx serve -l 3000 .
```
The frontend automatically connects to the backend API at `http://127.0.0.1:8000/api` or the URL configured in `window.ZUARD_API_URL`.
