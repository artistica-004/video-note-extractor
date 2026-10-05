"""
transcriber.py - Dual-mode transcript provider for Video Note Extractor.

LOCAL mode       -> yt-dlp downloads the audio, Groq Whisper transcribes it.
HUGGINGFACE mode -> the user pastes the YouTube transcript; we parse it here.

Both modes return the SAME shape that notes_generator.process_transcription expects:
    {"full_text": str, "segments": [{"start": float, "end": float, "text": str}, ...]}
"""

import os
import re
import glob
import socket
import tempfile

from dotenv import load_dotenv

load_dotenv()

GROQ_WHISPER_MODEL = "whisper-large-v3-turbo"
MAX_AUDIO_BYTES = 25 * 1024 * 1024  # Groq free-tier upload limit (25 MB)


# --------------------------------------------------------------------------- #
# Environment detection
# --------------------------------------------------------------------------- #
def youtube_reachable(timeout: float = 3.0) -> bool:
    """Quick TCP check - can this machine open a connection to youtube.com:443?"""
    try:
        with socket.create_connection(("www.youtube.com", 443), timeout=timeout):
            return True
    except OSError:
        return False


def detect_mode() -> str:
    """
    Returns "local" or "huggingface".

    Priority:
      1. APP_MODE env var ("local" / "huggingface") - manual override.
      2. SPACE_ID env var - Hugging Face sets this automatically in every Space.
      3. Fallback: if youtube.com is unreachable, use paste mode.
    """
    override = os.getenv("APP_MODE", "").strip().lower()
    if override in ("local", "huggingface"):
        return override

    if os.getenv("SPACE_ID"):
        return "huggingface"

    return "local" if youtube_reachable() else "huggingface"


# --------------------------------------------------------------------------- #
# Shared helpers
# --------------------------------------------------------------------------- #
def get_video_id(youtube_url: str) -> str:
    """Extract the 11-char video ID from watch / youtu.be / embed / shorts / live URLs."""
    patterns = [
        r"(?:v=)([0-9A-Za-z_-]{11})",
        r"(?:youtu\.be/)([0-9A-Za-z_-]{11})",
        r"(?:embed/|shorts/|live/)([0-9A-Za-z_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, youtube_url or "")
        if match:
            return match.group(1)
    raise ValueError("Invalid YouTube URL! Please check the link and try again.")


def _build_result(segments: list) -> dict:
    segments = [s for s in segments if s.get("text", "").strip()]
    full_text = " ".join(s["text"].strip() for s in segments)
    return {"full_text": full_text, "segments": segments}


# --------------------------------------------------------------------------- #
# LOCAL mode: yt-dlp + Groq Whisper
# --------------------------------------------------------------------------- #
def download_audio(youtube_url: str, out_dir: str) -> str:
    """Download the smallest usable audio stream. No ffmpeg required."""
    try:
        import yt_dlp
    except ImportError as e:
        raise RuntimeError(
            "yt-dlp is not installed. Run: pip install -r requirements.txt"
        ) from e

    ydl_opts = {
        # Prefer an audio-only stream under 25 MB; fall back to the smallest audio.
        "format": "bestaudio[filesize<25M]/bestaudio[filesize_approx<25M]/worstaudio/bestaudio",
        "outtmpl": os.path.join(out_dir, "audio.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
    }

    print("[*] Downloading audio with yt-dlp...")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([youtube_url])

    files = glob.glob(os.path.join(out_dir, "audio.*"))
    if not files:
        raise RuntimeError("Audio download failed - no file was created.")
    path = files[0]
    print(f"[+] Downloaded {os.path.basename(path)} ({os.path.getsize(path) / 1e6:.1f} MB)")
    return path


def transcribe_with_groq(audio_path: str) -> dict:
    """Send the audio file to Groq Whisper and return the standard transcript dict."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is missing. Add it to your .env file.")

    size = os.path.getsize(audio_path)
    if size > MAX_AUDIO_BYTES:
        raise RuntimeError(
            f"Audio is {size / 1e6:.1f} MB, above Groq's 25 MB limit. "
            "Try a shorter video (roughly under 25-30 minutes)."
        )

    from groq import Groq

    client = Groq(api_key=api_key)
    print("[*] Transcribing with Groq Whisper...")
    with open(audio_path, "rb") as f:
        resp = client.audio.transcriptions.create(
            file=(os.path.basename(audio_path), f.read()),
            model=GROQ_WHISPER_MODEL,
            response_format="verbose_json",
        )

    # The SDK may return an object or a dict depending on version.
    raw_segments = getattr(resp, "segments", None)
    if raw_segments is None and isinstance(resp, dict):
        raw_segments = resp.get("segments")
    text = getattr(resp, "text", None) or (resp.get("text") if isinstance(resp, dict) else "")

    segments = []
    for seg in raw_segments or []:
        get = seg.get if isinstance(seg, dict) else lambda k, d=None: getattr(seg, k, d)
        segments.append({
            "start": float(get("start", 0) or 0),
            "end": float(get("end", 0) or 0),
            "text": (get("text", "") or "").strip(),
        })

    if not segments and text:
        segments = [{"start": 0.0, "end": 0.0, "text": text.strip()}]

    result = _build_result(segments)
    print(f"[+] Transcribed {len(result['full_text'])} characters")
    return result


def process_video(youtube_url: str) -> dict:
    """LOCAL mode entry point: URL -> transcript dict."""
    get_video_id(youtube_url)  # validates the URL early
    with tempfile.TemporaryDirectory() as tmp:
        audio_path = download_audio(youtube_url, tmp)
        result = transcribe_with_groq(audio_path)

    if not result["full_text"]:
        raise RuntimeError("Transcription came back empty. Try another video.")
    return result


# --------------------------------------------------------------------------- #
# HUGGINGFACE mode: parse a pasted YouTube transcript
# --------------------------------------------------------------------------- #
# Matches "0:05", "12:34", "1:02:03" at the start of a line, optionally followed by text.
_TS_LINE = re.compile(r"^\s*\[?((?:\d{1,2}:)?\d{1,2}:\d{2})\]?\s*(.*)$")


def _ts_to_seconds(ts: str) -> float:
    parts = [int(p) for p in ts.split(":")]
    seconds = 0
    for p in parts:
        seconds = seconds * 60 + p
    return float(seconds)


def parse_pasted_transcript(raw_text: str) -> dict:
    """
    Accepts the text copied from YouTube's "Show transcript" panel, in either layout:

        0:00                         0:00 hello everyone
        hello everyone      OR       0:04 today we will...
        0:04
        today we will...

    Also accepts plain text with no timestamps (segments get start=0).
    Ignores YouTube's "X seconds" / "X minutes, Y seconds" accessibility lines.
    """
    if not raw_text or not raw_text.strip():
        raise ValueError("The pasted transcript is empty.")

    noise = re.compile(r"^\d+\s+(hours?|minutes?|seconds?)(,\s*\d+\s+(minutes?|seconds?))*$", re.I)

    segments = []
    current_start = None
    current_text = []

    def flush():
        if current_start is not None and current_text:
            segments.append({
                "start": current_start,
                "end": current_start,
                "text": " ".join(current_text).strip(),
            })

    for line in raw_text.splitlines():
        line = line.strip()
        if not line or noise.match(line):
            continue
        m = _TS_LINE.match(line)
        if m:
            flush()
            current_start = _ts_to_seconds(m.group(1))
            current_text = [m.group(2)] if m.group(2) else []
        else:
            if current_start is None:
                current_start = 0.0
            current_text.append(line)
    flush()

    # Fill in end times from the next segment's start.
    for i, seg in enumerate(segments):
        nxt = segments[i + 1]["start"] if i + 1 < len(segments) else seg["start"] + 5
        seg["end"] = max(nxt, seg["start"])

    result = _build_result(segments)
    if not result["full_text"]:
        raise ValueError("Couldn't find any transcript text in what you pasted.")
    return result