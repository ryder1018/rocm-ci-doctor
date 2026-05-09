"""Small helpers used by the Streamlit UI."""

from __future__ import annotations

import io
import re
import zipfile
from pathlib import Path
from typing import Any


SAMPLE_ROOT = Path("samples")
STACK_LABELS = {
    "docker": "Dockerfile",
    "github_actions": "GitHub Actions",
    "python": "Python",
    "pytorch": "PyTorch",
    "sglang": "SGLang",
    "tests": "Python tests",
    "transformers": "Transformers",
    "vllm": "vLLM",
}


def list_sample_repositories(root: Path = SAMPLE_ROOT) -> list[tuple[str, str]]:
    """Return display label and path pairs for bundled sample repositories."""

    if not root.exists():
        return []
    samples: list[tuple[str, str]] = []
    for path in sorted(root.iterdir()):
        if path.is_dir():
            label = path.name.replace("_", " ").replace("-", " ").title()
            samples.append((label, path.as_posix()))
    return samples


def slugify_source(source: str) -> str:
    """Create a filesystem-safe short name for output folders."""

    slug = re.sub(r"[^A-Za-z0-9]+", "-", source.strip()).strip("-").lower()
    return slug[:80] or "repository"


def default_bundle_dir(source: str, output_root: Path = Path("outputs/ui-bundles")) -> Path:
    """Return the default generated bundle directory for a source."""

    return output_root / slugify_source(source)


def stack_rows(analysis: dict[str, Any]) -> list[dict[str, str]]:
    """Convert detected stack data into rows for display."""

    stack = analysis.get("detected_stack", {})
    return [
        {
            "Signal": STACK_LABELS.get(key, key.replace("_", " ").title()),
            "Detected": "Yes" if bool(value) else "No",
        }
        for key, value in sorted(stack.items())
    ]


def risk_rows(analysis: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten assessed risks into display rows."""

    assessment = analysis.get("assessment", {})
    rows: list[dict[str, Any]] = []
    for severity in ("high", "medium", "low"):
        for risk in assessment.get("risks_by_severity", {}).get(severity, []):
            rows.append(
                {
                    "Severity": severity.title(),
                    "Risk ID": risk.get("id", ""),
                    "Finding": risk.get("message", ""),
                    "Findings": risk.get("count", 1),
                    "Category": risk.get("fix_category", ""),
                    "Recommended fix": risk.get("recommended_fix", ""),
                }
            )
    return rows


def zip_directory_bytes(directory: Path) -> bytes:
    """Return a zip archive containing all files under directory."""

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(directory.rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                archive.write(path, path.relative_to(directory).as_posix())
    return buffer.getvalue()


def generated_file_paths(bundle_manifest: dict[str, Any]) -> list[str]:
    """Return generated asset paths from a bundle manifest."""

    return [str(file["path"]) for file in bundle_manifest.get("files", [])]
