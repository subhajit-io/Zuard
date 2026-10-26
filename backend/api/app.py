import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Ensure backend directory in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import config as config
from api.routes import router

app = FastAPI(
    title="Zuard - Static RAG & Governance Engine",
    description="4-Worker Deterministic Pre-Check + Branched RAG + Delta-Only LLM Pipeline",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)

# Mount frontend web portal
frontend_dir = getattr(config, "FRONTEND_DIR", config.BASE_DIR.parent / "frontend")
if not frontend_dir.exists():
    frontend_dir = config.BASE_DIR / "web"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")

def start():
    import uvicorn
    uvicorn.run("api.app:app", host=config.HOST, port=config.PORT, reload=False)

if __name__ == "__main__":
    start()
