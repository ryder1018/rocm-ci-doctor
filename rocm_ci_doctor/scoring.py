"""Readiness scoring and risk enrichment for Phase 2."""

from __future__ import annotations

from typing import Any


SEVERITIES = ("high", "medium", "low")
ASSESSMENT_VERSION = "phase2"

RISK_GUIDANCE: dict[str, dict[str, str]] = {
    "gap:missing_github_actions": {
        "explanation": "Without CI, AMD compatibility can regress without maintainers noticing.",
        "fix_category": "workflow",
        "recommended_fix": "Add a dedicated ROCm workflow that runs on a self-hosted AMD GPU runner or AMD Developer Cloud.",
    },
    "gap:missing_rocm_workflow": {
        "explanation": "Existing CI is useful, but it does not currently prove that the project runs on AMD GPUs.",
        "fix_category": "workflow",
        "recommended_fix": "Add a ROCm-specific GitHub Actions workflow for smoke tests and optional benchmarks.",
    },
    "gap:missing_dockerfile": {
        "explanation": "A reproducible container makes AMD GPU validation easier to run and share.",
        "fix_category": "container",
        "recommended_fix": "Add a ROCm-compatible Dockerfile based on an AMD ROCm/PyTorch image.",
    },
    "gap:missing_tests": {
        "explanation": "Runtime compatibility cannot be checked continuously without a minimal test suite.",
        "fix_category": "test coverage",
        "recommended_fix": "Add a small test suite that can run in CPU CI and a targeted ROCm smoke test for GPU CI.",
    },
    "gap:missing_rocm_smoke_test": {
        "explanation": "PyTorch can run on ROCm, but the repository should prove that its key path sees and uses an AMD GPU.",
        "fix_category": "runtime validation",
        "recommended_fix": "Add `tests/test_rocm_smoke.py` with PyTorch import, device discovery, and a small tensor operation.",
    },
    "pattern:cuda_method": {
        "explanation": "Direct `.cuda()` calls make the code less explicit about device selection and should be validated on ROCm.",
        "fix_category": "runtime portability",
        "recommended_fix": "Route device selection through a shared helper and cover the path with a ROCm smoke test.",
    },
    "pattern:hardcoded_cuda_device": {
        "explanation": "Hard-coded CUDA device strings can hide assumptions that only show up at runtime.",
        "fix_category": "runtime portability",
        "recommended_fix": "Centralize device selection and test the same entrypoint on AMD ROCm.",
    },
    "pattern:torch_cuda_api": {
        "explanation": "PyTorch ROCm intentionally exposes many GPU APIs through `torch.cuda`, so this is a validation signal rather than an automatic failure.",
        "fix_category": "runtime validation",
        "recommended_fix": "Keep the API if needed, but prove expected behavior with a ROCm runtime check.",
    },
    "pattern:nvidia_smi": {
        "explanation": "`nvidia-smi` is NVIDIA-specific and does not verify AMD GPU availability.",
        "fix_category": "runtime portability",
        "recommended_fix": "Use PyTorch device checks in tests and document AMD runner diagnostics separately.",
    },
    "pattern:cuda_base_image": {
        "explanation": "CUDA base images install an NVIDIA runtime stack and are not a ROCm validation environment.",
        "fix_category": "container",
        "recommended_fix": "Create `Dockerfile.rocm` from an AMD ROCm/PyTorch base image.",
    },
    "pattern:cuda_package": {
        "explanation": "CUDA-specific wheels and packages can fail installation or silently select the wrong backend on AMD runners.",
        "fix_category": "dependency portability",
        "recommended_fix": "Move CUDA-specific dependencies behind extras or replace them with ROCm-compatible installation instructions.",
    },
    "pattern:nvcc": {
        "explanation": "`nvcc` indicates CUDA compiler assumptions that are not available in a ROCm environment.",
        "fix_category": "build portability",
        "recommended_fix": "Guard CUDA-specific build steps and provide a ROCm-compatible build path when needed.",
    },
    "pattern:cuda_visible_devices": {
        "explanation": "GPU visibility environment variables should be documented and validated for AMD runners.",
        "fix_category": "runtime portability",
        "recommended_fix": "Document expected AMD runner device visibility and validate device selection in the smoke test.",
    },
    "pattern:tensorrt": {
        "explanation": "TensorRT-specific paths usually require an alternate backend for AMD deployments.",
        "fix_category": "backend portability",
        "recommended_fix": "Add an AMD-compatible inference path, then validate it in CI.",
    },
}


def assess_repository(analysis: dict[str, Any]) -> dict[str, Any]:
    """Build a deterministic readiness assessment from analyzer output."""

    checks = _build_score_checks(analysis)
    score = sum(check["awarded"] for check in checks)
    max_score = sum(check["points"] for check in checks)
    score = max(0, min(max_score, score))

    enriched_risks = enrich_risks(analysis.get("risks", []))
    risks_by_severity = categorize_risks(enriched_risks)
    risk_counts = {
        severity: len(risks_by_severity[severity])
        for severity in SEVERITIES
    }

    return {
        "assessment_version": ASSESSMENT_VERSION,
        "score": score,
        "max_score": max_score,
        "label": _score_label(score),
        "summary": _score_summary(score, risk_counts),
        "checks": checks,
        "risks_by_severity": risks_by_severity,
        "risk_counts": risk_counts,
        "fix_categories": _build_fix_categories(enriched_risks),
    }


def enrich_risks(risks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Attach explanation, category, and recommended fix text to risks."""

    enriched: list[dict[str, Any]] = []
    for risk in risks:
        risk_id = str(risk.get("id", "unknown"))
        guidance = RISK_GUIDANCE.get(
            risk_id,
            {
                "explanation": "This item may affect ROCm CI readiness and should be reviewed.",
                "fix_category": "manual review",
                "recommended_fix": "Review the finding and decide whether a ROCm-specific validation step is needed.",
            },
        )
        enriched.append(
            {
                **risk,
                "count": int(risk.get("count", 1)),
                "explanation": guidance["explanation"],
                "fix_category": guidance["fix_category"],
                "recommended_fix": guidance["recommended_fix"],
            }
        )
    return enriched


def categorize_risks(risks: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Group enriched risks by severity."""

    grouped: dict[str, list[dict[str, Any]]] = {severity: [] for severity in SEVERITIES}
    for risk in risks:
        severity = str(risk.get("severity", "low")).lower()
        if severity not in grouped:
            severity = "low"
        grouped[severity].append(risk)

    for severity in SEVERITIES:
        grouped[severity] = sorted(grouped[severity], key=lambda item: str(item.get("id", "")))
    return grouped


def _build_score_checks(analysis: dict[str, Any]) -> list[dict[str, Any]]:
    stack = analysis.get("detected_stack", {})
    files = analysis.get("files", {})
    risk_ids = {risk.get("id") for risk in analysis.get("risks", [])}

    has_pytorch = bool(stack.get("pytorch"))
    has_cuda_runtime_assumptions = bool(
        {"pattern:cuda_method", "pattern:hardcoded_cuda_device"} & risk_ids
    )
    has_cuda_packages = "pattern:cuda_package" in risk_ids
    has_cuda_base_image = "pattern:cuda_base_image" in risk_ids
    has_docker = bool(stack.get("docker"))
    has_ci = bool(stack.get("github_actions"))
    has_tests = bool(stack.get("tests"))
    has_entrypoint = bool(files.get("entrypoint_files"))
    has_readme = bool(files.get("readme_files"))

    checks = [
        _score_check(
            "portable_pytorch_usage",
            "Portable PyTorch usage",
            20,
            20 if has_pytorch and not has_cuda_runtime_assumptions else 10 if not has_pytorch else 0,
            "PyTorch code is present without direct CUDA transfer assumptions."
            if has_pytorch and not has_cuda_runtime_assumptions
            else "No PyTorch workload was detected; AMD GPU readiness is less relevant."
            if not has_pytorch
            else "Direct CUDA device assumptions were detected in PyTorch code.",
        ),
        _score_check(
            "cuda_neutral_dependencies",
            "CUDA-neutral dependencies",
            15,
            0 if has_cuda_packages else 15,
            "No CUDA-specific Python packages were detected."
            if not has_cuda_packages
            else "CUDA-specific packages were detected.",
        ),
        _score_check(
            "rocm_safe_container",
            "ROCm-safe container path",
            15,
            15 if has_docker and not has_cuda_base_image else 0,
            "A Dockerfile exists without a CUDA/NVIDIA base image."
            if has_docker and not has_cuda_base_image
            else "No Dockerfile exists."
            if not has_docker
            else "The Dockerfile uses a CUDA/NVIDIA base image.",
        ),
        _score_check(
            "no_hardcoded_cuda_device",
            "No hard-coded CUDA device transfer",
            15,
            0 if has_cuda_runtime_assumptions else 15,
            "No direct `.cuda()` or hard-coded CUDA device transfer patterns were detected."
            if not has_cuda_runtime_assumptions
            else "Hard-coded CUDA transfer/device patterns were detected.",
        ),
        _score_check(
            "ci_exists",
            "CI exists",
            10,
            10 if has_ci else 0,
            "GitHub Actions workflow files were detected."
            if has_ci
            else "No GitHub Actions workflow files were detected.",
        ),
        _score_check(
            "tests_exist",
            "Tests exist",
            10,
            10 if has_tests else 0,
            "Python tests were detected."
            if has_tests
            else "No Python tests were detected.",
        ),
        _score_check(
            "entrypoint_discoverable",
            "Runtime entrypoint is discoverable",
            10,
            10 if has_entrypoint else 0,
            "A train, inference, serve, benchmark, main, or app file was detected."
            if has_entrypoint
            else "No obvious runtime entrypoint was detected.",
        ),
        _score_check(
            "readme_present",
            "README is present",
            5,
            5 if has_readme else 0,
            "A README file was detected."
            if has_readme
            else "No README file was detected.",
        ),
    ]
    return checks


def _score_check(
    check_id: str,
    name: str,
    points: int,
    awarded: int,
    rationale: str,
) -> dict[str, Any]:
    return {
        "id": check_id,
        "name": name,
        "points": points,
        "awarded": awarded,
        "status": "pass" if awarded == points else "partial" if awarded > 0 else "fail",
        "rationale": rationale,
    }


def _score_label(score: int) -> str:
    if score >= 85:
        return "AMD-ready candidate"
    if score >= 65:
        return "Close, needs ROCm CI validation"
    if score >= 40:
        return "Needs remediation before AMD-ready"
    return "High-risk for ROCm CI"


def _score_summary(score: int, risk_counts: dict[str, int]) -> str:
    if score >= 85 and risk_counts["high"] == 0:
        return "The repository has strong static readiness signals. Runtime validation is still required on AMD ROCm."
    if risk_counts["high"]:
        return "High-severity issues should be addressed before this repository is treated as AMD-ready."
    if score >= 65:
        return "The repository has useful portability signals but still needs a ROCm-specific CI gate."
    return "The repository needs clearer tests, containers, or runtime validation before ROCm readiness can be trusted."


def _build_fix_categories(risks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    categories: dict[str, dict[str, Any]] = {}
    for risk in risks:
        category = str(risk["fix_category"])
        bucket = categories.setdefault(category, {"category": category, "risk_ids": [], "count": 0})
        bucket["risk_ids"].append(risk["id"])
        bucket["count"] += int(risk.get("count", 1))

    return sorted(categories.values(), key=lambda item: (-int(item["count"]), str(item["category"])))
