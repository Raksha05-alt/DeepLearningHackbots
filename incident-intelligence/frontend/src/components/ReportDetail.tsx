/** IntelResponse – Report detail panel for Incoming Reports tab.
 *  Language simplified for members of the public.
 */

import { useState } from "react";
import type { IncomingReport } from "../types";

// Maps internal action codes → plain-English labels
const ACTION_LABELS: Record<string, { color: string; emoji: string; label: string; sub: string }> = {
    dispatch_now: { color: "var(--priority-p0)", emoji: "🚨", label: "Send Help Now", sub: "This situation needs an immediate response." },
    dispatch_soon: { color: "var(--priority-p1)", emoji: "🔔", label: "Send Help Shortly", sub: "Help should be sent as soon as possible." },
    monitor: { color: "var(--priority-p2)", emoji: "👁️", label: "Keep an Eye On It", sub: "Watch the situation closely but no immediate action needed." },
    request_more_info: { color: "var(--priority-p3)", emoji: "❓", label: "Need More Details", sub: "We need more information before deciding what to do." },
};

// Maps priority codes → plain words and colour
const URGENCY: Record<string, { label: string; color: string }> = {
    p0: { label: "Critical", color: "var(--priority-p0)" },
    p1: { label: "High", color: "var(--priority-p1)" },
    p2: { label: "Medium", color: "var(--priority-p2)" },
    p3: { label: "Low", color: "var(--priority-p3)" },
};

// Human-readable danger field names
function toHumanLabel(key: string) {
    const map: Record<string, string> = {
        location: "📍 Location unknown",
        people_count: "👥 Number of people unclear",
        injuries_present: "🩹 Injury status unclear",
        weapon_mentioned: "⚠️ Weapon involvement unclear",
        smoke_fire_present: "🔥 Fire / smoke status unclear",
        injury_status_unclear: "🩹 Injury status unclear",
    };
    return map[key] ?? key.replace(/_/g, " ");
}

interface Props {
    report: IncomingReport;
    onCreateIncident: (reportId: string) => void;
    onDismiss: (reportId: string) => void;
    creating: boolean;
}

export default function ReportDetail({ report, onCreateIncident, onDismiss, creating }: Props) {
    const [dismissed, setDismissed] = useState(false);

    const s = report.extracted_features;
    const t = report.triage;
    const r = report.recommended;

    // Resolve urgency from triage priority or risk_level
    const priorityKey = t?.priority?.toLowerCase() ?? ({ critical: "p0", high: "p1", medium: "p2", low: "p3" }[report.risk_level] ?? "p2");
    const urgency = URGENCY[priorityKey] ?? URGENCY.p2;

    const action = r ? (ACTION_LABELS[r.action] ?? ACTION_LABELS.monitor) : null;

    return (
        <div className="detail-panel" id="report-detail">
            {/* ---- Header ---- */}
            <div className="detail-header">
                <h2>{report.type.replace(/_/g, " ").toUpperCase()}</h2>
                <span className="detail-id">#{report.id.slice(0, 8)}</span>
            </div>

            {/* ---- What was reported ---- */}
            <section className="detail-section">
                <h3>📝 What Was Reported</h3>
                <div className="report-box">
                    <p>{report.text}</p>
                    <div className="report-meta">
                        <span>Reported via: {report.source === "voice" ? "🎙️ Voice recording" : report.source}</span>
                        <span>Location: {report.location}</span>
                        <span>Time: {new Date(report.time).toLocaleString()}</span>
                    </div>
                </div>
            </section>

            {/* ---- Situation Summary ---- */}
            {s && (
                <section className="detail-section">
                    <h3>📋 Situation Summary</h3>
                    <div className="features-grid">
                        <div className="feature-item">
                            <label>Incident Type</label>
                            <span className="feature-value type-tag">
                                {s.incident_type.replace(/_/g, " ")}
                            </span>
                        </div>
                        <div className="feature-item">
                            <label>Location</label>
                            <span className="feature-value">
                                {s.key_entities.location ?? "Not mentioned"}
                            </span>
                        </div>

                        <div className="feature-item">
                            <label>Anyone Injured?</label>
                            <span className={`feature-value ${s.key_entities.injuries_present ? "danger" : ""}`}>
                                {s.key_entities.injuries_present === true ? "⚠️ Yes" : s.key_entities.injuries_present === false ? "No" : "Unknown"}
                            </span>
                        </div>
                        <div className="feature-item">
                            <label>Weapon Involved?</label>
                            <span className={`feature-value ${s.key_entities.weapon_mentioned ? "danger" : ""}`}>
                                {s.key_entities.weapon_mentioned === true ? "⚠️ Yes" : s.key_entities.weapon_mentioned === false ? "No" : "Unknown"}
                            </span>
                        </div>
                        <div className="feature-item">
                            <label>Fire or Smoke?</label>
                            <span className={`feature-value ${s.key_entities.smoke_fire_present ? "danger" : ""}`}>
                                {s.key_entities.smoke_fire_present === true ? "🔥 Yes" : s.key_entities.smoke_fire_present === false ? "No" : "Unknown"}
                            </span>
                        </div>

                        <div className="feature-item">
                            <label>Ongoing Danger?</label>
                            <span className={`feature-value ${s.risk_factors.active_threat ? "danger" : ""}`}>
                                {s.risk_factors.active_threat ? "⚠️ Yes — still unfolding" : "No"}
                            </span>
                        </div>
                        <div className="feature-item">
                            <label>AI Certainty</label>
                            <span className="feature-value">
                                {(s.confidence * 100).toFixed(0)}% sure
                            </span>
                        </div>
                    </div>
                </section>
            )}

            {/* ---- Urgency Level (replaces "Triage Score") ---- */}
            {t && (
                <section className="detail-section">
                    <h3>🚦 Urgency Level</h3>
                    <div className="triage-display">
                        <div className="triage-score">
                            <div
                                className="score-ring"
                                style={{
                                    background: `conic-gradient(${urgency.color} ${t.score * 3.6}deg, var(--bg-tertiary) 0deg)`,
                                }}
                            >
                                <div className="score-inner">
                                    <span className="score-num" style={{ color: urgency.color }}>{urgency.label}</span>
                                </div>
                            </div>
                        </div>
                        <div className="triage-reasons">
                            <h4>Why this urgency?</h4>
                            <ul>
                                {t.reasons.map((reason, i) => (
                                    <li key={i}>{reason.replace(/_/g, " ")}</li>
                                ))}
                            </ul>
                        </div>
                    </div>
                </section>
            )}

            {/* ---- What we still need to know ---- */}
            {s && s.missing_info.length > 0 && (
                <section className="detail-section">
                    <h3>❓ What We Still Need to Know</h3>
                    <ul className="missing-list">
                        {s.missing_info.map((info, i) => (
                            <li key={i} className="missing-item">{toHumanLabel(info)}</li>
                        ))}
                    </ul>
                </section>
            )}

            {/* ---- Suggested Response ---- */}
            {r && (
                <section className="detail-section">
                    <h3>✅ Suggested Response</h3>
                    {action && (
                        <div className="action-banner" style={{ borderLeftColor: action.color }}>
                            <span className="action-label">{action.emoji} {action.label}</span>
                            <p className="action-rationale">{action.sub}</p>
                            {r.rationale && <p className="action-rationale" style={{ marginTop: "6px" }}>{r.rationale}</p>}
                        </div>
                    )}
                    <div className="rec-columns">
                        <div className="rec-col">
                            <h4>📋 Steps to Take</h4>
                            <ul className="checklist">
                                {r.checklist.map((item, i) => (
                                    <li key={i}>
                                        <input type="checkbox" id={`rchk-${i}`} />
                                        <label htmlFor={`rchk-${i}`}>{item}</label>
                                    </li>
                                ))}
                            </ul>
                        </div>
                        <div className="rec-col">
                            <h4>💬 Questions to Ask the Reporter</h4>
                            <ol className="followup-list">
                                {r.follow_up_questions.map((q, i) => (
                                    <li key={i}>{q}</li>
                                ))}
                            </ol>
                        </div>
                    </div>
                </section>
            )}

            {/* ---- Action Buttons ---- */}
            <div className="report-actions">
                <button
                    className="btn btn-create-incident"
                    onClick={() => onCreateIncident(report.id)}
                    disabled={creating || dismissed}
                >
                    {creating ? "Sending…" : "🚨 Send for Response"}
                </button>
                <button className="btn btn-request-info" disabled={dismissed}>
                    💬 Ask for More Info
                </button>
                <button
                    className="btn btn-dismiss"
                    onClick={() => { setDismissed(true); onDismiss(report.id); }}
                    disabled={creating || dismissed}
                >
                    {dismissed ? "Closed" : "✕ Not an Incident"}
                </button>
            </div>
        </div>
    );
}
