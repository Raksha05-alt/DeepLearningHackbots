"""
IntelResponse – Recommended-response generator.

Produces actionable recommendations (dispatch action, follow-up questions,
checklists, and rationale) from structured features, triage results, and
similar-case statistics.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Incident-type-specific checklists (5 items each)
# ---------------------------------------------------------------------------

_CHECKLISTS: Dict[str, List[str]] = {
    "medical": [
        "Confirm number and condition of casualties",
        "Request ambulance / paramedic dispatch",
        "Secure scene to allow medical access",
        "Identify nearest hospital or trauma centre",
        "Gather witness contact information",
    ],
    "fire_smoke": [
        "Alert fire department immediately",
        "Evacuate affected area and set perimeter",
        "Identify potential hazardous materials",
        "Check for trapped or injured persons",
        "Notify building management / utilities",
    ],
    "violence_conflict": [
        "Dispatch law enforcement to scene",
        "Determine if weapon is involved",
        "Identify and separate involved parties",
        "Secure perimeter to protect bystanders",
        "Collect witness statements",
    ],
    "suspicious_person": [
        "Obtain physical description of suspect",
        "Note last-known direction of travel",
        "Check nearby CCTV / security footage",
        "Advise nearby residents to stay alert",
        "Dispatch patrol unit for area sweep",
    ],
    "crowd_risk": [
        "Assess crowd size and density",
        "Deploy crowd-control resources",
        "Identify exit routes and clear them",
        "Set up medical triage station nearby",
        "Coordinate with event organisers if applicable",
    ],
    "traffic_accident": [
        "Dispatch traffic police and ambulance",
        "Set up traffic diversion around scene",
        "Check for fuel / hazmat spill risk",
        "Assist with vehicle extrication if needed",
        "Document vehicle registrations and IDs",
    ],
    "other": [
        "Gather additional details from caller",
        "Dispatch nearest available patrol unit",
        "Assess whether specialised response is needed",
        "Document scene observations",
        "Follow up within 30 minutes for status update",
    ],
}

# ---------------------------------------------------------------------------
# Follow-up question templates by incident type
# ---------------------------------------------------------------------------

_FOLLOWUP_TEMPLATES: Dict[str, List[str]] = {
    "medical": [
        "Is the victim conscious and breathing?",
        "Are there any known allergies or medical conditions?",
        "How many people are injured?",
    ],
    "fire_smoke": [
        "Is the fire spreading or contained?",
        "Are there people trapped inside the building?",
        "Can you see what is burning (structure, vehicle, vegetation)?",
    ],
    "violence_conflict": [
        "Is the attacker still on scene?",
        "Can you describe the weapon (if any)?",
        "How many people are involved in the altercation?",
    ],
    "suspicious_person": [
        "What is the suspect doing right now?",
        "Can you describe their clothing and appearance?",
        "Are they carrying anything (bags, tools, weapons)?",
    ],
    "crowd_risk": [
        "Is the crowd moving or stationary?",
        "Are there any visible agitators or instigators?",
        "What triggered the crowd gathering?",
    ],
    "traffic_accident": [
        "How many vehicles are involved?",
        "Is anyone trapped inside a vehicle?",
        "Is there visible fuel or fluid leaking?",
    ],
    "other": [
        "Can you describe exactly what you are seeing?",
        "Is anyone in immediate danger?",
        "Have emergency services already been contacted?",
    ],
}

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def recommend_response(
    features: Dict[str, Any],
    triage: Dict[str, Any],
    similar_cases_stats: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Generate recommended response based on extracted features, triage
    score, and similar-case information.

    Returns
    -------
    dict
        {
          "action": "dispatch_now" | "dispatch_soon" | "monitor" | "request_more_info",
          "follow_up_questions": [str, str, str],
          "checklist": [str × 5],
          "rationale": str,
        }
    """
    priority = triage.get("priority", "P3")
    score = triage.get("score", 0)
    missing = features.get("missing_info", [])
    incident_type = features.get("incident_type", "other")

    # ---- Action decision ------------------------------------------------
    if priority == "P0":
        action = "dispatch_now"
    elif priority == "P1":
        action = "dispatch_soon"
    elif len(missing) >= 3:
        # Too many unknowns – ask before committing resources
        action = "request_more_info"
    elif priority == "P2":
        action = "monitor"
    else:
        action = "monitor" if len(missing) < 2 else "request_more_info"

    # ---- Follow-up questions --------------------------------------------
    base_questions = _FOLLOWUP_TEMPLATES.get(
        incident_type, _FOLLOWUP_TEMPLATES["other"]
    )
    # Inject a missing-info-specific question if location is unknown
    questions = list(base_questions)  # copy
    if "location" in missing and not any("location" in q.lower() for q in questions):
        questions[0] = "Can you provide the exact location or nearest landmark?"

    follow_up_questions = questions[:3]

    # ---- Checklist ------------------------------------------------------
    checklist = _CHECKLISTS.get(incident_type, _CHECKLISTS["other"])

    # ---- Rationale ------------------------------------------------------
    reasons = triage.get("reasons", [])
    reason_text = ", ".join(reasons) if reasons else "general assessment"

    similar_note = ""
    if similar_cases_stats:
        top = similar_cases_stats[0]
        similar_note = (
            f" Similar past incident ({top.get('incident_type', 'N/A')}, "
            f"similarity {top.get('similarity_score', 0):.0%}) supports this assessment."
        )

    rationale = (
        f"Triage score {score}/100 ({priority}). "
        f"Key factors: {reason_text}.{similar_note}"
    )
    if missing:
        rationale += f" Missing info: {', '.join(missing)}."

    return {
        "action": action,
        "follow_up_questions": follow_up_questions,
        "checklist": checklist,
        "rationale": rationale,
    }
