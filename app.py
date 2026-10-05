import streamlit as st

from transcriber import detect_mode, get_video_id, process_video, parse_pasted_transcript
from notes_generator import process_transcription

# ---- PAGE SETUP ----
st.set_page_config(page_title="Video Note Extractor", page_icon="🎬", layout="wide")


@st.cache_data(show_spinner=False)
def cached_mode() -> str:
    return detect_mode()


MODE = cached_mode()

# ---- HEADER ----
st.title("🎬 Video Note Extractor")
st.markdown("### Convert any YouTube video into organized notes instantly!")
if MODE == "local":
    st.caption("🖥️ Local mode — audio is downloaded and transcribed automatically with Groq Whisper.")
else:
    st.caption("☁️ Cloud mode — YouTube can't be reached from this server, so paste the transcript below.")
st.divider()

# ---- INPUT ----
youtube_url = st.text_input(
    "📎 YouTube URL" + ("" if MODE == "local" else " (optional — used for labels only)"),
    placeholder="https://www.youtube.com/watch?v=...",
)

pasted_transcript = ""
if MODE == "huggingface":
    with st.expander("❓ How do I get the transcript?", expanded=False):
        st.markdown(
            "1. Open the video on YouTube.\n"
            "2. Click **…more** under the video description.\n"
            "3. Scroll down and click **Show transcript**.\n"
            "4. Click inside the transcript panel, press **Ctrl+A** then **Ctrl+C** "
            "(or drag-select all lines).\n"
            "5. Paste it below. Timestamps are kept automatically."
        )
    pasted_transcript = st.text_area(
        "📄 Paste the YouTube transcript here",
        height=300,
        placeholder="0:00\nHello everyone, welcome back...\n0:05\nToday we're going to...",
    )

extract_button = st.button("🚀 Extract Notes!")
st.divider()


def render_results(transcription: dict, results: dict, url: str) -> None:
    st.success("🎉 Notes extracted successfully!")
    if url:
        st.caption(f"📎 {url}")
    st.divider()

    tab1, tab2, tab3, tab4 = st.tabs(
        ["📝 Notes", "⏱️ Timestamps", "✅ Action Items", "📄 Full Transcript"]
    )
    with tab1:
        st.markdown(results["notes"])
    with tab2:
        st.markdown(results["timestamps"])
    with tab3:
        st.markdown(results["action_items"])
    with tab4:
        st.markdown("### 📄 Full Transcription")
        st.text_area("Complete transcript", transcription["full_text"], height=400)

    st.divider()
    full_output = f"""VIDEO NOTE EXTRACTOR 🎬
=======================
Video: {url or "N/A"}

{results['notes']}

---

{results['timestamps']}

---

{results['action_items']}

---

FULL TRANSCRIPT
===============
{transcription['full_text']}
"""
    st.download_button(
        label="⬇️ Download Notes as .txt",
        data=full_output,
        file_name="video_notes.txt",
        mime="text/plain",
    )


# ---- BUTTON CLICKED ----
if extract_button:
    try:
        if MODE == "local":
            if not youtube_url:
                st.error("⚠️ Please paste a YouTube URL first!")
                st.stop()
            get_video_id(youtube_url)  # validate early with a friendly message
            with st.spinner("⏬ Downloading and transcribing audio... please wait!"):
                transcription = process_video(youtube_url)
        else:
            if not pasted_transcript.strip():
                st.error("⚠️ Please paste the video transcript first!")
                st.stop()
            with st.spinner("📄 Reading your transcript..."):
                transcription = parse_pasted_transcript(pasted_transcript)

        with st.spinner("🧠 AI is generating your notes..."):
            results = process_transcription(transcription)

        render_results(transcription, results, youtube_url)

    except ValueError as e:
        st.error(f"⚠️ {e}")
    except Exception as e:
        st.error(f"❌ Something went wrong: {e}")
        if MODE == "local":
            st.info(
                "💡 Check the URL, your internet connection, and that yt-dlp is up to date "
                "(`pip install -U yt-dlp`)."
            )
        else:
            st.info("💡 Make sure you pasted the full transcript text from YouTube.")
        if "model_not_found" in str(e) or "decommissioned" in str(e):
            st.info(
                "💡 This Groq model was retired. Set `GROQ_MODEL` in your `.env` "
                "(or HF Space secrets) to a current model from "
                "https://console.groq.com/docs/models"
            )