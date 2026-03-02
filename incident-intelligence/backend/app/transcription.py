"""
IntelResponse – OpenAI Whisper Speech-to-Text module.

Provides:
  - transcribe_audio(file_path, language)      → dict
  - transcribe_audio_bytes(bytes, name, lang)  → dict

Both functions return:
  {
    "text":     str,   # transcribed text
    "language": str,   # ISO language code used
  }

All OpenAI-specific errors are mapped to a domain-level TranscriptionError
so callers (e.g. the FastAPI endpoint) can handle them uniformly.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load .env from the directory this file (or its parent package) lives in.
# Walk up until we find a .env file or reach the filesystem root.
_HERE = Path(__file__).resolve().parent
for _candidate in [_HERE, _HERE.parent, _HERE.parent.parent]:
    _dotenv_path = _candidate / ".env"
    if _dotenv_path.exists():
        load_dotenv(_dotenv_path)
        break

try:
    import openai
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "The 'openai' package is required for transcription. "
        "Run: pip install openai>=1.0.0"
    ) from exc


# ---------------------------------------------------------------------------
# Custom exception
# ---------------------------------------------------------------------------


class TranscriptionError(Exception):
    """Raised when audio transcription fails for any reason."""

    def __init__(self, message: str, status_code: int = 500) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


# ---------------------------------------------------------------------------
# Internal – build a configured OpenAI client
# ---------------------------------------------------------------------------


def _get_client() -> "openai.OpenAI":
    """Return a configured OpenAI client, raising TranscriptionError if the
    API key is missing."""
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise TranscriptionError(
            "OPENAI_API_KEY is not set. Add it to backend/.env or your "
            "environment variables.",
            status_code=401,
        )
    return openai.OpenAI(api_key=api_key)


# ---------------------------------------------------------------------------
# Supported audio MIME types (Whisper API accepts these)
# ---------------------------------------------------------------------------

_SUPPORTED_EXTENSIONS = {
    ".mp3", ".mp4", ".mpeg", ".mpga", ".m4a",
    ".wav", ".webm", ".ogg", ".flac",
}


def _validate_extension(filename: str) -> None:
    ext = Path(filename).suffix.lower()
    if ext not in _SUPPORTED_EXTENSIONS:
        raise TranscriptionError(
            f"Unsupported audio format '{ext}'. "
            f"Supported formats: {', '.join(sorted(_SUPPORTED_EXTENSIONS))}.",
            status_code=400,
        )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def transcribe_audio(
    file_path: str | Path,
    language: Optional[str] = "en",
) -> dict:
    """Transcribe an audio file at *file_path* using OpenAI Whisper.

    Parameters
    ----------
    file_path:
        Absolute or relative path to the audio file. Must be one of the
        formats accepted by the Whisper API (mp3, wav, mp4, m4a, webm, etc.).
    language:
        ISO-639-1 language code (e.g. ``"en"``, ``"zh"``, ``"ms"``).
        Pass ``None`` to let Whisper auto-detect the language.

    Returns
    -------
    dict
        ``{"text": str, "language": str}``

    Raises
    ------
    TranscriptionError
        On any failure (bad key, network error, empty audio, bad format, …).
    FileNotFoundError
        If *file_path* does not exist on disk.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {file_path}")

    _validate_extension(path.name)
    client = _get_client()

    try:
        with open(path, "rb") as audio_file:
            kwargs: dict = {
                "model": "whisper-1",
                "file": audio_file,
                "response_format": "text",
            }
            if language:
                kwargs["language"] = language

            raw_text: str = client.audio.transcriptions.create(**kwargs)  # type: ignore[assignment]

    except openai.AuthenticationError as exc:
        raise TranscriptionError(
            "Invalid or missing OpenAI API key. Check your OPENAI_API_KEY.",
            status_code=401,
        ) from exc

    except openai.BadRequestError as exc:
        raise TranscriptionError(
            "Audio could not be processed – check that the file is not "
            "corrupted, silent, or in an unsupported format. "
            f"OpenAI detail: {exc}",
            status_code=400,
        ) from exc

    except openai.RateLimitError as exc:
        raise TranscriptionError(
            "OpenAI rate limit exceeded – please wait a moment and retry.",
            status_code=429,
        ) from exc

    except openai.APIConnectionError as exc:
        raise TranscriptionError(
            "Could not reach the OpenAI API. Check your internet connection.",
            status_code=503,
        ) from exc

    except openai.APIStatusError as exc:
        raise TranscriptionError(
            f"OpenAI API returned an unexpected error (HTTP {exc.status_code}): {exc.message}",
            status_code=502,
        ) from exc

    # Guard against empty / whitespace-only transcriptions
    text = raw_text.strip() if isinstance(raw_text, str) else ""
    if not text:
        raise TranscriptionError(
            "Transcription returned empty text. The audio may be silent, "
            "too short, or inaudible.",
            status_code=400,
        )

    return {
        "text": text,
        "language": language or "auto",
    }


def transcribe_audio_bytes(
    audio_bytes: bytes,
    filename: str = "upload.wav",
    language: Optional[str] = "en",
) -> dict:
    """Transcribe raw audio *bytes* (e.g. from an HTTP upload).

    Writes the bytes to a temporary file, delegates to :func:`transcribe_audio`,
    then cleans up the temp file.

    Parameters
    ----------
    audio_bytes:
        Raw binary content of the audio file.
    filename:
        Original filename (used to determine the extension for format
        validation and for the temp file suffix).
    language:
        ISO-639-1 language code.  Pass ``None`` for auto-detection.

    Returns
    -------
    dict
        ``{"text": str, "language": str}``
    """
    if not audio_bytes:
        raise TranscriptionError(
            "No audio data received – the uploaded file is empty.",
            status_code=400,
        )

    ext = Path(filename).suffix.lower() or ".wav"
    _validate_extension(filename)

    # Write to a named temp file so the OpenAI client can open it
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    print(f"[DEBUG] Received audio file '{filename}' with size {len(audio_bytes)} bytes", flush=True)

    try:
        import shutil
        debug_path = f"/tmp/debug_audio{ext}"
        shutil.copy2(tmp_path, debug_path)
        print(f"[DEBUG] Saved debug audio copy to {debug_path}", flush=True)
    except Exception as e:
        print(f"[DEBUG] Failed to save debug audio copy: {e}", flush=True)

    try:
        return transcribe_audio(tmp_path, language=language)
    finally:
        # Always clean up the temp file
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
