# api/check_env.py — debug env loading
from pathlib import Path
from dotenv import load_dotenv
import os

# Load .env from root
env_path = Path(__file__).resolve().parent.parent / ".env"
print(f"Looking for .env at: {env_path}")
print(f".env file exists: {env_path.exists()}")

load_dotenv(dotenv_path=env_path)

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

print(f"\nSUPABASE_URL = {url}")
print(f"SUPABASE_KEY = {key[:20] if key else 'NOT FOUND'}...")