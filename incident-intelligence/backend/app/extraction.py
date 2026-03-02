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
        # Natural speech
        "someone got hurt", "someone is hurt", "person down", "man down",
        "not breathing", "can't breathe", "passed out", "fell down",
        "needs help", "need an ambulance", "call ambulance", "send ambulance",
        "having a heart attack", "having a stroke", "broken leg", "broken arm",
        "in pain", "badly hurt", "seriously hurt", "head injury",
        "lying on the ground", "on the floor", "not moving", "not responding",
    ],
    "fire_smoke": [
        "fire", "smoke", "burning", "flames", "blaze", "arson", "explosion",
        "exploded", "gas leak", "chemical spill", "hazmat", "inferno",
        # Natural speech
        "on fire", "there's a fire", "building is burning", "I can see smoke",
        "see flames", "smell smoke", "something is burning", "the fire",
        "fire alarm", "fire engine", "call the fire department",
        "smoke coming from", "smoke everywhere", "thick smoke",
    ],
    "violence_conflict": [
        "fight", "fighting", "assault", "attacked", "stabbed", "stabbing",
        "shot", "shooting", "punch", "punched", "brawl", "domestic violence",
        "battery", "hit", "beaten", "hostage", "robbery", "mugging",
        # Natural speech
        "gonna kill", "going to kill", "trying to kill", "killed someone",
        "someone got stabbed", "someone got shot", "people fighting",
        "beating someone up", "attacking someone", "chasing someone",
        "pulling a knife", "has a knife", "with a knife", "threatening",
        "being robbed", "getting mugged", "someone stole", "break in",
        "breaking in", "slashing", "slashed",
    ],
    "suspicious_person": [
        "suspicious", "lurking", "stalking", "loitering", "trespassing",
        "peeping", "following", "prowler", "watching", "casing",
        # Natural speech
        "suspicious person", "strange man", "strange person", "weird guy",
        "someone suspicious", "acting strange", "acting weird",
        "following me", "following someone", "watching me",
        "creepy", "peeping tom", "left a bag", "unattended bag",
        "suspicious package", "abandoned bag",
    ],
    "crowd_risk": [
        "crowd", "stampede", "overcrowding", "gathering", "riot", "protest",
        "mob", "unruly crowd", "crowd surge", "mosh", "panic",
        # Natural speech
        "too many people", "people pushing", "getting crushed",
        "people panicking", "everyone running", "people screaming",
        "big crowd", "huge crowd", "out of control",
    ],
    "traffic_accident": [
        "accident", "crash", "collision", "hit and run", "vehicle",
        "car crash", "motorcycle", "pedestrian hit", "road", "traffic",
        "pile-up", "rollover", "overturned",
        # Natural speech
        "car accident", "been a crash", "there's been an accident",
        "car hit", "got hit by a car", "knocked down", "run over",
        "bus accident", "lorry", "truck accident", "bike accident",
        "road accident", "traffic accident", "fender bender",
    ],
}

_WEAPON_KEYWORDS = [
    "knife", "gun", "firearm", "pistol", "rifle", "weapon", "machete",
    "sword", "bat", "axe", "hammer", "explosive", "bomb", "grenade",
    "blade", "armed",
    # Natural speech
    "has a knife", "with a knife", "pulled a knife", "pulled a gun",
    "holding a weapon", "carrying a weapon", "sharp object",
    "parang", "chopper", "cleaver",
]

_AGGRESSION_KEYWORDS_HIGH = [
    "attacking", "rampage", "killing", "murder", "threatening to kill",
    "active shooter", "hostage", "brandishing",
    "gonna kill", "going to kill", "trying to kill", "slashing people",
    "running around with a knife", "with a knife", "swinging a knife",
]
_AGGRESSION_KEYWORDS_MED = [
    "threatening", "aggressive", "violent", "hostile", "confrontation",
    "intimidating", "yelling", "screaming",
    "chasing", "cornered", "won't let me leave", "blocking the exit",
]
_AGGRESSION_KEYWORDS_LOW = [
    "argument", "dispute", "quarrel", "shouting", "pushing",
    "heated", "angry", "upset", "agitated", "raising voice",
]

_INTOXICATION_KEYWORDS = [
    "drunk", "intoxicated", "alcohol", "drugs", "substance", "high",
    "inebriated", "under the influence", "smells of alcohol",
]

_FIRE_KEYWORDS = ["fire", "smoke", "flames", "burning", "blaze", "inferno"]

_INJURY_KEYWORDS = [
    "injured", "injury", "bleeding", "wound", "hurt", "casualty",
    "casualties", "victim", "unconscious", "dead", "killed",
    # Natural speech
    "someone got hurt", "people hurt", "badly hurt", "seriously hurt",
    "blood everywhere", "covered in blood", "need medical",
    "not moving", "not breathing", "passed out", "on the ground",
    "broken", "fractured", "in pain", "screaming in pain",
    "stabbed", "stabbing", "stab", "shot",
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PEOPLE_RE = re.compile(
    r"(\d+)\s*(?:people|persons|individuals|victims|casualties|injured|men|women|children|kids|bystanders|guys|persons)",
    re.IGNORECASE,
)

# Match spoken number words and vague counts
_SPOKEN_COUNT_MAP = {
    "a person": 1, "one person": 1, "a man": 1, "a woman": 1,
    "a guy": 1, "someone": 1, "one guy": 1, "one man": 1,
    "two people": 2, "two men": 2, "two guys": 2, "two persons": 2,
    "three people": 3, "three men": 3, "three guys": 3,
    "four people": 4, "five people": 5, "six people": 6,
    "a few people": 3, "a few guys": 3, "several people": 4,
    "a group of people": 8, "a group": 8, "many people": 15,
    "a lot of people": 20, "lots of people": 20,
}

# ---------------------------------------------------------------------------
# Singapore location keywords for extraction
# ---------------------------------------------------------------------------

_SG_LOCATIONS = [
    "Ang Mo Kio", "Bedok", "Bishan", "Bukit Batok", "Bukit Merah",
    "Bukit Panjang", "Bukit Timah", "Choa Chu Kang", "Clementi",
    "Geylang", "Hougang", "Jurong East", "Jurong West", "Kallang",
    "Marine Parade", "Pasir Ris", "Punggol", "Queenstown", "Sembawang",
    "Sengkang", "Serangoon", "Tampines", "Toa Payoh", "Woodlands",
    "Yishun", "Changi", "Sentosa", "Marina Bay", "Orchard", "Clarke Quay",
    "Chinatown", "Little India", "Lavender", "Bugis", "City Hall",
    "Raffles Place", "Tanjong Pagar", "Tiong Bahru", "Novena",
    "Newton", "Dhoby Ghaut", "Somerset", "Bayfront", "Harbourfront",
    "Outram Park", "Boon Lay", "Pioneer", "Dover", "Holland Village",
    "Paya Lebar", "Aljunied", "Eunos", "Kembangan", "Simei",
    "Tanah Merah", "Expo", "East Coast Park", "West Coast",
    "Upper Thomson", "Braddell", "Potong Pasir", "Bartley",
    "Mountbatten", "Stadium", "Promenade", "Esplanade",
    "Fort Canning", "Rochor", "Bencoolen", "Bras Basah",
]

_LOCATION_RE = re.compile(
    r"\b(?:at|near|in|outside|opposite)\b\s+(.+?)(?:\.|,|$)",
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

    # Location: prefer explicit hint, then regex (for fuller names), then known SG place names
    location = location_hint if location_hint else None
    if not location:
        # Try "at/near/in <location>" pattern first to catch full names like "Bishan Junction 8"
        loc_match = _LOCATION_RE.search(text)
        if loc_match:
            candidate = loc_match.group(1).strip()
            # Only accept if it looks like a proper noun (starts with uppercase)
            if candidate and candidate[0].isupper() and len(candidate) > 2:
                location = candidate
    if not location:
        # Fallback: Search for known Singapore locations in the text (case-insensitive)
        for sg_loc in sorted(_SG_LOCATIONS, key=len, reverse=True):
            if sg_loc.lower() in text_lower:
                location = sg_loc
                break

    people_count = None
    for phrase, count in _SPOKEN_COUNT_MAP.items():
        if phrase in text_lower:
            # Take the largest match if we wanted to be rigorous, but a simple 
            # find is usually good enough for these short reports.
            people_count = count
            break

    if people_count is None:
        people_match = _PEOPLE_RE.search(text)
        if people_match:
            people_count = int(people_match.group(1))

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
