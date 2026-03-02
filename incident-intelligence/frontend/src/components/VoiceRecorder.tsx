/**
 * VoiceRecorder – mic button component for IntelResponse.
 *
 * Records audio via the browser MediaRecorder API, POSTs the blob to
 * POST /api/transcribe, and returns the result to the parent.
 *
 * States:  idle → recording (pulsing) → processing (spinner) → idle
 */

import { useRef, useState } from "react";
import { transcribeAudio } from "../api";
import type { IncomingReport } from "../types";

type RecordState = "idle" | "recording" | "processing";

interface Props {
    onResult: (report: IncomingReport) => void;
}

export default function VoiceRecorder({ onResult }: Props) {
    const [state, setState] = useState<RecordState>("idle");
    const [error, setError] = useState<string | null>(null);
    const [lastText, setLastText] = useState<string | null>(null);

    const mediaRef = useRef<MediaRecorder | null>(null);
    const chunksRef = useRef<Blob[]>([]);

    async function startRecording() {
        setError(null);
        setLastText(null);
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const mediaRecorder = new MediaRecorder(stream);
            chunksRef.current = [];

            mediaRecorder.ondataavailable = (e) => {
                if (e.data.size > 0) chunksRef.current.push(e.data);
            };

            mediaRecorder.onstop = async () => {
                // Stop all tracks
                stream.getTracks().forEach((t) => t.stop());

                const blob = new Blob(chunksRef.current, { type: "audio/webm" });
                setState("processing");
                try {
                    const result = await transcribeAudio(blob, "en");
                    setLastText(result.transcription);
                    onResult(result.report);
                } catch (err: any) {
                    setError(err.message ?? "Transcription failed. Please try again.");
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

    return (
        <div className="voice-recorder">
            {/* Header */}
            <div className="vr-header">
                <h2 className="vr-title">🎙️ Voice Report</h2>
                <p className="vr-subtitle">
                    Record an incident report and it will be automatically
                    transcribed, classified, and added to the queue.
                </p>
            </div>

            {/* Big mic button */}
            <div className="vr-button-area">
                <button
                    id="voice-record-btn"
                    className={`vr-mic-btn ${state}`}
                    onClick={handleClick}
                    disabled={state === "processing"}
                    title={
                        state === "idle"
                            ? "Start recording"
                            : state === "recording"
                                ? "Stop recording"
                                : "Processing…"
                    }
                >
                    {state === "processing" ? (
                        <span className="vr-spinner" />
                    ) : state === "recording" ? (
                        <svg viewBox="0 0 24 24" fill="currentColor" className="vr-icon">
                            <rect x="6" y="6" width="12" height="12" rx="2" />
                        </svg>
                    ) : (
                        <svg viewBox="0 0 24 24" fill="currentColor" className="vr-icon">
                            <path d="M12 1a4 4 0 0 1 4 4v7a4 4 0 0 1-8 0V5a4 4 0 0 1 4-4zm0 2a2 2 0 0 0-2 2v7a2 2 0 1 0 4 0V5a2 2 0 0 0-2-2zm-7 9a7 7 0 0 0 14 0h2a9 9 0 0 1-8 8.94V23h-2v-2.06A9 9 0 0 1 3 12h2z" />
                        </svg>
                    )}
                </button>

                <p className="vr-status-label">
                    {state === "idle" && "Tap to start recording"}
                    {state === "recording" && (
                        <span className="vr-recording-label">
                            <span className="vr-dot" /> Recording… tap to stop
                        </span>
                    )}
                    {state === "processing" && "Transcribing with Whisper…"}
                </p>
            </div>

            {/* Error */}
            {error && (
                <div className="vr-error">
                    <span>⚠</span> {error}
                </div>
            )}

            {/* Last transcription preview */}
            {lastText && !error && (
                <div className="vr-result">
                    <p className="vr-result-label">✅ Transcription added to queue:</p>
                    <p className="vr-result-text">"{lastText}"</p>
                </div>
            )}

            {/* Tips */}
            <div className="vr-tips">
                <p className="vr-tips-title">Tips for best results</p>
                <ul>
                    <li>Speak clearly and describe the incident type, location, and severity</li>
                    <li>Example: <em>"There is a fire at Orchard MRT, smoke visible from the platform, people evacuating"</em></li>
                    <li>Keep recordings under 2 minutes for fastest processing</li>
                </ul>
            </div>
        </div>
    );
}
