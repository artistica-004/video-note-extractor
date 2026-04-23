from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._clients import _RequestsClient
import re
import urllib3
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Disable SSL warnings and verification for Hugging Face environment
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

# Custom HTTP client with better headers and retries
class CustomRequestsClient(_RequestsClient):
    def __init__(self):
        self.session = requests.Session()

        # Set up retries
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        # Better headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        })

    def make_request(self, endpoint, additional_params=None, headers=None):
        if headers is None:
            headers = {}

        try:
            response = self.session.get(endpoint, params=additional_params, headers=headers, timeout=30, verify=False)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error: {str(e)}")

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
    """Fetches subtitles/captions using youtube-transcript-api with custom HTTP client"""

    print("🔍 Getting video ID...")
    video_id = get_video_id(youtube_url)
    print(f"✅ Video ID: {video_id}")

    print("📜 Fetching captions...")

    try:
        # Use custom client with better headers and retries
        custom_client = CustomRequestsClient()

        try:
            transcripts = YouTubeTranscriptApi.get_transcript(
                video_id,
                languages=['en'],
                http_client=custom_client
            )
            print("✅ English captions found (manual)")
        except Exception as e1:
            print(f"⚠️ Manual captions not available, trying auto-generated...")
            try:
                transcripts = YouTubeTranscriptApi.get_transcript(
                    video_id,
                    languages=['en-US'],
                    http_client=custom_client
                )
                print("✅ Auto-generated captions found (en-US)")
            except Exception as e2:
                print(f"⚠️ Trying any available language...")
                try:
                    # Get all available transcripts and pick first English one
                    all_transcripts = YouTubeTranscriptApi.list_transcripts(video_id, http_client=custom_client)

                    # Try English first, then fallback
                    for lang in ['en', 'en-US', 'en-GB']:
                        try:
                            transcript_obj = all_transcripts.find_transcript([lang])
                            transcripts = transcript_obj.fetch()
                            print(f"✅ Found captions in {lang}")
                            break
                        except:
                            continue
                    else:
                        # If no English, get any available
                        if all_transcripts.manually_created_transcripts:
                            transcripts = all_transcripts.manually_created_transcripts[0].fetch()
                        elif all_transcripts.generated_transcripts:
                            transcripts = all_transcripts.generated_transcripts[0].fetch()
                        else:
                            raise Exception("No transcripts available for this video")

                except Exception as e3:
                    raise Exception(f"Could not fetch any captions after 3 attempts. Last error: {str(e3)}")

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
        elif 'ssl' in error_msg or 'certificate' in error_msg or 'eof' in error_msg or 'network' in error_msg:
            raise Exception(
                f"❌ Network connection error. Please try again in a few seconds."
            )
        else:
            raise Exception(
                f"Error fetching captions: {str(e)}"
            )