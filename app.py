import streamlit as st
import http.client
import json
import re
from datetime import datetime

# ==============================================================================
# CORE SETUP & INTEGRATION
# ==============================================================================

API_KEY = "AQ.Ab8RN6IoXLxuInnMJqVshvfm2yvpZsd7zsgSeWISfzxBL2ecMA"

GEMINI_HOST = "generativelanguage.googleapis.com"
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_PATH = f"/v1beta/models/{GEMINI_MODEL}:generateContent?key={API_KEY}"

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
    """Calls the Gemini API using http.client and returns the raw text response."""
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
    headers = {"Content-Type": "application/json"}

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
        raise RuntimeError(f"Could not parse Gemini API response: {e}\nRaw response: {raw_data}")

    return text_output


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
    }
    .history-meta {
        color: #94a3b8;
        font-size: 0.85rem;
    }

    /* ---- Section divider label ---- */
    .section-label {
        color: #38bdf8;
        font-weight: 700;
        font-size: 0.95rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.4rem;
    }

    /* ---- Misc cleanup ---- */
    [data-testid="stExpander"] {
        background-color: #11161d;
        border-radius: 10px;
        border: 1px solid rgba(148, 163, 184, 0.15);
    }
</style>
"""

st.markdown(PREMIUM_CSS, unsafe_allow_html=True)


# ==============================================================================
# SESSION STATE INITIALIZATION
# ==============================================================================

if "history" not in st.session_state:
    st.session_state.history = []

if "last_result" not in st.session_state:
    st.session_state.last_result = None

if "last_task_type" not in st.session_state:
    st.session_state.last_task_type = None


# ==============================================================================
# HERO HEADER
# ==============================================================================

st.markdown(
    """
    <div class="ielts-hero">
        <h1>🎓 IELTS AI Tutor <span class="accent">Pro</span></h1>
        <p>Brutal, examiner-grade feedback powered by Gemini 2.5 Flash — built for candidates who want the <span class="accent">real</span> score, not a comforting one.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ==============================================================================
# SIDEBAR CONTROLS
# ==============================================================================

with st.sidebar:
    st.markdown("## ⚙️ Exam Configuration")
    st.markdown("---")

    task_type = st.selectbox(
        "IELTS Task Type",
        options=["Task 1 Academic", "Task 1 General", "Task 2 Essay"],
        index=2,
        help="Select the writing task category your essay belongs to.",
    )

    target_band = st.slider(
        "🎯 Target Band Score",
        min_value=5.0,
        max_value=9.0,
        value=7.0,
        step=0.5,
        help="The band score you are aiming to achieve.",
    )

    st.markdown("---")
    st.markdown(
        f"""
        <div style="font-size: 0.85rem; color: #94a3b8;">
            Current Task: <span style="color:#38bdf8; font-weight:700;">{task_type}</span><br>
            Target Band: <span style="color:#38bdf8; font-weight:700;">{target_band}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown(
        """
        <div style="font-size: 0.78rem; color: #64748b;">
            Model: gemini-2.5-flash<br>
            Mode: Strict Examiner
        </div>
        """,
        unsafe_allow_html=True,
    )


# ==============================================================================
# MAIN TABS
# ==============================================================================

tab1, tab2, tab3 = st.tabs(
    ["📝 Essay Evaluation", "💡 Vocabulary Upgrades", "📊 Session History"]
)

# ------------------------------------------------------------------------
# TAB 1: ESSAY EVALUATION
# ------------------------------------------------------------------------
with tab1:
    st.markdown('<div class="section-label">Paste Your Essay Below</div>', unsafe_allow_html=True)

    essay_text = st.text_area(
        label="Essay Input",
        height=280,
        placeholder="Paste your full IELTS essay response here...",
        label_visibility="collapsed",
    )

    col_btn, col_count = st.columns([1, 3])
    with col_btn:
        analyze_clicked = st.button("🚀 Analyze Essay", use_container_width=True)
    with col_count:
        word_count = len(essay_text.split()) if essay_text else 0
        st.markdown(
            f"<div style='padding-top: 0.6rem; color: #94a3b8;'>Word count: <span style='color:#38bdf8; font-weight:700;'>{word_count}</span></div>",
            unsafe_allow_html=True,
        )

    if analyze_clicked:
        if not essay_text or not essay_text.strip():
            st.warning("⚠️ Please paste an essay before requesting an analysis.")
        elif API_KEY == "YOUR_GEMINI_API_KEY_HERE":
            st.error("🔑 Please set your Gemini API_KEY at the top of app.py before using the analyzer.")
        else:
            with st.spinner("🧐 The examiner is reading your essay closely... grading rigorously..."):
                try:
                    raw_response = call_gemini(task_type, target_band, essay_text)
                    result = parse_gemini_response(raw_response)
                    st.session_state.last_result = result
                    st.session_state.last_task_type = task_type

                    st.session_state.history.append(
                        {
                            "title": f"{task_type} Submission",
                            "task_type": task_type,
                            "target_band": target_band,
                            "overall": result["overall"],
                            "grammar": result["grammar"],
                            "vocab": result["vocab"],
                            "cohesion": result["cohesion"],
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        }
                    )
                    st.success("✅ Analysis complete. Scroll down for your scorecard.")
                except RuntimeError as e:
                    st.error(f"❌ Analysis failed: {e}")

    # Display results if available
    if st.session_state.last_result:
        result = st.session_state.last_result
        st.markdown("---")
        st.markdown('<div class="section-label">Examiner Scorecard</div>', unsafe_allow_html=True)

        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        with kpi1:
            st.metric("Overall Band", f"{result['overall']:.1f}")
        with kpi2:
            st.metric("Grammar", f"{result['grammar']:.1f}")
        with kpi3:
            st.metric("Vocabulary", f"{result['vocab']:.1f}")
        with kpi4:
            st.metric("Cohesion", f"{result['cohesion']:.1f}")

        st.markdown("---")
        st.markdown('<div class="section-label">Detailed Examiner Feedback</div>', unsafe_allow_html=True)

        feedback_html = result["feedback"] if result["feedback"] else "_No feedback was returned. Please try again._"
        st.markdown(
            f"""
            <div class="feedback-card">
                {feedback_html.replace(chr(10), "<br>")}
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.info("👆 Paste an essay above and click **Analyze Essay** to receive your band score breakdown.")


# ------------------------------------------------------------------------
# TAB 2: VOCABULARY UPGRADES
# ------------------------------------------------------------------------
with tab2:
    st.markdown('<div class="section-label">Lexical Resource Upgrade Table</div>', unsafe_allow_html=True)
    st.caption("Weak or repetitive words detected in your essay, mapped to Band 9.0-level alternatives with example usage.")

    if st.session_state.last_result and st.session_state.last_result.get("upgrades"):
        st.markdown(st.session_state.last_result["upgrades"])
    else:
        st.info("💡 Run an analysis in the **Essay Evaluation** tab to generate your personalized vocabulary upgrade table.")


# ------------------------------------------------------------------------
# TAB 3: SESSION HISTORY
# ------------------------------------------------------------------------
with tab3:
    st.markdown('<div class="section-label">Your Session Progress</div>', unsafe_allow_html=True)

    if not st.session_state.history:
        st.info("📭 No submissions yet this session. Analyze an essay to start tracking your progress.")
    else:
        avg_score = sum(item["overall"] for item in st.session_state.history) / len(st.session_state.history)
        best_score = max(item["overall"] for item in st.session_state.history)

        stat1, stat2, stat3 = st.columns(3)
        with stat1:
            st.metric("Total Submissions", len(st.session_state.history))
        with stat2:
            st.metric("Average Band", f"{avg_score:.1f}")
        with stat3:
            st.metric("Best Band", f"{best_score:.1f}")

        st.markdown("---")

        for idx, item in enumerate(reversed(st.session_state.history), start=1):
            st.markdown(
                f"""
                <div class="history-card">
                    <div style="display:flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-weight:700; color:#e6edf3;">{item['title']}</div>
                            <div class="history-meta">{item['timestamp']} &nbsp;•&nbsp; Target: Band {item['target_band']}</div>
                            <div class="history-meta">Grammar {item['grammar']:.1f} · Vocab {item['vocab']:.1f} · Cohesion {item['cohesion']:.1f}</div>
                        </div>
                        <div class="history-score">{item['overall']:.1f}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("---")
        if st.button("🗑️ Clear History"):
            st.session_state.history = []
            st.rerun()