"""
Clinical Note Summariser — W6D1
Pre-Stanmore AI for Biomedical Engineering — Kevin Kirui

Streamlit app: user pastes a clinical note, clicks Summarise, sees structured JSON output from summarise_v2 logic.

Run: streamlit run app.py
"""

import json
import os
import streamlit as st
from openai import OpenAI

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Clinical Note Summariser",
    page_icon="🩺",
    layout="centered",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
/* Import fonts */
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
}

/* App background */
.stApp {
    background-color: #0d1117;
    color: #e6edf3;
}

/* Header */
.header-block {
    border-left: 3px solid #58a6ff;
    padding: 0.4rem 0 0.4rem 1rem;
    margin-bottom: 1.5rem;
}

.header-block h1 {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.4rem;
    font-weight: 600;
    color: #e6edf3;
    margin: 0;
    letter-spacing: -0.02em;
}

.header-block p {
    font-size: 0.82rem;
    color: #8b949e;
    margin: 0.2rem 0 0 0;
}

/* Disclaimer banner */
.disclaimer {
    background: #1a1008;
    border: 1px solid #d29922;
    border-left: 4px solid #d29922;
    border-radius: 4px;
    padding: 0.75rem 1rem;
    margin-bottom: 1.5rem;
    font-size: 0.82rem;
    color: #d29922;
    font-family: 'IBM Plex Mono', monospace;
}

.disclaimer strong {
    color: #f0a500;
}

/* Section labels */
.section-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #8b949e;
    margin-bottom: 0.3rem;
}

/* Output card */
.output-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1rem;
}

.output-card .field-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #58a6ff;
    margin-bottom: 0.35rem;
}

.output-card .field-value {
    font-size: 0.95rem;
    color: #e6edf3;
    line-height: 1.55;
}

/* Caveat box */
.caveat-box {
    background: #0d1117;
    border: 1px solid #30363d;
    border-radius: 4px;
    padding: 0.6rem 0.9rem;
    margin-top: 1rem;
    font-size: 0.78rem;
    color: #6e7681;
    font-family: 'IBM Plex Mono', monospace;
}

/* Button styling override */
.stButton > button {
    background: #1f6feb;
    color: #ffffff;
    border: none;
    border-radius: 4px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.85rem;
    font-weight: 600;
    padding: 0.5rem 1.5rem;
    letter-spacing: 0.04em;
    transition: background 0.15s;
}

.stButton > button:hover {
    background: #388bfd;
    border: none;
}

/* Text area */
.stTextArea textarea {
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    color: #e6edf3 !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.83rem !important;
    border-radius: 4px !important;
}

/* API key input */
.stTextInput input {
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    color: #e6edf3 !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.83rem !important;
    border-radius: 4px !important;
}

/* Error box */
.stAlert {
    border-radius: 4px !important;
}

/* Divider */
hr {
    border-color: #21262d;
}

/* Hide Streamlit chrome */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
""",
    unsafe_allow_html=True,
)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    """
<div class="header-block">
    <h1>🩺 Clinical Note Summariser</h1>
    <p>Pre-Stanmore AI for Biomedical Engineering · Week 6 · Kevin Kirui</p>
</div>
""",
    unsafe_allow_html=True,
)

# ── Disclaimer ────────────────────────────────────────────────────────────────
st.markdown(
    """
<div class="disclaimer">
    <strong>⚠ NOT FOR CLINICAL USE.</strong>&nbsp; This tool is a research prototype built for educational purposes only. Outputs are AI-generated, have not been clinically validated, and <strong>must not be used to inform patient care decisions</strong>. A qualified clinician must review all clinical notes directly.
</div>
""",
    unsafe_allow_html=True,
)

# ── System prompt (summarise_v2 logic) ───────────────────────────────────────
SYSTEM_PROMPT = """You are a clinical documentation assistant. Your task is to read a clinical note and extract three structured fields. Return ONLY a JSON object with exactly these four keys:

"reasoning" - brief internal chain-of-thought (2-3 sentences)
"chief_complaint" - the patient's primary presenting complaint, in plain language
"diagnosis" - the clinician's working or confirmed diagnosis (be specific; do not copy a pre-operative diagnosis if the operative or assessment findings differ)
"plan" - the management or treatment plan, including key medications, procedures, and follow-up steps

Rules:
- Do NOT omit quantitative data (doses, weights, durations, device details)
- For surgical/procedure reports: the diagnosis MUST be derived from operative FINDINGS, not the pre-operative diagnosis. If the pre-op diagnosis listed a condition that was ruled out intraoperatively, state it was excluded.
- If you cannot determine a field with confidence, write "Not specified"
- Return valid JSON only. No markdown, no extra text.

Example 1 — medical note:
Input: "CC: chest pain x 2 days. Assessment: NSTEMI confirmed on troponin. Plan: Heparin 5000u IV bolus, cardiology consult, admit CCU."
Output:
{
    "reasoning": "Patient presents with chest pain; troponin confirms NSTEMI. Plan includes anticoagulation and specialist referral.",
    "chief_complaint": "Chest pain for 2 days",
    "diagnosis": "Non-ST-elevation myocardial infarction (NSTEMI)",
    "plan": "Heparin 5000u IV bolus; cardiology consult; admit to CCU"
}

Example 2 — operative report (pre-op diagnosis differs from operative findings):
Input: "Pre-op diagnosis: suspected appendicitis, possible perforated viscus. Operative findings: 150mL purulent fluid in right iliac fossa; inflamed appendix with contained perforation; no free perforation; remainder of peritoneum clear. Procedure: laparoscopic appendicectomy; peritoneal washout with 2L warm saline; wound closed in layers. Patient tolerated procedure well; transferred to recovery stable."
Output:
{
    "reasoning": "Pre-op listed suspected appendicitis and possible perforated viscus. Operative findings confirmed appendicitis with contained perforation only — no free perforation. Diagnosis must reflect the operative conclusion, not the pre-op suspicion.",
    "chief_complaint": "Suspected appendicitis",
    "diagnosis": "Acute appendicitis with contained perforation (no free perforation confirmed intraoperatively); 150mL purulent collection right iliac fossa",
    "plan": "Laparoscopic appendicectomy; peritoneal washout with 2L warm saline; wound closed in layers; transferred to recovery stable"
}"""

# ── Summarise function ────────────────────────────────────────────────────────
def summarise(note: str, api_key: str) -> dict:
    """Call gpt-4o-mini with the summarise_v2 prompt. Returns parsed dict."""
    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Clinical note:\n\n{note.strip()}"},
        ],
    )

    raw = response.choices[0].message.content
    parsed = json.loads(raw)

    # Strip reasoning from returned payload (internal CoT only)
    return {
        "chief_complaint": parsed.get("chief_complaint", "Not specified"),
        "diagnosis": parsed.get("diagnosis", "Not specified"),
        "plan": parsed.get("plan", "Not specified"),
    }


# ── API key input ─────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">OpenAI API Key</div>', unsafe_allow_html=True)
api_key_input = st.text_input(
    label="api_key",
    label_visibility="collapsed",
    type="password",
    placeholder="sk-...",
    help="Your key is used only for this request and never stored.",
)

# Use env var as fallback (for local dev with OPENAI_API_KEY set)
api_key = api_key_input.strip() or os.environ.get("OPENAI_API_KEY", "")

st.markdown("<br>", unsafe_allow_html=True)

# ── Note input ────────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Clinical Note</div>', unsafe_allow_html=True)
note_text = st.text_area(
    label="clinical_note",
    label_visibility="collapsed",
    placeholder="Paste a clinical note here…\n\nE.g. a discharge summary, operative report, or consultation note from MTSamples.",
    height=220,
)

st.markdown("<br>", unsafe_allow_html=True)

# ── Summarise button ──────────────────────────────────────────────────────────
col1, col2 = st.columns([1, 4])
with col1:
    run = st.button("Summarise →")

# ── Output ────────────────────────────────────────────────────────────────────
if run:
    if not api_key:
        st.error("Please enter your OpenAI API key above.")
    elif not note_text.strip():
        st.error("Please paste a clinical note before clicking Summarise.")
    else:
        with st.spinner("Calling gpt-4o-mini…"):
            try:
                result = summarise(note_text, api_key)

                st.markdown("---")
                st.markdown('<div class="section-label">Structured Output</div>', unsafe_allow_html=True)

                for field, label in [
                    ("chief_complaint", "Chief Complaint"),
                    ("diagnosis", "Diagnosis"),
                    ("plan", "Plan"),
                ]:
                    st.markdown(
                        f"""
<div class="output-card">
    <div class="field-label">{label}</div>
    <div class="field-value">{result[field]}</div>
</div>
""",
                        unsafe_allow_html=True,
                    )

                st.markdown(
                    """
<div class="caveat-box">
    ⚠ AI-generated output · Confidence not guaranteed · Always verify against the original note · Not validated for clinical use
</div>
""",
                    unsafe_allow_html=True,
                )

                # Raw JSON expander for debugging
                with st.expander("Raw JSON"):
                    st.code(json.dumps(result, indent=2), language="json")

            except json.JSONDecodeError as e:
                st.error(f"JSON parsing error: {e}. The model returned an unexpected format.")
            except Exception as e:
                st.error(f"API error: {e}")
