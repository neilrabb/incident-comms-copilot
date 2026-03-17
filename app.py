"""Incident Comms Copilot — Streamlit UI."""

import os
import json
import streamlit as st
from pathlib import Path
from collections import defaultdict

from ingest import ingest_folder, ingest_uploaded_files
from parse import normalize_all, NormalizedArtifact, ARTIFACT_TYPE_LABELS, ARTIFACT_TYPE_ICONS
from llm import extract_evidence, generate_customer_message
from validate import validate_message

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Incident Comms Copilot",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Google-Drive-inspired styling
# ---------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;600&family=Inter:wght@400;500;600&display=swap');

/* Global */
html, body, [class*="css"] {
    font-family: 'Inter', 'Google Sans', -apple-system, BlinkMacSystemFont, sans-serif;
}
.block-container {
    padding: 2rem 2.5rem 3rem 2.5rem;
    max-width: 1200px;
}

/* Hide default Streamlit branding */
#MainMenu, footer, header {visibility: hidden;}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #f8f9fa;
    border-right: 1px solid #e8eaed;
}
section[data-testid="stSidebar"] .stRadio > label {
    font-weight: 500;
}

/* Cards / Metrics */
div[data-testid="stMetric"] {
    background: #ffffff;
    border: 1px solid #e8eaed;
    border-radius: 12px;
    padding: 16px 20px;
    box-shadow: 0 1px 3px rgba(60,64,67,0.08);
    transition: box-shadow 0.2s;
}
div[data-testid="stMetric"]:hover {
    box-shadow: 0 1px 6px rgba(60,64,67,0.15);
}
div[data-testid="stMetric"] label {
    font-size: 0.75rem;
    font-weight: 500;
    color: #5f6368;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    font-size: 1.75rem;
    font-weight: 600;
    color: #202124;
}

/* Headings */
h1 {
    font-weight: 600 !important;
    color: #202124 !important;
    font-size: 1.75rem !important;
    letter-spacing: -0.3px;
}
h2 {
    font-weight: 500 !important;
    color: #202124 !important;
    font-size: 1.15rem !important;
    padding-bottom: 8px;
    border-bottom: 1px solid #e8eaed;
    margin-top: 2rem !important;
}
h3 {
    font-weight: 500 !important;
    color: #202124 !important;
    font-size: 1.05rem !important;
}

/* Expanders */
details[data-testid="stExpander"] {
    background: #ffffff;
    border: 1px solid #e8eaed !important;
    border-radius: 12px !important;
    box-shadow: 0 1px 2px rgba(60,64,67,0.06);
    margin-bottom: 8px;
}
details[data-testid="stExpander"] summary {
    font-weight: 500;
    color: #202124;
    padding: 12px 16px;
}

/* Buttons */
button[data-testid="stBaseButton-primary"] {
    background: #1a73e8 !important;
    border: none !important;
    border-radius: 24px !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
    padding: 10px 24px !important;
    letter-spacing: 0.2px;
    box-shadow: 0 1px 3px rgba(26,115,232,0.3);
    transition: background 0.2s, box-shadow 0.2s;
}
button[data-testid="stBaseButton-primary"]:hover {
    background: #1765cc !important;
    box-shadow: 0 2px 6px rgba(26,115,232,0.4);
}
button[data-testid="stBaseButton-secondary"] {
    border-radius: 24px !important;
    border: 1px solid #dadce0 !important;
    font-weight: 500 !important;
    color: #1a73e8 !important;
    transition: background 0.15s;
}
button[data-testid="stBaseButton-secondary"]:hover {
    background: #f0f6ff !important;
}

/* Text area */
textarea {
    border: 1px solid #dadce0 !important;
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.9rem !important;
    padding: 12px !important;
    transition: border-color 0.2s;
}
textarea:focus {
    border-color: #1a73e8 !important;
    box-shadow: 0 0 0 2px rgba(26,115,232,0.15) !important;
}

/* Code blocks */
code {
    background: #f1f3f4 !important;
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 0.82rem;
    color: #37474f;
}
pre {
    background: #f8f9fa !important;
    border: 1px solid #e8eaed !important;
    border-radius: 8px !important;
}

/* Dividers */
hr {
    border-color: #e8eaed !important;
    margin: 1.5rem 0 !important;
}

/* Alert boxes */
div[data-testid="stAlert"] {
    border-radius: 8px;
    border: none;
    font-size: 0.88rem;
}

/* Dataframe */
div[data-testid="stDataFrame"] {
    border: 1px solid #e8eaed;
    border-radius: 8px;
    overflow: hidden;
}

/* Download button */
button[data-testid="stDownloadButton"] > button {
    border-radius: 24px !important;
}

/* Timeline items */
.timeline-item {
    display: flex;
    align-items: flex-start;
    padding: 10px 16px;
    margin: 0;
    border-left: 2px solid #dadce0;
    margin-left: 8px;
    font-size: 0.9rem;
}
.timeline-item:last-child {
    border-left-color: transparent;
}
.timeline-dot {
    width: 10px;
    height: 10px;
    background: #1a73e8;
    border-radius: 50%;
    margin-left: -22px;
    margin-right: 12px;
    margin-top: 5px;
    flex-shrink: 0;
}
.timeline-time {
    color: #5f6368;
    font-size: 0.8rem;
    font-family: 'Roboto Mono', monospace;
    min-width: 180px;
    flex-shrink: 0;
}
.timeline-label {
    color: #202124;
    font-weight: 500;
}
.timeline-type {
    color: #5f6368;
    font-size: 0.8rem;
    margin-left: 6px;
}

/* Fact cards */
.fact-card {
    background: #ffffff;
    border: 1px solid #e8eaed;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 1px 3px rgba(60,64,67,0.08);
    height: 100%;
}
.fact-card h4 {
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid #e8eaed;
}
.fact-card.internal h4 { color: #d93025; }
.fact-card.safe h4 { color: #1e8e3e; }
.fact-item {
    padding: 6px 0;
    font-size: 0.88rem;
    color: #3c4043;
    line-height: 1.5;
}
.fact-item::before {
    content: '';
    display: inline-block;
    width: 6px;
    height: 6px;
    border-radius: 50%;
    margin-right: 10px;
    vertical-align: middle;
}
.fact-card.internal .fact-item::before { background: #d93025; }
.fact-card.safe .fact-item::before { background: #1e8e3e; }

/* Status update card */
.status-card {
    background: #ffffff;
    border: 1px solid #e8eaed;
    border-radius: 12px;
    padding: 24px 28px;
    box-shadow: 0 1px 4px rgba(60,64,67,0.1);
    margin: 12px 0;
}
.status-headline {
    font-size: 1.2rem;
    font-weight: 600;
    color: #202124;
    margin-bottom: 6px;
}
.status-phase {
    display: inline-block;
    padding: 3px 12px;
    border-radius: 16px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 14px;
}
.phase-investigating { background: #fef7e0; color: #e37400; }
.phase-identified { background: #fce8e6; color: #c5221f; }
.phase-monitoring { background: #e8f0fe; color: #1a73e8; }
.phase-resolved { background: #e6f4ea; color: #1e8e3e; }
.status-body {
    font-size: 0.95rem;
    line-height: 1.7;
    color: #3c4043;
}
.status-next {
    font-size: 0.85rem;
    color: #5f6368;
    font-style: italic;
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px solid #f1f3f4;
}

/* Validation card */
.validation-item {
    display: flex;
    align-items: flex-start;
    padding: 10px 14px;
    margin: 6px 0;
    border-radius: 8px;
    font-size: 0.88rem;
}
.validation-item.error { background: #fce8e6; }
.validation-item.warning { background: #fef7e0; }
.validation-item.info { background: #e8f0fe; }
.validation-icon { margin-right: 10px; flex-shrink: 0; font-size: 1rem; }
.validation-text { color: #3c4043; }
.validation-text strong { color: #202124; }
.validation-suggestion { color: #5f6368; font-size: 0.82rem; margin-top: 2px; }

/* Summary grid */
.summary-grid {
    display: grid;
    grid-template-columns: 120px 1fr;
    gap: 6px 16px;
    font-size: 0.9rem;
    line-height: 1.6;
}
.summary-label {
    color: #5f6368;
    font-weight: 500;
}
.summary-value {
    color: #202124;
}

/* Chip / badge */
.chip {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 0.78rem;
    font-weight: 500;
    background: #e8eaed;
    color: #3c4043;
    margin-right: 4px;
}
.chip.sev1 { background: #fce8e6; color: #c5221f; }
.chip.sev2 { background: #fef7e0; color: #e37400; }
.chip.sev3 { background: #e8f0fe; color: #1a73e8; }
.chip.high { background: #e6f4ea; color: #1e8e3e; }
.chip.medium { background: #fef7e0; color: #e37400; }
.chip.low { background: #fce8e6; color: #c5221f; }

/* Success bar */
.success-bar {
    background: #e6f4ea;
    border-radius: 8px;
    padding: 12px 16px;
    color: #1e8e3e;
    font-weight: 500;
    font-size: 0.88rem;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown("# Incident Comms Copilot")
st.markdown(
    '<span style="color:#5f6368; font-size:0.95rem;">'
    "Ingest incident artifacts &rarr; Extract customer-relevant facts &rarr; "
    "Generate a status page update &rarr; Human review"
    "</span>",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        '<div style="padding:4px 0 16px 0; font-size:1.1rem; font-weight:600; color:#202124;">'
        "Data Source</div>",
        unsafe_allow_html=True,
    )
    ingest_mode = st.radio(
        "Source",
        ["Sample incident", "Upload files", "Local folder path"],
        index=0,
        label_visibility="collapsed",
    )

    SAMPLE_DIR = str(Path(__file__).parent / "sample_data")

    if ingest_mode == "Sample incident":
        st.markdown(
            '<div style="background:#e6f4ea; border-radius:8px; padding:10px 14px; '
            'color:#1e8e3e; font-size:0.82rem; font-weight:500; margin-top:8px;">'
            "Loaded: auth-service degradation scenario</div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown(
        '<div style="color:#5f6368; font-size:0.78rem; line-height:1.5;">'
        "Supports .txt, .log, .md, .json, .csv, .yaml<br>"
        "Binary files are skipped automatically."
        "</div>",
        unsafe_allow_html=True,
    )


def load_artifacts():
    if ingest_mode == "Sample incident":
        return ingest_folder(SAMPLE_DIR)
    elif ingest_mode == "Upload files":
        uploaded = st.sidebar.file_uploader(
            "Upload incident artifacts",
            accept_multiple_files=True,
            type=["txt", "log", "md", "json", "csv", "yaml", "yml"],
        )
        if uploaded:
            return ingest_uploaded_files(uploaded)
        return None
    else:
        folder = st.sidebar.text_input("Folder path", placeholder="/path/to/incident/data")
        if folder and os.path.isdir(folder):
            return ingest_folder(folder)
        elif folder:
            st.sidebar.error("Invalid directory path.")
        return None


result = load_artifacts()

if result is None or not result.artifacts:
    if ingest_mode == "Sample incident":
        st.error("Could not load sample data. Ensure `sample_data/` directory exists.")
    else:
        st.markdown(
            '<div style="background:#f8f9fa; border:1px solid #e8eaed; border-radius:12px; '
            'padding:40px; text-align:center; color:#5f6368; margin-top:40px;">'
            '<div style="font-size:2rem; margin-bottom:12px;">📂</div>'
            "Select a data source in the sidebar to get started."
            "</div>",
            unsafe_allow_html=True,
        )
    st.stop()

# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------
artifacts = normalize_all(result.artifacts)

# ---------------------------------------------------------------------------
# Metrics row
# ---------------------------------------------------------------------------
st.markdown("## Ingestion")
type_counts = defaultdict(int)
for a in artifacts:
    type_counts[a.artifact_type] += 1
total_chars = sum(len(a.content) for a in artifacts)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Files Loaded", len(artifacts))
m2.metric("Skipped", len(result.skipped))
m3.metric("Source Types", len(type_counts))
m4.metric("Total Size", f"{total_chars:,} chars")

# ---------------------------------------------------------------------------
# Artifacts grouped by type
# ---------------------------------------------------------------------------
st.markdown("## Artifacts")

grouped: dict[str, list[NormalizedArtifact]] = defaultdict(list)
for a in artifacts:
    grouped[a.artifact_type].append(a)

for atype in sorted(grouped.keys()):
    items = grouped[atype]
    icon = ARTIFACT_TYPE_ICONS.get(atype, "📄")
    label = ARTIFACT_TYPE_LABELS.get(atype, atype)
    with st.expander(f"{icon}  {label}  ·  {len(items)} file{'s' if len(items) != 1 else ''}"):
        for a in items:
            st.markdown(
                f"**{a.file_name}** &nbsp;&middot;&nbsp; "
                f"`{len(a.content):,} chars` &nbsp;&middot;&nbsp; "
                f"Timestamp: `{a.timestamp or 'none detected'}`"
            )
            st.code(a.content[:2000] + ("\n..." if len(a.content) > 2000 else ""), language="text")

if result.skipped:
    with st.expander(f"Skipped  ·  {len(result.skipped)} files"):
        for f in result.skipped:
            st.caption(f)

# ---------------------------------------------------------------------------
# Timeline
# ---------------------------------------------------------------------------
st.markdown("## Timeline")
timestamped = sorted(
    [a for a in artifacts if a.timestamp],
    key=lambda a: a.timestamp,
)

if timestamped:
    timeline_html = ""
    for a in timestamped:
        icon = ARTIFACT_TYPE_ICONS.get(a.artifact_type, "📄")
        label = ARTIFACT_TYPE_LABELS.get(a.artifact_type, a.artifact_type)
        timeline_html += f"""
        <div class="timeline-item">
            <div class="timeline-dot"></div>
            <span class="timeline-time">{a.timestamp}</span>
            <span class="timeline-label">{icon} {a.file_name}</span>
            <span class="timeline-type">{label}</span>
        </div>"""
    st.markdown(timeline_html, unsafe_allow_html=True)
else:
    st.caption("No timestamps detected in artifacts.")

# ---------------------------------------------------------------------------
# LLM Pipeline
# ---------------------------------------------------------------------------
st.markdown("## AI Analysis")

api_key_set = bool(os.environ.get("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY", None))
if not api_key_set:
    st.warning("Set `OPENAI_API_KEY` as an environment variable or Streamlit secret.")
    st.stop()

run_pipeline = st.button("Extract Evidence & Generate Update", type="primary", use_container_width=True)

if run_pipeline:
    with st.spinner("Stage 1 / 2 — Extracting structured evidence..."):
        try:
            evidence = extract_evidence(artifacts)
            st.session_state.evidence = evidence
        except Exception as e:
            st.error(f"Evidence extraction failed: {e}")
            st.stop()

    with st.spinner("Stage 2 / 2 — Generating customer update..."):
        try:
            message = generate_customer_message(evidence)
            st.session_state.message = message
        except Exception as e:
            st.error(f"Message generation failed: {e}")
            st.stop()

    warnings = validate_message(
        message.get("headline", ""),
        message.get("body", ""),
    )
    st.session_state.warnings = warnings

# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------
if "evidence" not in st.session_state:
    st.markdown(
        '<div style="background:#f8f9fa; border:1px solid #e8eaed; border-radius:12px; '
        'padding:32px; text-align:center; color:#5f6368;">'
        "Click the button above to run the two-stage AI pipeline."
        "</div>",
        unsafe_allow_html=True,
    )
    st.stop()

evidence = st.session_state.evidence

# --- Technical summary ---
st.markdown("## Incident Summary")

severity = evidence.get("severity", "Unknown")
phase = evidence.get("incident_phase", "Unknown")
confidence = evidence.get("confidence", "Unknown")

sev_class = "sev1" if "1" in severity else "sev2" if "2" in severity else "sev3"
conf_class = confidence.lower() if confidence.lower() in ("high", "medium", "low") else ""

chips_html = (
    f'<span class="chip {sev_class}">{severity}</span>'
    f'<span class="chip">{phase}</span>'
    f'<span class="chip {conf_class}">Confidence: {confidence}</span>'
)
st.markdown(chips_html, unsafe_allow_html=True)

summary_html = f"""
<div class="summary-grid" style="margin-top:16px;">
    <div class="summary-label">Title</div>
    <div class="summary-value">{evidence.get('incident_title', '—')}</div>
    <div class="summary-label">Impact</div>
    <div class="summary-value">{evidence.get('customer_impact', '—')}</div>
    <div class="summary-label">Affected</div>
    <div class="summary-value">{evidence.get('affected_surface', '—')}</div>
    <div class="summary-label">Scope</div>
    <div class="summary-value">{evidence.get('known_scope', '—')}</div>
    <div class="summary-label">Trigger</div>
    <div class="summary-value">{evidence.get('what_changed', '—')}</div>
    <div class="summary-label">Mitigation</div>
    <div class="summary-value">{evidence.get('mitigation_status', '—')}</div>
</div>
"""
st.markdown(summary_html, unsafe_allow_html=True)

if evidence.get("open_questions"):
    st.markdown("**Open questions:**")
    for q in evidence["open_questions"]:
        st.markdown(f"- {q}")

# Fact split
st.markdown("", unsafe_allow_html=True)  # spacing
col_int, col_cust = st.columns(2)

with col_int:
    internal_facts = evidence.get("internal_only_facts", [])
    facts_html = '<div class="fact-card internal"><h4>Internal Only</h4>'
    if internal_facts:
        for f in internal_facts:
            facts_html += f'<div class="fact-item">{f}</div>'
    else:
        facts_html += '<div style="color:#5f6368; font-size:0.85rem;">None extracted.</div>'
    facts_html += "</div>"
    st.markdown(facts_html, unsafe_allow_html=True)

with col_cust:
    safe_facts = evidence.get("customer_safe_facts", [])
    facts_html = '<div class="fact-card safe"><h4>Customer Safe</h4>'
    if safe_facts:
        for f in safe_facts:
            facts_html += f'<div class="fact-item">{f}</div>'
    else:
        facts_html += '<div style="color:#5f6368; font-size:0.85rem;">None extracted.</div>'
    facts_html += "</div>"
    st.markdown(facts_html, unsafe_allow_html=True)

with st.expander("Full extracted JSON"):
    st.json(evidence)

# --- Customer update ---
if "message" in st.session_state:
    st.markdown("## Customer Status Update")
    message = st.session_state.message
    msg_phase = message.get("phase", "")

    phase_class = {
        "Investigating": "phase-investigating",
        "Identified": "phase-identified",
        "Monitoring": "phase-monitoring",
        "Resolved": "phase-resolved",
    }.get(msg_phase, "")

    phase_icon = {
        "Investigating": "🟡",
        "Identified": "🟠",
        "Monitoring": "🔵",
        "Resolved": "🟢",
    }.get(msg_phase, "⚪")

    next_line_html = ""
    if message.get("next_update_line"):
        next_line_html = f'<div class="status-next">{message["next_update_line"]}</div>'

    status_html = f"""
    <div class="status-card">
        <div class="status-headline">{phase_icon} {message.get('headline', '')}</div>
        <span class="status-phase {phase_class}">{msg_phase}</span>
        <div class="status-body">{message.get('body', '')}</div>
        {next_line_html}
    </div>
    """
    st.markdown(status_html, unsafe_allow_html=True)

    # --- Validation ---
    if "warnings" in st.session_state and st.session_state.warnings:
        st.markdown("### Validation")
        for w in st.session_state.warnings:
            level_class = w.level
            icon = {"error": "🔴", "warning": "🟡", "info": "🔵"}.get(w.level, "⚪")
            v_html = f"""
            <div class="validation-item {level_class}">
                <span class="validation-icon">{icon}</span>
                <div>
                    <div class="validation-text"><strong>{w.category}:</strong> {w.message}</div>
                    <div class="validation-suggestion">{w.suggestion}</div>
                </div>
            </div>"""
            st.markdown(v_html, unsafe_allow_html=True)
    else:
        st.markdown('<div class="success-bar">All validation checks passed</div>', unsafe_allow_html=True)

    # --- Edit & export ---
    st.markdown("## Edit & Export")

    default_text = f"{message.get('headline', '')}\n\n"
    default_text += f"Status: {msg_phase}\n\n"
    default_text += message.get("body", "")
    if message.get("next_update_line"):
        default_text += f"\n\n{message['next_update_line']}"

    edited = st.text_area(
        "Edit before publishing",
        value=default_text,
        height=180,
        key="edited_message",
        label_visibility="collapsed",
    )

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        st.markdown(
            '<span style="color:#5f6368; font-size:0.82rem;">Edit the text above, then preview or download.</span>',
            unsafe_allow_html=True,
        )
    with c2:
        st.download_button(
            "Download .md",
            data=edited,
            file_name="incident_update.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with c3:
        st.download_button(
            "Download .txt",
            data=edited,
            file_name="incident_update.txt",
            mime="text/plain",
            use_container_width=True,
        )

    with st.expander("Preview"):
        st.code(edited, language="markdown")
