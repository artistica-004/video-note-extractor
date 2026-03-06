from youtube_transcript_api import YouTubeTranscriptApi, FetchedTranscript
from youtube_transcript_api._api import YouTubeTranscriptApi as YTApi
import re

def get_video_id(youtube_url):
    """Extracts video ID from any YouTube URL format"""
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})',
        r'(?:embed\/)([0-9A-Za-z_-]{11})'
    ]
    for pattern in patterns:
        match = re.search(pattern, youtube_url)
        if match:
            return match.group(1)
    raise Exception("Could not extract video ID! Please check your YouTube link.")


def process_video(youtube_url):
    """Fetches transcript directly from YouTube captions"""
    
    print("🔍 Extracting video ID...")
    video_id = get_video_id(youtube_url)
    print(f"✅ Video ID: {video_id}")
    
    print("📜 Fetching transcript from YouTube...")
    
    try:
        ytt = YouTubeTranscriptApi()
        transcript_list = ytt.fetch(video_id)
        entries = list(transcript_list)
        
    except Exception as e1:
        print(f"First attempt failed: {e1}")
        try:
            # Try older API style
            entries = YouTubeTranscriptApi.list_transcripts(video_id)
            transcript = entries.find_transcript(['en', 'en-US', 'en-GB'])
            entries = transcript.fetch()
            entries = list(entries)
        except Exception as e2:
            print(f"Second attempt failed: {e2}")
            raise Exception(
                "No captions found for this video! "
                "Please try a video with subtitles enabled. "
                f"Details: {str(e2)}"
            )
    
    print(f"✅ Got {len(entries)} transcript entries!")
    
    # Build full text
    full_text = " ".join([
        entry.get('text', '') if isinstance(entry, dict) else str(entry.text)
        for entry in entries
    ])
    
    # Build segments
    segments = []
    for entry in entries:
        if isinstance(entry, dict):
            segments.append({
                'start': entry.get('start', 0),
                'end': entry.get('start', 0) + entry.get('duration', 0),
                'text': entry.get('text', '')
            })
        else:
            segments.append({
                'start': entry.start,
                'end': entry.start + getattr(entry, 'duration', 0),
                'text': entry.text
            })
    
    print(f"✅ Got {len(full_text)} characters!")
    print(f"📝 Preview: {full_text[:200]}")
    
    return {
        "full_text": full_text,
        "segments": segments
    }
