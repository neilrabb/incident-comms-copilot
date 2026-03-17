# Incident Comms Copilot

A browser-based prototype that ingests messy incident artifacts — alerts, logs, Slack conversations, deploy records, metrics — and generates clear, customer-facing status page updates using a two-stage LLM pipeline with human-in-the-loop review.

## Why this exists

During customer-impacting incidents, engineering and support teams face a communication bottleneck: incident artifacts (alerts, logs, chat threads) are noisy and technical, but customers need clear, timely, non-technical updates. This tool bridges that gap by extracting customer-relevant facts from raw incident data and drafting a status page update that a human can review, edit, and publish.

## How it works

```
Incident Artifacts → Ingest → Parse & Classify → [LLM] Evidence Extraction → [LLM] Message Generation → Validation → Human Review → Export
```

**Two-stage LLM pipeline:**

1. **Evidence Extraction** — Reads all normalized artifacts and produces structured JSON: incident title, severity, phase, customer impact, scope, internal-only facts, and customer-safe facts.
2. **Message Generation** — Takes the structured evidence and generates a status page update with headline, body, phase label, and next-update line. Tone matches the incident phase (Investigating → Resolved).

**Guardrails:** Rule-based validation checks the generated message for internal jargon, system names, speculative root-cause claims, and message length — surfacing warnings before the human publishes.

## Quick start

```bash
pip install -r requirements.txt
export OPENAI_API_KEY=sk-your-key-here
streamlit run app.py
```

The app opens at `http://localhost:8501`.

## Demo walkthrough

1. **Launch** — the app loads with "Sample incident" selected (a realistic auth-service degradation scenario with 5 artifact files).
2. **Review ingestion** — top metrics show files loaded, skipped, source types, and total size. Artifacts are grouped by detected type (Alert, Deployment, Metric, Slack, Postmortem).
3. **Check the timeline** — artifacts sorted by first detected timestamp.
4. **Click "Extract Evidence & Generate Update"** — runs the two-stage LLM pipeline.
5. **Review the technical summary** — structured incident facts including severity, phase, scope, and the internal-vs-customer fact split.
6. **Review the customer update** — a draft status page message with phase indicator, calm professional tone.
7. **Check validation warnings** — any flagged jargon, internal references, or speculation.
8. **Edit and export** — modify the draft in the text area, preview, and download as markdown.

## Project structure

```
app.py          Streamlit UI — full pipeline from ingestion to export
ingest.py       File loading from folder or Streamlit uploads
parse.py        Normalization, timestamp extraction, artifact type classification
prompts.py      LLM prompt templates (evidence extraction + message generation)
llm.py          OpenAI API integration with chunking for large inputs
validate.py     Rule-based guardrails (jargon, internal refs, speculation, length)
utils.py        Timestamp parsing, text truncation, token estimation
sample_data/    5 anonymized incident artifacts for demo
```

## Sample data

The `sample_data/` folder contains a realistic incident scenario (auth-service degradation caused by a Redis migration):

| File | Type | Contents |
|------|------|----------|
| `alerts.json` | Alert | Datadog/PagerDuty alerts for latency spike and error rate |
| `deploy.log` | Deployment | Deploy log showing rollout, failure detection, and rollback |
| `metrics_summary.csv` | Metric | Time-series latency, error rate, and session counts |
| `oncall_slack.txt` | Slack | On-call team conversation during triage and mitigation |
| `postmortem_notes.md` | Postmortem | Post-incident timeline, impact summary, root cause, action items |

## Design decisions

- **Two-stage pipeline** — separating extraction from generation makes each stage's output inspectable and debuggable. The intermediate JSON schema acts as a contract between stages.
- **Chunking** — if total artifact size exceeds context limits, artifacts are chunked and summarized before extraction, so the tool handles large incident datasets.
- **Rule-based validation** — lightweight regex checks catch common leaks (internal service names, @mentions, version numbers) without requiring another LLM call.
- **Human-in-the-loop** — the generated message is always editable before export. The tool drafts; the human decides.
