/** IntelResponse – Report card component for Incoming Reports tab. */

import type { IncomingReport } from "../types";

const RISK_STYLES: Record<string, { bg: string; label: string }> = {
    critical: { bg: "var(--priority-p0)", label: "CRITICAL" },
    high: { bg: "var(--priority-p1)", label: "HIGH" },
    medium: { bg: "var(--priority-p2)", label: "MEDIUM" },
    low: { bg: "var(--priority-p3)", label: "LOW" },
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
    report: IncomingReport;
    selected: boolean;
    onClick: () => void;
}

export default function ReportCard({ report, selected, onClick }: Props) {
    const rs = RISK_STYLES[report.risk_level] ?? RISK_STYLES.medium;

    return (
        <div
            className={`incident-card ${selected ? "selected" : ""}`}
            onClick={onClick}
            id={`report-${report.id}`}
        >
            <div className="card-priority-bar" style={{ background: rs.bg }} />
            <div className="card-body">
                <div className="card-header">
                    <span className="priority-badge" style={{ background: rs.bg }}>
                        {rs.label}
                    </span>
                    <span className="card-time">{timeAgo(report.time)}</span>
                </div>
                <div className="card-type">
                    <span className="type-icon">
                        {TYPE_ICONS[report.type] ?? "📋"}
                    </span>
                    <span className="type-label">
                        {report.type.replace(/_/g, " ")}
                    </span>
                    <span className="card-source">{report.source}</span>
                </div>
                <div className="card-location">📍 {report.location}</div>
                <p className="card-preview">{report.text.slice(0, 100)}…</p>
                <div className="card-footer-row">
                    <span className="confidence-badge">
                        {(report.confidence * 100).toFixed(0)}% confidence
                    </span>
                </div>
            </div>
        </div>
    );
}
