"""LLM integration: evidence extraction and message generation via OpenAI."""

import os
import json
import logging

from openai import OpenAI

from parse import NormalizedArtifact
from prompts import (
    EVIDENCE_EXTRACTION_SYSTEM,
    EVIDENCE_EXTRACTION_USER,
    CHUNK_SUMMARY_SYSTEM,
    CHUNK_SUMMARY_USER,
    MESSAGE_GENERATION_SYSTEM,
    MESSAGE_GENERATION_USER,
)
from utils import truncate, estimate_tokens

logger = logging.getLogger(__name__)

MODEL = "gpt-4o"
MAX_CONTEXT_CHARS = 80_000  # Stay well within context limits
CHUNK_SIZE_CHARS = 30_000


def get_client() -> OpenAI:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set.")
    return OpenAI(api_key=api_key)


def _call_llm(system: str, user: str, max_tokens: int = 2000) -> str:
    """Make a single LLM call and return the text response."""
    client = get_client()
    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return response.choices[0].message.content


def _parse_json_response(text: str) -> dict:
    """Parse JSON from LLM response, handling common issues."""
    cleaned = text.strip()
    # Strip markdown fences if the model added them
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
    # Remove leading "json" label
    if cleaned.startswith("json"):
        cleaned = cleaned[4:].strip()
    return json.loads(cleaned)


def _format_artifacts_for_prompt(artifacts: list[NormalizedArtifact]) -> str:
    """Format artifacts into a single text block for the LLM prompt."""
    parts = []
    for a in artifacts:
        header = f"[{a.artifact_type.upper()}] {a.file_name}"
        if a.timestamp:
            header += f" (first timestamp: {a.timestamp})"
        parts.append(f"=== {header} ===\n{truncate(a.content, 12000)}")
    return "\n\n".join(parts)


def _chunk_artifacts(artifacts: list[NormalizedArtifact]) -> list[list[NormalizedArtifact]]:
    """Split artifacts into chunks that fit within context limits."""
    chunks: list[list[NormalizedArtifact]] = []
    current_chunk: list[NormalizedArtifact] = []
    current_size = 0

    for a in artifacts:
        artifact_size = len(a.content)
        if current_size + artifact_size > CHUNK_SIZE_CHARS and current_chunk:
            chunks.append(current_chunk)
            current_chunk = []
            current_size = 0
        current_chunk.append(a)
        current_size += artifact_size

    if current_chunk:
        chunks.append(current_chunk)
    return chunks


def _summarize_chunk(artifacts: list[NormalizedArtifact]) -> str:
    """Summarize a chunk of artifacts using the LLM."""
    text = _format_artifacts_for_prompt(artifacts)
    prompt = CHUNK_SUMMARY_USER.format(chunk_text=truncate(text, CHUNK_SIZE_CHARS))
    return _call_llm(CHUNK_SUMMARY_SYSTEM, prompt, max_tokens=1500)


def extract_evidence(artifacts: list[NormalizedArtifact]) -> dict:
    """
    Stage 1: Extract structured incident evidence from artifacts.
    Chunks and summarizes if artifacts are too large.
    """
    total_chars = sum(len(a.content) for a in artifacts)

    if total_chars <= MAX_CONTEXT_CHARS:
        # Fits in one call
        artifacts_text = _format_artifacts_for_prompt(artifacts)
        prompt = EVIDENCE_EXTRACTION_USER.format(artifacts_text=artifacts_text)
        raw = _call_llm(EVIDENCE_EXTRACTION_SYSTEM, prompt, max_tokens=2000)
        return _parse_json_response(raw)
    else:
        # Chunk, summarize each, then extract from summaries
        logger.info(f"Artifacts too large ({total_chars} chars), chunking into summaries")
        chunks = _chunk_artifacts(artifacts)
        summaries = []
        for i, chunk in enumerate(chunks):
            logger.info(f"Summarizing chunk {i+1}/{len(chunks)}")
            summaries.append(_summarize_chunk(chunk))

        combined = "\n\n---\n\n".join(
            f"[Chunk {i+1} Summary]\n{s}" for i, s in enumerate(summaries)
        )
        prompt = EVIDENCE_EXTRACTION_USER.format(artifacts_text=combined)
        raw = _call_llm(EVIDENCE_EXTRACTION_SYSTEM, prompt, max_tokens=2000)
        return _parse_json_response(raw)


def generate_customer_message(evidence: dict) -> dict:
    """
    Stage 2: Generate a customer-facing status page update from structured evidence.
    """
    incident_json = json.dumps(evidence, indent=2)
    prompt = MESSAGE_GENERATION_USER.format(incident_json=incident_json)
    raw = _call_llm(MESSAGE_GENERATION_SYSTEM, prompt, max_tokens=1000)
    return _parse_json_response(raw)
