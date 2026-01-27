from dotenv import load_dotenv
load_dotenv()

from core.config import get_settings
from core.pipeline import ingest

if __name__ == "__main__":
    settings = get_settings()
    result = ingest(settings)
    print("Ingest complete:", result)
