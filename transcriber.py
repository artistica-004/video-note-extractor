import re
import requests
import json
import urllib.parse
import time

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


def fetch_captions_from_youtube(video_id):
    """Fetch captions directly from YouTube's servers"""

    print(f"[*] Fetching caption data for video: {video_id}")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        # Step 1: Get video page to find caption tracks
        print("[*] Getting video page...")
        video_url = f"https://www.youtube.com/watch?v={video_id}"

        session = requests.Session()
        session.headers.update(headers)

        response = session.get(video_url, timeout=15, verify=False)
        response.raise_for_status()

        # Extract caption track data from initial data
        html = response.text

        # Find the initial data JSON in the page
        match = re.search(r'var ytInitialData = ({.*?});', html)
        if not match:
            match = re.search(r'"captions":\{"playerCaptionsTracklistRenderer":(.*?),"', html)

        if not match:
            raise Exception("Could not find caption data in page")

        print("[+] Found caption tracks")

        # Try to extract caption URLs from the response
        caption_tracks = re.findall(r'"url":"(.*?caption[^"]*)"', html)

        if not caption_tracks:
            # Try another pattern
            caption_tracks = re.findall(r'caption_tracks":\[\{"baseUrl":"([^"]+)"', html)

        if not caption_tracks:
            raise Exception("No caption tracks found")

        print(f"[+] Found {len(caption_tracks)} caption track(s)")

        # Step 2: Fetch the actual captions
        for caption_url in caption_tracks:
            try:
                # Decode URL if needed
                caption_url = caption_url.replace('\\u0026', '&')

                print(f"[*] Downloading captions from: {caption_url[:50]}...")

                cap_response = session.get(caption_url, timeout=15, verify=False)
                cap_response.raise_for_status()

                # Parse VTT or XML format
                captions_text = cap_response.text

                if 'WEBVTT' in captions_text or 'Kind: captions' in captions_text:
                    # VTT format
                    print("[+] Got VTT format captions")
                    entries = parse_vtt(captions_text)
                elif captions_text.strip().startswith('<?xml'):
                    # XML format
                    print("[+] Got XML format captions")
                    entries = parse_xml(captions_text)
                else:
                    continue

                if entries:
                    return entries

            except Exception as e:
                print(f"[-] Failed to fetch from this track: {str(e)}")
                continue

        raise Exception("Could not fetch captions from any track")

    except Exception as e:
        raise Exception(f"Caption fetch failed: {str(e)}")


def parse_vtt(vtt_text):
    """Parse VTT format captions"""
    entries = []
    lines = vtt_text.split('\n')

    current_time = None
    current_text = []

    for line in lines:
        line = line.strip()

        if '-->' in line:
            # Parse timestamp
            try:
                start_str = line.split('-->')[0].strip()
                start = vtt_time_to_seconds(start_str)
                current_time = start
            except:
                pass
        elif line and current_time is not None and '-->' not in line:
            # This is caption text
            if line != 'WEBVTT' and not line.startswith('Kind:') and not line.startswith('Language:'):
                current_text.append(line)
        elif not line and current_text:
            # Empty line - end of caption block
            text = ' '.join(current_text)
            if text.strip():
                entries.append({
                    'text': text.strip(),
                    'start': current_time,
                    'end': current_time + 5
                })
            current_text = []
            current_time = None

    return entries


def parse_xml(xml_text):
    """Parse XML format captions"""
    entries = []

    try:
        from xml.etree import ElementTree as ET

        root = ET.fromstring(xml_text)

        # Find all text elements
        for item in root.findall('.//p'):
            text = ''.join(item.itertext()).strip()
            if text:
                start = float(item.get('t', 0)) / 1000  # Convert to seconds
                duration = float(item.get('d', 5000)) / 1000

                entries.append({
                    'text': text,
                    'start': start,
                    'end': start + duration
                })
    except Exception as e:
        raise Exception(f"XML parsing failed: {str(e)}")

    return entries


def vtt_time_to_seconds(time_str):
    """Convert VTT timestamp to seconds"""
    try:
        parts = time_str.replace(',', '.').split(':')
        if len(parts) == 3:
            hours, minutes, seconds = parts
            return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
        elif len(parts) == 2:
            minutes, seconds = parts
            return int(minutes) * 60 + float(seconds)
    except:
        pass
    return 0


def process_video(youtube_url):
    """Main function to process YouTube video and extract captions"""

    print("[*] Getting video ID...")
    video_id = get_video_id(youtube_url)
    print(f"[+] Video ID: {video_id}")

    print("[*] Fetching captions...")

    try:
        # Fetch captions directly from YouTube
        entries = fetch_captions_from_youtube(video_id)

        if not entries:
            raise Exception("No caption entries found")

        # Process entries
        full_text = ' '.join([e['text'] for e in entries])
        segments = [
            {
                'start': e['start'],
                'end': e['end'],
                'text': e['text']
            }
            for e in entries
        ]

        print(f"[+] {len(full_text)} characters fetched!")
        print(f"[*] Preview: {full_text[:200]}")

        return {
            "full_text": full_text,
            "segments": segments
        }

    except Exception as e:
        error_msg = str(e).lower()
        raise Exception(
            f"Error extracting captions: {str(e)}"
        )
