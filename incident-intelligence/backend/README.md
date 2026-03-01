# IntelResponse – Backend

FastAPI backend for the IntelResponse incident intelligence platform.

## Setup
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

## Run
```bash
uvicorn app.main:app --reload
```

## Demo Flow
1. POST sample incident reports to `/api/incidents`
2. GET extracted IOCs from `/api/iocs`
3. GET risk scores from `/api/scores`
4. GET similar incidents from `/api/similar`

<!-- TODO: Add API documentation -->
