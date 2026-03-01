"""
IntelResponse – Seed data for development / demo.

Provides a small corpus of pre-structured historical incidents so that the
similarity engine can return results immediately after first start-up.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List

from .extraction import extract_incident_features
from .scoring import compute_triage_score

# ---------------------------------------------------------------------------
# Raw seed reports
# ---------------------------------------------------------------------------

_SEED_REPORTS: List[Dict[str, Any]] = [
    {
        "source": "hotline_text",
        "report_text": (
            "Two men fighting outside a bar on Clarke Quay, one has a broken "
            "bottle, crowd of about 15 people watching, one person bleeding "
            "from the head."
        ),
        "location_hint": "Clarke Quay",
    },
    {
        "source": "radio_transcript",
        "report_text": (
            "Smoke coming from the 5th floor of a residential building on "
            "Tampines Street 21. Residents evacuating. No injuries reported yet."
        ),
        "location_hint": "Tampines Street 21",
    },
    {
        "source": "citizen_app",
        "report_text": (
            "Suspicious man loitering near the primary school entrance on "
            "Bukit Timah Road. Wearing a dark hoodie, carrying a large bag. "
            "Has been there for over 30 minutes."
        ),
        "location_hint": "Bukit Timah Road",
    },
    {
        "source": "hotline_text",
        "report_text": (
            "Major traffic accident on PIE near Toa Payoh exit. 3 vehicles "
            "involved including a motorcycle. 2 people injured, one trapped "
            "in the car."
        ),
        "location_hint": "PIE Toa Payoh Exit",
    },
    {
        "source": "radio_transcript",
        "report_text": (
            "Large crowd gathering at Speakers Corner, estimated 200 people, "
            "some pushing and shoving at the front. Situation could escalate. "
            "Drunk individuals spotted."
        ),
        "location_hint": "Speakers Corner",
    },
    {
        "source": "citizen_app",
        "report_text": (
            "Elderly woman collapsed at Bedok MRT station, appears unconscious, "
            "bystanders performing CPR. No AED available on site."
        ),
        "location_hint": "Bedok MRT",
    },
]

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_seed_incidents() -> List[Dict[str, Any]]:
    """Return pre-built historical incidents with extraction & triage data.

    Each incident is fully processed (structured, triaged) so the similarity
    engine can use them immediately.
    """
    incidents: List[Dict[str, Any]] = []
    base_time = datetime.now(timezone.utc) - timedelta(days=7)

    for idx, raw in enumerate(_SEED_REPORTS):
        created_at = (base_time + timedelta(hours=idx * 6)).isoformat()

        structured = extract_incident_features(
            raw["report_text"], raw.get("location_hint")
        )
        triage = compute_triage_score(structured)

        incidents.append({
            "id": str(uuid.uuid4()),
            "created_at": created_at,
            "source": raw["source"],
            "report_text": raw["report_text"],
            "location_hint": raw.get("location_hint"),
            "structured": structured,
            "triage": triage,
            "recommended": None,   # historical records don't need live recs
            "status": "resolved",
        })

    return incidents


def seed_if_empty() -> int:
    """Populate the storage layer with seed data if it is currently empty.

    Returns the number of incidents inserted (0 if storage was not empty).
    """
    # Import here to avoid circular dependency at module level
    from .storage import _read_db, _write_db

    records = _read_db()
    if records:
        return 0

    seed = get_seed_incidents()
    _write_db(seed)
    return len(seed)
