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

## Seed Data

On first startup, if `app/data/incidents.json` is empty or missing, the server **automatically seeds 30 historical incidents** covering all incident types (medical, fire/smoke, violence, suspicious person, crowd risk, traffic accident, other).

Each seed incident includes:
- `report_text` – realistic free-text report
- `structured` – extracted features (incident type, entities, risk factors)
- `triage` – score (0-100) and priority (P0-P3)
- `outcome` – `resolved`, `escalated`, or `false_alarm`
- `response_taken` – `monitor`, `verbal_engagement`, `security_dispatched`, `medical_dispatched`, or `evacuation`

To **re-seed**, simply delete (or empty) the data file and restart:

```bash
rm app/data/incidents.json
uvicorn app.main:app --reload --port 8000
# → [seed] Inserted 30 historical incidents.
```

The similarity engine uses only incidents with a non-null `outcome` as historical references, so new (unresolved) incidents don't pollute the comparison corpus.

## API Endpoints

| Method | Path                          | Description                      |
|--------|-------------------------------|----------------------------------|
| GET    | `/health`                     | Health check                     |
| POST   | `/incidents`                  | Create a new incident            |
| GET    | `/incidents`                  | List all incidents (sorted)      |
| GET    | `/incidents/{id}`             | Get a single incident            |
| POST   | `/incidents/{id}/status`      | Update incident status           |
| GET    | `/stats`                      | Aggregate counts by outcome & type |

### Create an incident

```bash
curl -X POST http://localhost:8000/incidents \
  -H "Content-Type: application/json" \
  -d '{"source":"hotline_text","report_text":"Man with knife at MRT station, 2 injured","location_hint":"Orchard"}'
```

### Update status

```bash
curl -X POST http://localhost:8000/incidents/<ID>/status \
  -H "Content-Type: application/json" \
  -d '{"status":"resolved"}'
```

### Get stats

```bash
curl http://localhost:8000/stats
```
