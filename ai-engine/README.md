# QSFI AI Engine

FastAPI backend for the QSFI platform: uploads a calibration CSV, cleans it,
computes per-qubit QSFI and stability status, saves each analysis, and
compares the two most recent ones.

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Liveness check |
| POST | `/upload` | Validate and store a CSV, report its shape |
| POST | `/analyze` | Upload + analyze, persisting the result |
| GET | `/history` | List saved analyses, newest first |
| GET | `/compare/latest` | Compare the two most recent analyses |

Interactive docs at `/docs`.

## Structure

```
ai-engine/
├── main.py           # FastAPI app, CORS, route registration
├── requirements.txt
├── runtime.txt        # Python version pin for deployment
├── .env.example       # All supported AI_ENGINE_* settings
├── uploads/           # Incoming files (e.g. calibration CSVs) awaiting processing
├── processed/         # Saved analysis JSON, read by /history and /compare/latest
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

## Run (development)

```bash
uvicorn main:app --reload --port 8001
```

## Verify

```bash
curl http://localhost:8001/health
# {"status":"running"}
```

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

## Configuration

Every value in `utils/config.py` is overridable with an `AI_ENGINE_`-prefixed
environment variable (or a local `.env`). See `.env.example` for the full list
and defaults; the app runs correctly with none of them set.

The two that matter for deployment:

- `AI_ENGINE_ALLOWED_ORIGINS` — JSON list. Add the deployed frontend origin,
  e.g. `["https://qsfi.example.app"]`. Never `"*"`: the API sends credentials,
  which browsers reject alongside a wildcard.
- `AI_ENGINE_PROCESSED_DIR` — absolute path to a persistent volume in
  production. `/history` and `/compare/latest` read every JSON file in it, so
  on ephemeral storage all analysis history is lost on restart or redeploy.

## Deployment

`render.yaml` in the repository root defines the service. Production runs:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

No `--reload` — that is a development-only file watcher.

### Production storage

A 1 GB Render persistent disk (`qsfi-data`) is mounted at `/var/data`:

```
/var/data/                 # Render persistent disk mount
├── uploads/               # raw uploaded CSV files
└── processed/             # processed analysis JSON files
```

configured by:

```
AI_ENGINE_UPLOAD_DIR=/var/data/uploads
AI_ENGINE_PROCESSED_DIR=/var/data/processed
```

`/var/data` sits outside the repository checkout (`/opt/render/project/src`),
which Render replaces on every deploy. That is the whole point: anything
written inside the checkout is lost on redeploy.

- **`processed/` must persist.** `/history` lists every JSON file in it and
  `/compare/latest` reads the two most recent, so on ephemeral storage both
  endpoints silently reset to empty after each restart or deploy.
- **`uploads/` is retained for reproducibility.** Nothing re-reads the raw CSV
  after the initial parse, so this is source-file retention for audit and
  re-analysis rather than a functional requirement. It is also the storage
  that actually grows — an analysis JSON is roughly 27 KB, while an upload can
  be up to the 10 MB limit — so it is the first thing to prune if space runs
  short. No automatic cleanup or retention policy exists yet.

Two consequences of attaching a disk: it **requires the Render Starter plan**
(disks are unavailable on the free plan), and it pins the service to a single
instance with zero-downtime deploys disabled.

`main.py` creates both directories at startup, so an unwritable or
misconfigured mount fails immediately at boot rather than on the first upload.

**Local development is unaffected.** With these environment variables absent,
the defaults in `utils/config.py` still apply — the relative `uploads` and
`processed` directories inside `ai-engine/`. Set the absolute production
values only in Render, never in a local `.env`.

### Not production-ready for public multi-user use

**There is no authentication and no user isolation.** Every endpoint is public,
and `/history` and `/compare/latest` operate on the entire `processed/`
directory, so any caller can list every other caller's analyses and
`/compare/latest` may compare one person's upload against a stranger's.

Adding a persistent disk makes this sharing **permanent** rather than fixing
it. Until user isolation is implemented, deploy this service privately or
behind access control — do not expose it for unrestricted public use.
