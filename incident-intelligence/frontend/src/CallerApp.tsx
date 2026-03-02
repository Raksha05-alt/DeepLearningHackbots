/**
 * CallerApp — Standalone incident reporting page.
 *
 * This is shown at /caller.html and is intended for callers/citizens.
 * After recording, the transcription is classified and POSTed to the
 * dashboard's backend so it appears in the Incoming Reports queue.
 */

import { useRef, useState } from "react";
import { transcribeAudio } from "./api";
import { API_BASE } from "./config";
import type { IncomingReport } from "./types";

type RecordState = "idle" | "recording" | "processing";

export default function CallerApp() {
    const [state, setState] = useState<RecordState>("idle");
    const [error, setError] = useState<string | null>(null);
    const [submitted, setSubmitted] = useState<IncomingReport | null>(null);
    const [lastText, setLastText] = useState<string | null>(null);

    const mediaRef = useRef<MediaRecorder | null>(null);
    const chunksRef = useRef<Blob[]>([]);

    async function startRecording() {
        setError(null);
        setLastText(null);
        setSubmitted(null);
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const mediaRecorder = new MediaRecorder(stream);
            chunksRef.current = [];

            mediaRecorder.ondataavailable = (e) => {
                if (e.data.size > 0) chunksRef.current.push(e.data);
            };

            mediaRecorder.onstop = async () => {
                stream.getTracks().forEach((t) => t.stop());
                const blob = new Blob(chunksRef.current, { type: "audio/webm" });
                setState("processing");
                try {
                    const result = await transcribeAudio(blob, "en");
                    setLastText(result.transcription);

                    // POST the classified report to the dashboard backend
                    const res = await fetch(`${API_BASE}/api/reports`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(result.report),
                    });
                    if (!res.ok) throw new Error("Failed to submit report");
                    setSubmitted(result.report);
                } catch (err: any) {
                    setError(err.message ?? "Something went wrong. Please try again.");
                } finally {
                    setState("idle");
                }
            };

            mediaRecorder.start();
            mediaRef.current = mediaRecorder;
            setState("recording");
        } catch (err: any) {
            setError(
                err.name === "NotAllowedError"
                    ? "Microphone access denied. Please allow microphone access and try again."
                    : `Could not start recording: ${err.message}`
            );
            setState("idle");
        }
    }

    function stopRecording() {
        mediaRef.current?.stop();
    }

    function handleClick() {
        if (state === "idle") startRecording();
        else if (state === "recording") stopRecording();
    }

    function handleNewReport() {
        setSubmitted(null);
        setLastText(null);
        setError(null);
    }

    return (
        <div className="caller-app">
            {/* Header */}
            <header className="caller-header">
                <div className="caller-logo">
                    <span className="caller-logo-icon">📞</span>
                    <div>
                        <h1>Report an Incident</h1>
                        <p className="caller-subtitle">IntelResponse Public Safety Hotline</p>
                    </div>
                </div>
            </header>

            <main className="caller-main">
                {/* Success state */}
                {submitted ? (
                    <div className="caller-success">
                        <div className="caller-success-icon">✅</div>
                        <h2>Report Submitted</h2>
                        <p className="caller-success-text">
                            Your report has been received and is being processed by our dispatch team.
                        </p>

                        <div className="caller-summary">
                            <div className="caller-summary-row">
                                <span className="caller-summary-label">Type</span>
                                <span className="caller-summary-value">{submitted.type?.replace(/_/g, " ")}</span>
                            </div>
                            <div className="caller-summary-row">
                                <span className="caller-summary-label">Location</span>
                                <span className="caller-summary-value">{submitted.location}</span>
                            </div>
                            <div className="caller-summary-row">
                                <span className="caller-summary-label">Priority</span>
                                <span className={`caller-priority caller-priority-${submitted.risk_level}`}>
                                    {submitted.triage?.priority ?? "—"}
                                </span>
                            </div>
                            {lastText && (
                                <div className="caller-summary-row caller-summary-transcript">
                                    <span className="caller-summary-label">Transcript</span>
                                    <span className="caller-summary-value">"{lastText}"</span>
                                </div>
                            )}
                        </div>

                        <button className="caller-btn caller-btn-new" onClick={handleNewReport}>
                            Report Another Incident
                        </button>
                    </div>
                ) : (
                    <>
                        {/* Recording area */}
                        <div className="caller-record-area">
                            <p className="caller-instruction">
                                Tap the microphone and describe the incident.<br />
                                Include the <strong>type</strong>, <strong>location</strong>, and <strong>severity</strong>.
                            </p>

                            <button
                                className={`caller-mic-btn ${state}`}
                                onClick={handleClick}
                                disabled={state === "processing"}
                            >
                                {state === "processing" ? (
                                    <span className="vr-spinner" />
                                ) : state === "recording" ? (
                                    <svg viewBox="0 0 24 24" fill="currentColor" className="caller-mic-icon">
                                        <rect x="6" y="6" width="12" height="12" rx="2" />
                                    </svg>
                                ) : (
                                    <svg viewBox="0 0 24 24" fill="currentColor" className="caller-mic-icon">
                                        <path d="M12 1a4 4 0 0 1 4 4v7a4 4 0 0 1-8 0V5a4 4 0 0 1 4-4zm0 2a2 2 0 0 0-2 2v7a2 2 0 1 0 4 0V5a2 2 0 0 0-2-2zm-7 9a7 7 0 0 0 14 0h2a9 9 0 0 1-8 8.94V23h-2v-2.06A9 9 0 0 1 3 12h2z" />
                                    </svg>
                                )}
                            </button>

                            <p className="caller-status-label">
                                {state === "idle" && "Tap to start recording"}
                                {state === "recording" && (
                                    <span className="caller-recording-label">
                                        <span className="vr-dot" /> Recording… tap to stop
                                    </span>
                                )}
                                {state === "processing" && "Transcribing & classifying…"}
                            </p>
                        </div>

                        {/* Error */}
                        {error && (
                            <div className="caller-error">
                                <span>⚠</span> {error}
                            </div>
                        )}

                        {/* Tips */}
                        <div className="caller-tips">
                            <p className="caller-tips-title">Tips for best results</p>
                            <ul>
                                <li>Speak clearly and include the incident type, location, and severity</li>
                                <li>Example: <em>"There is a fire at Block 45, Toa Payoh Lorong 5, smoke visible from 4th floor"</em></li>
                                <li>Keep recordings under 2 minutes for fastest processing</li>
                            </ul>
                        </div>
                    </>
                )}
            </main>

            <footer className="caller-footer">
                <p>For life-threatening emergencies, call <strong>995</strong> (SCDF) or <strong>999</strong> (SPF)</p>
            </footer>
        </div>
    );
}
