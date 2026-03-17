# Demo Script — Incident Comms Copilot (~5 minutes)

> Intended for a screen-recorded walkthrough. Timings are approximate.
> Have the Streamlit app running at localhost:8501 before you start recording.

---

## [0:00–0:45] The Problem & Product Thinking

**Say something like:**

"During customer-impacting incidents, there's a communication bottleneck that costs real trust. Engineers are deep in triage — reading alerts, checking dashboards, coordinating in Slack — and the last thing they want to do is context-switch to write a polished status page update. But customers are waiting. Every minute without communication erodes confidence.

The result is predictable: updates are delayed, inconsistent in tone, sometimes overshare internal details like service names or deploy versions, and sometimes undersell the actual impact. This is a workflow problem that AI is well-suited to solve — not by replacing human judgment, but by doing the heavy lifting of reading noisy technical artifacts and drafting a clear first pass that a human can review and publish.

That's what Incident Comms Copilot does. I scoped it as a one-day prototype to validate one core hypothesis: can an LLM reliably extract customer-relevant facts from raw incident data and produce a status page update that's safe to publish with light human editing?"

---

## [0:45–1:30] Architecture & AI Approach

**Say something like:**

"Let me walk through the architecture before I show the demo.

The pipeline has five stages. First, ingestion — the tool loads incident artifacts from a folder. These can be any mix of alerts, logs, deploy records, metrics CSVs, Slack exports. It supports common text formats and skips binaries gracefully.

Second, parsing — each file gets normalized into a common schema and classified by type using lightweight heuristics. No LLM needed here — just pattern matching on filenames and content structure.

Third, and this is where AI comes in — evidence extraction. A single LLM call reads all the normalized artifacts and outputs structured JSON: incident title, severity, phase, customer impact, scope, and critically, a split between internal-only facts and customer-safe facts. This separation is the key design choice — it forces the model to think about what's appropriate for external communication before any message gets written.

Fourth — message generation. A second LLM call takes that structured JSON and produces a status page update: headline, body, and phase label. The prompt constrains the model to write in plain language, avoid internal details, avoid speculation, and match the tone to the incident phase.

Fifth — rule-based validation. Before the human sees the draft, regex checks scan for leaked internal terms, service names, @mentions, version numbers, and speculative root-cause language. These show up as warnings in the UI.

I deliberately chose a two-stage pipeline over a single prompt because it gives you inspectability — you can see exactly what facts the model extracted before it writes the message. And the intermediate JSON acts as a contract: if extraction is wrong, you fix it there, not in the prose."

**While saying this:** scroll slowly through the app so the viewer can see the UI sections, or show a simple architecture diagram if you made one.

---

## [1:30–3:30] Live Demo

**Say something like:**

"Let me show it working. The app is loaded with a sample incident — a realistic auth-service degradation scenario with five artifact files."

### Show ingestion (15 sec)
- Point to the top metrics: "5 files loaded, 4 source types detected, about 5,000 characters of raw incident data."
- Expand one artifact group briefly: "Artifacts are grouped by detected type — here's the Slack conversation, here's the deploy log."

### Show timeline (10 sec)
- "The timeline sorts artifacts by their first detected timestamp — so you can see the incident unfold chronologically without reading every file."

### Run the pipeline (30 sec)
- Click **"Extract Evidence & Generate Update"**
- "Two LLM calls happening now — extraction, then generation."
- Wait for results to appear.

### Walk through extracted evidence (45 sec)
- "Here's what the model extracted. Severity SEV-1, phase Resolved, high confidence."
- Point to customer impact and scope fields: "Plain-language impact description — users unable to log in, SSO failures, scoped to one region."
- Point to the two-column fact split: "This is the key output. On the left, internal-only facts — Redis migration, connection pool config, specific service names. On the right, customer-safe facts — login disruption, recovery timeline, the things customers actually care about."
- "This separation is what makes the next stage safe."

### Walk through generated message (30 sec)
- "And here's the draft status page update. Phase indicator, calm headline, 3-4 sentence body."
- Read the body aloud briefly: "Notice — no service names, no deploy versions, no speculation about root cause. Just clear impact, clear status, clear next steps."

### Show validation (15 sec)
- "Below the draft, validation checks. If the model had leaked an internal term or made a speculative claim, you'd see warnings here with specific suggestions."
- If there are warnings: "For example, this one flags [read the warning]. Easy to catch and fix."
- If clean: "In this case, all checks passed."

### Show edit & export (15 sec)
- "Finally, the human reviews and edits. The draft is fully editable. You can download it as markdown or copy it directly to your status page tool."

---

## [3:30–4:15] How I Used AI During Development

**Say something like:**

"I want to be transparent about how I used AI tools to build this. I used Claude Code as my primary development environment — it's an agentic coding tool that I used to scaffold the project structure, write the initial module implementations, generate realistic sample data, and iterate on the prompts.

Specifically: I described the architecture and component requirements in natural language, and Claude Code generated the module files — ingest, parse, LLM integration, validation, and the Streamlit app. I then reviewed each file, tested the pipeline, and iterated on the prompts and heuristics until the output quality was where I wanted it.

The sample incident data — the alerts, Slack messages, deploy logs — was also generated with AI assistance to create a realistic but fully anonymized scenario that exercises every part of the pipeline.

I think this is actually a good signal for the role — using AI tools effectively to ship faster is exactly the kind of workflow this product is designed to enable for incident responders."

---

## [4:15–5:00] Why This Validates the Concept

**Say something like:**

"Let me close with why I think this prototype answers the right question.

The hypothesis was: can an LLM turn messy incident artifacts into a publishable customer update? The answer from this prototype is yes, with appropriate guardrails. The two-stage pipeline produces structured, inspectable intermediate output. The fact separation prevents the most common communication mistake — leaking internal details. And the rule-based validation catches what the LLM misses.

If I had more time, the natural next steps would be: integrating with real incident sources like PagerDuty or Slack APIs, adding a feedback loop so the model improves from human edits, and building phase-aware templates so teams can enforce their specific communication standards.

But the core value proposition — reducing time-to-first-update from 15-20 minutes to under 2 — is demonstrated here. The human stays in the loop, but they're editing a solid draft instead of staring at a blank page during one of the most stressful moments in ops.

Thanks for watching."

---

## Pre-recording checklist

- [ ] App running at localhost:8501 with API key set
- [ ] "Sample incident" selected in sidebar
- [ ] No prior results in session state (fresh page load)
- [ ] Screen recording captures full browser window
- [ ] Microphone tested
- [ ] Practice the pipeline click once so you know the wait time (~10-15 sec)
