"""
IntelResponse – FastAPI application entry point.
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from .models import IncidentCreate, StatusUpdate
from .storage import create_incident, get_incident, list_incidents, update_incident

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="IntelResponse",
    description="AI-powered incident intelligence platform",
    version="0.1.0",
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
    """Create a new incident and return it."""
    incident = create_incident(body)
    return incident


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
