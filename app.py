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
)

# Minimal custom styling
st.markdown("""
<style>
    .block-container { padding-top: 2rem; }
    div[data-testid="stMetric"] {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 12px 16px;
        border: 1px solid #e9ecef;
    }
</style>
""", unsafe_allow_html=True)

st.title("📡 Incident Comms Copilot")
st.caption(
    "Ingest messy incident artifacts. Extract customer-relevant facts. "
    "Generate a status page update — ready for human review."
)

# ---------------------------------------------------------------------------
# Sidebar — ingestion controls
# ---------------------------------------------------------------------------
st.sidebar.header("Load Incident Data")
ingest_mode = st.sidebar.radio(
    "Source",
    ["Sample incident", "Upload files", "Local folder path"],
    index=0,
    help="Start with the built-in sample to see the full pipeline in action.",
)

SAMPLE_DIR = str(Path(__file__).parent / "sample_data")


def load_artifacts():
    """Load artifacts based on selected ingestion mode."""
    if ingest_mode == "Sample incident":
        st.sidebar.success("Using built-in sample: auth-service degradation incident")
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
        st.info("Select a data source in the sidebar to get started.")
    st.stop()

# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------
artifacts = normalize_all(result.artifacts)

# ---------------------------------------------------------------------------
# Ingestion summary metrics
# ---------------------------------------------------------------------------
st.header("Ingestion Summary")
type_counts = defaultdict(int)
for a in artifacts:
    type_counts[a.artifact_type] += 1

m1, m2, m3, m4 = st.columns(4)
m1.metric("Files Loaded", len(artifacts))
m2.metric("Files Skipped", len(result.skipped))
m3.metric("Source Types", len(type_counts))
m4.metric("Total Size", f"{sum(len(a.content) for a in artifacts):,} chars")

# ---------------------------------------------------------------------------
# Artifacts grouped by type
# ---------------------------------------------------------------------------
st.header("Parsed Artifacts")

grouped: dict[str, list[NormalizedArtifact]] = defaultdict(list)
for a in artifacts:
    grouped[a.artifact_type].append(a)

for atype in sorted(grouped.keys()):
    items = grouped[atype]
    icon = ARTIFACT_TYPE_ICONS.get(atype, "📄")
    label = ARTIFACT_TYPE_LABELS.get(atype, atype)
    with st.expander(f"{icon} {label} ({len(items)} file{'s' if len(items) != 1 else ''})", expanded=False):
        for a in items:
            st.markdown(f"**{a.file_name}**  ·  `{len(a.content):,} chars`  ·  First timestamp: `{a.timestamp or '—'}`")
            st.code(a.content[:2000] + ("\n..." if len(a.content) > 2000 else ""), language="text")

if result.skipped:
    with st.expander(f"Skipped files ({len(result.skipped)})"):
        for f in result.skipped:
            st.text(f"⏭️  {f}")

# ---------------------------------------------------------------------------
# Evidence Timeline
# ---------------------------------------------------------------------------
st.header("Evidence Timeline")
timestamped = sorted(
    [a for a in artifacts if a.timestamp],
    key=lambda a: a.timestamp,
)

if timestamped:
    for a in timestamped:
        icon = ARTIFACT_TYPE_ICONS.get(a.artifact_type, "📄")
        st.markdown(f"`{a.timestamp}`  {icon} **{a.file_name}**")
else:
    st.caption("No timestamps detected in the loaded artifacts.")

# ---------------------------------------------------------------------------
# LLM Pipeline
# ---------------------------------------------------------------------------
st.divider()
st.header("AI Analysis")

api_key_set = bool(os.environ.get("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY", None))
if not api_key_set:
    st.warning("Set the `OPENAI_API_KEY` environment variable or Streamlit secret to enable AI analysis.")
    st.stop()

run_pipeline = st.button("Extract Evidence & Generate Update", type="primary", use_container_width=True)

if run_pipeline:
    # Stage 1
    with st.spinner("Stage 1 / 2 — Extracting structured evidence from artifacts..."):
        try:
            evidence = extract_evidence(artifacts)
            st.session_state.evidence = evidence
        except Exception as e:
            st.error(f"Evidence extraction failed: {e}")
            st.stop()

    # Stage 2
    with st.spinner("Stage 2 / 2 — Generating customer-facing status update..."):
        try:
            message = generate_customer_message(evidence)
            st.session_state.message = message
        except Exception as e:
            st.error(f"Message generation failed: {e}")
            st.stop()

    # Validation
    warnings = validate_message(
        message.get("headline", ""),
        message.get("body", ""),
    )
    st.session_state.warnings = warnings

# ---------------------------------------------------------------------------
# Results display
# ---------------------------------------------------------------------------
if "evidence" not in st.session_state:
    st.caption("Click the button above to run the AI pipeline.")
    st.stop()

evidence = st.session_state.evidence

# --- Technical summary (internal) ---
st.subheader("Technical Incident Summary")
tc1, tc2, tc3 = st.columns(3)
tc1.markdown(f"**Severity:** `{evidence.get('severity', '—')}`")
tc2.markdown(f"**Phase:** `{evidence.get('incident_phase', '—')}`")
tc3.markdown(f"**Confidence:** `{evidence.get('confidence', '—')}`")

st.markdown(f"**Title:** {evidence.get('incident_title', '—')}")
st.markdown(f"**Affected Surface:** {evidence.get('affected_surface', '—')}")
st.markdown(f"**Customer Impact:** {evidence.get('customer_impact', '—')}")
st.markdown(f"**Scope:** {evidence.get('known_scope', '—')}")
st.markdown(f"**Trigger:** {evidence.get('what_changed', '—')}")
st.markdown(f"**Mitigation:** {evidence.get('mitigation_status', '—')}")

if evidence.get("open_questions"):
    st.markdown("**Open Questions:**")
    for q in evidence["open_questions"]:
        st.markdown(f"- {q}")

# Two-column fact split
col_int, col_cust = st.columns(2)
with col_int:
    st.markdown("##### 🔒 Internal-Only Facts")
    internal_facts = evidence.get("internal_only_facts", [])
    if internal_facts:
        for fact in internal_facts:
            st.markdown(f"- {fact}")
    else:
        st.caption("None extracted.")

with col_cust:
    st.markdown("##### ✅ Customer-Safe Facts")
    safe_facts = evidence.get("customer_safe_facts", [])
    if safe_facts:
        for fact in safe_facts:
            st.markdown(f"- {fact}")
    else:
        st.caption("None extracted.")

with st.expander("View full extracted JSON"):
    st.json(evidence)

# --- Customer-facing update ---
if "message" in st.session_state:
    st.divider()
    message = st.session_state.message
    phase = message.get("phase", "")

    phase_display = {
        "Investigating": ("🟡", "Investigating"),
        "Identified": ("🟠", "Identified"),
        "Monitoring": ("🔵", "Monitoring"),
        "Resolved": ("🟢", "Resolved"),
    }
    icon, label = phase_display.get(phase, ("⚪", phase))

    st.subheader("Customer Status Update")
    st.markdown(f"### {icon} {message.get('headline', '')}")
    st.markdown(f"**Status:** {label}")
    st.info(message.get("body", ""))
    if message.get("next_update_line"):
        st.caption(message["next_update_line"])

    # --- Validation warnings ---
    if "warnings" in st.session_state and st.session_state.warnings:
        st.subheader("Validation Checks")
        for w in st.session_state.warnings:
            if w.level == "error":
                st.error(f"**{w.category}:** {w.message}  \n↳ {w.suggestion}")
            elif w.level == "warning":
                st.warning(f"**{w.category}:** {w.message}  \n↳ {w.suggestion}")
            else:
                st.info(f"**{w.category}:** {w.message}  \n↳ {w.suggestion}")
    else:
        st.success("All validation checks passed.")

    # --- Edit & export ---
    st.divider()
    st.subheader("Edit & Export")

    default_text = f"{message.get('headline', '')}\n\n"
    default_text += f"Status: {phase}\n\n"
    default_text += message.get("body", "")
    if message.get("next_update_line"):
        default_text += f"\n\n{message['next_update_line']}"

    edited = st.text_area(
        "Edit the final message before publishing:",
        value=default_text,
        height=180,
        key="edited_message",
    )

    c_preview, c_export = st.columns(2)
    with c_preview:
        st.markdown("**Preview:**")
        st.code(edited, language="markdown")
    with c_export:
        st.download_button(
            "Download as Markdown",
            data=edited,
            file_name="incident_update.md",
            mime="text/markdown",
            use_container_width=True,
        )
