import { useEffect, useState, useCallback } from "react";
import { IncidentCard, IncidentDetail } from "./components";
import { fetchIncidents } from "./api";
import type { Incident, SimilarCase } from "./types";
import { API_BASE } from "./config";

function App() {
    const [incidents, setIncidents] = useState<Incident[]>([]);
    const [selectedId, setSelectedId] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [similarCases, setSimilarCases] = useState<SimilarCase[]>([]);

    const load = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await fetchIncidents();
            setIncidents(data);
            if (data.length > 0 && !selectedId) {
                setSelectedId(data[0].id);
            }
        } catch (e: any) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        load();
    }, [load]);

    // When selected incident changes, fetch its similar cases
    useEffect(() => {
        if (!selectedId) {
            setSimilarCases([]);
            return;
        }
        const selected = incidents.find((i) => i.id === selectedId);
        if (!selected?.structured) {
            setSimilarCases([]);
            return;
        }

        // Fetch similar cases by posting to a search or just computing client-side
        // For now, use the recommended data if available or fetch from incident detail
        const fetchSimilar = async () => {
            try {
                const res = await fetch(`${API_BASE}/incidents/${selectedId}`);
                if (res.ok) {
                    const detail = await res.json();
                    // Similar cases are computed at creation time—stored in incident context
                    // We'll derive them from the recommended data and historical matching
                    // For the demo, calculate from the full incidents list
                    if (detail.structured) {
                        const res2 = await fetch(`${API_BASE}/incidents`);
                        if (res2.ok) {
                            const all: Incident[] = await res2.json();
                            // Filter to those with outcomes (historical), exclude current
                            const historical = all.filter(
                                (i) => i.outcome !== null && i.id !== selectedId
                            );
                            // Simple client-side similarity for display
                            const cases: SimilarCase[] = historical
                                .map((h) => ({
                                    incident_id: h.id,
                                    incident_type: h.structured?.incident_type ?? "other",
                                    similarity_score: computeSimilarity(detail.structured, h.structured),
                                    outcome: h.outcome,
                                    response_taken: h.response_taken,
                                    report_text_preview: h.report_text.slice(0, 120),
                                }))
                                .sort((a, b) => b.similarity_score - a.similarity_score)
                                .slice(0, 5);
                            setSimilarCases(cases);
                        }
                    }
                }
            } catch {
                setSimilarCases([]);
            }
        };
        fetchSimilar();
    }, [selectedId, incidents]);

    const selected = incidents.find((i) => i.id === selectedId) ?? null;

    // Open incidents first, then by triage
    const openIncidents = incidents.filter((i) => i.status === "open");
    const closedIncidents = incidents.filter((i) => i.status !== "open");

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

                <div className="queue-header">
                    <h2>Active Incidents</h2>
                    <span className="queue-count">{openIncidents.length}</span>
                </div>

                {loading && <div className="loading-state">Loading incidents…</div>}
                {error && (
                    <div className="error-state">
                        <p>⚠ {error}</p>
                        <button className="btn btn-retry" onClick={load}>
                            Retry
                        </button>
                    </div>
                )}

                <div className="incident-queue">
                    {openIncidents.map((inc) => (
                        <IncidentCard
                            key={inc.id}
                            incident={inc}
                            selected={inc.id === selectedId}
                            onClick={() => setSelectedId(inc.id)}
                        />
                    ))}

                    {closedIncidents.length > 0 && (
                        <>
                            <div className="queue-divider">
                                <span>Closed ({closedIncidents.length})</span>
                            </div>
                            {closedIncidents.slice(0, 10).map((inc) => (
                                <IncidentCard
                                    key={inc.id}
                                    incident={inc}
                                    selected={inc.id === selectedId}
                                    onClick={() => setSelectedId(inc.id)}
                                />
                            ))}
                        </>
                    )}
                </div>
            </aside>

            {/* ---- Main Content ---- */}
            <main className="main-content">
                {selected ? (
                    <IncidentDetail
                        incident={selected}
                        similarCases={similarCases}
                        onStatusUpdated={load}
                    />
                ) : (
                    <div className="empty-state">
                        <span className="empty-icon">🛡️</span>
                        <h2>Select an incident</h2>
                        <p>Choose an incident from the queue to view details</p>
                    </div>
                )}
            </main>
        </div>
    );
}

/** Simple client-side similarity for display purposes. */
function computeSimilarity(a: any, b: any): number {
    if (!a || !b) return 0;
    const ra = a.risk_factors ?? {};
    const rb = b.risk_factors ?? {};
    const ea = a.key_entities ?? {};
    const eb = b.key_entities ?? {};

    const vec_a = [
        (ra.aggression_level ?? 0) / 3,
        (ra.crowd_level ?? 0) / 3,
        ea.weapon_mentioned ? 1 : 0,
        ea.injuries_present ? 1 : 0,
        ea.smoke_fire_present ? 1 : 0,
        ra.active_threat ? 1 : 0,
    ];
    const vec_b = [
        (rb.aggression_level ?? 0) / 3,
        (rb.crowd_level ?? 0) / 3,
        eb.weapon_mentioned ? 1 : 0,
        eb.injuries_present ? 1 : 0,
        eb.smoke_fire_present ? 1 : 0,
        rb.active_threat ? 1 : 0,
    ];
    const weights = [1.5, 1.0, 2.0, 1.5, 1.0, 2.0];
    let dist = 0;
    for (let i = 0; i < 6; i++) {
        dist += weights[i] * (vec_a[i] - vec_b[i]) ** 2;
    }
    return 1 / (1 + Math.sqrt(dist));
}

export default App;
