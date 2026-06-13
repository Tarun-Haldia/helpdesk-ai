# api/start.py
import sys
import os
from pathlib import Path

api_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(api_dir))
os.chdir(api_dir)

# Limit torch threads to save RAM on Render free tier
os.environ["OMP_NUM_THREADS"]        = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["TORCH_NUM_THREADS"]      = "1"

import uvicorn
uvicorn.run(
    "main:app",
    host    = "0.0.0.0",
    port    = int(os.getenv("PORT", 8000)),
    reload  = False,
    workers = 1
)