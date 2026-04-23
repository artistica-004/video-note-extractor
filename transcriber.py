from youtube_transcript_api import YouTubeTranscriptApi
import re
import urllib3

# Disable SSL warnings and verification for Hugging Face environment
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

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
    raise Exception("Invalid YouTube URL!")


def process_video(youtube_url):
    """Fetches subtitles/captions using youtube-transcript-api — works on Hugging Face!"""

    print("🔍 Getting video ID...")
    video_id = get_video_id(youtube_url)
    print(f"✅ Video ID: {video_id}")

    print("📜 Fetching captions...")

    try:
        # Try to get English transcripts (manual or auto-generated)
        transcripts = None

        try:
            transcripts = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
            print("✅ English captions found (manual)")
        except Exception as e1:
            print(f"⚠️ Manual captions not available ({str(e1)[:50]}), trying auto-generated...")
            try:
                transcripts = YouTubeTranscriptApi.get_transcript(video_id, languages=['en-US'])
                print("✅ Auto-generated captions found (en-US)")
            except Exception as e2:
                try:
                    transcripts = YouTubeTranscriptApi.get_transcript(video_id)
                    print("✅ Found captions in default language")
                except Exception as e3:
                    raise Exception(f"Could not fetch any captions. Tried: en, en-US, default. Last error: {str(e3)}")

        if not transcripts:
            raise Exception("No captions/transcripts available!")

        # Process transcripts into segments
        entries = []
        for item in transcripts:
            text = item.get('text', '').strip()
            if text:
                entries.append({
                    'text': text,
                    'start': item.get('start', 0),
                    'end': item.get('start', 0) + item.get('duration', 0)
                })

        if not entries:
            raise Exception("Transcript is empty!")

        full_text = ' '.join([e['text'] for e in entries])
        segments = [
            {
                'start': e['start'],
                'end': e['end'],
                'text': e['text']
            }
            for e in entries
        ]

        print(f"✅ {len(full_text)} characters fetched!")
        print(f"📝 Preview: {full_text[:200]}")

        return {
            "full_text": full_text,
            "segments": segments
        }

    except Exception as e:
        error_msg = str(e).lower()

        if 'no transcript' in error_msg or 'unavailable' in error_msg:
            raise Exception(
                f"❌ This video has NO captions/subtitles available. "
                f"Please try a different video with English captions enabled."
            )
        elif 'invalid' in error_msg or 'not found' in error_msg:
            raise Exception(
                f"❌ Invalid YouTube URL or video not found. Please check the URL."
            )
        elif 'ssl' in error_msg or 'certificate' in error_msg or 'eof' in error_msg:
            raise Exception(
                f"❌ Network connection error. This is a Hugging Face environment issue. "
                f"Please try again in a few seconds or try a different video."
            )
        else:
            raise Exception(
                f"Error fetching captions: {str(e)}"
            )