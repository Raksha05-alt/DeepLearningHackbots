"""
IntelResponse – Incident feature extraction module.

Rule-based heuristics to structure free-text incident reports into a
normalised JSON representation used by the triage and similarity pipeline.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Keyword dictionaries for incident-type classification
# ---------------------------------------------------------------------------

_TYPE_KEYWORDS: Dict[str, List[str]] = {
    "medical": [
        "medical", "ambulance", "injured", "injury", "bleeding", "unconscious",
        "heart attack", "cardiac", "seizure", "fainted", "collapse", "overdose",
        "choking", "fracture", "broken bone", "burn", "wound", "trauma",
        "breathing difficulty", "chest pain", "stroke", "allergic reaction",
    ],
    "fire_smoke": [
        "fire", "smoke", "burning", "flames", "blaze", "arson", "explosion",
        "exploded", "gas leak", "chemical spill", "hazmat", "inferno",
    ],
    "violence_conflict": [
        "fight", "fighting", "assault", "attacked", "stabbed", "stabbing",
        "shot", "shooting", "punch", "punched", "brawl", "domestic violence",
        "battery", "hit", "beaten", "hostage", "robbery", "mugging",
    ],
    "suspicious_person": [
        "suspicious", "lurking", "stalking", "loitering", "trespassing",
        "peeping", "following", "prowler", "watching", "casing",
    ],
    "crowd_risk": [
        "crowd", "stampede", "overcrowding", "gathering", "riot", "protest",
        "mob", "unruly crowd", "crowd surge", "mosh", "panic",
    ],
    "traffic_accident": [
        "accident", "crash", "collision", "hit and run", "vehicle",
        "car crash", "motorcycle", "pedestrian hit", "road", "traffic",
        "pile-up", "rollover", "overturned",
    ],
}

_WEAPON_KEYWORDS = [
    "knife", "gun", "firearm", "pistol", "rifle", "weapon", "machete",
    "sword", "bat", "axe", "hammer", "explosive", "bomb", "grenade",
    "blade", "armed",
]

_AGGRESSION_KEYWORDS_HIGH = [
    "attacking", "rampage", "killing", "murder", "threatening to kill",
    "active shooter", "hostage", "brandishing",
]
_AGGRESSION_KEYWORDS_MED = [
    "threatening", "aggressive", "violent", "hostile", "confrontation",
    "intimidating", "yelling", "screaming",
]
_AGGRESSION_KEYWORDS_LOW = [
    "argument", "dispute", "quarrel", "shouting", "pushing",
]

_INTOXICATION_KEYWORDS = [
    "drunk", "intoxicated", "alcohol", "drugs", "substance", "high",
    "inebriated", "under the influence", "smells of alcohol",
]

_FIRE_KEYWORDS = ["fire", "smoke", "flames", "burning", "blaze", "inferno"]

_INJURY_KEYWORDS = [
    "injured", "injury", "bleeding", "wound", "hurt", "casualty",
    "casualties", "victim", "unconscious", "dead", "killed",
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PEOPLE_RE = re.compile(
    r"(\d+)\s*(?:people|persons|individuals|victims|casualties|injured|men|women|children|kids|bystanders)",
    re.IGNORECASE,
)


def _has_any(text: str, keywords: List[str]) -> bool:
    """Return True if *text* contains any of the *keywords* (case-insensitive)."""
    lower = text.lower()
    return any(kw in lower for kw in keywords)


def _count_matches(text: str, keywords: List[str]) -> int:
    lower = text.lower()
    return sum(1 for kw in keywords if kw in lower)

# ---------------------------------------------------------------------------
# Main extraction function – RULE-BASED
# ---------------------------------------------------------------------------


def extract_incident_features(
    report_text: str,
    location_hint: Optional[str] = None,
) -> Dict[str, Any]:
    """Extract structured features from a free-text incident report.

    Uses keyword-matching heuristics (no ML/LLM dependency).

    Returns a dict matching the schema:
    {
      "incident_type": str,
      "key_entities": { location, people_count, injuries_present,
                        weapon_mentioned, smoke_fire_present },
      "risk_factors": { aggression_level (0-3), crowd_level (0-3),
                        intoxication_suspected, active_threat },
      "confidence": float 0-1,
      "missing_info": [str]
    }
    """
    text = report_text.strip()
    text_lower = text.lower()

    # ---- Incident type --------------------------------------------------
    type_scores: Dict[str, int] = {}
    for itype, kws in _TYPE_KEYWORDS.items():
        score = _count_matches(text, kws)
        if score > 0:
            type_scores[itype] = score

    if type_scores:
        incident_type = max(type_scores, key=type_scores.get)  # type: ignore[arg-type]
    else:
        incident_type = "other"

    # ---- Key entities ---------------------------------------------------
    location = location_hint if location_hint else None

    people_match = _PEOPLE_RE.search(text)
    people_count = int(people_match.group(1)) if people_match else None

    injuries_present = _has_any(text, _INJURY_KEYWORDS)
    weapon_mentioned = _has_any(text, _WEAPON_KEYWORDS)
    smoke_fire_present = _has_any(text, _FIRE_KEYWORDS)

    # ---- Risk factors ---------------------------------------------------
    if _has_any(text, _AGGRESSION_KEYWORDS_HIGH):
        aggression_level = 3
    elif _has_any(text, _AGGRESSION_KEYWORDS_MED):
        aggression_level = 2
    elif _has_any(text, _AGGRESSION_KEYWORDS_LOW):
        aggression_level = 1
    else:
        aggression_level = 0

    # Crowd level from keywords + people count
    crowd_kws = _count_matches(text, _TYPE_KEYWORDS["crowd_risk"])
    if crowd_kws >= 3 or (people_count and people_count > 50):
        crowd_level = 3
    elif crowd_kws >= 2 or (people_count and people_count > 20):
        crowd_level = 2
    elif crowd_kws >= 1 or (people_count and people_count > 5):
        crowd_level = 1
    else:
        crowd_level = 0

    intoxication_suspected = _has_any(text, _INTOXICATION_KEYWORDS)

    # Active threat: weapon + aggression, or high-aggression keywords
    active_threat = (weapon_mentioned and aggression_level >= 2) or _has_any(
        text, ["active shooter", "hostage", "rampage", "bomb threat"]
    )

    # ---- Confidence & missing info --------------------------------------
    filled = sum([
        location is not None,
        people_count is not None,
        injuries_present,
        weapon_mentioned or smoke_fire_present,
        incident_type != "other",
    ])
    confidence = round(min(1.0, 0.3 + filled * 0.14), 2)

    missing_info: List[str] = []
    if location is None:
        missing_info.append("location")
    if people_count is None:
        missing_info.append("people_count")
    if not injuries_present and not any(
        w in text_lower for w in ["no injur", "no one hurt", "nobody hurt"]
    ):
        missing_info.append("injury_status_unclear")
    if incident_type == "other":
        missing_info.append("incident_type_unclear")

    return {
        "incident_type": incident_type,
        "key_entities": {
            "location": location,
            "people_count": people_count,
            "injuries_present": injuries_present,
            "weapon_mentioned": weapon_mentioned,
            "smoke_fire_present": smoke_fire_present,
        },
        "risk_factors": {
            "aggression_level": aggression_level,
            "crowd_level": crowd_level,
            "intoxication_suspected": intoxication_suspected,
            "active_threat": active_threat,
        },
        "confidence": confidence,
        "missing_info": missing_info,
    }


# ---------------------------------------------------------------------------
# LLM-based extraction – PLACEHOLDER (not used by default)
# ---------------------------------------------------------------------------


def extract_incident_features_llm(
    report_text: str,
    location_hint: Optional[str] = None,
) -> Dict[str, Any]:
    """Extract incident features using an LLM (e.g., GPT-4, Gemini).

    This is a placeholder for future integration.  The function should:
    1.  Construct a prompt containing the report text and expected JSON schema.
    2.  Call the LLM API (OpenAI / Google / local model).
    3.  Parse and validate the returned JSON against the same schema used by
        ``extract_incident_features``.

    Until an LLM backend is configured, this function is intentionally
    non-functional so callers fall through to the rule-based implementation.
    """
    raise NotImplementedError(
        "LLM-based extraction is not yet configured. "
        "Use extract_incident_features() for rule-based extraction."
    )
