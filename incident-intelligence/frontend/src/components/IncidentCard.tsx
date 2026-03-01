/** IntelResponse – Incident queue card component. */

import type { Incident } from "../types";

const PRIORITY_STYLES: Record<string, { bg: string; label: string }> = {
    P0: { bg: "var(--priority-p0)", label: "P0 CRITICAL" },
    P1: { bg: "var(--priority-p1)", label: "P1 HIGH" },
    P2: { bg: "var(--priority-p2)", label: "P2 MEDIUM" },
    P3: { bg: "var(--priority-p3)", label: "P3 LOW" },
};

const TYPE_ICONS: Record<string, string> = {
    medical: "🏥",
    fire_smoke: "🔥",
    violence_conflict: "⚔️",
    suspicious_person: "🕵️",
    crowd_risk: "👥",
    traffic_accident: "🚗",
    other: "📋",
};

function timeAgo(iso: string): string {
    const diff = Date.now() - new Date(iso).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return "just now";
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    return `${Math.floor(hrs / 24)}d ago`;
}

interface Props {
    incident: Incident;
    selected: boolean;
    onClick: () => void;
}

export default function IncidentCard({ incident, selected, onClick }: Props) {
    const type = incident.structured?.incident_type ?? "other";
    const priority = incident.triage?.priority ?? "P3";
    const ps = PRIORITY_STYLES[priority] ?? PRIORITY_STYLES.P3;
    const location =
        incident.structured?.key_entities?.location ??
        incident.location_hint ??
        "Unknown location";

    return (
        <div
            className={`incident-card ${selected ? "selected" : ""}`}
            onClick={onClick}
            id={`card-${incident.id}`}
        >
            <div className="card-priority-bar" style={{ background: ps.bg }} />
            <div className="card-body">
                <div className="card-header">
                    <span className="priority-badge" style={{ background: ps.bg }}>
                        {ps.label}
                    </span>
                    <span className="card-time">{timeAgo(incident.created_at)}</span>
                </div>
                <div className="card-type">
                    <span className="type-icon">{TYPE_ICONS[type] ?? "📋"}</span>
                    <span className="type-label">{type.replace(/_/g, " ")}</span>
                    <span className="card-source">{incident.source.replace(/_/g, " ")}</span>
                </div>
                <div className="card-location">📍 {location}</div>
                <p className="card-preview">{incident.report_text.slice(0, 100)}…</p>
                {incident.status !== "open" && (
                    <span className={`status-chip status-${incident.status}`}>
                        {incident.status}
                    </span>
                )}
            </div>
        </div>
    );
}
