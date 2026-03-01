/** IntelResponse – API fetch helpers. */

import { API_BASE } from "./config";
import type { Incident } from "./types";

export async function fetchIncidents(): Promise<Incident[]> {
    const res = await fetch(`${API_BASE}/incidents`);
    if (!res.ok) throw new Error(`Failed to fetch incidents: ${res.status}`);
    return res.json();
}

export async function fetchIncident(id: string): Promise<Incident> {
    const res = await fetch(`${API_BASE}/incidents/${id}`);
    if (!res.ok) throw new Error(`Failed to fetch incident: ${res.status}`);
    return res.json();
}

export async function updateIncidentStatus(
    id: string,
    status: string
): Promise<Incident> {
    const res = await fetch(`${API_BASE}/incidents/${id}/status`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status }),
    });
    if (!res.ok) throw new Error(`Failed to update status: ${res.status}`);
    return res.json();
}

export async function fetchStats(): Promise<{
    total_incidents: number;
    by_outcome: Record<string, number>;
    by_incident_type: Record<string, number>;
}> {
    const res = await fetch(`${API_BASE}/stats`);
    if (!res.ok) throw new Error(`Failed to fetch stats: ${res.status}`);
    return res.json();
}
