"""
IntelResponse – Simulated radio transmission generator.

Provides contextual radio messages per incident type for the
live WebSocket feed. In production, these would come from actual
radio STT transcription.
"""

from __future__ import annotations

import random
from typing import List, Dict

# ---------------------------------------------------------------------------
# Radio message pools by incident type
# ---------------------------------------------------------------------------

_RADIO_MESSAGES: Dict[str, List[str]] = {
    "violence_conflict": [
        "Control, suspect is moving towards exit B. Requesting backup.",
        "Perimeter secured at north entrance. Civilians being evacuated.",
        "Suspect appears to be armed. Maintaining safe distance.",
        "Witnesses report a second individual fled the scene on foot heading east.",
        "Victim is conscious and responsive. EMS providing first aid on site.",
        "CCTV team confirms suspect last seen near platform level 2.",
        "Negotiator en route, ETA 4 minutes.",
        "All exits now covered. Tightening cordon.",
        "Suspect has dropped weapon. Approaching with caution.",
        "Situation de-escalating. Suspect is compliant. Preparing for apprehension.",
        "One additional minor injury reported — bystander fell during evacuation.",
        "Ambulance standing by at Rally Point Alpha.",
        "Control, we have visual on suspect. Male, approximately 30s, dark clothing.",
        "Crowd is dispersing. Area becoming manageable.",
        "Weapon recovered. Securing evidence before forensics arrives.",
    ],
    "fire_smoke": [
        "Heavy smoke on floors 4 and 5. Visibility near zero. Donning SCBA.",
        "Search team entering unit 05-412. No signs of occupants yet.",
        "Water supply established. Attacking fire from stairwell B.",
        "Control, fire is spreading to adjacent unit. Requesting second engine.",
        "Two residents rescued from balcony. Minor smoke inhalation. EMS treating.",
        "Structural integrity check — floor appears stable but monitoring.",
        "Ventilation team on roof. Cutting ventilation hole now.",
        "Fire appears contained to two units. Not spreading further.",
        "Gas supply to building has been shut off by SP Group.",
        "All residents from floors 3-7 accounted for at assembly point.",
        "Flashover risk on floor 5 — pulling back teams temporarily.",
        "Thermal camera showing hotspot on south-facing wall of unit 412.",
        "Fire under control. Transitioning to overhaul operations.",
        "One firefighter reporting heat exhaustion. Rotating crew.",
        "Building management confirms gas lines isolated. Safe to proceed.",
    ],
    "suspicious_person": [
        "Subject still at location. No threatening behavior observed.",
        "Running ID check through dispatch. Awaiting results.",
        "Subject appears to be taking photographs of the building entrance.",
        "Approaching subject for welfare check. Maintaining safe distance.",
        "Subject is cooperative. Claims to be waiting for someone. No ID on person.",
        "Control, checking CCTV for how long subject has been here.",
        "Bag has been visually inspected. Appears to contain personal items only.",
        "K-9 unit en route for secondary sweep. ETA 10 minutes.",
        "Area cordoned off as precaution. Public redirected.",
        "Subject has provided identification. Verifying against database.",
        "ID check clean. No warrants or flags.",
        "Background check complete. Subject appears to be a delivery worker on break.",
        "Releasing cordon. Resuming normal operations.",
    ],
    "crowd_risk": [
        "Crowd estimated at 250 now. Still growing. Music amplifiers set up.",
        "Control, checking with NParks for any event permits filed.",
        "Multiple alcohol coolers spotted. Possible unlicensed event.",
        "Crowd is peaceful. No signs of aggression or disorder.",
        "Second patrol unit requesting guidance on crowd management approach.",
        "PA system being used. Cannot identify organizer yet.",
        "Exit routes have been identified and are clear. No bottlenecks.",
        "Crowd size stabilizing. Appears to have peaked.",
        "Organizer identified and made contact. Cooperative attitude.",
        "Event appears to be a birthday celebration. Crowd is upbeat.",
        "Monitoring for any escalation. Will remain on scene.",
        "Crowd starting to thin out. Down to approximately 150.",
    ],
    "traffic_accident": [
        "Two lanes blocked. Setting up lane diversion at 500m marker.",
        "One driver complaining of neck pain. Ambulance requested.",
        "Fuel spillage on road. Requesting hazmat assessment.",
        "Tow truck on scene. Beginning removal of first vehicle.",
        "Traffic backing up 2km. LTA activated electronic signs for diversion.",
        "Second vehicle cleared. One lane reopening now.",
        "Driver of vehicle 3 showing signs of impairment. Breathalyzer requested.",
        "All occupants extracted. No one trapped.",
        "Road surface damaged at impact point. LTA notified for repair.",
        "Hazmat confirms fuel spillage is minor. Applying absorbent material.",
        "Final vehicle being towed now. Full lane access in approximately 10 minutes.",
        "Scene cleared. Resuming normal traffic flow.",
    ],
    "medical": [
        "Patient is male, approximately 65-70 years old. Unresponsive.",
        "CPR in progress. Bystander using chest compressions. Good form.",
        "AED located at nearby community center. Runner dispatched to retrieve.",
        "Ambulance 3 minutes out. Paramedic on phone guiding CPR.",
        "AED applied. Analyzing rhythm. Stand clear.",
        "Shock delivered. Resuming CPR.",
        "Patient showing signs of response. Pulse detected — weak but present.",
        "Ambulance on scene. Paramedics taking over.",
        "IV access established. Administering medication.",
        "Patient stabilized. Preparing for transport to Changi General Hospital.",
        "Patient loaded into ambulance. Transporting now. ETA 12 minutes.",
        "Hospital notified and standing by. Cardiac team activated.",
    ],
    "other": [
        "Patrol unit on scene. Assessing situation.",
        "No immediate threat detected. Continuing observation.",
        "Requesting guidance from control on next steps.",
        "Area is secure. Situation appears under control.",
        "Standing by for further instructions.",
    ],
}


def get_radio_message(incident_type: str) -> str:
    """Return a random contextual radio message for the given incident type."""
    pool = _RADIO_MESSAGES.get(incident_type, _RADIO_MESSAGES["other"])
    return random.choice(pool)


def get_radio_sequence(incident_type: str, count: int = 5) -> List[str]:
    """Return a sequence of radio messages (no repeats if pool is large enough)."""
    pool = _RADIO_MESSAGES.get(incident_type, _RADIO_MESSAGES["other"])
    k = min(count, len(pool))
    return random.sample(pool, k)
