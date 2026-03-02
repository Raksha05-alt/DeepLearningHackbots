"""
IntelResponse – FastAPI application entry point.
Two-tab dispatch workflow: Incoming Reports + Active Incidents.
"""

from collections import Counter
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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
# In-memory stores for the dispatch workflow
# ---------------------------------------------------------------------------

_incoming_reports: List[Dict[str, Any]] = []
_active_incidents: List[Dict[str, Any]] = []


def _seed_reports() -> None:
    """Populate incoming reports with simulated data."""
    global _incoming_reports
    reports = [
        {
            "id": str(uuid.uuid4()),
            "text": "Man with knife threatening shoppers at Orchard MRT platform. Two people injured, crowd forming.",
            "location": "Orchard MRT Station",
            "type": "violence_conflict",
            "risk_level": "critical",
            "confidence": 0.95,
            "source": "hotline",
            "time": datetime.now(timezone.utc).isoformat(),
            "extracted_features": {
                "incident_type": "violence_conflict",
                "key_entities": {"location": "Orchard MRT Station", "people_count": 2, "injuries_present": True, "weapon_mentioned": True, "smoke_fire_present": False},
                "risk_factors": {"aggression_level": 3, "crowd_level": 2, "intoxication_suspected": False, "active_threat": True},
                "confidence": 0.95,
                "missing_info": [],
            },
            "triage": {"score": 95, "priority": "P0", "reasons": ["weapon mentioned", "active threat detected", "injuries reported"]},
            "recommended": {"action": "dispatch_now", "follow_up_questions": ["How many attackers?", "Are police already on scene?", "Is crowd dispersing or growing?"], "checklist": ["Dispatch armed response team", "Alert nearby hospitals", "Secure perimeter", "Deploy crowd control"], "rationale": "Active weapon threat with injuries. Immediate armed response required."},
        },
        {
            "id": str(uuid.uuid4()),
            "text": "Smoke visible from 3rd floor window of HDB block at Ang Mo Kio Ave 6. Residents starting to evacuate.",
            "location": "Ang Mo Kio Ave 6, Block 412",
            "type": "fire_smoke",
            "risk_level": "critical",
            "confidence": 0.90,
            "source": "citizen",
            "time": datetime.now(timezone.utc).isoformat(),
            "extracted_features": {
                "incident_type": "fire_smoke",
                "key_entities": {"location": "Ang Mo Kio Ave 6, Block 412", "people_count": None, "injuries_present": False, "weapon_mentioned": False, "smoke_fire_present": True},
                "risk_factors": {"aggression_level": 0, "crowd_level": 1, "intoxication_suspected": False, "active_threat": False},
                "confidence": 0.90,
                "missing_info": ["Exact floor", "Number of residents affected"],
            },
            "triage": {"score": 78, "priority": "P1", "reasons": ["fire/smoke detected", "residential area", "evacuation in progress"]},
            "recommended": {"action": "dispatch_now", "follow_up_questions": ["Which exact floor?", "Any elderly or disabled residents?", "Has SCDF been called?"], "checklist": ["Dispatch fire engine", "Alert SCDF", "Coordinate evacuation", "Set up assembly point"], "rationale": "Active fire/smoke in residential building with residents evacuating. Requires immediate fire response."},
        },
        {
            "id": str(uuid.uuid4()),
            "text": "Suspicious unattended bag left near bus stop at Tampines MRT. Black backpack sitting alone for 20+ minutes.",
            "location": "Tampines MRT Bus Interchange",
            "type": "suspicious_person",
            "risk_level": "high",
            "confidence": 0.70,
            "source": "citizen",
            "time": datetime.now(timezone.utc).isoformat(),
            "extracted_features": {
                "incident_type": "suspicious_person",
                "key_entities": {"location": "Tampines MRT Bus Interchange", "people_count": None, "injuries_present": False, "weapon_mentioned": False, "smoke_fire_present": False},
                "risk_factors": {"aggression_level": 0, "crowd_level": 2, "intoxication_suspected": False, "active_threat": False},
                "confidence": 0.70,
                "missing_info": ["Description of bag owner", "Has anyone touched the bag"],
            },
            "triage": {"score": 55, "priority": "P2", "reasons": ["suspicious item in public area", "high-traffic location", "extended unattended duration"]},
            "recommended": {"action": "dispatch_soon", "follow_up_questions": ["Can you describe the bag in detail?", "Is there CCTV coverage?", "How close are civilians?"], "checklist": ["Dispatch bomb disposal unit", "Cordon off area", "Check CCTV footage", "Interview nearby witnesses"], "rationale": "Unattended item in high-traffic transit area. Warrants investigation with bomb disposal standby."},
        },
        {
            "id": str(uuid.uuid4()),
            "text": "Two groups of men arguing loudly outside bar at Clarke Quay. About 8-10 people involved, some pushing.",
            "location": "Clarke Quay, Block 3A",
            "type": "violence_conflict",
            "risk_level": "high",
            "confidence": 0.85,
            "source": "hotline",
            "time": datetime.now(timezone.utc).isoformat(),
            "extracted_features": {
                "incident_type": "violence_conflict",
                "key_entities": {"location": "Clarke Quay, Block 3A", "people_count": 10, "injuries_present": False, "weapon_mentioned": False, "smoke_fire_present": False},
                "risk_factors": {"aggression_level": 2, "crowd_level": 2, "intoxication_suspected": True, "active_threat": False},
                "confidence": 0.85,
                "missing_info": ["Any weapons visible?"],
            },
            "triage": {"score": 60, "priority": "P1", "reasons": ["physical confrontation", "multiple individuals", "alcohol likely involved"]},
            "recommended": {"action": "dispatch_soon", "follow_up_questions": ["Are any weapons visible?", "Has anyone been hit?", "Are bouncers intervening?"], "checklist": ["Dispatch patrol unit", "Alert nearby units", "Monitor for escalation", "Prepare ambulance standby"], "rationale": "Group altercation with alcohol involvement. De-escalation team needed before situation worsens."},
        },
        {
            "id": str(uuid.uuid4()),
            "text": "Elderly man collapsed at bus stop near Bedok South. Passersby performing CPR. Ambulance requested.",
            "location": "Bedok South, Bus Stop 84349",
            "type": "medical",
            "risk_level": "critical",
            "confidence": 0.92,
            "source": "hotline",
            "time": datetime.now(timezone.utc).isoformat(),
            "extracted_features": {
                "incident_type": "medical",
                "key_entities": {"location": "Bedok South, Bus Stop 84349", "people_count": 1, "injuries_present": True, "weapon_mentioned": False, "smoke_fire_present": False},
                "risk_factors": {"aggression_level": 0, "crowd_level": 0, "intoxication_suspected": False, "active_threat": False},
                "confidence": 0.92,
                "missing_info": [],
            },
            "triage": {"score": 80, "priority": "P0", "reasons": ["cardiac event suspected", "CPR in progress", "elderly victim"]},
            "recommended": {"action": "dispatch_now", "follow_up_questions": ["Is the person breathing?", "How long has CPR been going?", "Is there an AED nearby?"], "checklist": ["Dispatch ambulance", "Guide bystander CPR via phone", "Locate nearest AED", "Alert receiving hospital"], "rationale": "Life-threatening medical emergency with bystander CPR in progress. Immediate ambulance dispatch critical."},
        },
        {
            "id": str(uuid.uuid4()),
            "text": "Reports of a man loitering near primary school at Jurong West. Parents concerned. No threatening behavior observed yet.",
            "location": "Jurong West Primary School",
            "type": "suspicious_person",
            "risk_level": "medium",
            "confidence": 0.55,
            "source": "citizen",
            "time": datetime.now(timezone.utc).isoformat(),
            "extracted_features": {
                "incident_type": "suspicious_person",
                "key_entities": {"location": "Jurong West Primary School", "people_count": 1, "injuries_present": False, "weapon_mentioned": False, "smoke_fire_present": False},
                "risk_factors": {"aggression_level": 0, "crowd_level": 0, "intoxication_suspected": False, "active_threat": False},
                "confidence": 0.55,
                "missing_info": ["Description of individual", "Duration of loitering", "Any interaction with children"],
            },
            "triage": {"score": 35, "priority": "P2", "reasons": ["proximity to school", "concerned parent reports", "no immediate threat"]},
            "recommended": {"action": "monitor", "follow_up_questions": ["What does the person look like?", "Has the person interacted with anyone?", "Is the school session active?"], "checklist": ["Dispatch patrol for welfare check", "Alert school security", "Check against known persons database"], "rationale": "Low-threat suspicious behavior near school. Patrol welfare check recommended for community reassurance."},
        },
        {
            "id": str(uuid.uuid4()),
            "text": "Multiple car accident at PIE near Toa Payoh exit. 3 vehicles involved. Traffic backing up significantly.",
            "location": "PIE, Toa Payoh Exit",
            "type": "traffic_accident",
            "risk_level": "high",
            "confidence": 0.88,
            "source": "hotline",
            "time": datetime.now(timezone.utc).isoformat(),
            "extracted_features": {
                "incident_type": "traffic_accident",
                "key_entities": {"location": "PIE, Toa Payoh Exit", "people_count": None, "injuries_present": False, "weapon_mentioned": False, "smoke_fire_present": False},
                "risk_factors": {"aggression_level": 0, "crowd_level": 0, "intoxication_suspected": False, "active_threat": False},
                "confidence": 0.88,
                "missing_info": ["Number of injured", "Are vehicles blocking lanes?"],
            },
            "triage": {"score": 50, "priority": "P2", "reasons": ["multiple vehicles involved", "expressway location", "traffic disruption"]},
            "recommended": {"action": "dispatch_soon", "follow_up_questions": ["Any injuries observed?", "How many lanes are blocked?", "Is there fuel spillage?"], "checklist": ["Dispatch traffic police", "Alert LTA for traffic management", "Standby ambulance", "Deploy tow truck"], "rationale": "Multi-vehicle accident on expressway. Traffic management and safety assessment needed."},
        },
        {
            "id": str(uuid.uuid4()),
            "text": "Large crowd gathering at East Coast Park for unauthorized event. Estimated 200+ people. No permit found.",
            "location": "East Coast Park, Area D",
            "type": "crowd_risk",
            "risk_level": "medium",
            "confidence": 0.75,
            "source": "citizen",
            "time": datetime.now(timezone.utc).isoformat(),
            "extracted_features": {
                "incident_type": "crowd_risk",
                "key_entities": {"location": "East Coast Park, Area D", "people_count": 200, "injuries_present": False, "weapon_mentioned": False, "smoke_fire_present": False},
                "risk_factors": {"aggression_level": 0, "crowd_level": 3, "intoxication_suspected": False, "active_threat": False},
                "confidence": 0.75,
                "missing_info": ["Nature of event", "Is it growing?"],
            },
            "triage": {"score": 40, "priority": "P2", "reasons": ["large unauthorized gathering", "crowd management risk", "public space"]},
            "recommended": {"action": "monitor", "follow_up_questions": ["What type of event is it?", "Any alcohol being served?", "Are there any agitators?"], "checklist": ["Dispatch community policing unit", "Monitor crowd size", "Check for event permits", "Identify exit routes"], "rationale": "Large unauthorized gathering. Monitor for escalation while checking permits."},
        },
    ]
    _incoming_reports = reports


def _seed_active_incidents() -> None:
    """Populate some pre-existing active incidents."""
    global _active_incidents
    now = datetime.now(timezone.utc)
    _active_incidents = [
        {
            "id": str(uuid.uuid4()),
            "summary": "Armed robbery at Clementi MRT",
            "location": "Clementi MRT Station",
            "priority": "P0",
            "status": "active",
            "type": "violence_conflict",
            "responders": [
                {"name": "SGT Tan Wei", "role": "Lead Officer", "unit": "Alpha-1"},
                {"name": "CPL Ng Li", "role": "Backup", "unit": "Alpha-2"},
                {"name": "AMB Unit 14", "role": "Medical", "unit": "EMS"},
            ],
            "timeline": [
                {"time": (now.replace(minute=max(now.minute - 45, 0))).isoformat(), "type": "report", "description": "Hotline report received: armed suspect at Clementi MRT"},
                {"time": (now.replace(minute=max(now.minute - 42, 0))).isoformat(), "type": "dispatch", "description": "Alpha-1 and Alpha-2 dispatched. ETA 8 minutes."},
                {"time": (now.replace(minute=max(now.minute - 35, 0))).isoformat(), "type": "radio", "description": "Alpha-1 on scene. Suspect cornered at platform level. Area cordoned."},
                {"time": (now.replace(minute=max(now.minute - 28, 0))).isoformat(), "type": "radio", "description": "Suspect apprehended. One civilian with minor injuries."},
                {"time": (now.replace(minute=max(now.minute - 25, 0))).isoformat(), "type": "update", "description": "AMB Unit 14 treating injured civilian. Non-life-threatening."},
            ],
            "extracted_features": {
                "incident_type": "violence_conflict",
                "key_entities": {"location": "Clementi MRT Station", "people_count": 1, "injuries_present": True, "weapon_mentioned": True, "smoke_fire_present": False},
                "risk_factors": {"aggression_level": 3, "crowd_level": 1, "intoxication_suspected": False, "active_threat": False},
                "confidence": 0.95,
                "missing_info": [],
            },
        },
        {
            "id": str(uuid.uuid4()),
            "summary": "Building fire at Toa Payoh Block 45",
            "location": "Toa Payoh Lorong 5, Block 45",
            "priority": "P1",
            "status": "deploying",
            "type": "fire_smoke",
            "responders": [
                {"name": "SCDF Engine 7", "role": "Fire Response", "unit": "Fire-7"},
                {"name": "SCDF Rescue 3", "role": "Search & Rescue", "unit": "Rescue-3"},
            ],
            "timeline": [
                {"time": (now.replace(minute=max(now.minute - 12, 0))).isoformat(), "type": "report", "description": "Citizen app report: smoke from 5th floor window of Block 45"},
                {"time": (now.replace(minute=max(now.minute - 10, 0))).isoformat(), "type": "dispatch", "description": "SCDF Engine 7 and Rescue 3 dispatched. ETA 6 minutes."},
                {"time": (now.replace(minute=max(now.minute - 5, 0))).isoformat(), "type": "radio", "description": "Engine 7 en route. Residents self-evacuating."},
            ],
            "extracted_features": {
                "incident_type": "fire_smoke",
                "key_entities": {"location": "Toa Payoh Lorong 5, Block 45", "people_count": None, "injuries_present": False, "weapon_mentioned": False, "smoke_fire_present": True},
                "risk_factors": {"aggression_level": 0, "crowd_level": 1, "intoxication_suspected": False, "active_threat": False},
                "confidence": 0.90,
                "missing_info": ["Exact unit on fire", "Number of elderly residents"],
            },
        },
        {
            "id": str(uuid.uuid4()),
            "summary": "Traffic pile-up on CTE Southbound",
            "location": "CTE Southbound, Braddell exit",
            "priority": "P2",
            "status": "active",
            "type": "traffic_accident",
            "responders": [
                {"name": "TP Unit 22", "role": "Traffic Police", "unit": "TP-22"},
            ],
            "timeline": [
                {"time": (now.replace(minute=max(now.minute - 30, 0))).isoformat(), "type": "report", "description": "Hotline report: 4-car pile-up on CTE Southbound near Braddell"},
                {"time": (now.replace(minute=max(now.minute - 27, 0))).isoformat(), "type": "dispatch", "description": "TP Unit 22 dispatched. Tow truck alerted."},
                {"time": (now.replace(minute=max(now.minute - 20, 0))).isoformat(), "type": "radio", "description": "TP-22 on scene. 2 lanes blocked. Directing traffic."},
                {"time": (now.replace(minute=max(now.minute - 10, 0))).isoformat(), "type": "update", "description": "One vehicle towed. Remaining vehicles movable. No injuries."},
            ],
            "extracted_features": {
                "incident_type": "traffic_accident",
                "key_entities": {"location": "CTE Southbound, Braddell exit", "people_count": None, "injuries_present": False, "weapon_mentioned": False, "smoke_fire_present": False},
                "risk_factors": {"aggression_level": 0, "crowd_level": 0, "intoxication_suspected": False, "active_threat": False},
                "confidence": 0.88,
                "missing_info": [],
            },
        },
    ]


# ---------------------------------------------------------------------------
# Lifespan – seed data on startup
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Seed the database and in-memory stores on startup."""
    count = seed_if_empty()
    if count:
        print(f"[seed] Inserted {count} historical incidents.")
    _seed_reports()
    print(f"[seed] Loaded {len(_incoming_reports)} incoming reports.")
    _seed_active_incidents()
    print(f"[seed] Loaded {len(_active_incidents)} active incidents.")
    yield


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="IntelResponse",
    description="AI-powered incident intelligence platform – dispatch workflow",
    version="0.4.0",
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
# Dispatch workflow endpoints
# ---------------------------------------------------------------------------


@app.get("/api/reports")
async def get_reports():
    """Return all incoming reports."""
    return _incoming_reports


@app.get("/api/reports/{report_id}")
async def get_report(report_id: str):
    """Return a single incoming report."""
    for r in _incoming_reports:
        if r["id"] == report_id:
            return r
    raise HTTPException(status_code=404, detail="Report not found")


@app.get("/api/incidents")
async def get_active_incidents():
    """Return all active incidents."""
    return _active_incidents


@app.get("/api/incidents/{incident_id}")
async def get_active_incident(incident_id: str):
    """Return a single active incident."""
    for inc in _active_incidents:
        if inc["id"] == incident_id:
            return inc
    raise HTTPException(status_code=404, detail="Incident not found")


class CreateFromReport(BaseModel):
    report_id: str


@app.post("/api/incidents/create_from_report", status_code=201)
async def create_from_report(body: CreateFromReport):
    """Promote an incoming report into an active incident."""
    # Find the report
    report = None
    report_idx = -1
    for i, r in enumerate(_incoming_reports):
        if r["id"] == body.report_id:
            report = r
            report_idx = i
            break

    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")

    now = datetime.now(timezone.utc).isoformat()

    incident = {
        "id": str(uuid.uuid4()),
        "summary": report["text"][:80],
        "location": report["location"],
        "priority": report.get("triage", {}).get("priority", "P2"),
        "status": "deploying",
        "type": report["type"],
        "responders": [],
        "timeline": [
            {"time": now, "type": "report", "description": f"Incident created from {report['source']} report"},
            {"time": now, "type": "update", "description": "Status: Deploying — awaiting responder assignment"},
        ],
        "extracted_features": report.get("extracted_features"),
    }

    # Remove from incoming, add to active
    _incoming_reports.pop(report_idx)
    _active_incidents.insert(0, incident)

    return incident


class TimelineEntry(BaseModel):
    type: str  # report | dispatch | radio | escalation | update | resolved
    description: str


@app.post("/api/incidents/{incident_id}/timeline")
async def add_timeline_entry(incident_id: str, body: TimelineEntry):
    """Append a timeline event to an active incident."""
    for inc in _active_incidents:
        if inc["id"] == incident_id:
            entry = {
                "time": datetime.now(timezone.utc).isoformat(),
                "type": body.type,
                "description": body.description,
            }
            inc["timeline"].append(entry)

            # Auto-update status if resolved
            if body.type == "resolved":
                inc["status"] = "resolved"

            return inc
    raise HTTPException(status_code=404, detail="Incident not found")


class StatusUpdateV2(BaseModel):
    status: str  # deploying | active | resolved


@app.post("/api/incidents/{incident_id}/status")
async def update_active_incident_status(incident_id: str, body: StatusUpdateV2):
    """Update status of an active incident."""
    for inc in _active_incidents:
        if inc["id"] == incident_id:
            inc["status"] = body.status
            now = datetime.now(timezone.utc).isoformat()
            inc["timeline"].append({
                "time": now,
                "type": "update",
                "description": f"Status changed to: {body.status}",
            })
            return inc
    raise HTTPException(status_code=404, detail="Incident not found")


# ---------------------------------------------------------------------------
# Legacy endpoints (kept for compatibility)
# ---------------------------------------------------------------------------


@app.post("/incidents", status_code=201)
async def post_incident(body: IncidentCreate):
    """Create a new incident via the intelligence pipeline."""
    incident = create_incident(body)
    structured = extract_incident_features(incident.report_text, incident.location_hint)
    triage = compute_triage_score(structured)
    historical = list_incidents_raw()
    historical = [h for h in historical if h.get("id") != incident.id]
    similar = get_similar_cases(structured, historical, k=5)
    recommended = recommend_response(structured, triage, similar)
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


# ---------------------------------------------------------------------------
# Stats endpoint
# ---------------------------------------------------------------------------


@app.get("/stats")
async def get_stats():
    """Return aggregate counts by outcome and incident_type."""
    records = list_incidents_raw()
    outcome_counts: Counter = Counter()
    type_counts: Counter = Counter()

    for r in records:
        outcome = r.get("outcome")
        if outcome:
            outcome_counts[outcome] += 1
        structured = r.get("structured")
        if isinstance(structured, dict):
            itype = structured.get("incident_type", "unknown")
            type_counts[itype] += 1

    return {
        "total_incidents": len(records),
        "by_outcome": dict(outcome_counts),
        "by_incident_type": dict(type_counts),
    }
