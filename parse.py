"""Parsing and normalization: convert raw artifacts into a common schema."""

import re
from dataclasses import dataclass, asdict
from typing import Optional

from ingest import RawArtifact
from utils import extract_first_timestamp


@dataclass
class NormalizedArtifact:
    source: str
    file_name: str
    timestamp: Optional[str]
    content: str
    artifact_type: str  # slack|alert|log|deployment|metric|postmortem|unknown

    def to_dict(self) -> dict:
        return asdict(self)


# Weighted keyword rules for artifact type classification
_TYPE_RULES: list[tuple[str, list[tuple[str, int]]]] = [
    ("slack", [
        ("slack", 2), ("channel", 1), ("chat", 1), ("conversation", 1),
    ]),
    ("alert", [
        ("alert", 2), ("pagerduty", 3), ("opsgenie", 3), ("triggered", 1),
        ("acknowledged", 1), ("alert_id", 3),
    ]),
    ("deployment", [
        ("deploy", 3), ("[deploy]", 5), ("rollback", 3), ("rollout", 2),
        ("release", 1), ("canary", 2), ("promoting", 2),
    ]),
    ("metric", [
        ("metric", 2), ("grafana", 3), ("dashboard", 1), ("timeseries", 2),
        ("p99", 2), ("p50", 2), ("latency", 1), ("error_rate", 2),
    ]),
    ("log", [
        (".log", 1), ("stdout", 2), ("stderr", 2), ("syslog", 2),
    ]),
    ("postmortem", [
        ("postmortem", 5), ("post-mortem", 5), ("root cause", 3),
        ("action items", 3), ("## timeline", 3), ("## impact", 3),
        ("lessons learned", 3),
    ]),
]


def infer_artifact_type(file_name: str, content: str) -> str:
    """Score-based artifact type classification from filename and content."""
    fn_lower = file_name.lower()
    content_sample = content[:1500].lower()
    combined = fn_lower + " " + content_sample

    scores: dict[str, int] = {t: 0 for t, _ in _TYPE_RULES}

    for atype, keywords in _TYPE_RULES:
        for keyword, weight in keywords:
            if keyword in combined:
                scores[atype] += weight

    # Structural pattern boosts
    # Slack: lines with [@user] or [timestamp] @user patterns
    if re.search(r"\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}", content_sample) and "@" in content_sample:
        scores["slack"] += 5

    # Alert: JSON with severity/alert fields
    if '"severity"' in content_sample and '"alert_id"' in content_sample:
        scores["alert"] += 5

    # Metric: CSV with numeric columns
    if fn_lower.endswith(".csv") and re.search(r"\d+\.\d+", content_sample):
        scores["metric"] += 4

    # Deploy log: timestamped [deploy] lines
    if re.search(r"\[deploy\]", content_sample):
        scores["deployment"] += 5

    best_type = max(scores, key=lambda k: scores[k])
    if scores[best_type] > 0:
        return best_type
    return "unknown"


# Display labels for artifact types
ARTIFACT_TYPE_LABELS = {
    "slack": "Slack",
    "alert": "Alert",
    "deployment": "Deployment",
    "metric": "Metric",
    "log": "Log",
    "postmortem": "Postmortem",
    "unknown": "Unknown",
}

ARTIFACT_TYPE_ICONS = {
    "slack": "💬",
    "alert": "🚨",
    "deployment": "🚀",
    "metric": "📊",
    "log": "📋",
    "postmortem": "📝",
    "unknown": "❓",
}


def normalize_artifact(raw: RawArtifact) -> NormalizedArtifact:
    """Convert a raw artifact to normalized form."""
    return NormalizedArtifact(
        source=raw.source_path,
        file_name=raw.file_name,
        timestamp=extract_first_timestamp(raw.content),
        content=raw.content,
        artifact_type=infer_artifact_type(raw.file_name, raw.content),
    )


def normalize_all(raw_artifacts: list[RawArtifact]) -> list[NormalizedArtifact]:
    """Normalize a list of raw artifacts."""
    return [normalize_artifact(r) for r in raw_artifacts]
