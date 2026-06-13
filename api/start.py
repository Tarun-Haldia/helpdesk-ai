# api/start.py
# Reliable startup script for Render deployment
# Sets Python path before uvicorn loads

import sys
import os
from pathlib import Path

# Add api/ to path so all imports resolve
api_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(api_dir))

# Change working directory to api/
os.chdir(api_dir)

# Now start uvicorn programmatically
import uvicorn
uvicorn.run(
    "main:app",
    host    = "0.0.0.0",
    port    = int(os.getenv("PORT", 8000)),
    reload  = False
)