import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# max_retries lets the SDK wait and retry automatically on rate limits (HTTP 429).
client = Groq(api_key=os.getenv("GROQ_API_KEY"), max_retries=5)

# llama-3.1-8b-instant was removed from Groq's free plan (Aug 2026).
# Override with GROQ_MODEL in .env / HF secrets if you want a different model.
MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

# Long transcripts are split into parts of this many characters (~2.5k tokens each),
# so the WHOLE video is covered instead of only the first few minutes.
CHUNK_CHARS = 10000
# Max timestamped lines sent for the timestamps step (sampled across the whole video).
MAX_TIMESTAMP_LINES = 150


def call_groq(prompt, max_tokens=2500):
    """Helper function to call Groq API safely"""
    # gpt-oss models "think" first; keep that short so tokens go to the answer.
    extra = {"reasoning_effort": "low"} if MODEL.startswith("openai/gpt-oss") else {}
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=max_tokens,
            **extra
        )
    except Exception as e:
        print(f"Groq API error: {str(e)}")
        raise RuntimeError(f"Groq model '{MODEL}' failed: {e}") from e

    if response and response.choices and response.choices[0].message.content:
        return response.choices[0].message.content

    raise RuntimeError("Groq returned an empty response. Please try again.")


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def fmt_time(seconds):
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h:d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def split_into_chunks(full_text, segments):
    """
    Split the transcript into ~CHUNK_CHARS parts.
    Uses segments when available so each part knows its time range.
    Returns a list of (label, text).
    """
    chunks = []
    if segments:
        buf, start = [], None
        for seg in segments:
            if start is None:
                start = seg["start"]
            buf.append(seg["text"])
            if sum(len(t) for t in buf) >= CHUNK_CHARS:
                chunks.append((f"{fmt_time(start)} - {fmt_time(seg['end'])}", " ".join(buf)))
                buf, start = [], None
        if buf:
            chunks.append((f"{fmt_time(start)} - {fmt_time(segments[-1]['end'])}", " ".join(buf)))
    else:
        for i in range(0, len(full_text), CHUNK_CHARS):
            chunks.append((f"Part {i // CHUNK_CHARS + 1}", full_text[i:i + CHUNK_CHARS]))
    return chunks


# --------------------------------------------------------------------------- #
# Notes
# --------------------------------------------------------------------------- #
def notes_for_chunk(text, label, part_no, total_parts):
    prompt = f"""
You are an expert teacher writing detailed STUDY NOTES for a student from a video lecture.
This is part {part_no} of {total_parts} of the transcript (time range: {label}).

Write thorough, well-structured notes for THIS part only:
- Use '#### ' sub-headings for each topic or concept, in the order they are taught.
- Under each heading, explain the concept clearly in bullet points, as a teacher would.
- **Bold** every key term the first time it appears and define it in simple words.
- Include every example, analogy, formula, code snippet (in ``` code blocks ```),
  step-by-step process, number and comparison the speaker gives.
- Add a short "💡 Note:" line for tips, common mistakes or important warnings mentioned.
- Do NOT write an introduction or conclusion, do NOT summarise the whole video,
  do NOT invent facts that are not in the transcript.

Transcript part:
{text}
"""
    return call_groq(prompt, max_tokens=3000)


def summary_and_takeaways(detailed_notes):
    # Send the combined notes (already condensed) rather than the raw transcript.
    source = detailed_notes[:24000]
    prompt = f"""
Below are detailed study notes made from a video. Write:

## 📋 SUMMARY
A clear 5-8 sentence overview of what the whole video teaches.

## 🎯 WHAT YOU WILL LEARN
4-8 bullet points of the main topics covered.

## 💡 KEY TAKEAWAYS
5-8 bullet points with the most important things a learner must remember.

## 📖 GLOSSARY
Key terms from the notes with a one-line definition each (format: **Term** - definition).

## ❓ REVISION QUESTIONS
5 short questions a student can use to test themselves (no answers).

Use exactly these headings. Do not invent facts.

Notes:
{source}
"""
    return call_groq(prompt, max_tokens=2500)


def generate_notes(full_text, segments=None):
    """Takes transcribed text and generates detailed, organized study notes for the whole video"""

    print("📝 Generating notes...")

    chunks = split_into_chunks(full_text, segments or [])
    print(f"📝 Transcript split into {len(chunks)} part(s)")

    sections = []
    for i, (label, text) in enumerate(chunks, start=1):
        print(f"📝 Writing notes for part {i}/{len(chunks)} ({label})")
        part_notes = notes_for_chunk(text, label, i, len(chunks))
        header = f"### ⏱️ {label}\n\n" if len(chunks) > 1 else ""
        sections.append(header + part_notes)

    detailed = "\n\n---\n\n".join(sections)
    overview = summary_and_takeaways(detailed)

    result = f"{overview}\n\n---\n\n## 📝 DETAILED NOTES\n\n{detailed}"
    print(f"📝 Notes generated: {len(result)} characters")
    return result


# --------------------------------------------------------------------------- #
# Timestamps
# --------------------------------------------------------------------------- #
def sample_segments(segments, max_lines=MAX_TIMESTAMP_LINES):
    """Merge segments into evenly spaced blocks so the WHOLE video fits in one prompt."""
    if len(segments) <= max_lines:
        return segments
    group = -(-len(segments) // max_lines)  # ceiling division
    merged = []
    for i in range(0, len(segments), group):
        block = segments[i:i + group]
        text = " ".join(s["text"] for s in block)
        merged.append({"start": block[0]["start"], "text": text[:200]})
    return merged


def generate_timestamps(segments):
    """Creates important timestamps spread across the entire video"""

    print("⏱️ Generating timestamps...")

    if not segments:
        return "## ⏱️ IMPORTANT TIMESTAMPS\n- No timestamp data available for this video."

    duration = segments[-1].get("end") or segments[-1]["start"]
    # Roughly one timestamp every 2 minutes, between 8 and 25 total.
    target = max(8, min(25, int(duration // 120)))

    segments_text = "\n".join(
        f"[{fmt_time(seg['start'])}] {seg['text']}" for seg in sample_segments(segments)
    )

    prompt = f"""
You are given a timestamped transcript of a video that is {fmt_time(duration)} long.
Pick about {target} important moments spread across the ENTIRE video, from the start
all the way to the end (do not stop early). Each should mark where a new topic,
key concept, example or conclusion begins.

Format EXACTLY like this, in time order, using only times that appear in the transcript:
## ⏱️ IMPORTANT TIMESTAMPS
- [MM:SS] - **Topic name** - one-line description

Timestamped transcript:
{segments_text}
"""

    result = call_groq(prompt, max_tokens=2000)
    print(f"⏱️ Timestamps generated: {len(result)} characters")
    return result


# --------------------------------------------------------------------------- #
# Action items
# --------------------------------------------------------------------------- #
def generate_action_items(full_text):
    """Extracts action items / practice tasks from the whole transcription"""

    print("✅ Generating action items...")

    # Sample the beginning, middle and end so the whole video is represented.
    if len(full_text) > 12000:
        mid = len(full_text) // 2
        full_text = (full_text[:4000] + "\n...\n" + full_text[mid - 2000:mid + 2000]
                     + "\n...\n" + full_text[-4000:])

    prompt = f"""
Read this transcription and extract ACTION ITEMS or TASKS mentioned by the speaker.
If few are mentioned, add practical next steps and practice exercises a learner
should do to master this topic.

Format EXACTLY like this:
## ✅ ACTION ITEMS
- [ ] Action item 1
- [ ] Action item 2

## 🏋️ PRACTICE EXERCISES
- [ ] Exercise 1
- [ ] Exercise 2

Transcription:
{full_text}
"""

    result = call_groq(prompt, max_tokens=1500)
    print(f"✅ Action items generated: {len(result)} characters")
    return result


# --------------------------------------------------------------------------- #
# Main entry point (same signature and return shape as before)
# --------------------------------------------------------------------------- #
def process_transcription(transcription):
    """Main function - takes transcription dict and returns all notes"""

    full_text = transcription.get("full_text", "") if transcription else ""
    segments = transcription.get("segments", []) if transcription else []

    print(f"🔍 Full text length: {len(full_text)} | segments: {len(segments)}")

    if not full_text:
        raise Exception("Transcription is empty! Please try another video.")

    notes = generate_notes(full_text, segments)
    timestamps = generate_timestamps(segments)
    action_items = generate_action_items(full_text)

    print("🎉 All content generated successfully!")

    return {
        "notes": notes,
        "timestamps": timestamps,
        "action_items": action_items
    }