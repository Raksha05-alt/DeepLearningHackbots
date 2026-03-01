"""
IntelResponse – Pydantic models / data schemas.
"""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

SourceType = Literal["hotline_text", "radio_transcript", "citizen_app"]
StatusType = Literal["open", "resolved", "escalated", "false_alarm"]

# ---------------------------------------------------------------------------
# Request bodies
# ---------------------------------------------------------------------------


class IncidentCreate(BaseModel):
    """Payload accepted by POST /incidents."""

    source: SourceType
    report_text: str
    location_hint: Optional[str] = None


class StatusUpdate(BaseModel):
    """Payload accepted by POST /incidents/{id}/status."""

    status: StatusType

# ---------------------------------------------------------------------------
# Full incident model (stored + returned)
# ---------------------------------------------------------------------------


class Incident(BaseModel):
    """Complete incident record persisted in the JSON store."""

    id: str
    created_at: str
    source: SourceType
    report_text: str
    location_hint: Optional[str] = None
    structured: Optional[Any] = None
    triage: Optional[Any] = None
    recommended: Optional[Any] = None
    status: StatusType = "open"
