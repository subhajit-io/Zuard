import os
import sys
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
# Load environment variables from backend directory or parent
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR.parent / ".env")
load_dotenv()

# Ensure backend directory is in sys.path for direct imports
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

VAULT_DIR = BASE_DIR / "vault"
SAMPLE_DATA_DIR = VAULT_DIR / "sample_data"
DB_PATH = VAULT_DIR / "zuard_vault.db"

FRONTEND_DIR = BASE_DIR.parent / "web"
DOCS_DIR = BASE_DIR.parent / "docs"

# Delta-Only Synthesizer Settings
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "text-embedding-004")
LOCAL_PRIVACY_MODE = os.getenv("LOCAL_PRIVACY_MODE", "false").lower() in ("true", "1", "yes")

# Worker 1: Lexical & Style Thresholds
DEFAULT_READING_GRADE_MIN = 8.0
DEFAULT_READING_GRADE_MAX = 12.0
DEFAULT_READING_EASE_MIN = 50.0

# Worker 2: Fact & Claim Thresholds
CLAIM_CONFIDENCE_THRESHOLD = 0.75

# Worker 3: Visual & Color Thresholds
DEFAULT_DELTA_E_THRESHOLD = 12.0
LOGO_ASPECT_RATIO_TOLERANCE_PCT = 5.0

# Worker 4: WCAG 2.1 Accessibility Standards
WCAG_AA_NORMAL_TEXT_CONTRAST = 4.5
WCAG_AA_LARGE_TEXT_CONTRAST = 3.0
WCAG_AAA_CONTRAST = 7.0

# Server Settings
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
