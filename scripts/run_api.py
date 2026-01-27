import os
from dotenv import load_dotenv
load_dotenv()

import uvicorn
from core.config import get_settings

if __name__ == "__main__":
    s = get_settings()
    uvicorn.run("apps.api.main:app", host=s.host, port=s.port, reload=True)
