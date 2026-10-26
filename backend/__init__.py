import sys
from pathlib import Path

# Auto-add backend directory to sys.path so modules can import directly
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
