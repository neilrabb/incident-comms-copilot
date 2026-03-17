"""Incident Comms Copilot — Streamlit UI with Google Material Design 3 styling."""

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
# Material Design 3 / Google Drive styling
# ---------------------------------------------------------------------------
st.markdown("""
<style>
/* ===== Google Fonts ===== */
@import url('https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700&family=Google+Sans+Text:wght@400;500&family=Roboto+Mono:wght@400;500&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');

/* ===== MD3 Color Tokens ===== */
:root {
    --md-primary: #1a73e8;
    --md-on-primary: #ffffff;
    --md-primary-container: #d3e3fd;
    --md-surface: #ffffff;
    --md-surface-dim: #f8f9fa;
    --md-surface-container: #f1f3f4;
    --md-surface-container-high: #e8eaed;
    --md-on-surface: #1f1f1f;
    --md-on-surface-variant: #5f6368;
    --md-outline: #dadce0;
    --md-outline-variant: #e8eaed;
    --md-error: #d93025;
    --md-error-container: #fce8e6;
    --md-success: #1e8e3e;
    --md-success-container: #e6f4ea;
    --md-warning: #e37400;
    --md-warning-container: #fef7e0;
    --md-info: #1a73e8;
    --md-info-container: #e8f0fe;
    --md-radius-sm: 8px;
    --md-radius-md: 12px;
    --md-radius-lg: 16px;
    --md-radius-full: 100px;
    --md-elevation-1: 0 1px 2px rgba(60,64,67,0.3), 0 1px 3px 1px rgba(60,64,67,0.15);
    --md-elevation-2: 0 1px 2px rgba(60,64,67,0.3), 0 2px 6px 2px rgba(60,64,67,0.15);
}

/* ===== Global Reset ===== */
html, body, [class*="css"] {
    font-family: 'Google Sans Text', 'Google Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    -webkit-font-smoothing: antialiased;
}
.block-container {
    padding: 1.5rem 2.5rem 4rem 2.5rem;
    max-width: 1100px;
}

/* Hide Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
div[data-testid="stToolbar"] { display: none; }

/* ===== Sidebar ===== */
section[data-testid="stSidebar"] {
    background: var(--md-surface);
    border-right: none;
    box-shadow: 1px 0 0 var(--md-outline);
    padding-top: 0.5rem;
}
section[data-testid="stSidebar"] > div { padding-top: 1rem; }

/* ===== Typography ===== */
h1 {
    font-family: 'Google Sans', sans-serif !important;
    font-weight: 500 !important;
    font-size: 1.5rem !important;
    color: var(--md-on-surface) !important;
    letter-spacing: 0;
    line-height: 1.3 !important;
    margin-bottom: 0 !important;
}
h2 {
    font-family: 'Google Sans', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.875rem !important;
    color: var(--md-on-surface-variant) !important;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-top: 2rem !important;
    margin-bottom: 0.75rem !important;
    padding: 0 !important;
    border: none !important;
}
h3 {
    font-family: 'Google Sans', sans-serif !important;
    font-weight: 500 !important;
    font-size: 1rem !important;
    color: var(--md-on-surface) !important;
}

/* ===== Metric Cards ===== */
div[data-testid="stMetric"] {
    background: var(--md-surface);
    border: 1px solid var(--md-outline);
    border-radius: var(--md-radius-md);
    padding: 14px 18px;
    transition: box-shadow 0.2s cubic-bezier(0.4,0,0.2,1);
}
div[data-testid="stMetric"]:hover {
    box-shadow: var(--md-elevation-1);
}
div[data-testid="stMetric"] label {
    font-family: 'Google Sans Text', sans-serif !important;
    font-size: 0.7rem !important;
    font-weight: 500 !important;
    color: var(--md-on-surface-variant) !important;
    text-transform: uppercase;
    letter-spacing: 0.6px;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    font-family: 'Google Sans', sans-serif !important;
    font-size: 1.5rem !important;
    font-weight: 500 !important;
    color: var(--md-on-surface) !important;
}

/* ===== Primary Button — Google style filled ===== */
button[data-testid="stBaseButton-primary"] {
    background: var(--md-primary) !important;
    color: var(--md-on-primary) !important;
    border: none !important;
    border-radius: var(--md-radius-full) !important;
    font-family: 'Google Sans', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.875rem !important;
    padding: 10px 24px !important;
    letter-spacing: 0.25px;
    box-shadow: none !important;
    transition: background 0.2s, box-shadow 0.2s;
}
button[data-testid="stBaseButton-primary"]:hover {
    background: #1765cc !important;
    box-shadow: var(--md-elevation-1) !important;
}
button[data-testid="stBaseButton-primary"]:active {
    background: #185abc !important;
}

/* ===== Secondary / Download Buttons ===== */
button[data-testid="stBaseButton-secondary"],
button[data-testid="stDownloadButton"] button {
    border: 1px solid var(--md-outline) !important;
    border-radius: var(--md-radius-full) !important;
    background: var(--md-surface) !important;
    color: var(--md-primary) !important;
    font-family: 'Google Sans', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.875rem !important;
    transition: background 0.15s;
}
button[data-testid="stBaseButton-secondary"]:hover,
button[data-testid="stDownloadButton"] button:hover {
    background: var(--md-info-container) !important;
}

/* ===== Expanders ===== */
details[data-testid="stExpander"] {
    background: var(--md-surface);
    border: 1px solid var(--md-outline) !important;
    border-radius: var(--md-radius-md) !important;
    margin-bottom: 8px;
    overflow: hidden;
    transition: box-shadow 0.2s;
}
details[data-testid="stExpander"]:hover {
    box-shadow: var(--md-elevation-1);
}
details[data-testid="stExpander"] summary {
    font-family: 'Google Sans Text', sans-serif;
    font-weight: 500;
    font-size: 0.875rem;
    color: var(--md-on-surface);
    padding: 14px 16px;
}

/* ===== Text Input & Text Area ===== */
textarea, input[type="text"] {
    border: 1px solid var(--md-outline) !important;
    border-radius: var(--md-radius-sm) !important;
    font-family: 'Google Sans Text', sans-serif !important;
    font-size: 0.875rem !important;
    padding: 12px !important;
    color: var(--md-on-surface) !important;
    transition: border-color 0.2s;
}
textarea:focus, input[type="text"]:focus {
    border-color: var(--md-primary) !important;
    box-shadow: 0 0 0 2px rgba(26,115,232,0.12) !important;
}

/* ===== Code Blocks ===== */
code {
    background: var(--md-surface-container) !important;
    border-radius: 4px;
    padding: 2px 6px;
    font-family: 'Roboto Mono', monospace !important;
    font-size: 0.8rem;
    color: var(--md-on-surface);
}
pre {
    background: var(--md-surface-dim) !important;
    border: 1px solid var(--md-outline-variant) !important;
    border-radius: var(--md-radius-sm) !important;
}

/* ===== Dividers ===== */
hr {
    border-color: var(--md-outline-variant) !important;
    margin: 1.5rem 0 !important;
}

/* ===== Alert Boxes ===== */
div[data-testid="stAlert"] {
    border-radius: var(--md-radius-sm);
    border: none;
    font-size: 0.85rem;
}

/* ===== Custom Components ===== */

/* --- Nav header --- */
.app-header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding-bottom: 4px;
    margin-bottom: 2px;
}
.app-header-icon {
    width: 36px;
    height: 36px;
    background: var(--md-primary);
    border-radius: var(--md-radius-md);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 18px;
    flex-shrink: 0;
}
.app-header-text {
    font-family: 'Google Sans', sans-serif;
    font-size: 1.375rem;
    font-weight: 500;
    color: var(--md-on-surface);
}
.app-subtitle {
    font-family: 'Google Sans Text', sans-serif;
    font-size: 0.85rem;
    color: var(--md-on-surface-variant);
    line-height: 1.5;
    margin-top: 2px;
}

/* --- Sidebar nav item --- */
.sidebar-label {
    font-family: 'Google Sans', sans-serif;
    font-size: 0.8rem;
    font-weight: 500;
    color: var(--md-on-surface-variant);
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-bottom: 12px;
}
.sidebar-chip {
    background: var(--md-success-container);
    color: var(--md-success);
    font-family: 'Google Sans Text', sans-serif;
    font-size: 0.78rem;
    font-weight: 500;
    padding: 8px 14px;
    border-radius: var(--md-radius-sm);
    margin-top: 8px;
    line-height: 1.4;
}
.sidebar-hint {
    font-family: 'Google Sans Text', sans-serif;
    color: var(--md-on-surface-variant);
    font-size: 0.75rem;
    line-height: 1.55;
    margin-top: 4px;
}

/* --- Section label --- */
.section-label {
    font-family: 'Google Sans', sans-serif;
    font-size: 0.75rem;
    font-weight: 500;
    color: var(--md-on-surface-variant);
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin: 28px 0 12px 0;
    display: flex;
    align-items: center;
    gap: 8px;
}
.section-label .material-symbols-outlined {
    font-size: 18px;
    color: var(--md-on-surface-variant);
}

/* --- Timeline --- */
.tl-container {
    padding: 4px 0 4px 20px;
    border-left: 2px solid var(--md-outline);
    margin-left: 6px;
}
.tl-item {
    position: relative;
    padding: 8px 0 8px 16px;
    display: flex;
    align-items: baseline;
    gap: 14px;
}
.tl-item::before {
    content: '';
    position: absolute;
    left: -27px;
    top: 14px;
    width: 10px;
    height: 10px;
    background: var(--md-primary);
    border-radius: 50%;
    border: 2px solid var(--md-surface);
    box-shadow: 0 0 0 2px var(--md-primary);
}
.tl-time {
    font-family: 'Roboto Mono', monospace;
    font-size: 0.78rem;
    color: var(--md-on-surface-variant);
    white-space: nowrap;
    min-width: 190px;
}
.tl-file {
    font-family: 'Google Sans Text', sans-serif;
    font-weight: 500;
    font-size: 0.875rem;
    color: var(--md-on-surface);
}
.tl-type {
    font-family: 'Google Sans Text', sans-serif;
    font-size: 0.78rem;
    color: var(--md-on-surface-variant);
    background: var(--md-surface-container);
    padding: 2px 8px;
    border-radius: var(--md-radius-full);
}

/* --- Chips / Badges --- */
.chip-row { display: flex; gap: 8px; flex-wrap: wrap; margin: 8px 0 16px 0; }
.md-chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 14px;
    border-radius: var(--md-radius-full);
    font-family: 'Google Sans Text', sans-serif;
    font-size: 0.78rem;
    font-weight: 500;
    border: 1px solid var(--md-outline);
    background: var(--md-surface);
    color: var(--md-on-surface);
}
.md-chip.sev1 { background: var(--md-error-container); color: var(--md-error); border-color: transparent; }
.md-chip.sev2 { background: var(--md-warning-container); color: var(--md-warning); border-color: transparent; }
.md-chip.sev3 { background: var(--md-info-container); color: var(--md-info); border-color: transparent; }
.md-chip.conf-high { background: var(--md-success-container); color: var(--md-success); border-color: transparent; }
.md-chip.conf-medium { background: var(--md-warning-container); color: var(--md-warning); border-color: transparent; }
.md-chip.conf-low { background: var(--md-error-container); color: var(--md-error); border-color: transparent; }

/* --- Summary grid --- */
.sg {
    display: grid;
    grid-template-columns: 100px 1fr;
    gap: 2px 20px;
    font-size: 0.875rem;
    line-height: 1.7;
    margin-top: 12px;
    padding: 16px 20px;
    background: var(--md-surface);
    border: 1px solid var(--md-outline);
    border-radius: var(--md-radius-md);
}
.sg-label {
    font-family: 'Google Sans Text', sans-serif;
    font-weight: 500;
    color: var(--md-on-surface-variant);
    font-size: 0.8rem;
}
.sg-value {
    font-family: 'Google Sans Text', sans-serif;
    color: var(--md-on-surface);
}

/* --- Fact cards --- */
.facts-row { display: flex; gap: 16px; margin-top: 16px; }
.fact-card {
    flex: 1;
    background: var(--md-surface);
    border: 1px solid var(--md-outline);
    border-radius: var(--md-radius-md);
    padding: 18px 20px;
    min-width: 0;
}
.fact-card-header {
    font-family: 'Google Sans', sans-serif;
    font-size: 0.72rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    padding-bottom: 10px;
    margin-bottom: 10px;
    border-bottom: 1px solid var(--md-outline-variant);
    display: flex;
    align-items: center;
    gap: 6px;
}
.fact-card-header.internal { color: var(--md-error); }
.fact-card-header.safe { color: var(--md-success); }
.fact-card-header .material-symbols-outlined { font-size: 16px; }
.fact-item {
    font-family: 'Google Sans Text', sans-serif;
    font-size: 0.84rem;
    color: var(--md-on-surface);
    padding: 5px 0;
    line-height: 1.5;
    display: flex;
    align-items: flex-start;
    gap: 10px;
}
.fact-dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    margin-top: 7px;
    flex-shrink: 0;
}
.fact-dot.internal { background: var(--md-error); }
.fact-dot.safe { background: var(--md-success); }

/* --- Status update card --- */
.status-card {
    background: var(--md-surface);
    border: 1px solid var(--md-outline);
    border-radius: var(--md-radius-lg);
    padding: 28px 32px;
    box-shadow: var(--md-elevation-1);
    margin: 12px 0 20px 0;
}
.status-hl {
    font-family: 'Google Sans', sans-serif;
    font-size: 1.25rem;
    font-weight: 500;
    color: var(--md-on-surface);
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 10px;
}
.phase-badge {
    display: inline-block;
    font-family: 'Google Sans Text', sans-serif;
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding: 3px 12px;
    border-radius: var(--md-radius-full);
    margin-bottom: 16px;
}
.phase-investigating { background: var(--md-warning-container); color: var(--md-warning); }
.phase-identified { background: var(--md-error-container); color: var(--md-error); }
.phase-monitoring { background: var(--md-info-container); color: var(--md-info); }
.phase-resolved { background: var(--md-success-container); color: var(--md-success); }
.status-body {
    font-family: 'Google Sans Text', sans-serif;
    font-size: 0.92rem;
    line-height: 1.75;
    color: var(--md-on-surface);
}
.status-next {
    font-family: 'Google Sans Text', sans-serif;
    font-size: 0.82rem;
    color: var(--md-on-surface-variant);
    font-style: italic;
    margin-top: 14px;
    padding-top: 14px;
    border-top: 1px solid var(--md-outline-variant);
}

/* --- Validation --- */
.v-item {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 10px 14px;
    margin: 6px 0;
    border-radius: var(--md-radius-sm);
    font-family: 'Google Sans Text', sans-serif;
    font-size: 0.84rem;
}
.v-item.v-error { background: var(--md-error-container); }
.v-item.v-warning { background: var(--md-warning-container); }
.v-item.v-info { background: var(--md-info-container); }
.v-icon { font-size: 1rem; flex-shrink: 0; line-height: 1.4; }
.v-body { color: var(--md-on-surface); }
.v-body strong { font-weight: 500; }
.v-hint {
    font-size: 0.78rem;
    color: var(--md-on-surface-variant);
    margin-top: 2px;
}

/* --- Success bar --- */
.pass-bar {
    background: var(--md-success-container);
    border-radius: var(--md-radius-sm);
    padding: 12px 16px;
    color: var(--md-success);
    font-family: 'Google Sans Text', sans-serif;
    font-weight: 500;
    font-size: 0.84rem;
    display: flex;
    align-items: center;
    gap: 8px;
}
.pass-bar .material-symbols-outlined { font-size: 18px; }

/* --- Empty state --- */
.empty-state {
    background: var(--md-surface-dim);
    border: 1px dashed var(--md-outline);
    border-radius: var(--md-radius-lg);
    padding: 48px 24px;
    text-align: center;
    color: var(--md-on-surface-variant);
    font-family: 'Google Sans Text', sans-serif;
    font-size: 0.9rem;
    margin: 24px 0;
}
.empty-state-icon {
    font-size: 2.5rem;
    margin-bottom: 12px;
    opacity: 0.6;
}

/* --- Export row --- */
.export-hint {
    font-family: 'Google Sans Text', sans-serif;
    font-size: 0.78rem;
    color: var(--md-on-surface-variant);
    margin-top: 4px;
}
</style>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" rel="stylesheet" />
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown("""
<div class="app-header">
    <div class="app-header-icon">📡</div>
    <div class="app-header-text">Incident Comms Copilot</div>
</div>
<div class="app-subtitle">
    Ingest incident artifacts &rarr; Extract customer-relevant facts &rarr; Generate a status page update &rarr; Human review
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="sidebar-label">Data Source</div>', unsafe_allow_html=True)
    ingest_mode = st.radio(
        "Source",
        ["Sample incident", "Upload files", "Local folder path"],
        index=0,
        label_visibility="collapsed",
    )
    SAMPLE_DIR = str(Path(__file__).parent / "sample_data")

    if ingest_mode == "Sample incident":
        st.markdown(
            '<div class="sidebar-chip">'
            '<span class="material-symbols-outlined" style="font-size:14px; vertical-align:-2px;">check_circle</span> '
            "Loaded: auth-service degradation scenario</div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown(
        '<div class="sidebar-hint">'
        "Supports .txt .log .md .json .csv .yaml<br>"
        "Binary files are skipped automatically.</div>",
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
        return ingest_uploaded_files(uploaded) if uploaded else None
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
            '<div class="empty-state">'
            '<div class="empty-state-icon">📂</div>'
            "Select a data source in the sidebar to get started.</div>",
            unsafe_allow_html=True,
        )
    st.stop()

# ---------------------------------------------------------------------------
# Parse
# ---------------------------------------------------------------------------
artifacts = normalize_all(result.artifacts)

# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------
st.markdown(
    '<div class="section-label">'
    '<span class="material-symbols-outlined">inventory_2</span> INGESTION</div>',
    unsafe_allow_html=True,
)

type_counts = defaultdict(int)
for a in artifacts:
    type_counts[a.artifact_type] += 1

m1, m2, m3, m4 = st.columns(4)
m1.metric("Files Loaded", len(artifacts))
m2.metric("Skipped", len(result.skipped))
m3.metric("Source Types", len(type_counts))
m4.metric("Total Size", f"{sum(len(a.content) for a in artifacts):,} chars")

# ---------------------------------------------------------------------------
# Artifacts
# ---------------------------------------------------------------------------
st.markdown(
    '<div class="section-label">'
    '<span class="material-symbols-outlined">description</span> ARTIFACTS</div>',
    unsafe_allow_html=True,
)

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
st.markdown(
    '<div class="section-label">'
    '<span class="material-symbols-outlined">timeline</span> TIMELINE</div>',
    unsafe_allow_html=True,
)

timestamped = sorted([a for a in artifacts if a.timestamp], key=lambda a: a.timestamp)

if timestamped:
    tl_html = '<div class="tl-container">'
    for a in timestamped:
        icon = ARTIFACT_TYPE_ICONS.get(a.artifact_type, "📄")
        label = ARTIFACT_TYPE_LABELS.get(a.artifact_type, a.artifact_type)
        tl_html += f"""
        <div class="tl-item">
            <span class="tl-time">{a.timestamp}</span>
            <span class="tl-file">{icon} {a.file_name}</span>
            <span class="tl-type">{label}</span>
        </div>"""
    tl_html += "</div>"
    st.markdown(tl_html, unsafe_allow_html=True)
else:
    st.caption("No timestamps detected.")

# ---------------------------------------------------------------------------
# AI Pipeline
# ---------------------------------------------------------------------------
st.markdown(
    '<div class="section-label">'
    '<span class="material-symbols-outlined">auto_awesome</span> AI ANALYSIS</div>',
    unsafe_allow_html=True,
)

api_key_set = bool(os.environ.get("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY", None))
if not api_key_set:
    st.warning("Set `OPENAI_API_KEY` as an environment variable or Streamlit secret.")
    st.stop()

if st.button("Extract Evidence & Generate Update", type="primary", use_container_width=True):
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

    st.session_state.warnings = validate_message(
        message.get("headline", ""), message.get("body", ""),
    )

# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------
if "evidence" not in st.session_state:
    st.markdown(
        '<div class="empty-state">'
        '<div class="empty-state-icon">'
        '<span class="material-symbols-outlined" style="font-size:2.5rem;">auto_awesome</span></div>'
        "Click the button above to run the two-stage AI pipeline.</div>",
        unsafe_allow_html=True,
    )
    st.stop()

evidence = st.session_state.evidence

# --- Summary ---
st.markdown(
    '<div class="section-label">'
    '<span class="material-symbols-outlined">summarize</span> INCIDENT SUMMARY</div>',
    unsafe_allow_html=True,
)

severity = evidence.get("severity", "Unknown")
phase = evidence.get("incident_phase", "Unknown")
confidence = evidence.get("confidence", "unknown").lower()

sev_class = "sev1" if "1" in severity else "sev2" if "2" in severity else "sev3"
conf_class = f"conf-{confidence}" if confidence in ("high", "medium", "low") else ""

st.markdown(
    f'<div class="chip-row">'
    f'<span class="md-chip {sev_class}">{severity}</span>'
    f'<span class="md-chip">{phase}</span>'
    f'<span class="md-chip {conf_class}">Confidence: {confidence}</span>'
    f'</div>',
    unsafe_allow_html=True,
)

sg = f"""
<div class="sg">
    <div class="sg-label">Title</div><div class="sg-value">{evidence.get('incident_title', '—')}</div>
    <div class="sg-label">Impact</div><div class="sg-value">{evidence.get('customer_impact', '—')}</div>
    <div class="sg-label">Affected</div><div class="sg-value">{evidence.get('affected_surface', '—')}</div>
    <div class="sg-label">Scope</div><div class="sg-value">{evidence.get('known_scope', '—')}</div>
    <div class="sg-label">Trigger</div><div class="sg-value">{evidence.get('what_changed', '—')}</div>
    <div class="sg-label">Mitigation</div><div class="sg-value">{evidence.get('mitigation_status', '—')}</div>
</div>"""
st.markdown(sg, unsafe_allow_html=True)

if evidence.get("open_questions"):
    st.markdown("**Open questions:**")
    for q in evidence["open_questions"]:
        st.markdown(f"- {q}")

# Facts
internal_facts = evidence.get("internal_only_facts", [])
safe_facts = evidence.get("customer_safe_facts", [])

int_items = "".join(
    f'<div class="fact-item"><div class="fact-dot internal"></div>{f}</div>'
    for f in internal_facts
) if internal_facts else '<div style="color:var(--md-on-surface-variant); font-size:0.84rem;">None extracted.</div>'

safe_items = "".join(
    f'<div class="fact-item"><div class="fact-dot safe"></div>{f}</div>'
    for f in safe_facts
) if safe_facts else '<div style="color:var(--md-on-surface-variant); font-size:0.84rem;">None extracted.</div>'

st.markdown(f"""
<div class="facts-row">
    <div class="fact-card">
        <div class="fact-card-header internal">
            <span class="material-symbols-outlined">lock</span> INTERNAL ONLY
        </div>
        {int_items}
    </div>
    <div class="fact-card">
        <div class="fact-card-header safe">
            <span class="material-symbols-outlined">check_circle</span> CUSTOMER SAFE
        </div>
        {safe_items}
    </div>
</div>
""", unsafe_allow_html=True)

with st.expander("Full extracted JSON"):
    st.json(evidence)

# --- Customer update ---
if "message" in st.session_state:
    st.markdown(
        '<div class="section-label">'
        '<span class="material-symbols-outlined">edit_note</span> CUSTOMER STATUS UPDATE</div>',
        unsafe_allow_html=True,
    )

    message = st.session_state.message
    msg_phase = message.get("phase", "")
    phase_class = msg_phase.lower().replace(" ", "-")
    phase_icon = {"Investigating": "🟡", "Identified": "🟠", "Monitoring": "🔵", "Resolved": "🟢"}.get(msg_phase, "⚪")

    next_html = ""
    if message.get("next_update_line"):
        next_html = f'<div class="status-next">{message["next_update_line"]}</div>'

    st.markdown(f"""
    <div class="status-card">
        <div class="status-hl">{phase_icon} {message.get('headline', '')}</div>
        <span class="phase-badge phase-{phase_class}">{msg_phase}</span>
        <div class="status-body">{message.get('body', '')}</div>
        {next_html}
    </div>
    """, unsafe_allow_html=True)

    # Validation
    if "warnings" in st.session_state and st.session_state.warnings:
        st.markdown(
            '<div class="section-label">'
            '<span class="material-symbols-outlined">verified_user</span> VALIDATION</div>',
            unsafe_allow_html=True,
        )
        for w in st.session_state.warnings:
            ic = {"error": "🔴", "warning": "🟡", "info": "🔵"}.get(w.level, "⚪")
            cls = f"v-{w.level}"
            st.markdown(f"""
            <div class="v-item {cls}">
                <span class="v-icon">{ic}</span>
                <div>
                    <div class="v-body"><strong>{w.category}:</strong> {w.message}</div>
                    <div class="v-hint">{w.suggestion}</div>
                </div>
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown(
            '<div class="pass-bar">'
            '<span class="material-symbols-outlined">check_circle</span>'
            'All validation checks passed</div>',
            unsafe_allow_html=True,
        )

    # Edit & Export
    st.markdown(
        '<div class="section-label">'
        '<span class="material-symbols-outlined">edit_document</span> EDIT & EXPORT</div>',
        unsafe_allow_html=True,
    )

    default_text = f"{message.get('headline', '')}\n\nStatus: {msg_phase}\n\n{message.get('body', '')}"
    if message.get("next_update_line"):
        default_text += f"\n\n{message['next_update_line']}"

    edited = st.text_area("Edit", value=default_text, height=180, key="edited_message", label_visibility="collapsed")

    c1, c2, c3 = st.columns([3, 1, 1])
    with c1:
        st.markdown('<div class="export-hint">Edit the text above, then preview or download.</div>', unsafe_allow_html=True)
    with c2:
        st.download_button("Download .md", data=edited, file_name="incident_update.md", mime="text/markdown", use_container_width=True)
    with c3:
        st.download_button("Download .txt", data=edited, file_name="incident_update.txt", mime="text/plain", use_container_width=True)

    with st.expander("Preview"):
        st.code(edited, language="markdown")
