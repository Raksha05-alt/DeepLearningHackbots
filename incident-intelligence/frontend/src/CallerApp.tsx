/**
 * CallerApp — Standalone incident reporting page.
 *
 * This is shown at /caller.html and is intended for callers/citizens.
 * After recording, the transcription is classified and POSTed to the
 * dashboard's backend so it appears in the Incoming Reports queue
 * (or merges into an existing active incident).
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

            // Prefer formats that Whisper handles best
            const mimeType = MediaRecorder.isTypeSupported("audio/mp4")
                ? "audio/mp4"
                : MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
                    ? "audio/webm;codecs=opus"
                    : "audio/webm";

            const mediaRecorder = new MediaRecorder(stream, { mimeType });
            chunksRef.current = [];

            mediaRecorder.ondataavailable = (e) => {
                if (e.data.size > 0) chunksRef.current.push(e.data);
            };

            mediaRecorder.onstop = async () => {
                stream.getTracks().forEach((t) => t.stop());
                const actualMime = mediaRecorder.mimeType || mimeType;
                const blob = new Blob(chunksRef.current, { type: actualMime });
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
                    const data = await res.json();
                    setSubmitted(result.report);

                    // If merged into existing incident, note it
                    if (data.status === "merged") {
                        setLastText(
                            `${result.transcription}\n\n(Merged into existing incident)`
                        );
                    }
                } catch (err: any) {
                    setError(err.message ?? "Something went wrong. Please try again.");
                } finally {
                    setState("idle");
                }
            };

            mediaRecorder.start(1000); // 1-second chunks
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
        <div className="caller-app-light">
            <main className="caller-main-light">
                {/* Success state */}
                {submitted ? (
                    <div className="caller-success-light">
                        <div className="caller-success-check">✅</div>
                        <h2>Report Submitted</h2>
                        <p className="caller-success-desc">
                            Your report has been received and is being processed by our dispatch team.
                        </p>

                        <div className="caller-summary-light">
                            <div className="caller-row">
                                <span className="caller-row-label">Type</span>
                                <span className="caller-row-value">{submitted.type?.replace(/_/g, " ")}</span>
                            </div>
                            <div className="caller-row">
                                <span className="caller-row-label">Location</span>
                                <span className="caller-row-value">{submitted.location}</span>
                            </div>
                            <div className="caller-row">
                                <span className="caller-row-label">Priority</span>
                                <span className={`caller-pri caller-pri-${submitted.risk_level}`}>
                                    {submitted.triage?.priority ?? "—"}
                                </span>
                            </div>
                            {lastText && (
                                <div className="caller-row caller-row-transcript">
                                    <span className="caller-row-label">Transcript</span>
                                    <span className="caller-row-value">&ldquo;{lastText}&rdquo;</span>
                                </div>
                            )}
                        </div>

                        <button className="caller-btn-light" onClick={handleNewReport}>
                            Report Another Incident
                        </button>
                    </div>
                ) : (
                    <>
                        {/* Prompt */}
                        <h1 className="caller-heading">
                            How can we help? Please <span className="caller-accent">tap the microphone</span> below and describe the situation.
                        </h1>

                        <p className="caller-categories">
                            <span>📍 Where</span>
                            <span className="caller-dot">•</span>
                            <span>🔥 What</span>
                            <span className="caller-dot">•</span>
                            <span>🚑 Injuries</span>
                        </p>

                        {/* Mic button */}
                        <div className="caller-mic-wrapper">
                            <button
                                className={`caller-mic-light ${state}`}
                                onClick={handleClick}
                                disabled={state === "processing"}
                            >
                                {state === "processing" ? (
                                    <span className="caller-spinner" />
                                ) : state === "recording" ? (
                                    <svg viewBox="0 0 24 24" fill="currentColor" className="caller-mic-svg">
                                        <rect x="6" y="6" width="12" height="12" rx="2" />
                                    </svg>
                                ) : (
                                    <svg viewBox="0 0 24 24" fill="currentColor" className="caller-mic-svg">
                                        <path d="M12 1a4 4 0 0 1 4 4v7a4 4 0 0 1-8 0V5a4 4 0 0 1 4-4zm0 2a2 2 0 0 0-2 2v7a2 2 0 1 0 4 0V5a2 2 0 0 0-2-2zm-7 9a7 7 0 0 0 14 0h2a9 9 0 0 1-8 8.94V23h-2v-2.06A9 9 0 0 1 3 12h2z" />
                                    </svg>
                                )}
                            </button>
                        </div>

                        <p className="caller-tap-label">
                            {state === "idle" && "Tap to start speaking"}
                            {state === "recording" && (
                                <span className="caller-rec-label">
                                    <span className="caller-rec-dot" /> Recording… tap to stop
                                </span>
                            )}
                            {state === "processing" && "Analysing your report…"}
                        </p>

                        {/* Error */}
                        {error && (
                            <div className="caller-error-light">
                                <strong>Oops!</strong> {error}
                            </div>
                        )}

                        {/* Helpful Tips */}
                        <div className="caller-tips-light">
                            <p className="caller-tips-heading">💡 <strong>Helpful Tips</strong></p>
                            <ul>
                                <li>
                                    <span className="caller-check">✓</span>
                                    Be specific about your location (block number, street, nearby landmarks).
                                </li>
                                <li>
                                    <span className="caller-check">✓</span>
                                    Describe clearly what you see (e.g., &ldquo;I see smoke from the 4th floor&rdquo;).
                                </li>
                                <li>
                                    <span className="caller-check">✓</span>
                                    Mention if anyone needs medical assistance immediately.
                                </li>
                            </ul>
                        </div>
                    </>
                )}
            </main>
        </div>
    );
}
