"""File ingestion: load incident artifacts from a folder or uploaded files."""

import os
import logging
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".txt", ".log", ".md", ".json", ".csv", ".yaml", ".yml"}
MAX_FILE_SIZE = 500_000  # 500KB per file


@dataclass
class RawArtifact:
    file_name: str
    content: str
    source_path: str
    size_bytes: int


@dataclass
class IngestionResult:
    artifacts: list[RawArtifact] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def is_supported(file_path: str) -> bool:
    return Path(file_path).suffix.lower() in SUPPORTED_EXTENSIONS


def load_file(file_path: str) -> Optional[RawArtifact]:
    """Load a single file, return None if unsupported or unreadable."""
    path = Path(file_path)
    if not path.is_file():
        return None
    if path.stat().st_size > MAX_FILE_SIZE:
        logger.warning(f"Skipping oversized file: {path.name} ({path.stat().st_size} bytes)")
        return None
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
        return RawArtifact(
            file_name=path.name,
            content=content,
            source_path=str(path),
            size_bytes=len(content.encode("utf-8")),
        )
    except Exception as e:
        logger.error(f"Error reading {path.name}: {e}")
        return None


def ingest_folder(folder_path: str) -> IngestionResult:
    """Recursively load all supported files from a folder."""
    result = IngestionResult()
    folder = Path(folder_path)

    if not folder.is_dir():
        result.errors.append(f"Not a valid directory: {folder_path}")
        return result

    for root, _dirs, files in os.walk(folder):
        for fname in sorted(files):
            fpath = os.path.join(root, fname)
            if not is_supported(fpath):
                result.skipped.append(fname)
                continue
            artifact = load_file(fpath)
            if artifact:
                result.artifacts.append(artifact)
            else:
                result.skipped.append(fname)

    return result


def ingest_uploaded_files(uploaded_files: list) -> IngestionResult:
    """Load artifacts from Streamlit uploaded file objects."""
    result = IngestionResult()

    for uf in uploaded_files:
        if not any(uf.name.lower().endswith(ext) for ext in SUPPORTED_EXTENSIONS):
            result.skipped.append(uf.name)
            continue
        try:
            content = uf.read().decode("utf-8", errors="replace")
            result.artifacts.append(RawArtifact(
                file_name=uf.name,
                content=content,
                source_path=f"uploaded:{uf.name}",
                size_bytes=len(content.encode("utf-8")),
            ))
        except Exception as e:
            result.errors.append(f"Error reading {uf.name}: {e}")

    return result
