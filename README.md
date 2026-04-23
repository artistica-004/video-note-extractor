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
| Groq LLaMA (llama-3.1-8b-instant) | Notes & summary generation |
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