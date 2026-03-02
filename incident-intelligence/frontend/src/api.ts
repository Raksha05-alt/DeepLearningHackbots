/** IntelResponse – API fetch helpers (dispatch workflow). */

import { API_BASE } from "./config";
import type { IncomingReport, ActiveIncident } from "./types";

// ---- Incoming Reports ----

export async function fetchReports(): Promise<IncomingReport[]> {
    const res = await fetch(`${API_BASE}/api/reports`);
    if (!res.ok) throw new Error(`Failed to fetch reports: ${res.status}`);
    return res.json();
}

// ---- Active Incidents ----

export async function fetchActiveIncidents(): Promise<ActiveIncident[]> {
    const res = await fetch(`${API_BASE}/api/incidents`);
    if (!res.ok) throw new Error(`Failed to fetch incidents: ${res.status}`);
    return res.json();
}

// ---- Promote report → incident ----

export async function createFromReport(reportId: string): Promise<ActiveIncident> {
    const res = await fetch(`${API_BASE}/api/incidents/create_from_report`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ report_id: reportId }),
    });
    if (!res.ok) throw new Error(`Failed to create incident: ${res.status}`);
    return res.json();
}

// ---- Timeline ----

export async function addTimelineEntry(
    incidentId: string,
    type: string,
    description: string
): Promise<ActiveIncident> {
    const res = await fetch(`${API_BASE}/api/incidents/${incidentId}/timeline`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type, description }),
    });
    if (!res.ok) throw new Error(`Failed to add timeline entry: ${res.status}`);
    return res.json();
}

// ---- Update status ----

export async function updateActiveStatus(
    incidentId: string,
    status: string
): Promise<ActiveIncident> {
    const res = await fetch(`${API_BASE}/api/incidents/${incidentId}/status`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status }),
    });
    if (!res.ok) throw new Error(`Failed to update status: ${res.status}`);
    return res.json();
}

// ---- Dismiss report (remove from list client-side) ----
// No backend endpoint needed — just filter locally
