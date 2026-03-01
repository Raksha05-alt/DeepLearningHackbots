"""
IntelResponse – Incident similarity module.

Computes feature-based similarity between the current incident and a corpus
of historical incidents using weighted Euclidean distance over normalised
risk-factor dimensions.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List

# ---------------------------------------------------------------------------
# Feature vector dimensions & weights
# ---------------------------------------------------------------------------
#
# Each dimension is normalised to [0, 1].  Weights reflect how much each
# dimension should contribute to the overall distance.
#
#   Dimension            | Normalisation     | Weight
#   ---------------------|-------------------|-------
#   aggression_level     | value / 3         |  1.5
#   crowd_level          | value / 3         |  1.0
#   weapon_mentioned     | bool → 0/1        |  2.0
#   injuries_present     | bool → 0/1        |  1.5
#   smoke_fire_present   | bool → 0/1        |  1.0
#   active_threat        | bool → 0/1        |  2.0
# ---------------------------------------------------------------------------

_DIM_WEIGHTS: List[float] = [
    1.5,   # aggression_level
    1.0,   # crowd_level
    2.0,   # weapon_mentioned
    1.5,   # injuries_present
    1.0,   # smoke_fire_present
    2.0,   # active_threat
]

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def feature_to_vector(features: Dict[str, Any]) -> List[float]:
    """Convert structured features into a 6-dimensional normalised vector.

    Dimensions (in order):
      0 – aggression_level / 3
      1 – crowd_level / 3
      2 – weapon_mentioned  (0 or 1)
      3 – injuries_present  (0 or 1)
      4 – smoke_fire_present (0 or 1)
      5 – active_threat      (0 or 1)
    """
    risk = features.get("risk_factors", {})
    entities = features.get("key_entities", {})

    return [
        risk.get("aggression_level", 0) / 3.0,
        risk.get("crowd_level", 0) / 3.0,
        1.0 if entities.get("weapon_mentioned") else 0.0,
        1.0 if entities.get("injuries_present") else 0.0,
        1.0 if entities.get("smoke_fire_present") else 0.0,
        1.0 if risk.get("active_threat") else 0.0,
    ]


def _weighted_distance(a: List[float], b: List[float]) -> float:
    """Weighted Euclidean distance between two feature vectors."""
    return math.sqrt(
        sum(w * (ai - bi) ** 2 for w, ai, bi in zip(_DIM_WEIGHTS, a, b))
    )


def get_similar_cases(
    current_features: Dict[str, Any],
    historical_incidents: List[Dict[str, Any]],
    k: int = 5,
) -> List[Dict[str, Any]]:
    """Return the *k* most similar historical incidents.

    Parameters
    ----------
    current_features : dict
        Structured features of the new incident.
    historical_incidents : list[dict]
        Raw incident dicts from storage.  Each must have a ``"structured"``
        key containing extraction output.
    k : int
        Number of results to return.

    Returns
    -------
    list[dict]
        Each entry:
        {
          "incident_id": str,
          "incident_type": str,
          "similarity_score": float (0-1, higher = more similar),
          "report_text_preview": str (first 120 chars),
        }

    Gracefully returns an empty list when there are no historical incidents
    or none have structured data.
    """
    if not historical_incidents:
        return []

    current_vec = feature_to_vector(current_features)
    scored: List[Dict[str, Any]] = []

    for inc in historical_incidents:
        structured = inc.get("structured")
        if not isinstance(structured, dict):
            continue  # skip incidents without extraction data

        hist_vec = feature_to_vector(structured)
        dist = _weighted_distance(current_vec, hist_vec)
        similarity = round(1.0 / (1.0 + dist), 4)

        scored.append({
            "incident_id": inc.get("id", "unknown"),
            "incident_type": structured.get("incident_type", "unknown"),
            "similarity_score": similarity,
            "report_text_preview": inc.get("report_text", "")[:120],
        })

    # Sort by similarity descending and return top-k
    scored.sort(key=lambda x: x["similarity_score"], reverse=True)
    return scored[:k]
