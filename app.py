"""
LinguaAI Pro X — Simple Edition
A single-file AI translation app. No Node.js, no build step, no servers to juggle.

Run it with:
    streamlit run app.py

Features:
- Real-time text translation with AI explanation (idioms, culture, grammar)
- Conversation Mode (two-way translated chat)
- AI Language Tutor (vocabulary, pronunciation, flashcards)
- Image Translator (OCR + translation)
- Document Translator (PDF/DOCX/TXT)
"""

import json
import re
import io
import streamlit as st
from google import genai
from google.genai import types as genai_types

# ----------------------------------------------------------------------------
# Page setup
# ----------------------------------------------------------------------------

st.set_page_config(
    page_title="LinguaAI Pro X",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)

LANGUAGES = [
    "Auto Detect", "English", "Hindi", "Spanish", "French", "German",
    "Chinese", "Japanese", "Korean", "Arabic", "Portuguese", "Russian",
    "Italian", "Turkish", "Bengali", "Tamil", "Urdu", "Vietnamese",
    "Thai", "Dutch", "Polish", "Greek", "Hebrew", "Indonesian", "Swahili",
]
TONES = ["Neutral", "Formal", "Casual", "Professional", "Friendly", "Academic"]

# ----------------------------------------------------------------------------
# Styling — premium dark theme to match the original design direction
# ----------------------------------------------------------------------------

st.markdown("""
<style>
    .stApp { background-color: #0a0817; }
    section[data-testid="stSidebar"] {
        background-color: #0d0b1a;
        border-right: 1px solid rgba(255,255,255,0.08);
    }
    section[data-testid="stSidebar"] .stRadio label {
        padding: 0.35rem 0.5rem;
        border-radius: 8px;
    }
    h1, h2, h3, h4, p, span, label, .stMarkdown, div { color: #f2f1f8; }
    .stTextArea textarea, .stTextInput input {
        background-color: rgba(255,255,255,0.04) !important;
        color: #f2f1f8 !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        border-radius: 12px !important;
    }
    .stSelectbox div[data-baseweb="select"] > div {
        background-color: rgba(255,255,255,0.04) !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        border-radius: 10px !important;
        color: #f2f1f8 !important;
    }
    .stButton button {
        background: linear-gradient(90deg, #8b5cf6, #6366f1) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.2rem !important;
    }
    .stButton button:hover { opacity: 0.9; }
    .stButton button p { color: white !important; }

    /* ---- Result boxes (used across Text Translator, AI Tutor, etc.) ---- */
    .result-card {
        background: rgba(139, 92, 246, 0.08);
        border: 1px solid rgba(139, 92, 246, 0.25);
        border-radius: 14px;
        padding: 1.1rem 1.3rem;
        margin-top: 0.6rem;
    }
    .plain-card {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 14px;
        padding: 1.1rem 1.3rem;
        margin-top: 0.6rem;
    }
    .badge {
        display: inline-block; font-size: 0.7rem; font-weight: 700;
        padding: 2px 8px; border-radius: 6px; background: #6366f1; color: white;
        margin-left: 6px;
    }
    .confidence { color: #34d399; font-size: 0.8rem; font-weight: 600; }
    hr { border-color: rgba(255,255,255,0.08) !important; }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# Gemini client (lazy — app still runs fine before a key is added)
# ----------------------------------------------------------------------------

def get_client():
    api_key = st.session_state.get("api_key", "").strip()
    if not api_key:
        return None
    try:
        return genai.Client(api_key=api_key)
    except Exception:
        return None


def strip_json_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```json\s*|^```\s*|```$", "", text, flags=re.MULTILINE).strip()
    return text


def _sanitize_json_text(text: str) -> str:
    """
    Gemini occasionally returns text that LOOKS like JSON but has literal
    newlines/tabs inside string values (e.g. a multi-line answer for
    "Cómo estás? (informal) / Cómo está? (formal)"), which breaks
    json.loads even though the braces/quotes all line up. This walks the
    string char-by-char and escapes control characters that appear INSIDE
    a string value (where they're invalid), while leaving the JSON's own
    structural whitespace (between keys/values) untouched. It also strips
    trailing commas before a closing bracket/brace, another common
    small mistake models make.
    """
    out = []
    in_string = False
    escape_next = False
    for ch in text:
        if escape_next:
            out.append(ch)
            escape_next = False
            continue
        if ch == "\\" and in_string:
            out.append(ch)
            escape_next = True
            continue
        if ch == '"':
            in_string = not in_string
            out.append(ch)
            continue
        if in_string and ch == "\n":
            out.append("\\n")
            continue
        if in_string and ch == "\t":
            out.append("\\t")
            continue
        if in_string and ch == "\r":
            out.append("\\r")
            continue
        out.append(ch)
    cleaned = "".join(out)
    # Remove trailing commas like `"x": 1,}` or `[1, 2,]` — outside of
    # any string, a comma followed only by whitespace and then a closing
    # bracket/brace is always invalid JSON and safe to drop.
    cleaned = re.sub(r",(\s*[}\]])", r"\1", cleaned)
    return cleaned


def _parse_json_loose(raw: str) -> dict:
    """Try increasingly forgiving strategies to parse an AI JSON response."""
    cleaned = strip_json_fences(raw)

    # 1) Straightforward parse.
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # 2) Escape stray control characters inside string values, then retry.
    try:
        return json.loads(_sanitize_json_text(cleaned))
    except json.JSONDecodeError:
        pass

    # 3) Extract the outermost {...} block and retry both ways on just that.
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        block = match.group(0)
        try:
            return json.loads(block)
        except json.JSONDecodeError:
            return json.loads(_sanitize_json_text(block))

    raise ValueError(f"AI did not return valid JSON: {raw[:300]}")


def ask_json(prompt: str, max_tokens: int = 800) -> dict:
    client = get_client()
    if client is None:
        raise RuntimeError("No Gemini API key set yet. Paste your key into the sidebar on the left.")
    # Ask explicitly for single-line string values — avoids the model
    # putting literal line breaks inside a JSON string, which is the most
    # common cause of parse failures.
    prompt = prompt + "\n\nIMPORTANT: Every JSON string value must be a single line — no literal line breaks inside any string. If you need to show options, separate them with ' / ' on one line instead of a new line."
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=genai_types.GenerateContentConfig(
            temperature=0.3,
            max_output_tokens=max_tokens,
            response_mime_type="application/json",
        ),
    )
    raw = response.text or "{}"
    return _parse_json_loose(raw)


def ask_text(prompt: str, max_tokens: int = 400) -> str:
    client = get_client()
    if client is None:
        raise RuntimeError("No Gemini API key set yet. Paste your key into the sidebar on the left.")
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=genai_types.GenerateContentConfig(temperature=0.2, max_output_tokens=max_tokens),
    )
    return (response.text or "").strip()


# ----------------------------------------------------------------------------
# Shared session state
# ----------------------------------------------------------------------------

if "recent_translations" not in st.session_state:
    # Seed with a couple of examples so the Dashboard doesn't look empty
    # on first run — replaced by real entries as soon as you translate.
    st.session_state.recent_translations = [
        {"source": "How are you?", "from": "English", "to": "Hindi"},
        {"source": "Where is the station?", "from": "English", "to": "French"},
        {"source": "Thank you so much!", "from": "English", "to": "Spanish"},
    ]

NAV_PAGES = [
    "🏠 Dashboard", "📝 Text Translator", "💬 Conversation Mode",
    "🎓 AI Tutor", "🖼️ Image Translator", "📄 Document Translator",
]

# ----------------------------------------------------------------------------
# Sidebar
# ----------------------------------------------------------------------------

with st.sidebar:
    st.markdown("## ✨ LinguaAI <span class='badge'>Pro</span>", unsafe_allow_html=True)
    st.caption("Break language barriers. Connect the world.")
    st.divider()

    if "api_key" not in st.session_state:
        st.session_state.api_key = ""

    st.session_state.api_key = st.text_input(
        "Gemini API Key",
        value=st.session_state.api_key,
        type="password",
        placeholder="Paste your key here",
        help="Get a free key at https://aistudio.google.com/apikey",
    )

    if st.session_state.api_key:
        st.success("API key set — AI features are live.", icon="✅")
    else:
        st.warning("No API key yet — [get a free one](https://aistudio.google.com/apikey)", icon="⚠️")

    st.divider()
    page = st.radio(
        "Navigate",
        NAV_PAGES,
        label_visibility="collapsed",
    )
    st.divider()
    st.caption("Running 100% locally. Your API key stays in this browser session only.")

# ----------------------------------------------------------------------------
# Dashboard
# ----------------------------------------------------------------------------

if page == "🏠 Dashboard":
    st.title("LinguaAI Pro X")
    st.caption("Break language barriers. Connect the world.")
    st.divider()

    st.subheader("Tools")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown("**📝 Text Translator**")
        st.caption("Translate text with AI explanations.")
    with col2:
        st.markdown("**💬 Conversation**")
        st.caption("Two-way translated chat.")
    with col3:
        st.markdown("**🎓 AI Tutor**")
        st.caption("Turn phrases into lessons.")
    with col4:
        st.markdown("**🖼️ Image Translator**")
        st.caption("Translate text in photos.")
    with col5:
        st.markdown("**📄 Document**")
        st.caption("Translate PDF/DOCX/TXT.")

    st.caption("👈 Pick any tool from the sidebar to get started.")

    st.divider()

    st.subheader("Recent Translations")
    if st.session_state.recent_translations:
        for r in st.session_state.recent_translations[-5:][::-1]:
            c1, c2 = st.columns([4, 1])
            with c1:
                st.write(r["source"][:60])
                st.caption(f"{r['from']} → {r['to']}")
            with c2:
                st.write("⭐")
    else:
        st.caption("Nothing yet — try the Text Translator.")

# ----------------------------------------------------------------------------
# Text Translator
# ----------------------------------------------------------------------------

elif page == "📝 Text Translator":
    st.markdown('<p class="topbar-title">Text Translator</p>', unsafe_allow_html=True)
    st.markdown('<p class="topbar-sub">Real-time translation with grammar correction and a confidence score.</p>', unsafe_allow_html=True)
    st.write("")

    lc1, lc2, lc3 = st.columns([1.4, 1.4, 1])
    with lc1:
        source_lang = st.selectbox("From", LANGUAGES, index=0, label_visibility="collapsed")
    with lc2:
        target_lang = st.selectbox("To", LANGUAGES[1:], index=1, label_visibility="collapsed")
    with lc3:
        tone = st.selectbox("Tone", TONES, label_visibility="collapsed")

    panel_l, panel_r = st.columns(2)
    with panel_l:
        text_in = st.text_area("Enter text to translate", height=180, max_chars=5000,
                                placeholder="Enter text to translate...", label_visibility="collapsed")
        st.caption(f"{len(text_in)} / 5000")
    with panel_r:
        output_box = st.container()
        with output_box:
            if "last_translation" in st.session_state:
                r = st.session_state.last_translation
                st.markdown(f"""<div class="result-card" style="min-height:148px;">
                <span class="confidence">● {r.get('confidence', '—')}% confidence</span><br><br>
                <b style="font-size:1.1rem">{r.get('translated', '')}</b>
                </div>""", unsafe_allow_html=True)
                st.caption(f"Detected source: {r.get('detected_source', source_lang)}")
            else:
                st.markdown("""<div class="plain-card" style="min-height:148px;color:#6b6885;">
                Translated text will appear here...</div>""", unsafe_allow_html=True)

    col_a, col_b = st.columns([1, 1])
    translate_clicked = col_a.button("✨ Translate", use_container_width=True)
    explain_clicked = col_b.button("💡 Explain (after translating)", use_container_width=True)

    if translate_clicked and text_in.strip():
        with st.spinner("Translating..."):
            try:
                prompt = f"""You are a professional translation engine.

Source language: {source_lang}
Target language: {target_lang}
Tone: {tone}

Steps:
1. If source is "Auto Detect", detect the actual source language.
2. Lightly correct obvious grammar/spelling mistakes in the original (without changing meaning).
3. Translate the corrected text into the target language, matching the tone.
4. Estimate your translation confidence (0-100).

Text:
\"\"\"{text_in}\"\"\"

Respond ONLY with JSON: {{"detected_source": "", "corrected_text": "", "translated": "", "confidence": <int 0-100>}}"""
                result = ask_json(prompt, max_tokens=600)
                st.session_state.last_translation = result
                st.session_state.last_input = text_in
                st.session_state.last_source = result.get("detected_source", source_lang)
                st.session_state.last_target = target_lang
                st.session_state.recent_translations.append({
                    "source": text_in, "from": result.get("detected_source", source_lang), "to": target_lang,
                })
                st.rerun()
            except Exception as e:
                st.error(str(e))

    if explain_clicked:
        if "last_translation" not in st.session_state:
            st.warning("Translate something first, then click Explain.")
        else:
            with st.spinner("Generating explanation..."):
                try:
                    r = st.session_state.last_translation
                    prompt = f"""You are a linguistics expert. Explain this translation in depth.

Original ({st.session_state.last_source}): "{st.session_state.last_input}"
Translation ({st.session_state.last_target}): "{r.get('translated','')}"

Respond ONLY with JSON:
{{"word_meanings": [{{"word": "", "meaning": ""}}], "idiom_or_context": "", "cultural_note": "", "alternative_translations": ["", ""], "grammar_notes": ""}}"""
                    explanation = ask_json(prompt, max_tokens=700)

                    st.markdown("#### 💡 AI Explanation")
                    if explanation.get("word_meanings"):
                        st.markdown("**Word Meanings**")
                        for w in explanation["word_meanings"]:
                            st.markdown(f"- **{w.get('word','')}** — {w.get('meaning','')}")
                    if explanation.get("idiom_or_context"):
                        st.markdown(f"**Context & Idiom**\n\n{explanation['idiom_or_context']}")
                    if explanation.get("cultural_note"):
                        st.markdown(f"**Cultural Usage**\n\n{explanation['cultural_note']}")
                    if explanation.get("grammar_notes"):
                        st.markdown(f"**Grammar Notes**\n\n{explanation['grammar_notes']}")
                    if explanation.get("alternative_translations"):
                        st.markdown("**Alternative Translations**")
                        for alt in explanation["alternative_translations"]:
                            st.markdown(f"- {alt}")
                except Exception as e:
                    st.error(str(e))

# ----------------------------------------------------------------------------
# Conversation Mode
# ----------------------------------------------------------------------------

elif page == "💬 Conversation Mode":
    st.title("Conversation Mode")
    st.caption("A two-way translated conversation between two speakers.")

    c1, c2 = st.columns(2)
    with c1:
        lang_a = st.selectbox("Speaker A language", LANGUAGES[1:], index=0, key="lang_a")
    with c2:
        lang_b = st.selectbox("Speaker B language", LANGUAGES[1:], index=1, key="lang_b")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for msg in st.session_state.chat_history:
        with st.chat_message("user" if msg["speaker"] == "A" else "assistant"):
            st.markdown(f"**{msg['original']}**")
            st.caption(f"→ {msg['translated']}")

    speaker = st.radio("Who's typing?", ["Speaker A", "Speaker B"], horizontal=True)
    draft = st.chat_input(f"Type as {speaker}...")

    if draft:
        is_a = speaker == "Speaker A"
        src, tgt = (lang_a, lang_b) if is_a else (lang_b, lang_a)
        try:
            translated = ask_text(
                f"Translate this from {src} to {tgt}. Respond with ONLY the translated text, no quotes.\n\nText: {draft}",
                max_tokens=300,
            )
        except Exception as e:
            translated = f"⚠️ {e}"
        st.session_state.chat_history.append({
            "speaker": "A" if is_a else "B", "original": draft, "translated": translated,
        })
        st.rerun()

    if st.session_state.chat_history:
        if st.button("🗑️ Clear conversation"):
            st.session_state.chat_history = []
            st.rerun()

# ----------------------------------------------------------------------------
# AI Tutor
# ----------------------------------------------------------------------------

elif page == "🎓 AI Tutor":
    st.title("AI Language Tutor")
    st.caption("Turn any phrase into a mini lesson.")

    phrase = st.text_input("Phrase to learn", placeholder="e.g. 'I am feeling blue' or 'Where is the station?'")
    target = st.selectbox("Learning", LANGUAGES[1:], index=1)

    if st.button("🎓 Generate Lesson", use_container_width=True) and phrase.strip():
        with st.spinner("Building your lesson..."):
            try:
                prompt = f"""You are an AI language tutor. Create a mini-lesson for this phrase in {target}.

Phrase: "{phrase}"

Respond ONLY with JSON:
{{"translation": "", "pronunciation": "<phonetic guide for an English speaker>",
"vocabulary": [{{"word": "", "meaning": "", "part_of_speech": ""}}],
"grammar_note": "", "example_sentences": ["", ""],
"flashcard_front": "", "flashcard_back": ""}}"""
                lesson = ask_json(prompt, max_tokens=800)
                st.session_state.lesson = lesson
            except Exception as e:
                st.error(str(e))

    if "lesson" in st.session_state:
        l = st.session_state.lesson
        st.markdown(f"""<div class="result-card">
        <span style="font-size:1.3rem;font-weight:700">{l.get('translation','')}</span><br>
        <span style="color:#a78bfa;font-family:monospace">{l.get('pronunciation','')}</span>
        </div>""", unsafe_allow_html=True)

        if l.get("vocabulary"):
            st.markdown("#### 📚 Vocabulary")
            for v in l["vocabulary"]:
                st.markdown(f"- **{v.get('word','')}** *({v.get('part_of_speech','')})* — {v.get('meaning','')}")

        if l.get("grammar_note"):
            st.markdown(f"#### Grammar Note\n{l['grammar_note']}")

        if l.get("example_sentences"):
            st.markdown("#### Example Sentences")
            for ex in l["example_sentences"]:
                st.markdown(f"› {ex}")

        if l.get("flashcard_front"):
            st.markdown(f"""<div class="plain-card">
            <span style="color:#fbbf24;font-size:0.75rem;font-weight:700">⚡ FLASHCARD</span><br>
            <b>{l.get('flashcard_front','')}</b><br>
            <span style="color:#a3a3c2">{l.get('flashcard_back','')}</span>
            </div>""", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# Image Translator
# ----------------------------------------------------------------------------

elif page == "🖼️ Image Translator":
    st.title("Image Translator")
    st.caption("Upload a photo of text — menus, signs, labels — and get an instant translation.")

    target = st.selectbox("Translate to", LANGUAGES[1:], index=0)
    uploaded = st.file_uploader("Upload image", type=["png", "jpg", "jpeg", "webp"])

    if uploaded:
        st.image(uploaded, caption="Uploaded image")

        if st.button("🔍 Extract & Translate", use_container_width=True):
            with st.spinner("Reading and translating image text..."):
                try:
                    client = get_client()
                    if client is None:
                        raise RuntimeError("No Gemini API key set yet. Paste your key into the sidebar.")

                    image_bytes = uploaded.getvalue()
                    mime = uploaded.type or "image/png"

                    # Gemini is natively multimodal, so it can read the text
                    # straight out of the image and translate it in one call —
                    # no separate OCR library needed.
                    prompt = (
                        f"Read all visible text in this image, then translate it into {target}. "
                        f'Respond ONLY with JSON: {{"extracted_text": "", "translated_text": ""}}'
                    )
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=[
                            genai_types.Part.from_bytes(data=image_bytes, mime_type=mime),
                            prompt,
                        ],
                        config=genai_types.GenerateContentConfig(
                            temperature=0.2, response_mime_type="application/json",
                        ),
                    )
                    result = _parse_json_loose(response.text or "{}")

                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("**Extracted Text**")
                        st.markdown(f"""<div class="plain-card">{result.get('extracted_text', 'No text detected.')}</div>""", unsafe_allow_html=True)
                    with col2:
                        st.markdown("**Translation**")
                        st.markdown(f"""<div class="result-card">{result.get('translated_text', '—')}</div>""", unsafe_allow_html=True)
                except Exception as e:
                    st.error(str(e))

# ----------------------------------------------------------------------------
# Document Translator
# ----------------------------------------------------------------------------

elif page == "📄 Document Translator":
    st.title("Document Translator")
    st.caption("Translate or summarize a PDF, DOCX, or TXT file.")

    target = st.selectbox("Translate to", LANGUAGES[1:], index=0)
    uploaded = st.file_uploader("Upload document", type=["pdf", "docx", "txt"])

    def extract_text(file) -> str:
        name = file.name.lower()
        data = file.getvalue()
        if name.endswith(".pdf"):
            import fitz  # PyMuPDF
            doc = fitz.open(stream=data, filetype="pdf")
            text = "\n\n".join(page.get_text() for page in doc)
            doc.close()
            return text
        elif name.endswith(".docx"):
            import docx
            d = docx.Document(io.BytesIO(data))
            return "\n".join(p.text for p in d.paragraphs if p.text.strip())
        else:
            return data.decode("utf-8", errors="replace")

    if uploaded:
        col_a, col_b = st.columns(2)
        translate_doc = col_a.button("🌐 Translate Document", use_container_width=True)
        summarize_doc = col_b.button("💡 Summarize", use_container_width=True)

        if translate_doc:
            with st.spinner("Extracting and translating..."):
                try:
                    text = extract_text(uploaded)[:15000]  # guard very long docs
                    result_text = ask_text(
                        f"Translate this into {target}. Respond with ONLY the translated text:\n\n{text}",
                        max_tokens=2000,
                    )
                    st.markdown("#### Translation")
                    st.markdown(f"""<div class="result-card">{result_text}</div>""", unsafe_allow_html=True)
                except Exception as e:
                    st.error(str(e))

        if summarize_doc:
            with st.spinner("Summarizing..."):
                try:
                    text = extract_text(uploaded)[:15000]
                    prompt = f"""Summarize this document.

Document:
\"\"\"{text}\"\"\"

Respond ONLY with JSON: {{"summary": "", "key_points": ["", "", ""]}}"""
                    summary = ask_json(prompt, max_tokens=700)
                    st.markdown("#### Summary")
                    st.markdown(f"""<div class="plain-card">{summary.get('summary','')}</div>""", unsafe_allow_html=True)
                    if summary.get("key_points"):
                        st.markdown("**Key Points**")
                        for k in summary["key_points"]:
                            st.markdown(f"- {k}")
                except Exception as e:
                    st.error(str(e))
