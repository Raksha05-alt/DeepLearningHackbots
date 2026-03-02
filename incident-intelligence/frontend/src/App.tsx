import { useEffect, useState, useCallback } from "react";
import {
    ReportCard,
    ReportDetail,
    ActiveIncidentCard,
    ActiveIncidentDetail,
    VoiceRecorder,
} from "./components";
import { fetchReports, fetchActiveIncidents, createFromReport } from "./api";
import type { IncomingReport, ActiveIncident } from "./types";

type Tab = "reports" | "incidents" | "record";

function App() {
    const [activeTab, setActiveTab] = useState<Tab>("reports");

    // ---- Reports state ----
    const [reports, setReports] = useState<IncomingReport[]>([]);
    const [selectedReportId, setSelectedReportId] = useState<string | null>(null);
    const [reportsLoading, setReportsLoading] = useState(true);
    const [reportsError, setReportsError] = useState<string | null>(null);
    const [creating, setCreating] = useState(false);

    // ---- Incidents state ----
    const [incidents, setIncidents] = useState<ActiveIncident[]>([]);
    const [selectedIncidentId, setSelectedIncidentId] = useState<string | null>(null);
    const [incidentsLoading, setIncidentsLoading] = useState(true);
    const [incidentsError, setIncidentsError] = useState<string | null>(null);

    // ---- Load reports ----
    const loadReports = useCallback(async () => {
        setReportsLoading(true);
        setReportsError(null);
        try {
            const data = await fetchReports();
            setReports(data);
            if (data.length > 0 && !selectedReportId) {
                setSelectedReportId(data[0].id);
            }
        } catch (e: any) {
            setReportsError(e.message);
        } finally {
            setReportsLoading(false);
        }
    }, []);

    // ---- Load incidents ----
    const loadIncidents = useCallback(async () => {
        setIncidentsLoading(true);
        setIncidentsError(null);
        try {
            const data = await fetchActiveIncidents();
            setIncidents(data);
            if (data.length > 0 && !selectedIncidentId) {
                setSelectedIncidentId(data[0].id);
            }
        } catch (e: any) {
            setIncidentsError(e.message);
        } finally {
            setIncidentsLoading(false);
        }
    }, []);

    useEffect(() => {
        loadReports();
        loadIncidents();
    }, [loadReports, loadIncidents]);

    // ---- Create incident from report ----
    const handleCreateIncident = async (reportId: string) => {
        setCreating(true);
        try {
            await createFromReport(reportId);
            // Switch to incidents tab and refresh both
            await Promise.all([loadReports(), loadIncidents()]);
            setActiveTab("incidents");
            // Select the new incident (it's first in the list)
            const updatedIncidents = await fetchActiveIncidents();
            if (updatedIncidents.length > 0) {
                setSelectedIncidentId(updatedIncidents[0].id);
            }
        } catch (e: any) {
            setReportsError(e.message);
        } finally {
            setCreating(false);
        }
    };

    // ---- Dismiss report ----
    const handleDismiss = (reportId: string) => {
        setReports((prev) => prev.filter((r) => r.id !== reportId));
        if (selectedReportId === reportId) {
            const remaining = reports.filter((r) => r.id !== reportId);
            setSelectedReportId(remaining.length > 0 ? remaining[0].id : null);
        }
    };

    // ---- Voice report received ----
    const handleVoiceReport = (report: IncomingReport) => {
        setReports((prev) => [report, ...prev]);
        setSelectedReportId(report.id);
        // Switch to the reports tab so the user can see and triage the result
        setActiveTab("reports");
    };

    const selectedReport = reports.find((r) => r.id === selectedReportId) ?? null;
    const selectedIncident = incidents.find((i) => i.id === selectedIncidentId) ?? null;

    return (
        <div className="app-layout">
            {/* ---- Sidebar ---- */}
            <aside className="sidebar">
                <div className="sidebar-header">
                    <h1 className="logo">
                        <span className="logo-icon">🛡️</span> IntelResponse
                    </h1>
                    <p className="logo-sub">Incident Intelligence</p>
                </div>

                {/* ---- Tab Navigation ---- */}
                <div className="tab-nav">
                    <button
                        className={`tab-btn ${activeTab === "reports" ? "active" : ""}`}
                        onClick={() => setActiveTab("reports")}
                    >
                        <span className="tab-icon">📩</span>
                        Incoming
                        <span className="tab-count">{reports.length}</span>
                    </button>
                    <button
                        className={`tab-btn ${activeTab === "incidents" ? "active" : ""}`}
                        onClick={() => setActiveTab("incidents")}
                    >
                        <span className="tab-icon">🚨</span>
                        Active
                        <span className="tab-count">{incidents.length}</span>
                    </button>
                    <button
                        className={`tab-btn tab-btn-record ${activeTab === "record" ? "active" : ""}`}
                        onClick={() => setActiveTab("record")}
                        id="voice-tab-btn"
                    >
                        <span className="tab-icon">🎙️</span>
                        Record
                    </button>
                </div>

                {/* ---- Tab Content: Reports ---- */}
                {activeTab === "reports" && (
                    <>
                        <div className="queue-header">
                            <h2>Incoming Reports</h2>
                            <span className="queue-count">{reports.length}</span>
                        </div>

                        {reportsLoading && (
                            <div className="loading-state">Loading reports…</div>
                        )}
                        {reportsError && (
                            <div className="error-state">
                                <p>⚠ {reportsError}</p>
                                <button className="btn btn-retry" onClick={loadReports}>
                                    Retry
                                </button>
                            </div>
                        )}

                        <div className="incident-queue">
                            {reports.map((report) => (
                                <ReportCard
                                    key={report.id}
                                    report={report}
                                    selected={report.id === selectedReportId}
                                    onClick={() => setSelectedReportId(report.id)}
                                />
                            ))}
                            {!reportsLoading && reports.length === 0 && (
                                <div className="empty-queue">
                                    <span>📭</span>
                                    <p>No incoming reports</p>
                                </div>
                            )}
                        </div>
                    </>
                )}

                {/* ---- Tab Content: Incidents ---- */}
                {activeTab === "incidents" && (
                    <>
                        <div className="queue-header">
                            <h2>Active Incidents</h2>
                            <span className="queue-count">{incidents.length}</span>
                        </div>

                        {incidentsLoading && (
                            <div className="loading-state">Loading incidents…</div>
                        )}
                        {incidentsError && (
                            <div className="error-state">
                                <p>⚠ {incidentsError}</p>
                                <button className="btn btn-retry" onClick={loadIncidents}>
                                    Retry
                                </button>
                            </div>
                        )}

                        <div className="incident-queue">
                            {incidents.map((inc) => (
                                <ActiveIncidentCard
                                    key={inc.id}
                                    incident={inc}
                                    selected={inc.id === selectedIncidentId}
                                    onClick={() => setSelectedIncidentId(inc.id)}
                                />
                            ))}
                            {!incidentsLoading && incidents.length === 0 && (
                                <div className="empty-queue">
                                    <span>🏷️</span>
                                    <p>No active incidents</p>
                                </div>
                            )}
                        </div>
                    </>
                )}

                {/* ---- Tab Content: Record ---- */}
                {activeTab === "record" && (
                    <div className="incident-queue">
                        <VoiceRecorder onResult={handleVoiceReport} />
                    </div>
                )}
            </aside>

            {/* ---- Main Content ---- */}
            <main className="main-content">
                {activeTab === "reports" && selectedReport ? (
                    <ReportDetail
                        report={selectedReport}
                        onCreateIncident={handleCreateIncident}
                        onDismiss={handleDismiss}
                        creating={creating}
                    />
                ) : activeTab === "incidents" && selectedIncident ? (
                    <ActiveIncidentDetail
                        incident={selectedIncident}
                        onUpdated={() => loadIncidents()}
                    />
                ) : activeTab === "record" ? (
                    <div className="empty-state">
                        <span className="empty-icon" style={{ opacity: 1, fontSize: "4rem" }}>🎙️</span>
                        <h2 style={{ color: "var(--text-primary)", fontSize: "1.4rem", marginBottom: "8px" }}>
                            Voice-to-Incident
                        </h2>
                        <p style={{ color: "var(--text-secondary)", maxWidth: "380px", textAlign: "center", lineHeight: 1.6 }}>
                            Record an incident report on the left. OpenAI Whisper will transcribe it and automatically classify it — then it appears in your Incoming queue ready for triage.
                        </p>
                    </div>
                ) : (
                    <div className="empty-state">
                        <span className="empty-icon">🛡️</span>
                        <h2>
                            {activeTab === "reports"
                                ? "Select a report"
                                : "Select an incident"}
                        </h2>
                        <p>
                            {activeTab === "reports"
                                ? "Choose an incoming report to triage"
                                : "Choose an active incident to manage"}
                        </p>
                    </div>
                )}
            </main>
        </div>
    );
}

export default App;
