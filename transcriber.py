import yt_dlp
import os
import imageio_ffmpeg
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def download_audio(youtube_url):
    print("⏬ Downloading audio from YouTube...")
    
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    ffmpeg_dir = os.path.dirname(ffmpeg_exe)
    
    ydl_opts = {
        'format': 'worstaudio/worst',
        'outtmpl': 'audio.%(ext)s',
        'quiet': False,
        'ffmpeg_location': ffmpeg_dir,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=True)
        ext = info.get('ext', 'webm')
        audio_file = f"audio.{ext}"
    
    print(f"✅ Audio downloaded as {audio_file}!")
    return audio_file


def transcribe_audio(audio_path):
    print("🎙️ Transcribing using Groq Whisper API...")
    
    file_size = os.path.getsize(audio_path) / (1024 * 1024)
    print(f"📁 File size: {file_size:.1f} MB")
    
    if file_size > 40:
        raise Exception("File too large! Please try a shorter video.")
    
    with open(audio_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model="whisper-large-v3-turbo",
            file=(os.path.basename(audio_path), audio_file),
            response_format="verbose_json",
            timestamp_granularities=["segment"]
        )
    
    print("✅ Transcription complete!")
    print(f"📝 Text preview: {transcription.text[:200] if transcription.text else 'EMPTY!'}")
    
    segments = []
    if hasattr(transcription, 'segments') and transcription.segments:
        for seg in transcription.segments:
            if isinstance(seg, dict):
                segments.append({
                    'start': seg.get('start', 0),
                    'end': seg.get('end', 0),
                    'text': seg.get('text', '')
                })
            else:
                segments.append({
                    'start': seg.start,
                    'end': seg.end,
                    'text': seg.text
                })
    
    result = {
        "full_text": transcription.text if transcription.text else "",
        "segments": segments
    }
    
    print(f"✅ Returning result with {len(result['full_text'])} characters!")
    return result


def process_video(youtube_url):
    print("🎬 Starting process_video...")
    
    audio_path = download_audio(youtube_url)
    
    print(f"🎵 Audio file exists: {os.path.exists(audio_path)}")
    
    transcription = transcribe_audio(audio_path)
    
    print(f"📋 Transcription received: {type(transcription)}")
    print(f"📋 Full text length: {len(transcription['full_text'])}")
    
    if os.path.exists(audio_path):
        os.remove(audio_path)
        print("🗑️ Cleaned up audio file!")
    
    return transcription
