/** IntelResponse – Active incident card for Active Incidents tab. */

import type { ActiveIncident } from "../types";

const PRIORITY_STYLES: Record<string, { bg: string; label: string }> = {
    P0: { bg: "var(--priority-p0)", label: "P0 CRITICAL" },
    P1: { bg: "var(--priority-p1)", label: "P1 HIGH" },
    P2: { bg: "var(--priority-p2)", label: "P2 MEDIUM" },
    P3: { bg: "var(--priority-p3)", label: "P3 LOW" },
};

const STATUS_STYLES: Record<string, { color: string; bg: string }> = {
    deploying: { color: "var(--warning)", bg: "rgba(210, 153, 34, 0.15)" },
    active: { color: "var(--accent)", bg: "rgba(88, 166, 255, 0.15)" },
    resolved: { color: "var(--success)", bg: "rgba(63, 185, 80, 0.15)" },
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
    incident: ActiveIncident;
    selected: boolean;
    onClick: () => void;
}

export default function ActiveIncidentCard({ incident, selected, onClick }: Props) {
    const ps = PRIORITY_STYLES[incident.priority] ?? PRIORITY_STYLES.P2;
    const ss = STATUS_STYLES[incident.status] ?? STATUS_STYLES.active;
    const firstEvent = incident.timeline[0];

    return (
        <div
            className={`incident-card ${selected ? "selected" : ""}`}
            onClick={onClick}
            id={`active-${incident.id}`}
        >
            <div className="card-priority-bar" style={{ background: ps.bg }} />
            <div className="card-body">
                <div className="card-header">
                    <span className="priority-badge" style={{ background: ps.bg }}>
                        {ps.label}
                    </span>
                    <span className="card-time">
                        {firstEvent ? timeAgo(firstEvent.time) : "—"}
                    </span>
                </div>
                <div className="card-type">
                    <span className="type-icon">
                        {TYPE_ICONS[incident.type] ?? "📋"}
                    </span>
                    <span className="type-label">
                        {incident.type.replace(/_/g, " ")}
                    </span>
                    <span
                        className="card-status-badge"
                        style={{ background: ss.bg, color: ss.color }}
                    >
                        {incident.status}
                    </span>
                </div>
                <div className="card-location">📍 {incident.location}</div>
                <p className="card-preview">{incident.summary}</p>
                <div className="card-footer-row">
                    <span className="responder-count">
                        👤 {incident.responders.length} responder{incident.responders.length !== 1 ? "s" : ""}
                    </span>
                    <span className="timeline-count">
                        📋 {incident.timeline.length} updates
                    </span>
                </div>
            </div>
        </div>
    );
}
