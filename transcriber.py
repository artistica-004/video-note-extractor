import yt_dlp
import re
import os
import json

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
    """Fetches subtitles using yt-dlp — works on Hugging Face!"""
    
    print("🔍 Getting video ID...")
    video_id = get_video_id(youtube_url)
    print(f"✅ Video ID: {video_id}")

    print("📜 Fetching subtitles...")

    # yt-dlp options to download ONLY subtitles (no audio/video!)
    ydl_opts = {
        'skip_download': True,          # Don't download video/audio!
        'writesubtitles': True,         # Download manual subtitles
        'writeautomaticsub': True,      # Download auto-generated subtitles
        'subtitleslangs': ['en', 'en-US', 'en-GB'],
        'subtitlesformat': 'json3',     # JSON format - easy to parse
        'outtmpl': f'subtitle_{video_id}',
        'quiet': True,
    }

    subtitle_file = None

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])

        # Find the downloaded subtitle file
        for ext in ['en.json3', 'en-US.json3', 'en-GB.json3']:
            fname = f'subtitle_{video_id}.{ext}'
            if os.path.exists(fname):
                subtitle_file = fname
                break

        if not subtitle_file:
            raise Exception("No subtitle file downloaded!")

        print(f"✅ Subtitle file found: {subtitle_file}")

        # Parse the JSON3 subtitle file
        with open(subtitle_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        entries = []
        for event in data.get('events', []):
            if 'segs' not in event:
                continue
            text = ''.join(seg.get('utf8', '') for seg in event['segs'])
            text = text.strip().replace('\n', ' ')
            if text:
                start = event.get('tStartMs', 0) / 1000
                duration = event.get('dDurationMs', 0) / 1000
                entries.append({
                    'text': text,
                    'start': start,
                    'end': start + duration
                })

        # Clean up subtitle file
        if subtitle_file and os.path.exists(subtitle_file):
            os.remove(subtitle_file)

        if not entries:
            raise Exception("Subtitle file was empty!")

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
        # Clean up any subtitle files
        for f in os.listdir('.'):
            if f.startswith(f'subtitle_{video_id}'):
                os.remove(f)
        raise Exception(
            f"Could not fetch subtitles! Please try a video "
            f"that has English captions enabled. Error: {str(e)}"
        )