# QSFI AI Engine

FastAPI backend for the QSFI platform. Currently exposes only a health
check; `services/`, `models/`, and `utils/` are scaffolded for the
upcoming AI/ML analysis and qubit recommendation features.

## Structure

```
ai-engine/
├── main.py           # FastAPI app, CORS, route registration
├── requirements.txt
├── uploads/           # Incoming files (e.g. calibration CSVs) awaiting processing
├── processed/         # Output of processing/analysis jobs
├── services/          # Business logic / future AI-ML inference services
├── models/            # Pydantic schemas and (future) ML model definitions
└── utils/             # Shared helpers and app configuration
```

## Setup

```bash
cd ai-engine
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt
```

## Run

```bash
uvicorn main:app --reload --port 8000
```

## Verify

```bash
curl http://localhost:8000/health
# {"status":"running"}
```
