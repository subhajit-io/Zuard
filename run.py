import os
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Change current working directory to backend so all relative paths resolve
os.chdir(backend_dir)

if __name__ == "__main__":
    from run import main
    main()
