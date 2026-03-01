"""
IntelResponse – File-based JSON storage layer.

All incidents are persisted in backend/app/data/incidents.json.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import Incident, IncidentCreate

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_FILE = DATA_DIR / "incidents.json"

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

# Priority ordering for triage severity (lower index = higher priority).
_PRIORITY_ORDER: Dict[str, int] = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
}
_LOWEST_PRIORITY = 99  # used when triage is absent


def _ensure_file() -> None:
    """Create the data directory and JSON file if they don't exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        DATA_FILE.write_text("[]", encoding="utf-8")


def _read_db() -> List[Dict[str, Any]]:
    """Read all incidents from disk."""
    _ensure_file()
    raw = DATA_FILE.read_text(encoding="utf-8")
    return json.loads(raw) if raw.strip() else []


def _write_db(records: List[Dict[str, Any]]) -> None:
    """Write the full incident list back to disk."""
    _ensure_file()
    DATA_FILE.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")


def _sort_key(record: Dict[str, Any]) -> tuple:
    """Sort by triage priority ASC then created_at DESC."""
    triage = record.get("triage")
    if isinstance(triage, dict):
        severity = triage.get("severity", "")
        priority = _PRIORITY_ORDER.get(severity, _LOWEST_PRIORITY)
    else:
        priority = _LOWEST_PRIORITY
    # Negate timestamp for descending order (ISO strings sort lexicographically).
    created = record.get("created_at", "")
    return (priority, _negate_iso(created))


def _negate_iso(iso: str) -> str:
    """Return a string that sorts in the opposite direction of *iso*.

    Works because ISO-8601 strings are lexicographically sortable.  We invert
    each character so that a normal ascending sort produces descending order.
    """
    # Simple character-level inversion relative to '~' (largest printable ASCII).
    return "".join(chr(126 - ord(c)) for c in iso)

# ---------------------------------------------------------------------------
# Public CRUD API
# ---------------------------------------------------------------------------


def list_incidents() -> List[Incident]:
    """Return all incidents sorted by priority (triage) then newest first."""
    records = _read_db()
    records.sort(key=_sort_key)
    return [Incident(**r) for r in records]


def get_incident(incident_id: str) -> Optional[Incident]:
    """Return a single incident by *id*, or ``None`` if not found."""
    for record in _read_db():
        if record["id"] == incident_id:
            return Incident(**record)
    return None


def create_incident(data: IncidentCreate) -> Incident:
    """Create a new incident, persist it, and return the full model."""
    incident = Incident(
        id=str(uuid.uuid4()),
        created_at=datetime.now(timezone.utc).isoformat(),
        source=data.source,
        report_text=data.report_text,
        location_hint=data.location_hint,
        structured=None,
        triage=None,
        recommended=None,
        status="open",
    )
    records = _read_db()
    records.append(incident.model_dump())
    _write_db(records)
    return incident


def update_incident(incident_id: str, patch: Dict[str, Any]) -> Optional[Incident]:
    """Merge *patch* into the incident identified by *incident_id*.

    Returns the updated ``Incident`` or ``None`` if not found.
    """
    records = _read_db()
    for idx, record in enumerate(records):
        if record["id"] == incident_id:
            record.update(patch)
            records[idx] = record
            _write_db(records)
            return Incident(**record)
    return None
