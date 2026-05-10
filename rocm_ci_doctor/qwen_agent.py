"""Optional Qwen-powered explanation layer."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from typing import Any
from urllib import error, request

from .env_loader import load_dotenv


DEFAULT_QWEN_BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
DEFAULT_QWEN_MODEL = "qwen-plus"
QWEN_AGENT_VERSION = "phase6"


class QwenClientError(RuntimeError):
    """Raised when a Qwen Cloud request cannot be completed."""


@dataclass(frozen=True)
class QwenResponse:
    """Small normalized Qwen response used by the UI and tests."""

    content: str
    model: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


def qwen_configured(api_key: str | None = None) -> bool:
    """Return whether an API key is available."""

    load_dotenv()
    return bool((api_key or os.environ.get("DASHSCOPE_API_KEY") or "").strip())


def qwen_model(default: str = DEFAULT_QWEN_MODEL) -> str:
    """Return the configured Qwen model name."""

    load_dotenv()
    return os.environ.get("QWEN_MODEL", default).strip() or default


def deterministic_agent_steps(analysis: dict[str, Any]) -> list[dict[str, str]]:
    """Return deterministic agent workflow cards for the UI."""

    assessment = analysis.get("assessment", {})
    summary = analysis.get("summary", {})
    files = analysis.get("files", {})
    risk_counts = assessment.get("risk_counts", {})
    generated = analysis.get("generated_bundle", {}).get("files", [])

    return [
        {
            "agent": "Repo Inspector Agent",
            "status": "Complete",
            "output": (
                f"Scanned {summary.get('files_scanned', 0)} files, found "
                f"{summary.get('gpu_pattern_count', 0)} GPU portability signals, and identified "
                f"{summary.get('risk_count', 0)} readiness risks."
            ),
        },
        {
            "agent": "CI Architect Agent",
            "status": "Complete",
            "output": (
                f"Detected {len(files.get('workflow_files', []))} existing workflow file(s) and "
                f"{len(analysis.get('ci_gaps', []))} CI gap(s). Recommended a dedicated ROCm CI gate."
            ),
        },
        {
            "agent": "Validation Agent",
            "status": "Complete",
            "output": (
                "Generated ROCm smoke test, benchmark script, Dockerfile starter, and AMD Cloud "
                f"validation runner across {len(generated)} bundle asset(s)."
            ),
        },
        {
            "agent": "Report Agent",
            "status": "Complete",
            "output": (
                f"Readiness score is {assessment.get('score', 0)}/{assessment.get('max_score', 100)} "
                f"with {risk_counts.get('high', 0)} high-risk item(s). "
                f"Assessment: {assessment.get('label', 'unknown')}."
            ),
        },
    ]


def deterministic_summary(analysis: dict[str, Any]) -> str:
    """Build a useful local summary when Qwen is not configured."""

    context = _compact_analysis_context(analysis)
    high_risks = context["top_risks"][:5]
    lines = [
        f"### Deterministic Agent Summary",
        "",
        f"**Repository:** `{context['repo_name']}`",
        f"**Readiness:** {context['score']}/{context['max_score']} - {context['label']}",
        f"**Risk mix:** high {context['risk_counts'].get('high', 0)}, "
        f"medium {context['risk_counts'].get('medium', 0)}, low {context['risk_counts'].get('low', 0)}",
        "",
        "**Recommended path:** add the generated ROCm CI workflow, run the generated smoke test on AMD Developer Cloud, and treat benchmark output as evidence for future PR validation.",
    ]
    if high_risks:
        lines.extend(["", "**Top risks:**"])
        for risk in high_risks:
            lines.append(f"- `{risk['id']}`: {risk['recommended_fix']}")
    return "\n".join(lines)


def generate_qwen_summary(
    analysis: dict[str, Any],
    *,
    api_key: str | None = None,
    model: str | None = None,
    base_url: str = DEFAULT_QWEN_BASE_URL,
    timeout: int = 45,
) -> QwenResponse:
    """Use Qwen to create a maintainer-facing remediation summary."""

    context = _compact_analysis_context(analysis)
    messages = [
        {
            "role": "system",
            "content": (
                "You are ROCm CI Doctor, a concise senior ML infrastructure engineer. "
                "Use only the provided static analysis context. Do not claim runtime correctness "
                "unless evidence is present. Write practical maintainer guidance."
            ),
        },
        {
            "role": "user",
            "content": (
                "Create a maintainer-facing ROCm readiness summary for this repository. "
                "Use four short sections: Current state, Blocking risks, Generated CI plan, Next PR steps. "
                "Keep it under 220 words.\n\n"
                f"Context JSON:\n{json.dumps(context, indent=2, sort_keys=True)}"
            ),
        },
    ]
    return call_qwen(messages, api_key=api_key, model=model, base_url=base_url, timeout=timeout)


def answer_qwen_question(
    analysis: dict[str, Any],
    question: str,
    *,
    api_key: str | None = None,
    model: str | None = None,
    base_url: str = DEFAULT_QWEN_BASE_URL,
    timeout: int = 45,
) -> QwenResponse:
    """Use Qwen to answer a question about the analysis result."""

    context = _compact_analysis_context(analysis)
    messages = [
        {
            "role": "system",
            "content": (
                "You are ROCm CI Doctor. Answer only from the provided repository analysis context. "
                "If the question asks for unsupported certainty, explain what runtime validation is still needed. "
                "Prefer concrete file names and next steps."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Repository analysis context:\n{json.dumps(context, indent=2, sort_keys=True)}\n\n"
                f"Question: {question}"
            ),
        },
    ]
    return call_qwen(messages, api_key=api_key, model=model, base_url=base_url, timeout=timeout)


def call_qwen(
    messages: list[dict[str, str]],
    *,
    api_key: str | None = None,
    model: str | None = None,
    base_url: str = DEFAULT_QWEN_BASE_URL,
    timeout: int = 45,
) -> QwenResponse:
    """Call Qwen Cloud through the OpenAI-compatible chat completions endpoint."""

    load_dotenv()
    resolved_key = (api_key or os.environ.get("DASHSCOPE_API_KEY") or "").strip()
    if not resolved_key:
        raise QwenClientError("DASHSCOPE_API_KEY is not configured.")

    resolved_model = (model or qwen_model()).strip() or DEFAULT_QWEN_MODEL
    url = f"{base_url.rstrip('/')}/chat/completions"
    payload = {
        "model": resolved_model,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 900,
    }
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {resolved_key}",
            "Content-Type": "application/json",
        },
    )

    try:
        with request.urlopen(req, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise QwenClientError(f"Qwen request failed with HTTP {exc.code}: {body[:400]}") from exc
    except error.URLError as exc:
        raise QwenClientError(f"Qwen request failed: {exc.reason}") from exc
    except TimeoutError as exc:
        raise QwenClientError("Qwen request timed out.") from exc

    try:
        parsed = json.loads(raw)
        content = parsed["choices"][0]["message"]["content"]
        usage = parsed.get("usage", {})
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise QwenClientError(f"Unexpected Qwen response shape: {raw[:400]}") from exc

    return QwenResponse(
        content=str(content).strip(),
        model=str(parsed.get("model", resolved_model)),
        prompt_tokens=_optional_int(usage.get("prompt_tokens")),
        completion_tokens=_optional_int(usage.get("completion_tokens")),
    )


def _compact_analysis_context(analysis: dict[str, Any]) -> dict[str, Any]:
    assessment = analysis.get("assessment", {})
    bundle = analysis.get("generated_bundle", {})
    top_risks = []
    for severity in ("high", "medium", "low"):
        for risk in assessment.get("risks_by_severity", {}).get(severity, []):
            top_risks.append(
                {
                    "severity": severity,
                    "id": risk.get("id"),
                    "count": risk.get("count", 1),
                    "message": risk.get("message"),
                    "category": risk.get("fix_category"),
                    "recommended_fix": risk.get("recommended_fix"),
                }
            )

    return {
        "agent_version": QWEN_AGENT_VERSION,
        "repo_name": analysis.get("repo_name", "repository"),
        "source": analysis.get("source", "unknown"),
        "score": assessment.get("score", 0),
        "max_score": assessment.get("max_score", 100),
        "label": assessment.get("label", "unknown"),
        "summary": assessment.get("summary", ""),
        "risk_counts": assessment.get("risk_counts", {}),
        "detected_stack": analysis.get("detected_stack", {}),
        "ci_gaps": analysis.get("ci_gaps", []),
        "files": analysis.get("files", {}),
        "top_risks": top_risks[:12],
        "generated_assets": [file.get("path") for file in bundle.get("files", [])],
    }


def _optional_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
