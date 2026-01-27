import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv()

from core.config import get_settings
from core.pipeline import ingest

if __name__ == "__main__":
    settings = get_settings()
    result = ingest(settings)
    print("Ingest complete:", result)
