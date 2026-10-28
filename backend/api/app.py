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
@app.middleware("http")
async def add_no_cache_headers(request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)

# Mount frontend web portal — prefer web/, fall back to frontend/
web_dir = config.BASE_DIR.parent / "web"
frontend_dir = config.BASE_DIR.parent / "frontend"
serve_dir = web_dir if web_dir.exists() else frontend_dir
if serve_dir.exists():
    app.mount("/", StaticFiles(directory=str(serve_dir), html=True), name="frontend")

def start():
    import os
    import uvicorn
    host = "0.0.0.0" if os.environ.get("RENDER") else os.environ.get("HOST", getattr(config, "HOST", "0.0.0.0"))
    port = int(os.environ.get("PORT", getattr(config, "PORT", 8000)))
    uvicorn.run("api.app:app", host=host, port=port, reload=False)

if __name__ == "__main__":
    start()
