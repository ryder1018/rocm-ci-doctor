"""Static repository analyzer for Phase 1."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11 fallback.
    tomllib = None  # type: ignore[assignment]


ANALYSIS_VERSION = "phase1"
MAX_FILE_BYTES = 1_000_000
MAX_OCCURRENCES = 200

IGNORED_DIRS = {
    ".git",
    ".hg",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "site-packages",
    "venv",
}

SCAN_SUFFIXES = {
    ".cfg",
    ".ini",
    ".md",
    ".py",
    ".sh",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}

RELEVANT_NAMES = {
    "dockerfile",
    "environment.yml",
    "environment.yaml",
    "pyproject.toml",
    "readme.md",
    "readme.rst",
    "readme.txt",
    "requirements.txt",
    "setup.cfg",
    "setup.py",
}

ENTRYPOINT_KEYWORDS = (
    "app",
    "benchmark",
    "eval",
    "evaluate",
    "infer",
    "inference",
    "main",
    "predict",
    "serve",
    "server",
    "train",
)


@dataclass(frozen=True)
class PatternDefinition:
    id: str
    regex: re.Pattern[str]
    severity: str
    message: str


GPU_PATTERNS = [
    PatternDefinition(
        id="cuda_method",
        regex=re.compile(r"\.cuda\s*\("),
        severity="medium",
        message="Direct .cuda() calls may need a ROCm runtime smoke test.",
    ),
    PatternDefinition(
        id="hardcoded_cuda_device",
        regex=re.compile(
            r"(device\s*=\s*[\"']cuda[\"']|\bto\s*\(\s*[\"']cuda[\"']|\btorch\.device\s*\(\s*[\"']cuda[\"'])"
        ),
        severity="medium",
        message="Hard-coded CUDA device strings can hide portability issues.",
    ),
    PatternDefinition(
        id="torch_cuda_api",
        regex=re.compile(r"\btorch\.cuda\b"),
        severity="low",
        message="PyTorch on ROCm still uses torch.cuda APIs; validate behavior on ROCm.",
    ),
    PatternDefinition(
        id="nvidia_smi",
        regex=re.compile(r"\bnvidia-smi\b"),
        severity="high",
        message="nvidia-smi is NVIDIA-specific and will not validate AMD GPUs.",
    ),
    PatternDefinition(
        id="cuda_base_image",
        regex=re.compile(r"FROM\s+[\w./:-]*(nvidia/cuda|cuda|cudnn)[\w./:-]*", re.IGNORECASE),
        severity="high",
        message="CUDA/NVIDIA base images should be replaced with ROCm-compatible images.",
    ),
    PatternDefinition(
        id="cuda_package",
        regex=re.compile(
            r"(cupy-cuda|cuda-python|tensorflow-gpu|nvidia-cublas|nvidia-cuda|torch==.*\+cu\d+|torchvision==.*\+cu\d+)",
            re.IGNORECASE,
        ),
        severity="high",
        message="CUDA-specific packages can block ROCm environments.",
    ),
    PatternDefinition(
        id="nvcc",
        regex=re.compile(r"\bnvcc\b"),
        severity="high",
        message="nvcc usage indicates CUDA compiler assumptions.",
    ),
    PatternDefinition(
        id="cuda_visible_devices",
        regex=re.compile(r"\bCUDA_VISIBLE_DEVICES\b"),
        severity="low",
        message="CUDA_VISIBLE_DEVICES is commonly used by PyTorch but should be validated on ROCm.",
    ),
    PatternDefinition(
        id="tensorrt",
        regex=re.compile(r"\b(tensorrt|trtexec)\b", re.IGNORECASE),
        severity="medium",
        message="TensorRT-specific paths usually need alternatives for AMD deployments.",
    ),
]


def analyze_repository(root: Path, source: str | None = None, loaded_from: str = "local") -> dict[str, Any]:
    """Analyze a repository and return structured JSON-serializable data."""

    root = root.resolve()
    files = _collect_files(root)
    readable_files = [file for file in files if _is_readable_scan_file(file)]
    dependency_files = _parse_dependency_files(root, files)
    all_dependencies = sorted(
        {dependency for dependencies in dependency_files.values() for dependency in dependencies}
    )

    python_files = [file for file in files if file.suffix == ".py"]
    dockerfiles = [file for file in files if _is_dockerfile(file)]
    readme_files = [file for file in files if _is_readme_file(file)]
    entrypoint_files = [file for file in python_files if _is_entrypoint_file(file)]
    workflow_files = [
        file
        for file in files
        if ".github/workflows/" in _relative_posix(root, file)
        and file.suffix.lower() in {".yml", ".yaml"}
    ]

    occurrences = _find_gpu_pattern_occurrences(root, readable_files)
    detected_stack = _detect_stack(root, files, all_dependencies)
    ci_gaps = _detect_ci_gaps(root, files, workflow_files, dockerfiles, detected_stack)
    risks = _build_risks(occurrences, ci_gaps)
    recommended_assets = _recommend_assets(detected_stack, ci_gaps, occurrences)

    relevant_files = [_relative_posix(root, file) for file in files if _is_relevant_file(root, file)]

    return {
        "analysis_version": ANALYSIS_VERSION,
        "source": source or str(root),
        "loaded_from": loaded_from,
        "repo_name": root.name,
        "root": str(root),
        "summary": {
            "total_files_seen": len(files),
            "files_scanned": len(readable_files),
            "relevant_files": len(relevant_files),
            "dependency_count": len(all_dependencies),
            "gpu_pattern_count": len(occurrences),
            "risk_count": len(risks),
            "ci_gap_count": len(ci_gaps),
        },
        "files": {
            "relevant": relevant_files,
            "python_files_count": len(python_files),
            "dockerfiles": [_relative_posix(root, file) for file in dockerfiles],
            "readme_files": [_relative_posix(root, file) for file in readme_files],
            "entrypoint_files": [_relative_posix(root, file) for file in entrypoint_files],
            "workflow_files": [_relative_posix(root, file) for file in workflow_files],
        },
        "dependencies": {
            "by_file": dependency_files,
            "all": all_dependencies,
        },
        "detected_stack": detected_stack,
        "gpu_patterns": occurrences,
        "risks": risks,
        "ci_gaps": ci_gaps,
        "recommended_assets": recommended_assets,
    }


def _collect_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        if any(part in IGNORED_DIRS for part in path.relative_to(root).parts):
            continue
        files.append(path)
    return sorted(files)


def _is_readable_scan_file(path: Path) -> bool:
    if path.name.lower().startswith("dockerfile"):
        return True
    if path.suffix.lower() not in SCAN_SUFFIXES:
        return False
    try:
        return path.stat().st_size <= MAX_FILE_BYTES
    except OSError:
        return False


def _is_relevant_file(root: Path, path: Path) -> bool:
    rel = _relative_posix(root, path)
    lower_name = path.name.lower()
    if lower_name in RELEVANT_NAMES or lower_name.startswith("dockerfile"):
        return True
    if rel.startswith(".github/workflows/") and path.suffix.lower() in {".yml", ".yaml"}:
        return True
    if path.suffix.lower() in {".py", ".sh"}:
        return True
    return False


def _is_dockerfile(path: Path) -> bool:
    return path.name.lower().startswith("dockerfile")


def _is_readme_file(path: Path) -> bool:
    return path.name.lower() in {"readme.md", "readme.rst", "readme.txt"}


def _is_entrypoint_file(path: Path) -> bool:
    stem = path.stem.lower()
    return any(keyword in stem for keyword in ENTRYPOINT_KEYWORDS)


def _relative_posix(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _parse_dependency_files(root: Path, files: list[Path]) -> dict[str, list[str]]:
    parsed: dict[str, list[str]] = {}

    for file in files:
        name = file.name.lower()
        rel = _relative_posix(root, file)
        dependencies: list[str] = []

        if name == "requirements.txt":
            dependencies = _parse_requirements(_read_text(file))
        elif name == "pyproject.toml":
            dependencies = _parse_pyproject(file)
        elif name == "setup.py":
            dependencies = _parse_setup_py(_read_text(file))
        elif name in {"environment.yml", "environment.yaml"}:
            dependencies = _parse_environment_yml(_read_text(file))

        if dependencies:
            parsed[rel] = sorted(set(dependencies))

    return parsed


def _parse_requirements(content: str) -> list[str]:
    dependencies: list[str] = []
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith(("-r ", "--", "-f ", "-i ")):
            continue
        dependencies.append(_normalize_dependency(line))
    return [dependency for dependency in dependencies if dependency]


def _parse_pyproject(path: Path) -> list[str]:
    try:
        content = path.read_text(encoding="utf-8")
    except OSError:
        return []

    if tomllib is None:
        return _parse_pyproject_fallback(content)

    try:
        data = tomllib.loads(content)
    except tomllib.TOMLDecodeError:
        return _parse_pyproject_fallback(content)

    dependencies: list[str] = []
    project = data.get("project", {})
    for dependency in project.get("dependencies", []) or []:
        dependencies.append(_normalize_dependency(str(dependency)))
    optional = project.get("optional-dependencies", {}) or {}
    for optional_dependencies in optional.values():
        for dependency in optional_dependencies or []:
            dependencies.append(_normalize_dependency(str(dependency)))

    poetry_deps = data.get("tool", {}).get("poetry", {}).get("dependencies", {}) or {}
    for name in poetry_deps:
        if str(name).lower() != "python":
            dependencies.append(_normalize_dependency(str(name)))

    return [dependency for dependency in dependencies if dependency]


def _parse_pyproject_fallback(content: str) -> list[str]:
    dependencies: list[str] = []
    dependencies_block = re.search(r"dependencies\s*=\s*\[(.*?)\]", content, re.DOTALL)
    if dependencies_block:
        for dependency in re.findall(r"[\"']([^\"']+)[\"']", dependencies_block.group(1)):
            normalized = _normalize_dependency(dependency)
            if normalized:
                dependencies.append(normalized)

    poetry_block = re.search(
        r"\[tool\.poetry\.dependencies\](.*?)(?:\n\[|\Z)",
        content,
        re.DOTALL,
    )
    if poetry_block:
        for raw_line in poetry_block.group(1).splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name = line.split("=", 1)[0].strip().strip("\"'")
            if name.lower() != "python":
                dependencies.append(_normalize_dependency(name))

    return [dependency for dependency in dependencies if dependency]


def _parse_setup_py(content: str) -> list[str]:
    dependencies: list[str] = []
    match = re.search(r"install_requires\s*=\s*\[(.*?)\]", content, re.DOTALL)
    if not match:
        return dependencies
    for dependency in re.findall(r"[\"']([^\"']+)[\"']", match.group(1)):
        normalized = _normalize_dependency(dependency)
        if normalized:
            dependencies.append(normalized)
    return dependencies


def _parse_environment_yml(content: str) -> list[str]:
    dependencies: list[str] = []
    in_pip_block = False
    for raw_line in content.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped == "- pip:":
            in_pip_block = True
            continue
        if stripped.startswith("- "):
            value = stripped[2:].strip()
            if value and value not in {"pip"}:
                dependencies.append(_normalize_dependency(value))
            continue
        if in_pip_block and stripped.startswith("-"):
            dependencies.append(_normalize_dependency(stripped[1:].strip()))
    return [dependency for dependency in dependencies if dependency]


def _normalize_dependency(raw: str) -> str:
    dependency = raw.split(";", 1)[0].strip()
    if "#egg=" in dependency:
        dependency = dependency.rsplit("#egg=", 1)[-1]
    dependency = re.split(r"[\s<>=!~\[]", dependency, maxsplit=1)[0]
    dependency = dependency.strip().lower().replace("_", "-")
    return dependency


def _find_gpu_pattern_occurrences(root: Path, files: list[Path]) -> list[dict[str, Any]]:
    occurrences: list[dict[str, Any]] = []
    for file in files:
        rel = _relative_posix(root, file)
        for line_number, line in enumerate(_read_text(file).splitlines(), start=1):
            for pattern in GPU_PATTERNS:
                if pattern.regex.search(line):
                    occurrences.append(
                        {
                            "id": pattern.id,
                            "severity": pattern.severity,
                            "file": rel,
                            "line": line_number,
                            "message": pattern.message,
                            "snippet": line.strip()[:180],
                        }
                    )
                    if len(occurrences) >= MAX_OCCURRENCES:
                        return occurrences
    return occurrences


def _detect_stack(root: Path, files: list[Path], dependencies: list[str]) -> dict[str, bool]:
    dependency_set = set(dependencies)
    python_files = [file for file in files if file.suffix == ".py"]
    dockerfiles = [file for file in files if _is_dockerfile(file)]
    workflow_files = [
        file
        for file in files
        if ".github/workflows/" in _relative_posix(root, file)
        and file.suffix.lower() in {".yml", ".yaml"}
    ]
    code_text = "\n".join(_read_text(file) for file in python_files[:200])

    return {
        "python": bool(
            python_files
            or dependency_set
            or any(file.name in {"pyproject.toml", "setup.py"} for file in files)
        ),
        "pytorch": "torch" in dependency_set or _has_import(code_text, "torch"),
        "transformers": "transformers" in dependency_set or _has_import(code_text, "transformers"),
        "vllm": "vllm" in dependency_set or _has_import(code_text, "vllm"),
        "sglang": "sglang" in dependency_set or _has_import(code_text, "sglang"),
        "docker": bool(dockerfiles),
        "github_actions": bool(workflow_files),
        "tests": _has_tests(root, files),
    }


def _has_import(code_text: str, module: str) -> bool:
    return bool(re.search(rf"^\s*(import|from)\s+{re.escape(module)}\b", code_text, re.MULTILINE))


def _has_tests(root: Path, files: list[Path]) -> bool:
    for file in files:
        rel = _relative_posix(root, file)
        if rel.startswith("tests/") and file.suffix == ".py":
            return True
        if file.name.startswith("test_") and file.suffix == ".py":
            return True
    return False


def _detect_ci_gaps(
    root: Path,
    files: list[Path],
    workflow_files: list[Path],
    dockerfiles: list[Path],
    detected_stack: dict[str, bool],
) -> list[dict[str, str]]:
    gaps: list[dict[str, str]] = []
    if not workflow_files:
        gaps.append(
            {
                "id": "missing_github_actions",
                "severity": "medium",
                "message": "No GitHub Actions workflows were detected.",
            }
        )
    elif not _workflow_mentions_rocm(workflow_files):
        gaps.append(
            {
                "id": "missing_rocm_workflow",
                "severity": "high",
                "message": "Existing GitHub Actions workflows do not mention ROCm, AMD, MI300, or self-hosted GPU runners.",
            }
        )

    if not dockerfiles:
        gaps.append(
            {
                "id": "missing_dockerfile",
                "severity": "low",
                "message": "No Dockerfile was detected for reproducible GPU validation.",
            }
        )

    if detected_stack["python"] and not detected_stack["tests"]:
        gaps.append(
            {
                "id": "missing_tests",
                "severity": "medium",
                "message": "No Python test files were detected.",
            }
        )

    if detected_stack["pytorch"] and not _has_rocm_smoke_test(root, files):
        gaps.append(
            {
                "id": "missing_rocm_smoke_test",
                "severity": "high",
                "message": "PyTorch is present, but no ROCm smoke test was detected.",
            }
        )

    return gaps


def _workflow_mentions_rocm(workflow_files: list[Path]) -> bool:
    haystack = "\n".join(_read_text(file).lower() for file in workflow_files)
    return any(token in haystack for token in ("rocm", "amd", "mi300", "self-hosted"))


def _has_rocm_smoke_test(root: Path, files: list[Path]) -> bool:
    for file in files:
        rel = _relative_posix(root, file).lower()
        if "rocm" in rel and ("smoke" in rel or "test" in rel):
            return True
    return False


def _build_risks(
    occurrences: list[dict[str, Any]], ci_gaps: list[dict[str, str]]
) -> list[dict[str, str]]:
    risks_by_id: dict[str, dict[str, str]] = {}
    for occurrence in occurrences:
        risk_id = f"pattern:{occurrence['id']}"
        existing = risks_by_id.get(risk_id)
        if existing:
            existing["count"] = str(int(existing["count"]) + 1)
            continue
        risks_by_id[risk_id] = {
            "id": risk_id,
            "severity": occurrence["severity"],
            "message": occurrence["message"],
            "count": "1",
        }

    for gap in ci_gaps:
        risks_by_id[f"gap:{gap['id']}"] = {
            "id": f"gap:{gap['id']}",
            "severity": gap["severity"],
            "message": gap["message"],
            "count": "1",
        }

    severity_order = {"high": 0, "medium": 1, "low": 2}
    return sorted(
        risks_by_id.values(),
        key=lambda risk: (severity_order.get(risk["severity"], 99), risk["id"]),
    )


def _recommend_assets(
    detected_stack: dict[str, bool],
    ci_gaps: list[dict[str, str]],
    occurrences: list[dict[str, Any]],
) -> list[dict[str, str]]:
    gap_ids = {gap["id"] for gap in ci_gaps}
    pattern_ids = {occurrence["id"] for occurrence in occurrences}
    assets: list[dict[str, str]] = []

    if "missing_github_actions" in gap_ids or "missing_rocm_workflow" in gap_ids:
        assets.append(
            {
                "path": ".github/workflows/rocm-ci.yml",
                "reason": "Add a repeatable AMD/ROCm validation gate for pull requests.",
            }
        )

    if (
        "missing_dockerfile" in gap_ids
        or "cuda_base_image" in pattern_ids
        or "cuda_package" in pattern_ids
    ):
        assets.append(
            {
                "path": "Dockerfile.rocm",
                "reason": "Provide a ROCm-compatible container entrypoint.",
            }
        )

    if detected_stack["pytorch"] or "missing_rocm_smoke_test" in gap_ids:
        assets.append(
            {
                "path": "tests/test_rocm_smoke.py",
                "reason": "Verify PyTorch can see and use an AMD GPU through ROCm.",
            }
        )

    if detected_stack["pytorch"] or detected_stack["vllm"] or detected_stack["sglang"]:
        assets.append(
            {
                "path": "benchmarks/benchmark_rocm.py",
                "reason": "Capture minimal runtime performance evidence on AMD Developer Cloud.",
            }
        )

    assets.append(
        {
            "path": "ROCM_CI_REPORT.md",
            "reason": "Summarize detected risks, CI gaps, and AMD Developer Cloud run instructions.",
        }
    )

    return assets
