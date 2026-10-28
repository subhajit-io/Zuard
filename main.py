import os
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Expose app for ASGI servers: uvicorn main:app --host 0.0.0.0 --port $PORT
from api.app import app

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0" if os.environ.get("RENDER") else os.environ.get("HOST", "0.0.0.0")
    print(f"Starting Zuard on {host}:{port}")
    uvicorn.run("main:app", host=host, port=port, reload=False)
