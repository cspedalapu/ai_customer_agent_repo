import os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.config import get_settings
import uvicorn

if __name__ == "__main__":
    s = get_settings()
    uvicorn.run("apps.api.main:app", host=s.host, port=s.port, reload=True)
