/** IntelResponse – Incident detail panel. */

import { useState } from "react";
import type { Incident, SimilarCase } from "../types";
import { updateActiveStatus } from "../api";

interface Props {
    incident: Incident;
    similarCases: SimilarCase[];
    onStatusUpdated: () => void;
}

const ACTION_STYLES: Record<string, { color: string; label: string }> = {
    dispatch_now: { color: "var(--priority-p0)", label: "🚨 DISPATCH NOW" },
    dispatch_soon: { color: "var(--priority-p1)", label: "🔔 DISPATCH SOON" },
    monitor: { color: "var(--priority-p2)", label: "👁️ MONITOR" },
    request_more_info: { color: "var(--priority-p3)", label: "❓ REQUEST MORE INFO" },
};

export default function IncidentDetail({
    incident,
    similarCases,
    onStatusUpdated,
}: Props) {
    const [updating, setUpdating] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    const handleStatus = async (status: string) => {
        setUpdating(status);
        setError(null);
        try {
            await updateActiveStatus(incident.id, status);
            onStatusUpdated();
        } catch (e: any) {
            setError(e.message);
        } finally {
            setUpdating(null);
        }
    };

    const s = incident.structured;
    const t = incident.triage;
    const r = incident.recommended;
    const action = r ? ACTION_STYLES[r.action] ?? ACTION_STYLES.monitor : null;

    // Compute escalation rate among similar cases
    const escalatedCount = similarCases.filter(
        (c) => c.outcome === "escalated"
    ).length;
    const escalationRate =
        similarCases.length > 0
            ? Math.round((escalatedCount / similarCases.length) * 100)
            : 0;

    return (
        <div className="detail-panel" id="incident-detail">
            {/* ---- Header ---- */}
            <div className="detail-header">
                <h2>
                    {s
                        ? `${s.incident_type.replace(/_/g, " ").toUpperCase()}`
                        : "Incident Detail"}
                </h2>
                <span className="detail-id">#{incident.id.slice(0, 8)}</span>
            </div>

            {/* ---- Status Actions ---- */}
            {incident.status === "open" && (
                <div className="status-actions">
                    <button
                        className="btn btn-resolved"
                        onClick={() => handleStatus("resolved")}
                        disabled={updating !== null}
                    >
                        {updating === "resolved" ? "…" : "✓ Resolved"}
                    </button>
                    <button
                        className="btn btn-escalated"
                        onClick={() => handleStatus("escalated")}
                        disabled={updating !== null}
                    >
                        {updating === "escalated" ? "…" : "⬆ Escalate"}
                    </button>
                    <button
                        className="btn btn-false-alarm"
                        onClick={() => handleStatus("false_alarm")}
                        disabled={updating !== null}
                    >
                        {updating === "false_alarm" ? "…" : "✕ False Alarm"}
                    </button>
                </div>
            )}
            {incident.status !== "open" && (
                <div className={`status-banner status-${incident.status}`}>
                    Status: <strong>{incident.status.replace(/_/g, " ")}</strong>
                </div>
            )}
            {error && <div className="error-msg">{error}</div>}

            {/* ---- Raw Report ---- */}
            <section className="detail-section">
                <h3>📝 Raw Report</h3>
                <div className="report-box">
                    <p>{incident.report_text}</p>
                    <div className="report-meta">
                        <span>Source: {incident.source.replace(/_/g, " ")}</span>
                        {incident.location_hint && (
                            <span>Location hint: {incident.location_hint}</span>
                        )}
                        <span>
                            Time: {new Date(incident.created_at).toLocaleString()}
                        </span>
                    </div>
                </div>
            </section>

            {/* ---- Structured Extraction ---- */}
            {s && (
                <section className="detail-section">
                    <h3>🔍 Extracted Features</h3>
                    <div className="features-grid">
                        <div className="feature-item">
                            <label>Type</label>
                            <span className="feature-value type-tag">
                                {s.incident_type.replace(/_/g, " ")}
                            </span>
                        </div>
                        <div className="feature-item">
                            <label>Location</label>
                            <span className="feature-value">
                                {s.key_entities.location ?? "—"}
                            </span>
                        </div>
                        <div className="feature-item">
                            <label>People Count</label>
                            <span className="feature-value">
                                {s.key_entities.people_count ?? "—"}
                            </span>
                        </div>
                        <div className="feature-item">
                            <label>Injuries</label>
                            <span
                                className={`feature-value ${s.key_entities.injuries_present ? "danger" : ""
                                    }`}
                            >
                                {s.key_entities.injuries_present ? "Yes" : "No"}
                            </span>
                        </div>
                        <div className="feature-item">
                            <label>Weapon</label>
                            <span
                                className={`feature-value ${s.key_entities.weapon_mentioned ? "danger" : ""
                                    }`}
                            >
                                {s.key_entities.weapon_mentioned ? "Yes" : "No"}
                            </span>
                        </div>
                        <div className="feature-item">
                            <label>Fire / Smoke</label>
                            <span
                                className={`feature-value ${s.key_entities.smoke_fire_present ? "danger" : ""
                                    }`}
                            >
                                {s.key_entities.smoke_fire_present ? "Yes" : "No"}
                            </span>
                        </div>
                        <div className="feature-item">
                            <label>Aggression</label>
                            <div className="level-bar">
                                <div
                                    className="level-fill aggression"
                                    style={{
                                        width: `${(s.risk_factors.aggression_level / 3) * 100}%`,
                                    }}
                                />
                                <span>{s.risk_factors.aggression_level}/3</span>
                            </div>
                        </div>
                        <div className="feature-item">
                            <label>Crowd Level</label>
                            <div className="level-bar">
                                <div
                                    className="level-fill crowd"
                                    style={{
                                        width: `${(s.risk_factors.crowd_level / 3) * 100}%`,
                                    }}
                                />
                                <span>{s.risk_factors.crowd_level}/3</span>
                            </div>
                        </div>
                        <div className="feature-item">
                            <label>Active Threat</label>
                            <span
                                className={`feature-value ${s.risk_factors.active_threat ? "danger" : ""
                                    }`}
                            >
                                {s.risk_factors.active_threat ? "⚠ YES" : "No"}
                            </span>
                        </div>
                        <div className="feature-item">
                            <label>Confidence</label>
                            <span className="feature-value">
                                {(s.confidence * 100).toFixed(0)}%
                            </span>
                        </div>
                    </div>
                    {s.missing_info.length > 0 && (
                        <div className="missing-info">
                            ⚠ Missing: {s.missing_info.join(", ")}
                        </div>
                    )}
                </section>
            )}

            {/* ---- Triage ---- */}
            {t && (
                <section className="detail-section">
                    <h3>📊 Triage</h3>
                    <div className="triage-display">
                        <div className="triage-score">
                            <div
                                className="score-ring"
                                style={{
                                    background: `conic-gradient(var(--priority-${t.priority.toLowerCase()}) ${t.score * 3.6
                                        }deg, var(--bg-tertiary) 0deg)`,
                                }}
                            >
                                <div className="score-inner">
                                    <span className="score-num">{t.score}</span>
                                    <span className="score-label">{t.priority}</span>
                                </div>
                            </div>
                        </div>
                        <div className="triage-reasons">
                            <h4>Key Factors</h4>
                            <ul>
                                {t.reasons.map((r, i) => (
                                    <li key={i}>{r}</li>
                                ))}
                            </ul>
                        </div>
                    </div>
                </section>
            )}

            {/* ---- Recommended Action ---- */}
            {r && (
                <section className="detail-section">
                    <h3>🎯 Recommended Action</h3>
                    {action && (
                        <div
                            className="action-banner"
                            style={{ borderLeftColor: action.color }}
                        >
                            <span className="action-label">{action.label}</span>
                            <p className="action-rationale">{r.rationale}</p>
                        </div>
                    )}

                    <div className="rec-columns">
                        <div className="rec-col">
                            <h4>📋 Checklist</h4>
                            <ul className="checklist">
                                {r.checklist.map((item, i) => (
                                    <li key={i}>
                                        <input type="checkbox" id={`chk-${i}`} />
                                        <label htmlFor={`chk-${i}`}>{item}</label>
                                    </li>
                                ))}
                            </ul>
                        </div>
                        <div className="rec-col">
                            <h4>❓ Follow-up Questions</h4>
                            <ol className="followup-list">
                                {r.follow_up_questions.map((q, i) => (
                                    <li key={i}>{q}</li>
                                ))}
                            </ol>
                        </div>
                    </div>
                </section>
            )}

            {/* ---- Similar Cases ---- */}
            {similarCases.length > 0 && (
                <section className="detail-section">
                    <h3>🔗 Similar Historical Cases</h3>
                    <div className="similar-stats">
                        <div className="stat-box">
                            <span className="stat-num">{similarCases.length}</span>
                            <span className="stat-label">matches</span>
                        </div>
                        <div className="stat-box escalation">
                            <span className="stat-num">{escalationRate}%</span>
                            <span className="stat-label">escalation rate</span>
                        </div>
                    </div>
                    <div className="similar-list">
                        {similarCases.map((c) => (
                            <div key={c.incident_id} className="similar-card">
                                <div className="similar-header">
                                    <span className="similar-type">
                                        {c.incident_type.replace(/_/g, " ")}
                                    </span>
                                    <span className="similar-score">
                                        {(c.similarity_score * 100).toFixed(0)}% match
                                    </span>
                                </div>
                                <p className="similar-preview">{c.report_text_preview}</p>
                                <div className="similar-footer">
                                    {c.outcome && (
                                        <span className={`outcome-chip outcome-${c.outcome}`}>
                                            {c.outcome}
                                        </span>
                                    )}
                                    {c.response_taken && (
                                        <span className="response-chip">
                                            {c.response_taken.replace(/_/g, " ")}
                                        </span>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </section>
            )}
        </div>
    );
}
