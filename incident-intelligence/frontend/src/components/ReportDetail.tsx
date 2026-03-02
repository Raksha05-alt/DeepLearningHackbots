/** IntelResponse – Report detail panel for Incoming Reports tab. */

import { useState } from "react";
import type { IncomingReport } from "../types";

const ACTION_STYLES: Record<string, { color: string; label: string }> = {
    dispatch_now: { color: "var(--priority-p0)", label: "🚨 DISPATCH NOW" },
    dispatch_soon: { color: "var(--priority-p1)", label: "🔔 DISPATCH SOON" },
    monitor: { color: "var(--priority-p2)", label: "👁️ MONITOR" },
    request_more_info: { color: "var(--priority-p3)", label: "❓ REQUEST MORE INFO" },
};

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
    const action = r ? ACTION_STYLES[r.action] ?? ACTION_STYLES.monitor : null;

    return (
        <div className="detail-panel" id="report-detail">
            {/* ---- Header ---- */}
            <div className="detail-header">
                <h2>
                    {report.type.replace(/_/g, " ").toUpperCase()}
                </h2>
                <span className="detail-id">#{report.id.slice(0, 8)}</span>
            </div>

            {/* ---- Raw Report ---- */}
            <section className="detail-section">
                <h3>📝 Raw Report</h3>
                <div className="report-box">
                    <p>{report.text}</p>
                    <div className="report-meta">
                        <span>Source: {report.source}</span>
                        <span>Location: {report.location}</span>
                        <span>Time: {new Date(report.time).toLocaleString()}</span>
                    </div>
                </div>
            </section>

            {/* ---- Extracted Features ---- */}
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
                        <div className="feature-item">
                            <label>Active Threat</label>
                            <span className={`feature-value ${s.risk_factors.active_threat ? "danger" : ""}`}>
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

            {/* ---- Triage Score ---- */}
            {t && (
                <section className="detail-section">
                    <h3>📊 Triage Score</h3>
                    <div className="triage-display">
                        <div className="triage-score">
                            <div
                                className="score-ring"
                                style={{
                                    background: `conic-gradient(var(--priority-${t.priority.toLowerCase()}) ${t.score * 3.6}deg, var(--bg-tertiary) 0deg)`,
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
                                {t.reasons.map((reason, i) => (
                                    <li key={i}>{reason}</li>
                                ))}
                            </ul>
                        </div>
                    </div>
                </section>
            )}

            {/* ---- Missing Information ---- */}
            {s && s.missing_info.length > 0 && (
                <section className="detail-section">
                    <h3>⚠️ Missing Information</h3>
                    <ul className="missing-list">
                        {s.missing_info.map((info, i) => (
                            <li key={i} className="missing-item">{info}</li>
                        ))}
                    </ul>
                </section>
            )}

            {/* ---- Recommended Action ---- */}
            {r && (
                <section className="detail-section">
                    <h3>🎯 Recommended Action</h3>
                    {action && (
                        <div className="action-banner" style={{ borderLeftColor: action.color }}>
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
                                        <input type="checkbox" id={`rchk-${i}`} />
                                        <label htmlFor={`rchk-${i}`}>{item}</label>
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

            {/* ---- Action Buttons ---- */}
            <div className="report-actions">
                <button
                    className="btn btn-create-incident"
                    onClick={() => onCreateIncident(report.id)}
                    disabled={creating || dismissed}
                >
                    {creating ? "Creating…" : "🚀 Create Incident"}
                </button>
                <button className="btn btn-request-info" disabled={dismissed}>
                    ❓ Request More Info
                </button>
                <button
                    className="btn btn-dismiss"
                    onClick={() => { setDismissed(true); onDismiss(report.id); }}
                    disabled={creating || dismissed}
                >
                    {dismissed ? "Dismissed" : "✕ Dismiss"}
                </button>
            </div>
        </div>
    );
}
