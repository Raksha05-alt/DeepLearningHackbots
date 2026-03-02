/** IntelResponse – Active incident detail panel. */

import { useState } from "react";
import type { ActiveIncident } from "../types";
import { updateActiveStatus } from "../api";

const TIMELINE_ICONS: Record<string, string> = {
    report: "📩",
    dispatch: "🚨",
    radio: "📻",
    escalation: "⬆️",
    update: "📋",
    resolved: "✅",
};

const STATUS_STYLES: Record<string, { color: string; bg: string }> = {
    deploying: { color: "var(--warning)", bg: "rgba(210, 153, 34, 0.15)" },
    active: { color: "var(--accent)", bg: "rgba(88, 166, 255, 0.15)" },
    resolved: { color: "var(--success)", bg: "rgba(63, 185, 80, 0.15)" },
};

interface Props {
    incident: ActiveIncident;
    onUpdated: () => void;
}

export default function ActiveIncidentDetail({ incident, onUpdated }: Props) {
    const [updating, setUpdating] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    const handleStatusChange = async (newStatus: string) => {
        setUpdating(newStatus);
        setError(null);
        try {
            await updateActiveStatus(incident.id, newStatus);
            onUpdated();
        } catch (e: any) {
            setError(e.message);
        } finally {
            setUpdating(null);
        }
    };

    const s = incident.extracted_features;
    const ss = STATUS_STYLES[incident.status] ?? STATUS_STYLES.active;

    return (
        <div className="detail-panel" id="active-detail">
            {/* ---- Header ---- */}
            <div className="detail-header">
                <h2>{incident.summary}</h2>
                <span className="detail-id">#{incident.id.slice(0, 8)}</span>
            </div>

            {/* ---- Incident Overview ---- */}
            <section className="detail-section">
                <h3>📋 Incident Overview</h3>
                <div className="overview-grid">
                    <div className="feature-item">
                        <label>Location</label>
                        <span className="feature-value">{incident.location}</span>
                    </div>
                    <div className="feature-item">
                        <label>Type</label>
                        <span className="feature-value type-tag">
                            {incident.type.replace(/_/g, " ")}
                        </span>
                    </div>
                    <div className="feature-item">
                        <label>Priority</label>
                        <span className="feature-value">{incident.priority}</span>
                    </div>
                    <div className="feature-item">
                        <label>Status</label>
                        <span
                            className="feature-value status-value"
                            style={{ color: ss.color }}
                        >
                            {incident.status.toUpperCase()}
                        </span>
                    </div>
                </div>
            </section>

            {/* ---- Extracted Features ---- */}
            {s && (
                <section className="detail-section">
                    <h3>🔍 Extracted Features</h3>
                    <div className="features-grid">
                        <div className="feature-item">
                            <label>Injuries</label>
                            <span className={`feature-value ${s.key_entities.injuries_present ? "danger" : ""}`}>
                                {s.key_entities.injuries_present ? "Yes" : "No"}
                            </span>
                        </div>
                        <div className="feature-item">
                            <label>Weapon</label>
                            <span className={`feature-value ${s.key_entities.weapon_mentioned ? "danger" : ""}`}>
                                {s.key_entities.weapon_mentioned ? "Yes" : "No"}
                            </span>
                        </div>
                        <div className="feature-item">
                            <label>Fire / Smoke</label>
                            <span className={`feature-value ${s.key_entities.smoke_fire_present ? "danger" : ""}`}>
                                {s.key_entities.smoke_fire_present ? "Yes" : "No"}
                            </span>
                        </div>
                        <div className="feature-item">
                            <label>Active Threat</label>
                            <span className={`feature-value ${s.risk_factors.active_threat ? "danger" : ""}`}>
                                {s.risk_factors.active_threat ? "⚠ YES" : "No"}
                            </span>
                        </div>
                        <div className="feature-item">
                            <label>Aggression</label>
                            <div className="level-bar">
                                <div className="level-fill aggression" style={{ width: `${(s.risk_factors.aggression_level / 3) * 100}%` }} />
                                <span>{s.risk_factors.aggression_level}/3</span>
                            </div>
                        </div>
                        <div className="feature-item">
                            <label>Crowd Level</label>
                            <div className="level-bar">
                                <div className="level-fill crowd" style={{ width: `${(s.risk_factors.crowd_level / 3) * 100}%` }} />
                                <span>{s.risk_factors.crowd_level}/3</span>
                            </div>
                        </div>
                    </div>
                </section>
            )}

            {/* ---- Live Timeline ---- */}
            <section className="detail-section">
                <h3>⏱️ Live Timeline</h3>
                <div className="timeline">
                    {incident.timeline.map((event, i) => (
                        <div key={i} className={`timeline-entry timeline-${event.type}`}>
                            <div className="timeline-dot">
                                {TIMELINE_ICONS[event.type] ?? "📋"}
                            </div>
                            <div className="timeline-content">
                                <div className="timeline-header">
                                    <span className="timeline-type">{event.type}</span>
                                    <span className="timeline-time">
                                        {new Date(event.time).toLocaleTimeString()}
                                    </span>
                                </div>
                                <p className="timeline-desc">{event.description}</p>
                            </div>
                        </div>
                    ))}
                </div>
            </section>

            {/* ---- Responders ---- */}
            <section className="detail-section">
                <h3>👤 Responders</h3>
                {incident.responders.length > 0 ? (
                    <div className="responders-grid">
                        {incident.responders.map((r, i) => (
                            <div key={i} className="responder-card">
                                <div className="responder-name">{r.name}</div>
                                <div className="responder-role">{r.role}</div>
                                <div className="responder-unit">{r.unit}</div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="no-responders">
                        No responders assigned yet. Incident is deploying.
                    </div>
                )}
            </section>

            {/* ---- Status + Resolution ---- */}
            <section className="detail-section">
                <h3>🏷️ Status & Resolution</h3>
                <div
                    className="current-status"
                    style={{ background: ss.bg, color: ss.color, borderColor: ss.color }}
                >
                    Current Status: <strong>{incident.status.toUpperCase()}</strong>
                </div>
                {error && <div className="error-msg">{error}</div>}
                {incident.status !== "resolved" && (
                    <div className="status-actions">
                        {incident.status === "deploying" && (
                            <button
                                className="btn btn-status-active"
                                onClick={() => handleStatusChange("active")}
                                disabled={updating !== null}
                            >
                                {updating === "active" ? "…" : "▶ Mark Active"}
                            </button>
                        )}
                        <button
                            className="btn btn-resolved"
                            onClick={() => handleStatusChange("resolved")}
                            disabled={updating !== null}
                        >
                            {updating === "resolved" ? "…" : "✓ Resolve"}
                        </button>
                    </div>
                )}
            </section>
        </div>
    );
}
