import os
import subprocess
from dotenv import load_dotenv
load_dotenv()

if __name__ == "__main__":
    subprocess.run(["streamlit", "run", "apps/dashboard/app.py"], check=False)
