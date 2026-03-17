"""Rule-based validation and guardrails for generated customer messages."""

import re
from dataclasses import dataclass

# Internal jargon that should never appear in customer comms
INTERNAL_JARGON = [
    "redis", "kafka", "kubernetes", "k8s", "pod", "node", "container",
    "docker", "nginx", "consul", "terraform", "ansible", "jenkins",
    "datadog", "pagerduty", "opsgenie", "grafana", "prometheus", "splunk",
    "ec2", "s3", "rds", "lambda", "ecs", "eks", "fargate", "aurora",
    "us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1",
    "vpc", "subnet", "load balancer", "alb", "elb", "cdn", "cloudfront",
    "cron", "daemon", "mutex", "deadlock", "segfault", "core dump",
    "heap", "stack trace", "null pointer", "race condition",
    "connection pool", "thread pool", "cpu", "memory leak",
    "microservice", "monolith", "circuit breaker", "shard",
]

# Patterns suggesting internal references leaked into the message
INTERNAL_PATTERNS = [
    (r"@\w+", "Slack @mention"),
    (r"#[a-z\-_]+", "Slack channel reference"),
    (r"[a-z]+-service\b", "Internal service name"),
    (r"[a-z]+-cluster-[a-z]+-\d+", "Internal cluster identifier"),
    (r"v\d+\.\d+\.\d+", "Internal version number"),
    (r"sha-[a-f0-9]+", "Git commit SHA"),
    (r"\b[A-Z]{2,5}-\d{4,}\b", "Internal ticket/alert ID"),
    (r"\b[a-z]+\.[a-z]+@", "Internal email address"),
]

# Phrases suggesting unsupported root-cause speculation
SPECULATION_PHRASES = [
    "root cause is",
    "root cause was",
    "caused by a bug",
    "caused by a code",
    "due to a code change",
    "due to a deployment",
    "engineer error",
    "human error",
    "operator error",
    "we believe the cause",
    "appears to be caused by",
    "likely caused by",
    "probably due to",
]

MAX_HEADLINE_LENGTH = 100
MAX_BODY_LENGTH = 800
MIN_BODY_LENGTH = 50


@dataclass
class ValidationWarning:
    level: str  # "error" | "warning" | "info"
    category: str
    message: str
    suggestion: str = ""


def validate_message(headline: str, body: str) -> list[ValidationWarning]:
    """Run all validation checks on a generated message. Returns warnings."""
    warnings: list[ValidationWarning] = []
    full_text = f"{headline} {body}".lower()
    full_text_raw = f"{headline} {body}"

    # --- Internal jargon ---
    for term in INTERNAL_JARGON:
        if term.lower() in full_text:
            warnings.append(ValidationWarning(
                level="warning",
                category="Internal jargon",
                message=f"Contains internal term: \"{term}\"",
                suggestion=f"Remove or replace \"{term}\" with a customer-friendly description.",
            ))

    # --- Internal reference patterns ---
    for pattern, label in INTERNAL_PATTERNS:
        matches = re.findall(pattern, full_text_raw, re.IGNORECASE)
        for m in matches:
            warnings.append(ValidationWarning(
                level="warning",
                category="Internal reference",
                message=f"{label} detected: \"{m}\"",
                suggestion=f"Remove \"{m}\" — customers should not see internal identifiers.",
            ))

    # --- Speculation ---
    for phrase in SPECULATION_PHRASES:
        if phrase.lower() in full_text:
            warnings.append(ValidationWarning(
                level="error",
                category="Speculation",
                message=f"Possible unsupported root-cause claim: \"{phrase}\"",
                suggestion="Remove or soften. Only state confirmed, customer-appropriate causes.",
            ))

    # --- Length checks ---
    if len(headline) > MAX_HEADLINE_LENGTH:
        warnings.append(ValidationWarning(
            level="warning",
            category="Length",
            message=f"Headline is {len(headline)} chars (recommended max: {MAX_HEADLINE_LENGTH})",
            suggestion="Shorten the headline to be more scannable.",
        ))

    if len(body) > MAX_BODY_LENGTH:
        warnings.append(ValidationWarning(
            level="warning",
            category="Length",
            message=f"Body is {len(body)} chars (recommended max: {MAX_BODY_LENGTH})",
            suggestion="Trim the body. Status page updates should be concise.",
        ))

    if body and len(body) < MIN_BODY_LENGTH:
        warnings.append(ValidationWarning(
            level="info",
            category="Length",
            message=f"Body is only {len(body)} chars — may be too brief.",
            suggestion="Consider adding more context about impact or next steps.",
        ))

    # --- Tone checks ---
    negative_phrases = ["we apologize", "we are sorry", "unfortunately"]
    for phrase in negative_phrases:
        if phrase in full_text:
            warnings.append(ValidationWarning(
                level="info",
                category="Tone",
                message=f"Contains \"{phrase}\" — verify this matches your comms policy.",
                suggestion="Some teams prefer neutral tone over apology in status updates.",
            ))

    # Deduplicate by message
    seen = set()
    deduped = []
    for w in warnings:
        if w.message not in seen:
            seen.add(w.message)
            deduped.append(w)

    return deduped
