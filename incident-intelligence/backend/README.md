# IntelResponse – Backend

FastAPI backend for the IntelResponse incident intelligence platform.

## Setup

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

The server starts at **http://127.0.0.1:8000**.

## API Endpoints

| Method | Path                          | Description                      |
|--------|-------------------------------|----------------------------------|
| GET    | `/health`                     | Health check                     |
| POST   | `/incidents`                  | Create a new incident            |
| GET    | `/incidents`                  | List all incidents (sorted)      |
| GET    | `/incidents/{id}`             | Get a single incident            |
| POST   | `/incidents/{id}/status`      | Update incident status           |

### Create an incident

```bash
curl -X POST http://localhost:8000/incidents \
  -H "Content-Type: application/json" \
  -d '{"source":"hotline_text","report_text":"Suspicious USB device found"}'
```

### Update status

```bash
curl -X POST http://localhost:8000/incidents/<ID>/status \
  -H "Content-Type: application/json" \
  -d '{"status":"resolved"}'
```
