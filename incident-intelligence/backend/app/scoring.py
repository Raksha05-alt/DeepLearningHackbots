"""
IntelResponse – Triage scoring module.

Computes a transparent, weighted triage score from structured incident
features produced by the extraction module.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

# ---------------------------------------------------------------------------
# Weight configuration (documented for auditability)
# ---------------------------------------------------------------------------
#
# Each weight represents the number of *raw points* added to the score when
# the corresponding condition is true.  The final score is clamped to 0-100.
#
#   Factor                  | Points | Rationale
#   ------------------------|--------|------------------------------------------
#   weapon_mentioned        |   +30  | Lethal force potential
#   active_threat           |   +25  | Immediate danger to life
#   injuries_present        |   +20  | Confirmed harm already occurring
#   smoke_fire_present      |   +15  | Property / life risk
#   aggression_level (0-3)  |  ×8    | Escalation likelihood (max +24)
#   crowd_level      (0-3)  |  ×5    | Collateral risk (max +15)
#   intoxication_suspected  |   +5   | Unpredictability factor
#   missing_location_penalty|   +5   | Harder to dispatch responders
# ---------------------------------------------------------------------------

_WEIGHTS: Dict[str, int] = {
    "weapon_mentioned": 30,
    "active_threat": 25,
    "injuries_present": 20,
    "smoke_fire_present": 15,
    "aggression_per_level": 8,   # multiplied by aggression_level (0-3)
    "crowd_per_level": 5,        # multiplied by crowd_level (0-3)
    "intoxication_suspected": 5,
    "missing_location": 5,
}

# Priority thresholds
_PRIORITY_THRESHOLDS: List[Tuple[int, str]] = [
    (80, "P0"),  # critical – dispatch immediately
    (60, "P1"),  # high     – dispatch soon
    (40, "P2"),  # medium   – monitor / scheduled response
    (0,  "P3"),  # low      – informational / log
]

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def compute_triage_score(features: Dict[str, Any]) -> Dict[str, Any]:
    """Compute a triage score from structured incident features.

    Parameters
    ----------
    features : dict
        Output of ``extract_incident_features``.

    Returns
    -------
    dict
        {
          "score": int 0-100,
          "priority": "P0" | "P1" | "P2" | "P3",
          "reasons": [str]  # top contributing factors (up to 3)
        }
    """
    entities = features.get("key_entities", {})
    risk = features.get("risk_factors", {})

    # Accumulate (points, reason_label) tuples for transparency
    contributions: List[Tuple[int, str]] = []

    # Binary factors
    if entities.get("weapon_mentioned"):
        contributions.append((_WEIGHTS["weapon_mentioned"], "weapon mentioned"))
    if risk.get("active_threat"):
        contributions.append((_WEIGHTS["active_threat"], "active threat detected"))
    if entities.get("injuries_present"):
        contributions.append((_WEIGHTS["injuries_present"], "injuries reported"))
    if entities.get("smoke_fire_present"):
        contributions.append((_WEIGHTS["smoke_fire_present"], "fire/smoke detected"))
    if risk.get("intoxication_suspected"):
        contributions.append((_WEIGHTS["intoxication_suspected"], "intoxication suspected"))

    # Scaled factors
    aggression = risk.get("aggression_level", 0)
    if aggression > 0:
        pts = aggression * _WEIGHTS["aggression_per_level"]
        contributions.append((pts, f"aggression level {aggression}/3"))

    crowd = risk.get("crowd_level", 0)
    if crowd > 0:
        pts = crowd * _WEIGHTS["crowd_per_level"]
        contributions.append((pts, f"crowd level {crowd}/3"))

    # Penalty: no location makes dispatch harder
    if entities.get("location") is None:
        contributions.append((_WEIGHTS["missing_location"], "location unknown (penalty)"))

    # Total score (clamped)
    raw = sum(pts for pts, _ in contributions)
    score = max(0, min(100, raw))

    # Priority mapping
    priority = "P3"
    for threshold, label in _PRIORITY_THRESHOLDS:
        if score >= threshold:
            priority = label
            break

    # Top reasons (sorted by contribution descending)
    contributions.sort(key=lambda t: t[0], reverse=True)
    reasons = [reason for _, reason in contributions[:3]]

    return {
        "score": score,
        "priority": priority,
        "reasons": reasons,
    }
