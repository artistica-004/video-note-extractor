import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def call_groq(prompt):
    """Helper function to call Groq API safely"""
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1500
        )
        
        if response and response.choices and len(response.choices) > 0:
            content = response.choices[0].message.content
            if content:
                return content
        
        return "Could not generate content. Please try again."
    
    except Exception as e:
        print(f"Groq API error: {str(e)}")
        return f"Error generating content: {str(e)}"


def generate_notes(full_text):
    """Takes transcribed text and generates organized notes"""
    
    print("📝 Generating notes...")
    
    if len(full_text) > 3000:
        full_text = full_text[:3000] + "..."
    
    prompt = f"""
    You are an expert note taker. Read the following transcription and create:
    
    1. A brief SUMMARY (3-5 sentences)
    2. ORGANIZED NOTES in bullet points
    3. KEY TAKEAWAYS (max 5 points)
    
    Format EXACTLY like this:
    
    ## 📋 SUMMARY
    (write summary here)
    
    ## 📝 ORGANIZED NOTES
    (write bullet points here)
    
    ## 💡 KEY TAKEAWAYS
    (write takeaways here)
    
    Transcription:
    {full_text}
    """
    
    result = call_groq(prompt)
    print(f"📝 Notes generated: {len(result)} characters")
    return result


def generate_timestamps(segments):
    """Creates important timestamps from segments"""
    
    print("⏱️ Generating timestamps...")
    
    if not segments or len(segments) == 0:
        return "## ⏱️ IMPORTANT TIMESTAMPS\n- No timestamp data available for this video."
    
    segments_text = ""
    for seg in segments[:30]:
        start_time = int(seg['start'])
        minutes = start_time // 60
        seconds = start_time % 60
        time_label = f"{minutes:02d}:{seconds:02d}"
        segments_text += f"[{time_label}] {seg['text']}\n"
    
    if not segments_text.strip():
        return "## ⏱️ IMPORTANT TIMESTAMPS\n- No timestamp data available."
    
    prompt = f"""
    You are given a video transcription with timestamps.
    Identify the TOP 8 most important moments.
    
    Format EXACTLY like this:
    ## ⏱️ IMPORTANT TIMESTAMPS
    - [MM:SS] - Description
    - [MM:SS] - Description
    
    Timestamped transcription:
    {segments_text}
    """
    
    result = call_groq(prompt)
    print(f"⏱️ Timestamps generated: {len(result)} characters")
    return result


def generate_action_items(full_text):
    """Extracts action items from transcription"""
    
    print("✅ Generating action items...")
    
    if len(full_text) > 3000:
        full_text = full_text[:3000] + "..."
    
    prompt = f"""
    Read this transcription and extract ACTION ITEMS or TASKS.
    If none mentioned, suggest relevant actions for the viewer.
    
    Format EXACTLY like this:
    ## ✅ ACTION ITEMS
    - [ ] Action item 1
    - [ ] Action item 2
    - [ ] Action item 3
    
    Transcription:
    {full_text}
    """
    
    result = call_groq(prompt)
    print(f"✅ Action items generated: {len(result)} characters")
    return result


def process_transcription(transcription):
    """Main function - takes transcription dict and returns all notes"""
    
    print(f"🔍 Received transcription type: {type(transcription)}")
    print(f"🔍 Transcription keys: {transcription.keys() if transcription else 'NONE'}")
    print(f"🔍 Full text length: {len(transcription.get('full_text', '')) if transcription else 0}")
    
    full_text = transcription.get("full_text", "") if transcription else ""
    segments = transcription.get("segments", []) if transcription else []
    
    if not full_text:
        raise Exception("Transcription is empty! Please try another video.")
    
    notes = generate_notes(full_text)
    timestamps = generate_timestamps(segments)
    action_items = generate_action_items(full_text)
    
    # Make sure nothing is None
    final_notes = notes if notes and len(notes) > 5 else "## 📝 Notes\nCould not generate notes. Please try again."
    final_timestamps = timestamps if timestamps and len(timestamps) > 5 else "## ⏱️ Timestamps\nNo timestamps available."
    final_actions = action_items if action_items and len(action_items) > 5 else "## ✅ Action Items\nNo action items found."
    
    print("🎉 All content generated successfully!")
    
    return {
        "notes": final_notes,
        "timestamps": final_timestamps,
        "action_items": final_actions
    }
