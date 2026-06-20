import streamlit as st
import http.client
import json
import re
from datetime import datetime

# ==============================================================================
# CORE SETUP & INTEGRATION
# ==============================================================================

# Pulling the key securely from Streamlit Secrets so GitHub never blocks your upload
if "GEMINI_API_KEY" in st.secrets:
    API_KEY = st.secrets["GEMINI_API_KEY"]
else:
    API_KEY = "NOT_SET"

GEMINI_HOST = "generativelanguage.googleapis.com"
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_PATH = f"/v1beta/models/{GEMINI_MODEL}:generateContent"

SYSTEM_PROMPT = """You are a brutal, official IELTS examiner with 20 years of experience marking IELTS Writing scripts under strict band descriptors. You do not flatter the candidate. You assess exactly as the real IELTS band descriptors require: Task Achievement/Response, Coherence and Cohesion, Lexical Resource, and Grammatical Range and Accuracy.

You MUST respond using ONLY the following XML tag structure, with no text before or after it, and no markdown code fences around the whole response. Each tag must appear exactly once.

<overall>X.X</overall>
<grammar>X.X</grammar>
<vocab>X.X</vocab>
<cohesion>X.X</cohesion>
<feedback>
Write detailed bullet points (using "- " at the start of each line) covering the core criteria.
</feedback>
<upgrades>
| Weak Word Used | Band 9.0 Alternative | Context Sentence |
|---|---|---|
</upgrades>"""

# ==============================================================================
# API CALL LOGIC
# ==============================================================================

def call_gemini(task_type: str, target_band: float, essay_text: str) -> str:
    """Calls the Gemini API using http.client and returns the raw text response."""
    if API_KEY == "NOT_SET":
        raise RuntimeError("Gemini API Key is missing. Please add GEMINI_API_KEY to your Streamlit Advanced Secrets.")

    user_prompt = (
        f"IELTS Task Type: {task_type}\n"
        f"Candidate Target Band Score: {target_band}\n\n"
        f"Essay to mark:\n\"\"\"\n{essay_text}\n\"\"\""
    )

    payload = {
        "system_instruction": {
            "parts": [{"text": SYSTEM_PROMPT}]
        },
        "contents": [
            {
                "role": "user",
                "parts": [{"text": user_prompt}]
            }
        ],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 4096
        }
    }

    conn = http.client.HTTPSConnection(GEMINI_HOST, timeout=60)
    
    # Passing the new AQ key format securely via standard Authorization headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    try:
        conn.request("POST", GEMINI_PATH, body=json.dumps(payload), headers=headers)
        response = conn.getresponse()
        raw_data = response.read().decode("utf-8")
        status = response.status
        conn.close()
    except Exception as e:
        raise RuntimeError(f"Network error while contacting Gemini API: {e}")

    if status != 200:
        raise RuntimeError(f"Gemini API returned status {status}: {raw_data}")

    try:
        parsed = json.loads(raw_data)
        text_output = parsed["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        raise RuntimeError(f"Could not parse Gemini API response: {e}")

    return text_output

# ==============================================================================
# XML PARSING HELPERS
# ==============================================================================

def extract_tag(tag: str, text: str) -> str:
    pattern = rf"<{tag}>(.*?)</{tag}>"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return ""

def safe_float(value: str, fallback: float = 0.0) -> float:
    try:
        cleaned = re.sub(r"[^0-9.]", "", value)
        return float(cleaned) if cleaned else fallback
    except ValueError:
        return fallback

def parse_gemini_response(raw_text: str) -> dict:
    return {
        "overall": safe_float(extract_tag("overall", raw_text)),
        "grammar": safe_float(extract_tag("grammar", raw_text)),
        "vocab": safe_float(extract_tag("vocab", raw_text)),
        "cohesion": safe_float(extract_tag("cohesion", raw_text)),
        "feedback": extract_tag("feedback", raw_text),
        "upgrades": extract_tag("upgrades", raw_text),
        "raw": raw_text,
    }

# ==============================================================================
# PAGE CONFIG & PREMIUM CSS STYLING
# ==============================================================================

st.set_page_config(
    page_title="IELTS AI Tutor | Premium Band Score Analyzer",
    page_icon="🎓",
    layout="wide",
)

PREMIUM_CSS = """
<style>
    .stApp { background-color: #0e1117; color: #e6edf3; }
    .stButton > button {
        border-radius: 10px; padding: 0.65rem 1.4rem;
        background: linear-gradient(135deg, #38bdf8 0%, #0ea5e9 100%);
        color: #0b1320; font-weight: 700; border: none;
    }
    div[data-testid="stMetric"] {
        background: rgba(56, 189, 248, 0.05);
        border: 1px solid rgba(56, 189, 248, 0.2);
        border-radius: 14px; padding: 1rem;
    }
</style>
"""
st.markdown(PREMIUM_CSS, unsafe_allow_html=True)

if "history" not in st.session_state: st.session_state.history = []
if "last_result" not in st.session_state: st.session_state.last_result = None

st.title("🎓 IELTS AI Tutor Pro")

with st.sidebar:
    st.markdown("## ⚙️ Exam Configuration")
    task_type = st.selectbox("IELTS Task Type", ["Task 1 Academic", "Task 1 General", "Task 2 Essay"], index=2)
    target_band = st.slider("🎯 Target Band Score", 5.0, 9.0, 7.0, 0.5)

essay_text = st.text_area("Paste Your Essay Below", height=250)

if st.button("🚀 Analyze Essay"):
    if not essay_text.strip():
        st.warning("Please paste an essay first.")
    else:
        with st.spinner("The examiner is reading your essay..."):
            try:
                raw_response = call_gemini(task_type, target_band, essay_text)
                result = parse_gemini_response(raw_response)
                st.session_state.last_result = result
                st.success("Analysis complete!")
            except Exception as e:
                st.error(f"Analysis failed: {e}")

if st.session_state.last_result:
    res = st.session_state.last_result
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Overall", f"{res['overall']:.1f}")
    c2.metric("Grammar", f"{res['grammar']:.1f}")
    c3.metric("Vocabulary", f"{res['vocab']:.1f}")
    c4.metric("Cohesion", f"{res['cohesion']:.1f}")
    st.markdown("### Examiner Feedback")
    st.write(res["feedback"])
  