/** IntelResponse – Shared TypeScript types. */

export interface KeyEntities {
    location: string | null;
    people_count: number | null;
    injuries_present: boolean | null;
    weapon_mentioned: boolean | null;
    smoke_fire_present: boolean | null;
}

export interface RiskFactors {
    aggression_level: number;
    crowd_level: number;
    intoxication_suspected: boolean;
    active_threat: boolean;
}

export interface Structured {
    incident_type: string;
    key_entities: KeyEntities;
    risk_factors: RiskFactors;
    confidence: number;
    missing_info: string[];
}

export interface Triage {
    score: number;
    priority: string;
    reasons: string[];
}

export interface SimilarCase {
    incident_id: string;
    incident_type: string;
    similarity_score: number;
    outcome: string | null;
    response_taken: string | null;
    report_text_preview: string;
}

export interface Recommended {
    action: string;
    follow_up_questions: string[];
    checklist: string[];
    rationale: string;
}

export interface Incident {
    id: string;
    created_at: string;
    source: string;
    report_text: string;
    location_hint: string | null;
    structured: Structured | null;
    triage: Triage | null;
    recommended: Recommended | null;
    outcome: string | null;
    response_taken: string | null;
    status: string;
}
