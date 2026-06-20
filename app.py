import streamlit as st
from google import genai
from google.genai import types
import re
from datetime import datetime

# ==============================================================================
# CORE SETUP & INTEGRATION (OFFICIAL SDK PLATFORM)
# ==============================================================================

# Safely pulling the dynamic AQ key from the Streamlit Private Configuration
if "GEMINI_API_KEY" in st.secrets:
    API_KEY = st.secrets["GEMINI_API_KEY"]
else:
    API_KEY = "NOT_SET"

# Initializing the official Google Client framework
client = genai.Client(api_key=API_KEY)
GEMINI_MODEL = "gemini-2.5-flash"

SYSTEM_PROMPT = """You are a brutal, official IELTS examiner with 20 years of experience marking IELTS Writing scripts under strict band descriptors. You do not flatter the candidate. You assess exactly as the real IELTS band descriptors require: Task Achievement/Response, Coherence and Cohesion, Lexical Resource, and Grammatical Range and Accuracy.

You will be given:
- The IELTS Task Type (Task 1 Academic, Task 1 General, or Task 2 Essay)
- The candidate's Target Band Score
- The candidate's essay text

Your job is to mark the essay as strictly and accurately as a real IELTS examiner would, with no grade inflation. Be specific, cite exact phrases from the essay, and be honest even if the score is low.

You MUST respond using ONLY the following XML tag structure, with no text before or after it, and no markdown code fences around the whole response. Each tag must appear exactly once.

<overall>X.X</overall>
<grammar>X.X</grammar>
<vocab>X.X</vocab>
<cohesion>X.X</cohesion>
<feedback>
Write detailed bullet points (using "- " at the start of each line) covering:
- Task Achievement/Response analysis
- Coherence and Cohesion analysis
- Grammatical Range and Accuracy analysis
- Lexical Resource analysis
- What specifically must improve to reach the candidate's target band
Be direct, specific, and quote exact words or sentences from the essay where relevant.
</feedback>
<upgrades>
Produce a Markdown table with this exact header and structure, containing at least 5 rows of real examples taken from the candidate's actual essay:

| Weak Word Used | Band 9.0 Alternative | Context Sentence |
|---|---|---|
| word | alternative | example sentence using the alternative |
</upgrades>

Scores must be valid IELTS band scores in increments of 0.5 (e.g. 5.0, 5.5, 6.0, 6.5, 7.0). Do not output anything outside the tags above."""


# ==============================================================================
# API CALL LOGIC
# ==============================================================================

def call_gemini(task_type: str, target_band: float, essay_text: str) -> str:
    """Calls the Gemini API using the official Google GenAI SDK framework."""
    if API_KEY == "NOT_SET":
        raise RuntimeError("🔑 API Key is missing. Please populate the GEMINI_API_KEY value inside your Streamlit Secret Console.")

    user_prompt = (
        f"IELTS Task Type: {task_type}\n"
        f"Candidate Target Band Score: {target_band}\n\n"
        f"Essay to mark:\n\"\"\"\n{essay_text}\n\"\"\""
    )

    try:
        # The official SDK passes configuration tokens cleanly to prevent service blocks
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.4,
                max_output_tokens=4096
            ),
        )
        if not response.text:
            raise RuntimeError("Received an empty response from the backend framework.")
        return response.text
    except Exception as e:
        raise RuntimeError(f"Google Authorization Link Error: {e}")


# ==============================================================================
# XML PARSING HELPERS
# ==============================================================================

def extract_tag(tag: str, text: str) -> str:
    """Extracts the content between <tag>...</tag> using regex. Returns '' if not found."""
    pattern = rf"<{tag}>(.*?)</{tag}>"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return ""


def safe_float(value: str, fallback: float = 0.0) -> float:
    """Safely converts a band score string to float."""
    try:
        cleaned = re.sub(r"[^0-9.]", "", value)
        return float(cleaned) if cleaned else fallback
    except ValueError:
        return fallback


def parse_gemini_response(raw_text: str) -> dict:
    """Parses the full Gemini response into a structured dictionary."""
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
    initial_sidebar_state="expanded",
)

PREMIUM_CSS = """
<style>
    /* ---- Global app background ---- */
    .stApp {
        background-color: #0e1117;
        color: #e6edf3;
    }

    /* ---- Header / Title styling ---- */
    .ielts-hero {
        padding: 1.6rem 2rem;
        border-radius: 18px;
        background: linear-gradient(135deg, #0f1c2e 0%, #11243a 60%, #0e1117 100%);
        border: 1px solid rgba(56, 189, 248, 0.25);
        box-shadow: 0 0 35px rgba(56, 189, 248, 0.08);
        margin-bottom: 1.5rem;
    }
    .ielts-hero h1 {
        font-size: 2.1rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
        color: #f0f6fc;
        letter-spacing: -0.02em;
    }
    .ielts-hero p {
        color: #94a3b8;
        font-size: 1.0rem;
        margin: 0;
    }
    .ielts-hero .accent {
        color: #38bdf8;
    }

    /* ---- Buttons ---- */
    .stButton > button {
        border-radius: 10px;
        padding: 0.65rem 1.4rem;
        background: linear-gradient(135deg, #38bdf8 0%, #0ea5e9 100%);
        color: #0b1320;
        font-weight: 700;
        border: none;
        box-shadow: 0 4px 14px rgba(56, 189, 248, 0.35);
        transition: transform 0.18s ease, box-shadow 0.18s ease;
    }
    .stButton > button:hover {
        transform: scale(1.035);
        box-shadow: 0 6px 22px rgba(56, 189, 248, 0.55);
        color: #0b1320;
    }
    .stButton > button:active {
        transform: scale(0.98);
    }

    /* ---- Tabs ---- */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        border-bottom: 1px solid rgba(148, 163, 184, 0.15);
    }
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        border-radius: 10px 10px 0 0;
        padding: 0 1.2rem;
        background-color: rgba(56, 189, 248, 0.04);
        color: #94a3b8;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: rgba(56, 189, 248, 0.14) !important;
        color: #38bdf8 !important;
        border-bottom: 2px solid #38bdf8;
    }

    /* ---- Metric cards (glowing KPI scorecards) ---- */
    div[data-testid="stMetric"] {
        background: radial-gradient(circle at top left, rgba(56, 189, 248, 0.10), rgba(14, 17, 23, 0.0));
        border: 1px solid rgba(56, 189, 248, 0.22);
        border-radius: 14px;
        padding: 1.1rem 0.8rem 0.8rem 0.8rem;
        box-shadow: 0 0 18px rgba(56, 189, 248, 0.10);
        transition: box-shadow 0.25s ease, transform 0.25s ease;
    }
    div[data-testid="stMetric"]:hover {
        box-shadow: 0 0 28px rgba(56, 189, 248, 0.28);
        transform: translateY(-2px);
    }
    div[data-testid="stMetricLabel"] {
        color: #94a3b8 !important;
        font-weight: 600;
        text-transform: uppercase;
        font-size: 0.78rem;
        letter-spacing: 0.04em;
    }
    div[data-testid="stMetricValue"] {
        color: #38bdf8 !important;
        font-weight: 800;
    }

    /* ---- Sidebar ---- */
    section[data-testid="stSidebar"] {
        background-color: #0b0f16;
        border-right: 1px solid rgba(56, 189, 248, 0.12);
    }
    section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 {
        color: #38bdf8;
    }

    /* ---- Text areas / inputs ---- */
    .stTextArea textarea {
        background-color: #11161d;
        color: #e6edf3;
        border: 1px solid rgba(148, 163, 184, 0.25);
        border-radius: 12px;
    }
    .stTextArea textarea:focus {
        border: 1px solid #38bdf8;
        box-shadow: 0 0 0 1px #38bdf8;
    }

    /* ---- Feedback card ---- */
    .feedback-card {
        background-color: #11161d;
        border: 1px solid rgba(56, 189, 248, 0.18);
        border-radius: 14px;
        padding: 1.4rem 1.6rem;
        line-height: 1.65;
        color: #e6edf3;
    }
    .feedback-card h4 {
        color: #38bdf8;
        margin-top: 0;
    }

    /* ---- History item card ---- */
    .history-card {
        background-color: #11161d;
        border: 1px solid rgba(148, 163, 184, 0.18);
        border-left: 4px solid #38bdf8;
        border-radius: 10px;
        padding: 0.9rem 1.2rem;
        margin-bottom: 0.7rem;
        transition: transform 0.15s ease, border-color 0.15s ease;
    }
    .history-card:hover {
        transform: translateX(3px);
        border-left-color: #0ea5e9;
    }
    .history-score {
        color: #38bdf8;
        font-weight: 800;
        font-size: 1.3rem;