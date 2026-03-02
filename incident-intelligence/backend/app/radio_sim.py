"""
IntelResponse – Simulated radio transmission generator (SG context).

Each radio message is attributed to a specific responder using
realistic Singapore emergency service callsigns and conventions.

Singapore emergency response structure:
  - SPF  (999) — Police.  Divisions use NATO phonetic letters.
                  Fast Response Cars (FRC).  Ranks: INSP, ASP, SGT, CPL.
  - SCDF (995) — Fire / Rescue / EMS.
                  Callsign = appliance type + 3 digits (div-station-unit).
                  Appliance types: PL (Pumper Ladder), A (Ambulance),
                  LFAV (Red Rhino).  Ranks: CPT, LTA, SGT1, SGT2.
  - TP         — Traffic Police.  TP + unit number.
  - SOC        — Special Operations Command.  STAR, PTU (Police Tactical Unit).
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Type alias for a radio transmission
# ---------------------------------------------------------------------------
RadioTx = Dict[str, str]      # {speaker, callsign, message}


def _tx(speaker: str, callsign: str, message: str) -> RadioTx:
    return {"speaker": speaker, "callsign": callsign, "message": message}


# ---------------------------------------------------------------------------
# Message pools keyed by incident type.
# Each entry is (role_hint, message_template).
# role_hint is used to match to an appropriate responder:
#   "lead"    → lead officer / IC
#   "backup"  → backup / support unit
#   "medical" → EMS / ambulance
#   "fire"    → fire engine crew
#   "rescue"  → search & rescue
#   "traffic" → traffic police
#   "any"     → any responder
# ---------------------------------------------------------------------------
_MSG_POOL: Dict[str, List[Tuple[str, str]]] = {
    "violence_conflict": [
        ("lead",    "Control, suspect is moving towards exit B. Requesting backup."),
        ("backup",  "Perimeter secured at north entrance. Civilians being evacuated."),
        ("lead",    "Suspect appears to be armed. Maintaining safe distance."),
        ("backup",  "Witnesses report a second individual fled scene on foot heading east."),
        ("medical", "Victim is conscious and responsive. Providing first aid on site."),
        ("lead",    "CCTV team confirms suspect last seen near platform level 2."),
        ("any",     "Negotiator en route, ETA 4 minutes."),
        ("backup",  "All exits now covered. Tightening cordon."),
        ("lead",    "Suspect has dropped weapon. Approaching with caution."),
        ("lead",    "Situation de-escalating. Suspect is compliant. Preparing for apprehension."),
        ("medical", "One additional minor injury reported — bystander fell during evacuation."),
        ("medical", "Ambulance standing by at Rally Point Alpha."),
        ("backup",  "Control, we have visual on suspect. Male, approximately 30s, dark clothing."),
        ("any",     "Crowd is dispersing. Area becoming manageable."),
        ("lead",    "Weapon recovered and secured. Awaiting forensics."),
    ],
    "fire_smoke": [
        ("fire",    "Heavy smoke on floors 4 and 5. Visibility near zero. Donning SCBA."),
        ("rescue",  "Search team entering unit 05-412. No signs of occupants yet."),
        ("fire",    "Water supply established. Attacking fire from stairwell B."),
        ("fire",    "Control, fire is spreading to adjacent unit. Requesting second PL."),
        ("rescue",  "Two residents rescued from balcony. Minor smoke inhalation."),
        ("fire",    "Structural integrity check — floor appears stable but monitoring."),
        ("rescue",  "Ventilation team on roof. Cutting ventilation hole now."),
        ("fire",    "Fire appears contained to two units. Not spreading further."),
        ("any",     "Gas supply to building has been shut off by SP Group."),
        ("rescue",  "All residents from floors 3-7 accounted for at assembly point."),
        ("fire",    "Flashover risk on floor 5 — pulling back teams temporarily."),
        ("fire",    "Thermal camera showing hotspot on south-facing wall of unit 412."),
        ("fire",    "Fire under control. Transitioning to overhaul operations."),
        ("rescue",  "One firefighter reporting heat exhaustion. Rotating crew."),
        ("any",     "Building management confirms gas lines isolated. Safe to proceed."),
    ],
    "suspicious_person": [
        ("lead",    "Subject still at location. No threatening behaviour observed."),
        ("lead",    "Running ID check through Ops Room. Awaiting results."),
        ("backup",  "Subject appears to be taking photographs of the building entrance."),
        ("lead",    "Approaching subject for welfare check. Maintaining safe distance."),
        ("lead",    "Subject is cooperative. Claims to be waiting for someone. No ID on person."),
        ("backup",  "Control, checking CCTV for how long subject has been here."),
        ("any",     "K-9 unit en route for secondary sweep. ETA 10 minutes."),
        ("backup",  "Area cordoned off as precaution. Public redirected."),
        ("lead",    "Subject has provided identification. Verifying against database."),
        ("lead",    "ID check clean. No warrants or flags."),
        ("lead",    "Background check complete. Subject appears to be a delivery worker on break."),
        ("any",     "Releasing cordon. Resuming normal operations."),
    ],
    "crowd_risk": [
        ("lead",    "Crowd estimated at 250. Still growing. Amplifiers set up."),
        ("backup",  "Control, checking with NParks for event permits filed."),
        ("lead",    "Multiple alcohol coolers spotted. Possible unlicensed event."),
        ("backup",  "Crowd is peaceful. No signs of aggression or disorder."),
        ("lead",    "Patrol unit requesting guidance from Ops Room on crowd management approach."),
        ("backup",  "PA system being used. Cannot identify organiser yet."),
        ("any",     "Exit routes identified and clear. No bottlenecks."),
        ("lead",    "Crowd size stabilising. Appears to have peaked."),
        ("lead",    "Organiser identified and made contact. Cooperative attitude."),
        ("backup",  "Event appears to be a birthday celebration. Crowd is upbeat."),
        ("any",     "Monitoring for any escalation. Will remain on scene."),
        ("lead",    "Crowd starting to thin out. Down to approximately 150."),
    ],
    "traffic_accident": [
        ("traffic", "Two lanes blocked. Setting up lane diversion at 500m marker."),
        ("medical", "One driver complaining of neck pain. Ambulance requested."),
        ("traffic", "Fuel spillage on road. Requesting hazmat assessment."),
        ("traffic", "Tow truck on scene. Beginning removal of first vehicle."),
        ("traffic", "Traffic backing up 2km. LTA activated electronic signs for diversion."),
        ("traffic", "Second vehicle cleared. One lane reopening now."),
        ("traffic", "Driver of vehicle 3 showing signs of impairment. Breathalyser requested."),
        ("medical", "All occupants extracted. No one trapped."),
        ("traffic", "Road surface damaged at impact point. LTA notified for repair."),
        ("any",     "Hazmat confirms fuel spillage is minor. Applying absorbent material."),
        ("traffic", "Final vehicle being towed now. Full lane access in ~10 minutes."),
        ("traffic", "Scene cleared. Resuming normal traffic flow."),
    ],
    "medical": [
        ("medical", "Patient is male, approximately 65-70 years old. Unresponsive on arrival."),
        ("any",     "Bystander CPR in progress. Good compressions, guiding on technique."),
        ("medical", "AED located at nearby community centre. Runner dispatched to retrieve."),
        ("medical", "Ambulance 3 minutes out. Paramedic on phone guiding CPR."),
        ("medical", "AED applied. Analysing rhythm. Stand clear."),
        ("medical", "Shock delivered. Resuming CPR."),
        ("medical", "Patient showing signs of response. Pulse detected — weak but present."),
        ("medical", "Ambulance on scene. Paramedics taking over."),
        ("medical", "IV access established. Administering medication."),
        ("medical", "Patient stabilised. Preparing for transport to Changi General Hospital."),
        ("medical", "Patient loaded into ambulance. Transporting now. ETA 12 minutes to CGH."),
        ("medical", "Hospital notified and standing by. Cardiac team activated."),
    ],
    "other": [
        ("lead",    "Patrol unit on scene. Assessing situation."),
        ("any",     "No immediate threat detected. Continuing observation."),
        ("lead",    "Requesting guidance from Ops Room on next steps."),
        ("any",     "Area is secure. Situation appears under control."),
        ("lead",    "Standing by for further instructions."),
    ],
}

# Fallback generic speakers when no responders are assigned
_FALLBACK_SPEAKERS: Dict[str, List[Dict[str, str]]] = {
    "violence_conflict": [
        {"name": "SGT Lim", "callsign": "Echo-1", "role": "lead"},
        {"name": "CPL Ahmad", "callsign": "Echo-2", "role": "backup"},
        {"name": "Paramedic Tan", "callsign": "A241", "role": "medical"},
    ],
    "fire_smoke": [
        {"name": "CPT Wong", "callsign": "PL131", "role": "fire"},
        {"name": "SGT1 Chen", "callsign": "LFAV-132", "role": "rescue"},
        {"name": "Paramedic Lee", "callsign": "A131", "role": "medical"},
    ],
    "traffic_accident": [
        {"name": "SSGT Yeo", "callsign": "TP-22", "role": "traffic"},
        {"name": "Paramedic Raj", "callsign": "A341", "role": "medical"},
    ],
    "medical": [
        {"name": "Paramedic Ng", "callsign": "A242", "role": "medical"},
        {"name": "SGT2 Koh", "callsign": "A242-2", "role": "medical"},
    ],
    "suspicious_person": [
        {"name": "SGT Tay", "callsign": "Golf-3", "role": "lead"},
        {"name": "CPL Siti", "callsign": "Golf-4", "role": "backup"},
    ],
    "crowd_risk": [
        {"name": "INSP Low", "callsign": "Delta-1", "role": "lead"},
        {"name": "SGT Hassan", "callsign": "Delta-2", "role": "backup"},
    ],
    "other": [
        {"name": "SGT Chua", "callsign": "India-1", "role": "lead"},
    ],
}

# Role mapping from responder role strings → role_hint
_ROLE_MAP: Dict[str, str] = {
    "lead officer": "lead",
    "incident commander": "lead",
    "ground commander": "lead",
    "patrol officer": "lead",
    "backup": "backup",
    "support": "backup",
    "cordon": "backup",
    "perimeter": "backup",
    "medical": "medical",
    "ems": "medical",
    "paramedic": "medical",
    "ambulance": "medical",
    "fire response": "fire",
    "fire attack": "fire",
    "pump operator": "fire",
    "search & rescue": "rescue",
    "search and rescue": "rescue",
    "ventilation": "rescue",
    "traffic police": "traffic",
    "traffic control": "traffic",
}


def _match_role(role_hint: str, responders: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Find the best responder match for a role hint."""
    if not responders:
        return {}

    # Try exact role match first
    for r in responders:
        mapped = _ROLE_MAP.get(r.get("role", "").lower(), "any")
        if mapped == role_hint:
            return r

    # Fallback: pick any responder
    return random.choice(responders)


def get_radio_transmission(
    incident_type: str,
    responders: Optional[List[Dict[str, Any]]] = None,
) -> RadioTx:
    """Return a single speaker-attributed radio transmission.

    Args:
        incident_type: Type of incident (e.g., "violence_conflict").
        responders: List of responder dicts with name, callsign, role fields.
                    Falls back to generic SG callsigns if empty.

    Returns:
        Dict with {speaker, callsign, message}.
    """
    pool = _MSG_POOL.get(incident_type, _MSG_POOL["other"])
    role_hint, message = random.choice(pool)

    # Use actual responders if available, otherwise fallback
    speaker_pool = responders if responders else \
        _FALLBACK_SPEAKERS.get(incident_type, _FALLBACK_SPEAKERS["other"])

    if role_hint == "any":
        speaker = random.choice(speaker_pool)
    else:
        speaker = _match_role(role_hint, speaker_pool)
        if not speaker:
            speaker = random.choice(speaker_pool)

    return _tx(
        speaker=speaker.get("name", "Unknown"),
        callsign=speaker.get("callsign", "Control"),
        message=message,
    )


# Keep legacy function for backwards compatibility
def get_radio_message(incident_type: str) -> str:
    """Return a plain radio message string (legacy, no attribution)."""
    tx = get_radio_transmission(incident_type)
    return tx["message"]
