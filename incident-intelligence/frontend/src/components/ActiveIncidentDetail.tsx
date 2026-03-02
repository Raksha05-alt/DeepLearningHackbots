/** IntelResponse – Active incident detail panel with live WebSocket radio feed. */

import { useEffect, useRef, useState } from "react";
import type { ActiveIncident, TimelineEvent, Responder } from "../types";
import { updateActiveStatus } from "../api";

const WS_BASE = "ws://localhost:8000";

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

    // ---- WebSocket live feed state ----
    const [liveTimeline, setLiveTimeline] = useState<TimelineEvent[]>(incident.timeline);
    const [liveFeatures, setLiveFeatures] = useState(incident.extracted_features);
    const [liveStatus, setLiveStatus] = useState<string>(incident.status);
    const [liveResponders, setLiveResponders] = useState<Responder[]>(incident.responders);
    const [wsConnected, setWsConnected] = useState(false);
    const [newEntryIdx, setNewEntryIdx] = useState<number | null>(null);
    const wsRef = useRef<WebSocket | null>(null);
    const timelineEndRef = useRef<HTMLDivElement | null>(null);

    // Reset state when incident changes
    useEffect(() => {
        setLiveTimeline(incident.timeline);
        setLiveFeatures(incident.extracted_features);
        setLiveStatus(incident.status);
        setLiveResponders(incident.responders);
    }, [incident.id, incident.status, incident.responders]);

    // ---- WebSocket connection ----
    useEffect(() => {
        const ws = new WebSocket(`${WS_BASE}/ws/incidents/${incident.id}/radio`);
        wsRef.current = ws;

        ws.onopen = () => setWsConnected(true);
        ws.onclose = () => setWsConnected(false);
        ws.onerror = () => setWsConnected(false);

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.type === "connected") {
                    // Initial state from server
                    if (data.timeline) setLiveTimeline(data.timeline);
                    if (data.extracted_features) setLiveFeatures(data.extracted_features);
                } else if (data.type === "radio_update") {
                    // New radio transmission
                    setLiveTimeline((prev) => {
                        const updated = [...prev, data.entry];
                        // Flash the new entry
                        setNewEntryIdx(updated.length - 1);
                        setTimeout(() => setNewEntryIdx(null), 2500);
                        return updated;
                    });
                    // Update extracted features (continuous extraction)
                    if (data.extracted_features) {
                        setLiveFeatures(data.extracted_features);
                    }
                    if (data.status) {
                        setLiveStatus(data.status);
                    }
                    if (data.responders) {
                        setLiveResponders(data.responders);
                    }
                }
            } catch {
                // ignore malformed messages
            }
        };

        return () => {
            ws.close();
            setWsConnected(false);
        };
    }, [incident.id]);

    // Auto-scroll timeline on new entries
    useEffect(() => {
        timelineEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [liveTimeline.length]);

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

    const s = liveFeatures;
    const ss = STATUS_STYLES[liveStatus] ?? STATUS_STYLES.active;

    return (
        <div className="detail-panel" id="active-detail">
            {/* ---- Header ---- */}
            <div className="detail-header">
                <h2>{incident.summary}</h2>
                <div className="detail-header-right">
                    {wsConnected && (
                        <span className="live-indicator">
                            <span className="live-dot" />
                            LIVE
                        </span>
                    )}
                    <span className="detail-id">#{incident.id.slice(0, 8)}</span>
                </div>
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
                            {liveStatus.toUpperCase()}
                        </span>
                    </div>
                </div>
            </section>

            {/* ---- Extracted Features (updated live) ---- */}
            {s && (
                <section className="detail-section">
                    <h3>
                        🔍 Extracted Features
                        {wsConnected && <span className="live-badge">UPDATING LIVE</span>}
                    </h3>
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
                <h3>
                    ⏱️ Live Timeline
                    {wsConnected && (
                        <span className="live-badge">{liveTimeline.length} events</span>
                    )}
                </h3>
                <div className="timeline">
                    {liveTimeline.map((event, i) => (
                        <div
                            key={`${event.time}-${i}`}
                            className={`timeline-entry timeline-${event.type}${i === newEntryIdx ? " timeline-entry-new" : ""}`}
                        >
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
                                {(event as any).speaker && (
                                    <div className="timeline-speaker">
                                        <span className="speaker-callsign">{(event as any).callsign}</span>
                                        <span className="speaker-name">{(event as any).speaker}</span>
                                    </div>
                                )}
                                <p className="timeline-desc">{event.description}</p>
                            </div>
                        </div>
                    ))}
                    <div ref={timelineEndRef} />
                </div>
            </section>

            {/* ---- Responders ---- */}
            <section className="detail-section">
                <h3>👤 Responders</h3>
                {liveResponders.length > 0 ? (
                    <div className="responders-grid">
                        {liveResponders.map((r, i) => (
                            <div key={i} className="responder-card">
                                <div className="responder-header">
                                    <span className="responder-name">{r.name}</span>
                                    {(r as any).callsign && (
                                        <span className="responder-callsign">{(r as any).callsign}</span>
                                    )}
                                </div>
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
                    Current Status: <strong>{liveStatus.toUpperCase()}</strong>
                </div>
                {error && <div className="error-msg">{error}</div>}
                {liveStatus !== "resolved" && (
                    <div className="status-actions">
                        {liveStatus === "deploying" && (
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
