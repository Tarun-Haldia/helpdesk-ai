# 🛡️ HelpDesk AI — AI-Powered Self-Service Support System

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Render-0070D2?style=flat&logo=render)](https://helpdesk-ai-app.onrender.com)
[![API Docs](https://img.shields.io/badge/API%20Docs-Swagger-2E844A?style=flat&logo=fastapi)](https://helpdesk-ai-5ze4.onrender.com/docs)
[![GitHub](https://img.shields.io/badge/GitHub-helpdesk--ai-181818?style=flat&logo=github)](https://github.com/Tarun-Haldia/helpdesk-ai)

## Problem Statement

Organizations receive thousands of repetitive IT support tickets weekly.
Users wait hours for responses to issues that have standard solutions.
This project eliminates that wait by letting users self-resolve issues
through an AI pipeline — no engineer required for common problems.

## Live Demo



| Service | URL |
|---|---|
| Frontend (Streamlit) | https://helpdesk-ai-app.onrender.com |
| Backend API (FastAPI) | https://helpdesk-ai-5ze4.onrender.com |
| Swagger Docs | https://helpdesk-ai-5ze4.onrender.com/docs |

## Architecture

User → Streamlit UI

↓

FastAPI Backend

↓              ↓                    ↓

ML Classifier   Semantic Search      Gemini LLM

(scikit-learn)  (pgvector HNSW)   (solution gen)

↓              ↓

└──── Supabase PostgreSQL ────┘

## Key Results

| Metric | Value |
|---|---|
| Test Accuracy | **88.3%** |
| Mean F1 Score | **87.9%** |
| Intent Classes | 20 |
| Training Samples | 1,022 |
| Embedding Model | all-MiniLM-L6-v2 (384-dim) |
| Vector Index | HNSW cosine similarity |
| Confidence Threshold | 60% (auto-escalates below) |

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| Backend | FastAPI + Uvicorn |
| ML Classification | Scikit-Learn (LinearSVC + CalibratedCV) |
| Embeddings | fastembed (all-MiniLM-L6-v2 ONNX) |
| Vector Search | Supabase pgvector (HNSW index) |
| Database | Supabase PostgreSQL |
| LLM | Google Gemini 2.0 Flash Lite |
| Training | Google Colab (T4 GPU) |
| Deployment | Render (free tier) |
| Version Control | GitHub |

## How It Works

1. **User selects category** from 12 issue types (click-based, no typing needed)
2. **User describes issue** with quick-select prompts or free text
3. **ML classifier** predicts intent with confidence score
4. **Semantic search** retrieves top-3 similar historical tickets via pgvector
5. **Gemini LLM** generates step-by-step solution from retrieved context
6. **Confidence gate** — below 60% → auto-escalates to support engineer
7. **User feedback** (resolved/not resolved) logged for future improvement

## Project Structure

helpdesk-ai/

├── api/

│   ├── main.py          # FastAPI app + startup

│   ├── classifier.py    # ML prediction + confidence

│   ├── retriever.py     # pgvector semantic search

│   ├── gemini.py        # LLM solution generation

│   ├── routes.py        # API endpoints

│   ├── models.py        # Pydantic schemas

│   └── database.py      # SQLAlchemy + Supabase

├── frontend/

│   └── app.py           # Streamlit UI (3-step wizard)

├── render.yaml          # Render deployment config

└── requirements.txt

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/query` | Classify + retrieve + generate solution |
| POST | `/api/v1/ticket` | Create escalation ticket |
| POST | `/api/v1/feedback` | Submit resolved/not resolved |
| GET | `/api/v1/tickets` | List open tickets |
| GET | `/api/v1/health` | Health check |

## Local Setup

```bash
git clone https://github.com/Tarun-Haldia/helpdesk-ai.git
cd helpdesk-ai
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Add .env file with:
# SUPABASE_URL, SUPABASE_KEY, SUPABASE_DB_URL
# GEMINI_API_KEY, CONFIDENCE_THRESHOLD=60

# Terminal 1
cd api && uvicorn main:app --reload --port 8000

# Terminal 2
streamlit run frontend/app.py
```

## Author

**Tarun Haldia**
[GitHub](https://github.com/Tarun-Haldia/helpdesk-ai)
