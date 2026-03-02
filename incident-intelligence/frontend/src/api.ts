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

// ---- Speech-to-Text transcription → IncomingReport ----

export interface TranscribeResult {
    transcription: string;
    language: string;
    report: IncomingReport; // synthetic report built from the transcription
}

export async function transcribeAudio(
    audioBlob: Blob,
    language = "en"
): Promise<TranscribeResult> {
    const form = new FormData();
    // Use the correct extension based on the blob type we captured
    const ext = audioBlob.type.includes("mp4") ? "mp4" : "webm";
    form.append("file", audioBlob, `recording.${ext}`);

    const res = await fetch(`${API_BASE}/api/transcribe?language=${language}`, {
        method: "POST",
        body: form,
    });

    if (!res.ok) {
        const detail = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(detail.detail ?? `Transcription failed (${res.status})`);
    }

    const data = await res.json(); // { transcription, language, extracted_features }
    const ef = data.extracted_features;

    // Derive risk level from extracted features
    const riskLevel = (() => {
        const incidentType: string = ef?.incident_type ?? "other";
        const aggression: number = ef?.risk_factors?.aggression_level ?? 0;
        const crowdLevel: number = ef?.risk_factors?.crowd_level ?? 0;
        const activeThreat: boolean = ef?.risk_factors?.active_threat ?? false;
        const intoxicated: boolean = ef?.risk_factors?.intoxication_suspected ?? false;
        const weapon: boolean = ef?.key_entities?.weapon_mentioned ?? false;
        const injuries: boolean = ef?.key_entities?.injuries_present ?? false;
        const smokeFire: boolean = ef?.key_entities?.smoke_fire_present ?? false;

        // --- CRITICAL: immediate life-threatening ---
        if (
            activeThreat ||
            injuries ||
            (weapon && aggression >= 1) ||
            (smokeFire && injuries) ||
            (incidentType === "violence_conflict" && (weapon || aggression >= 2)) ||
            (incidentType === "fire_smoke" && injuries)
        ) return "critical";

        // --- HIGH: serious but not immediately life-threatening ---
        if (
            weapon ||
            aggression >= 2 ||
            smokeFire ||                         // any fire/smoke is at least HIGH
            incidentType === "fire_smoke" ||
            incidentType === "violence_conflict" ||
            (incidentType === "crowd_risk" && crowdLevel >= 2) ||
            (incidentType === "medical" && aggression >= 1)
        ) return "high";

        // --- MEDIUM ---
        if (
            aggression >= 1 ||
            intoxicated ||
            incidentType === "suspicious_person" ||
            incidentType === "medical" ||
            incidentType === "crowd_risk" ||
            crowdLevel >= 1
        ) return "medium";

        return "low";
    })();

    // Score and priority — give wider separation between levels
    const scoreMap: Record<string, number> = { critical: 92, high: 70, medium: 45, low: 18 };
    const priorityMap: Record<string, string> = { critical: "P0", high: "P1", medium: "P2", low: "P3" };

    // Build a synthetic IncomingReport from the transcription response
    const report: IncomingReport = {
        id: `voice-${Date.now()}`,
        text: data.transcription,
        location: ef?.key_entities?.location ?? "Unknown location",
        type: ef?.incident_type ?? "other",
        risk_level: riskLevel,
        confidence: ef?.confidence ?? 0.5,
        source: "voice",
        time: new Date().toISOString(),
        extracted_features: ef ?? null,
        triage: {
            score: scoreMap[riskLevel] ?? 40,
            priority: priorityMap[riskLevel] ?? "P2",
            reasons: ef?.missing_info?.length
                ? ["voice recording", ...ef.missing_info.slice(0, 2)]
                : ["voice recording"],
        },
        recommended: null,
    };

    return { transcription: data.transcription, language: data.language, report };
}
