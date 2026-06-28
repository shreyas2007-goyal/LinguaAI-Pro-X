# 🌍 LinguaAI Pro X

> **A Simple, Real-Time AI Translation App — Built with Streamlit & Gemini**

LinguaAI Pro X is an AI-powered translation app that lets you translate text, hold two-way translated conversations, learn languages through AI-generated lessons, and translate text inside images and documents—all from a single Python file.

Built with **Python**, **Streamlit**, and **Google Gemini AI**, this portfolio project focuses on delivering practical AI translation features with a simple, honest tech stack—no backend server, no cloud database, and no build tooling.

---

# ✨ Features

## 📝 AI Text Translation

- Real-time text translation
- Automatic source language detection
- Grammar correction before translation
- Tone selection (Neutral, Formal, Casual, Professional, Friendly, Academic)
- AI confidence score
- AI explanation of word meanings, idioms, cultural context, and grammar

---

## 💬 Conversation Mode

- Two-way translated conversations
- Select a language for each speaker
- Easily switch between speakers
- Session-based conversation history
- Clear/reset conversation option

---

## 🎓 AI Language Tutor

Turn any phrase into a mini language lesson.

- Translation with phonetic pronunciation
- Vocabulary breakdown (word, meaning, part of speech)
- Grammar explanations
- Example sentences
- Flashcard (front/back)

---

## 🖼️ Image Translator

- Upload PNG, JPG, JPEG, or WEBP images
- Gemini extracts and translates text directly (no separate OCR library)
- Displays extracted text alongside the translated version

---

## 📄 Document Translator

- Upload PDF, DOCX, or TXT files
- Translate the entire document
- Generate AI summaries with key points
- PDF extraction using **PyMuPDF**
- DOCX extraction using **python-docx**

---

# 🛠️ Technology Stack

This project intentionally keeps its technology stack simple.

| Layer | Technology |
|--------|------------|
| UI Framework | **Streamlit** |
| AI Engine | **Google Gemini API** (`google-genai`, `gemini-2.5-flash`) |
| PDF Processing | **PyMuPDF (fitz)** |
| DOCX Processing | **python-docx** |
| Image Understanding | Gemini Native Vision |
| Storage | Browser Session Only |
| Authentication | None (Local Single User) |

### Not Used (Yet)

- FastAPI
- Firebase / Firestore
- EasyOCR
- PaddleOCR
- SpeechRecognition
- Edge-TTS
- React

This version is intentionally designed as a lightweight, single-file application that can be run with one command.

---

# 📁 Project Structure

```text
linguaai-simple/
│
├── app.py              # Main application
├── requirements.txt
├── start.sh            # macOS/Linux launcher
├── start.bat           # Windows launcher
└── README.md
```

Everything is contained in a single Python file by design.

---

# 🚀 Getting Started

## 1. Install Python

Install **Python 3.10 or later** from:

https://www.python.org/downloads/

During installation, make sure to enable:

```
Add Python to PATH
```

---

## 2. Run the Application

### macOS / Linux

```bash
chmod +x start.sh
./start.sh
```

### Windows

Simply double-click:

```
start.bat
```

### Using a Shared Virtual Environment

If you use a shared `penv` folder across multiple projects, `start.bat` already searches for:

```
..\penv
```

If your setup is different, edit the following line inside `start.bat`:

```
set PENV=...
```

The first launch installs the required packages automatically and opens the application in your browser.

---

## 3. Add Your Gemini API Key

The interface can be explored without an API key, but translations require one.

1. Visit:

```
https://aistudio.google.com/apikey
```

2. Create a free API key.

3. Paste it into the **Gemini API Key** field in the Streamlit sidebar.

No `.env` file or restart is required.

---

# Notes

- Everything runs locally.
- Only translation requests are sent to Google's Gemini API.
- API keys are stored only in the current browser session.
- Press **Ctrl+C** in the terminal to stop the application.
- Launch again using `start.sh` or `start.bat`.

---

# Troubleshooting

## Image Error

```
TypeError:
ImageMixin.image() got an unexpected keyword argument 'use_container_width'
```

Your Streamlit version is older than **1.40**.

Upgrade Streamlit or download the latest version of the project.

---

## Invalid JSON

```
AI did not return valid JSON
```

Occasionally Gemini returns slightly malformed JSON.

The application automatically repairs common formatting issues before failing.

If necessary, simply retry the request.

---

## Response Cut Off

Gemini may occasionally stop generating long responses before completion due to token limits.

If this happens:

- Retry the request.
- Shorten the input.
- Split large documents into smaller sections.

---

# 🎯 Future Improvements

- Voice input and speech output
- Persistent history using SQLite
- Firebase Authentication
- Firestore cloud synchronization
- FastAPI backend
- React + Tailwind frontend
- Live microphone conversation mode
- Video subtitle translation
- Offline translation model
- Browser extension
- Mobile application

---

# 💼 Resume Description

### LinguaAI Pro X – AI Translation App

Developed an AI-powered multilingual translation application using **Python**, **Streamlit**, and **Google Gemini AI**. Implemented real-time translation, bilingual conversation mode, AI language tutoring, image translation, and document translation with context-aware grammar correction, tone adaptation, and cultural explanations. Designed as a lightweight single-file application that runs locally without requiring backend infrastructure.

---

# 📄 License

This project is licensed under the **MIT License**.

---

# 👨‍💻 Developer

**Shreyas Goyal**

If you found this project useful, consider giving it a ⭐ on GitHub.