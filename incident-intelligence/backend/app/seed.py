"""
IntelResponse – Seed data for development / demo.

Provides a corpus of 30 pre-structured historical incidents so that the
similarity engine can return meaningful results immediately after first
start-up.  Each incident includes an outcome and the response that was taken.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List

from .extraction import extract_incident_features
from .scoring import compute_triage_score

# ---------------------------------------------------------------------------
# Raw seed reports  (30 diverse incidents)
# ---------------------------------------------------------------------------

_SEED_REPORTS: List[Dict[str, Any]] = [
    # --- Medical (6) ---
    {
        "source": "hotline_text",
        "report_text": "Elderly woman collapsed at Bedok MRT station, appears unconscious, bystanders performing CPR. No AED available on site.",
        "location_hint": "Bedok MRT",
        "outcome": "resolved",
        "response_taken": "medical_dispatched",
    },
    {
        "source": "citizen_app",
        "report_text": "Man having a seizure on the floor at Jurong East mall food court. People are standing around but nobody seems trained to help.",
        "location_hint": "Jurong East Mall",
        "outcome": "resolved",
        "response_taken": "medical_dispatched",
    },
    {
        "source": "radio_transcript",
        "report_text": "Construction worker fell from scaffolding at Punggol site. Conscious but unable to move his legs, bleeding from head wound.",
        "location_hint": "Punggol Construction Site",
        "outcome": "escalated",
        "response_taken": "medical_dispatched",
    },
    {
        "source": "hotline_text",
        "report_text": "Child choking at a restaurant on East Coast Road. Parents panicking. Someone is attempting the Heimlich manoeuvre.",
        "location_hint": "East Coast Road",
        "outcome": "resolved",
        "response_taken": "medical_dispatched",
    },
    {
        "source": "citizen_app",
        "report_text": "Cyclist hit by opening car door at Tampines Ave 5. Cyclist on the ground, possible broken arm, conscious and alert.",
        "location_hint": "Tampines Ave 5",
        "outcome": "resolved",
        "response_taken": "medical_dispatched",
    },
    {
        "source": "hotline_text",
        "report_text": "Person fainted inside crowded bus 174 near Bishan. Bus has pulled over. Passenger appears dehydrated.",
        "location_hint": "Bishan",
        "outcome": "resolved",
        "response_taken": "medical_dispatched",
    },

    # --- Fire / Smoke (5) ---
    {
        "source": "radio_transcript",
        "report_text": "Smoke coming from the 5th floor of a residential building on Tampines Street 21. Residents evacuating. No injuries reported yet.",
        "location_hint": "Tampines Street 21",
        "outcome": "resolved",
        "response_taken": "evacuation",
    },
    {
        "source": "hotline_text",
        "report_text": "Kitchen fire in a HDB unit at Toa Payoh Lorong 4. Flames visible from window. Fire alarm triggered, residents in corridor.",
        "location_hint": "Toa Payoh Lorong 4",
        "outcome": "resolved",
        "response_taken": "evacuation",
    },
    {
        "source": "citizen_app",
        "report_text": "Car engine on fire in the carpark at Vivo City level B2. Thick black smoke. Sprinkler system has activated.",
        "location_hint": "Vivo City B2 Carpark",
        "outcome": "resolved",
        "response_taken": "evacuation",
    },
    {
        "source": "radio_transcript",
        "report_text": "Suspected gas leak at an industrial unit on Tuas South Ave 1. Strong smell of gas reported by multiple workers.",
        "location_hint": "Tuas South Ave 1",
        "outcome": "escalated",
        "response_taken": "evacuation",
    },
    {
        "source": "hotline_text",
        "report_text": "Small rubbish bin fire at a void deck on Yishun Ring Road. No injuries but smoke drifting towards the playground.",
        "location_hint": "Yishun Ring Road",
        "outcome": "resolved",
        "response_taken": "monitor",
    },

    # --- Violence / Conflict (5) ---
    {
        "source": "hotline_text",
        "report_text": "Two men fighting outside a bar on Clarke Quay, one has a broken bottle, crowd of about 15 people watching, one person bleeding from the head.",
        "location_hint": "Clarke Quay",
        "outcome": "resolved",
        "response_taken": "security_dispatched",
    },
    {
        "source": "citizen_app",
        "report_text": "Group of 4 teenagers punching a man near Ang Mo Kio MRT. Victim on the ground. Attackers still present.",
        "location_hint": "Ang Mo Kio MRT",
        "outcome": "escalated",
        "response_taken": "security_dispatched",
    },
    {
        "source": "radio_transcript",
        "report_text": "Domestic argument at Block 302 Hougang Ave 5. Shouting and sounds of things being thrown. Children heard crying inside the unit.",
        "location_hint": "Hougang Ave 5",
        "outcome": "resolved",
        "response_taken": "security_dispatched",
    },
    {
        "source": "hotline_text",
        "report_text": "Man with knife threatening staff at 7-Eleven on Geylang Road. Demanding money from the register. 2 customers inside.",
        "location_hint": "Geylang Road",
        "outcome": "escalated",
        "response_taken": "security_dispatched",
    },
    {
        "source": "citizen_app",
        "report_text": "Road rage incident on CTE near Braddell exit. Two drivers out of their cars pushing each other. Traffic building up.",
        "location_hint": "CTE Braddell Exit",
        "outcome": "resolved",
        "response_taken": "verbal_engagement",
    },

    # --- Suspicious Person (4) ---
    {
        "source": "citizen_app",
        "report_text": "Suspicious man loitering near the primary school entrance on Bukit Timah Road. Wearing a dark hoodie, carrying a large bag. Has been there for over 30 minutes.",
        "location_hint": "Bukit Timah Road",
        "outcome": "false_alarm",
        "response_taken": "verbal_engagement",
    },
    {
        "source": "hotline_text",
        "report_text": "Unknown person trying door handles of parked cars at Sengkang East Way carpark. Wearing gloves and looking around nervously.",
        "location_hint": "Sengkang East Way",
        "outcome": "escalated",
        "response_taken": "security_dispatched",
    },
    {
        "source": "radio_transcript",
        "report_text": "Woman reports being followed for three blocks by a man in a dark jacket near Novena MRT. She has ducked into a convenience store.",
        "location_hint": "Novena MRT",
        "outcome": "resolved",
        "response_taken": "security_dispatched",
    },
    {
        "source": "citizen_app",
        "report_text": "Someone spotted peering into ground-floor windows at Pasir Ris Street 11 at 2am. Left when a dog started barking.",
        "location_hint": "Pasir Ris Street 11",
        "outcome": "false_alarm",
        "response_taken": "monitor",
    },

    # --- Crowd Risk (4) ---
    {
        "source": "radio_transcript",
        "report_text": "Large crowd gathering at Speakers Corner, estimated 200 people, some pushing and shoving at the front. Situation could escalate. Drunk individuals spotted.",
        "location_hint": "Speakers Corner",
        "outcome": "resolved",
        "response_taken": "security_dispatched",
    },
    {
        "source": "hotline_text",
        "report_text": "Crowd surge at a concert venue near The Star Theatre. People at the front being crushed. Event staff overwhelmed.",
        "location_hint": "The Star Theatre",
        "outcome": "escalated",
        "response_taken": "evacuation",
    },
    {
        "source": "citizen_app",
        "report_text": "Flash mob gathering at Orchard Road causing pedestrian congestion. About 50 people dancing, blocking the pavement. No hostility.",
        "location_hint": "Orchard Road",
        "outcome": "resolved",
        "response_taken": "monitor",
    },
    {
        "source": "radio_transcript",
        "report_text": "Unruly crowd of about 30 outside a nightclub on Circular Road after a fight broke out inside. Some are intoxicated and aggressive.",
        "location_hint": "Circular Road",
        "outcome": "resolved",
        "response_taken": "security_dispatched",
    },

    # --- Traffic Accident (4) ---
    {
        "source": "hotline_text",
        "report_text": "Major traffic accident on PIE near Toa Payoh exit. 3 vehicles involved including a motorcycle. 2 people injured, one trapped in the car.",
        "location_hint": "PIE Toa Payoh Exit",
        "outcome": "escalated",
        "response_taken": "medical_dispatched",
    },
    {
        "source": "radio_transcript",
        "report_text": "Pedestrian hit by a van at the Woodlands Checkpoint. Victim is lying on the road, conscious. Van has stopped. Traffic jam forming.",
        "location_hint": "Woodlands Checkpoint",
        "outcome": "resolved",
        "response_taken": "medical_dispatched",
    },
    {
        "source": "citizen_app",
        "report_text": "Minor fender bender at the junction of Clementi Road and Commonwealth Ave. No injuries but both drivers arguing loudly.",
        "location_hint": "Clementi Rd / Commonwealth Ave",
        "outcome": "resolved",
        "response_taken": "verbal_engagement",
    },
    {
        "source": "hotline_text",
        "report_text": "Motorcycle skidded on wet road at Bukit Batok East Ave 3. Rider thrown off, helmet cracked. Not moving.",
        "location_hint": "Bukit Batok East Ave 3",
        "outcome": "escalated",
        "response_taken": "medical_dispatched",
    },

    # --- Other (2) ---
    {
        "source": "citizen_app",
        "report_text": "Strong chemical smell coming from a drain near Block 45 Lorong 5 Toa Payoh. Several residents complaining of nausea.",
        "location_hint": "Toa Payoh Lorong 5",
        "outcome": "resolved",
        "response_taken": "monitor",
    },
    {
        "source": "hotline_text",
        "report_text": "Stray dog acting aggressively in the playground at Sembawang Drive. Snapping at children. Parents keeping kids away.",
        "location_hint": "Sembawang Drive",
        "outcome": "resolved",
        "response_taken": "verbal_engagement",
    },
]

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_seed_incidents() -> List[Dict[str, Any]]:
    """Return 30 pre-built historical incidents with extraction, triage,
    outcome, and response_taken data.

    Each incident is fully processed so the similarity engine can use them
    as historical references immediately.
    """
    incidents: List[Dict[str, Any]] = []
    base_time = datetime.now(timezone.utc) - timedelta(days=30)

    for idx, raw in enumerate(_SEED_REPORTS):
        created_at = (base_time + timedelta(hours=idx * 8)).isoformat()

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
            "recommended": None,
            "outcome": raw.get("outcome"),
            "response_taken": raw.get("response_taken"),
            "status": "resolved" if raw.get("outcome") == "resolved" else "escalated",
        })

    return incidents


def seed_if_empty() -> int:
    """Populate the storage layer with seed data if it is currently empty.

    Returns the number of incidents inserted (0 if storage was not empty).
    """
    from .storage import _read_db, _write_db

    records = _read_db()
    if records:
        return 0

    seed = get_seed_incidents()
    _write_db(seed)
    return len(seed)
