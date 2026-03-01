"""
IntelResponse – FastAPI application entry point.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from .models import IncidentCreate, StatusUpdate
from .storage import (
    create_incident,
    get_incident,
    list_incidents,
    list_incidents_raw,
    update_incident,
)
from .extraction import extract_incident_features
from .scoring import compute_triage_score
from .similarity import get_similar_cases
from .recommendations import recommend_response
from .seed import seed_if_empty

# ---------------------------------------------------------------------------
# Lifespan – seed data on startup
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Seed the database with historical incidents if it's empty."""
    count = seed_if_empty()
    if count:
        print(f"[seed] Inserted {count} historical incidents.")
    yield


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="IntelResponse",
    description="AI-powered incident intelligence platform",
    version="0.2.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS – allow localhost frontends during development
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@app.get("/health")
async def health():
    """Simple health check."""
    return {"status": "ok"}

# ---------------------------------------------------------------------------
# Incident endpoints
# ---------------------------------------------------------------------------


@app.post("/incidents", status_code=status.HTTP_201_CREATED)
async def post_incident(body: IncidentCreate):
    """Create a new incident, run the intelligence pipeline, and return it."""
    # 1. Persist the raw incident
    incident = create_incident(body)

    # 2. Extract structured features
    structured = extract_incident_features(
        incident.report_text, incident.location_hint
    )

    # 3. Compute triage score
    triage = compute_triage_score(structured)

    # 4. Find similar historical cases (graceful if none exist)
    historical = list_incidents_raw()
    # Exclude the just-created incident from similarity search
    historical = [h for h in historical if h.get("id") != incident.id]
    similar = get_similar_cases(structured, historical, k=5)

    # 5. Generate recommendations
    recommended = recommend_response(structured, triage, similar)

    # 6. Persist enriched data back to the incident
    updated = update_incident(incident.id, {
        "structured": structured,
        "triage": triage,
        "recommended": recommended,
    })

    return updated


@app.get("/incidents")
async def get_incidents():
    """Return all incidents sorted by priority then created_at desc."""
    return list_incidents()


@app.get("/incidents/{incident_id}")
async def get_incident_by_id(incident_id: str):
    """Return a single incident or 404."""
    incident = get_incident(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@app.post("/incidents/{incident_id}/status")
async def update_incident_status(incident_id: str, body: StatusUpdate):
    """Update the status of an incident."""
    updated = update_incident(incident_id, {"status": body.status})
    if updated is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return updated
