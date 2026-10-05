---
title: Video Note Extractor
emoji: 🎬
colorFrom: purple
colorTo: blue
sdk: streamlit
sdk_version: 1.28.0
app_file: app.py
pinned: false
---

# 🎬 Video Note Extractor

> **Convert any YouTube video into organized notes instantly using AI.**

Simply paste a YouTube link and it automatically transcribes the audio, generates a summary, extracts key timestamps, and lists action items — all in under a minute. Built using Python, Streamlit, and Groq AI, it turns hours of video content into clear, downloadable notes with zero manual effort.

---

## ✨ Features

- 📋 **Organized Notes** — AI-generated summary, bullet-point notes and key takeaways
- ⏱️ **Smart Timestamps** — Top 8 most important moments with exact timestamps
- ✅ **Action Items** — Tasks and to-dos extracted from the video
- 📄 **Full Transcript** — Complete transcription of the video
- ⬇️ **Download Notes** — Save everything as a `.txt` file
- ⚡ **Fast** — Results in under 1 minute using Groq's cloud AI

---

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python 3.13 | Core programming language |
| Streamlit | Web interface |
| Requests | HTTP requests for caption fetching |
| Groq `openai/gpt-oss-20b` (configurable via `GROQ_MODEL`) | Notes & summary generation |
| Groq Whisper (`whisper-large-v3-turbo`) | Audio transcription |
| python-dotenv | API key management |

---

## ⚙️ Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/artistica-004/video-note-extractor.git
cd video-note-extractor
```

### 2. Create Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up API Key
Create a `.env` file in the project root:
```
GROQ_API_KEY=your_groq_api_key_here
# Optional: override default chat model (defaults to openai/gpt-oss-20b)
GROQ_MODEL=openai/gpt-oss-20b
```
Get your free API key at 👉 [console.groq.com](https://console.groq.com)

### 5. Run the App
```bash
streamlit run app.py
```

### 6. Open in Browser
```
http://localhost:8501
```

---

## 🔧 Troubleshooting

### `model_not_found` or Decommissioned Model Error
If you see an error like:
```
Error code: 404 - {'error': {'message': 'The model ... does not exist or you do not have access to it.', 'code': 'model_not_found'}}
```
Groq periodically updates its free tier model lineup. Set `GROQ_MODEL` in your `.env` (or Hugging Face Space secrets/variables) to an active model from [console.groq.com/docs/models](https://console.groq.com/docs/models) (e.g. `openai/gpt-oss-20b`).

---

## 🚀 How to Use

1. Paste any YouTube URL into the input box
2. Click **"Extract Notes!"**
3. Wait under 1 minute for AI to process
4. View results across 4 tabs — Notes, Timestamps, Action Items, Full Transcript
5. Click **"Download Notes as .txt"** to save

---

## 📁 Project Structure

```
video-note-extractor/
│
├── app.py                 # Main Streamlit web interface
├── transcriber.py         # Fetches YouTube captions directly
├── notes_generator.py     # AI generates notes, timestamps & tasks
├── requirements.txt       # Python dependencies
├── .env                   # API key (never uploaded to GitHub)
├── .gitignore             # Excludes .env and venv/
└── README.md              # This file
```

---

## 📦 Requirements

```
streamlit
groq
python-dotenv
requests
```

---

## 🔑 API Keys Needed

| API | Cost | Link |
|---|---|---|
| Groq API | FREE | [console.groq.com](https://console.groq.com) |

---

## 🙋‍♀️ Author

**Shivani Chaudhary**
- GitHub: [@artistica-004](https://github.com/artistica-004)

---

## 📄 License

This project is licensed under the MIT License.

---

⭐ If you found this useful, give it a star on GitHub!