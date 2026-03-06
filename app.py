import streamlit as st
from transcriber import process_video
from notes_generator import process_transcription

# ---- PAGE SETUP ----
st.set_page_config(
    page_title="Video Note Extractor",
    page_icon="🎬",
    layout="wide"
)

# ---- HEADER ----
st.title("🎬 Video Note Extractor")
st.markdown("### Convert any YouTube video into organized notes instantly!")
st.divider()

# ---- INPUT ----
youtube_url = st.text_input(
    "📎 Paste your YouTube URL here",
    placeholder="https://www.youtube.com/watch?v=..."
)

extract_button = st.button("🚀 Extract Notes!")

st.divider()

# ---- BUTTON CLICKED ----
if extract_button:
    if not youtube_url:
        st.error("⚠️ Please paste a YouTube URL first!")
    
    else:
        try:
            # Step 1 - Transcribe
            with st.spinner("⏬ Downloading and transcribing audio... please wait!"):
                transcription = process_video(youtube_url)
            
            # Step 2 - Generate Notes
            with st.spinner("🧠 AI is generating your notes..."):
                results = process_transcription(transcription)
            
            # Step 3 - Show results DIRECTLY here!
            st.success("🎉 Notes extracted successfully!")
            st.caption(f"📎 {youtube_url}")
            st.divider()
            
            tab1, tab2, tab3, tab4 = st.tabs([
                "📝 Notes",
                "⏱️ Timestamps",
                "✅ Action Items",
                "📄 Full Transcript"
            ])
            
            with tab1:
                st.markdown(results["notes"])
            
            with tab2:
                st.markdown(results["timestamps"])
            
            with tab3:
                st.markdown(results["action_items"])
            
            with tab4:
                st.markdown("### 📄 Full Transcription")
                st.text_area(
                    "Complete transcript",
                    transcription["full_text"],
                    height=400
                )
            
            st.divider()
            
            # Download button
            full_output = f"""
VIDEO NOTE EXTRACTOR 🎬
=======================
Video: {youtube_url}

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
                mime="text/plain"
            )

        except Exception as e:
            st.error(f"❌ Something went wrong: {str(e)}")
            st.info("💡 Make sure your YouTube URL is correct and try again!")
