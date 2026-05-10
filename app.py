"""Streamlit UI for ROCm CI Doctor."""

from __future__ import annotations

import base64
import html
import json
import os
import textwrap
from pathlib import Path
from typing import Any

import streamlit as st

from rocm_ci_doctor.analyzer import analyze_repository
from rocm_ci_doctor.generator import generate_asset_bundle
from rocm_ci_doctor.qwen_agent import (
    DEFAULT_QWEN_MODEL,
    QwenClientError,
    answer_qwen_question,
    deterministic_agent_steps,
    deterministic_summary,
    generate_qwen_summary,
    qwen_configured,
)
from rocm_ci_doctor.repo_loader import RepoLoadError, load_repository
from rocm_ci_doctor.scoring import assess_repository
from rocm_ci_doctor.ui_helpers import (
    default_bundle_dir,
    generated_file_paths,
    list_sample_repositories,
    risk_rows,
    stack_rows,
    zip_directory_bytes,
)


LOGO_PATH = Path("assets/logo-small.png")
SIDEBAR_LOGO_PATH = Path("assets/docter_1-small.png")


st.set_page_config(
    page_title="ROCm CI Doctor",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main() -> None:
    _inject_css()
    _render_header()

    source = _sidebar_source()
    _sidebar_qwen_settings()
    output_dir = st.sidebar.text_input(
        "Bundle output directory",
        value=default_bundle_dir(source).as_posix(),
    )

    analyze_clicked = st.sidebar.button("Run Analysis", type="primary", use_container_width=True)

    if analyze_clicked:
        _run_analysis(source, Path(output_dir))

    state = st.session_state.get("analysis_state")
    if not state:
        _empty_state()
        return

    if state.get("error"):
        st.error(state["error"])
        return

    _render_results(state)


def _sidebar_source() -> str:
    if SIDEBAR_LOGO_PATH.exists():
        st.sidebar.markdown(
            _dedent_html(
                f"""
            <div class="sidebar-logo-card">
              <img src="{_image_data_uri(SIDEBAR_LOGO_PATH)}" alt="ROCm CI Doctor logo" />
            </div>
            """
            ),
            unsafe_allow_html=True,
        )

    st.sidebar.markdown("### Analysis Target")
    source_mode = st.sidebar.radio(
        "Repository source",
        ["Sample repository", "Local path", "GitHub URL"],
        label_visibility="collapsed",
    )

    if source_mode == "Sample repository":
        samples = list_sample_repositories()
        if not samples:
            return "samples"
        labels = [label for label, _ in samples]
        selected_label = st.sidebar.selectbox("Sample", labels)
        return dict(samples)[selected_label]

    if source_mode == "Local path":
        return st.sidebar.text_input("Local path", value="samples/cuda_heavy_repo")

    return st.sidebar.text_input("GitHub URL", value="https://github.com/pypa/sampleproject")


def _run_analysis(source: str, output_dir: Path) -> None:
    if not source.strip():
        st.session_state["analysis_state"] = {"error": "Source is empty."}
        return

    try:
        with st.spinner("Analyzing repository and generating ROCm CI assets..."):
            with load_repository(source) as loaded_repo:
                analysis = analyze_repository(
                    loaded_repo.path,
                    source=source,
                    loaded_from=loaded_repo.loaded_from,
                )
                analysis["assessment"] = assess_repository(analysis)
                bundle = generate_asset_bundle(analysis, output_dir)
                analysis["generated_bundle"] = bundle
    except RepoLoadError as exc:
        st.session_state["analysis_state"] = {"error": str(exc)}
        return
    except Exception as exc:  # pragma: no cover - Streamlit surface for unexpected demo errors.
        st.session_state["analysis_state"] = {"error": f"Unexpected error: {exc!r}"}
        return

    st.session_state["analysis_state"] = {
        "analysis": analysis,
        "output_dir": output_dir.as_posix(),
    }


def _empty_state() -> None:
    samples = list_sample_repositories()
    default_sample = samples[0][1] if samples else "samples/cuda_heavy_repo"
    _render_html(
        f"""
        <section class="chart">
          <div class="chart-section-rule">
            <span class="hero-index">01 / Intake</span>
            <span class="chart-rule-line"></span>
            <span class="hero-stamp hero-stamp-quiet">AWAITING SUBJECT</span>
          </div>

          <div class="chart-grid">
            <div class="chart-headline">
              <div class="chart-eyebrow">A note from the attending</div>
              <h2>
                Validate <em>faster.</em><br/>
                Regress <em>never.</em>
              </h2>
              <p>
                Point the instrument at a repository. ROCm CI Doctor will read its surface—
                dependencies, tests, Docker, workflows—and return a triage chart with the assets
                needed to admit AMD/ROCm into your gate.
              </p>
              <div class="chart-pulse">
                <svg viewBox="0 0 480 36" preserveAspectRatio="none" aria-hidden="true">
                  <path d="M0 18 L96 18 L114 4 L132 30 L150 10 L168 26 L186 18 L260 18 L278 8 L294 28 L312 18 L480 18"
                        fill="none" stroke="currentColor" stroke-width="1.3"
                        stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </div>
            </div>

            <aside class="chart-card">
              <div class="chart-card-tab">Procedure</div>
              <ol class="procedure">
                <li>
                  <em>01</em>
                  <strong>Scan</strong>
                  <span>Read the repository surface — every file is signal.</span>
                </li>
                <li>
                  <em>02</em>
                  <strong>Score</strong>
                  <span>Triage AMD/ROCm readiness against a deterministic rubric.</span>
                </li>
                <li>
                  <em>03</em>
                  <strong>Ship</strong>
                  <span>Emit a CI validation bundle ready for AMD Developer Cloud.</span>
                </li>
              </ol>
              <div class="chart-card-foot">
                <span>Default subject</span>
                <code>{html.escape(default_sample)}</code>
              </div>
            </aside>
          </div>

          <div class="creed-rule">
            <span class="creed-num">02</span>
            <span class="creed-line"></span>
            <span class="creed-label">First principles</span>
          </div>
          <div class="creed-grid">
            <div>
              <strong>Everything is signal.</strong>
              <span>Dependencies, tests, Docker, workflows — every file leaves a trace.</span>
            </div>
            <div>
              <strong>Signal becomes CI.</strong>
              <span>Static evidence is forged into a repeatable AMD validation suite.</span>
            </div>
            <div>
              <strong>CI becomes confidence.</strong>
              <span>Keep ROCm support from regressing one merge at a time.</span>
            </div>
          </div>
        </section>
        """
    )


def _render_results(state: dict[str, Any]) -> None:
    analysis = state["analysis"]
    assessment = analysis["assessment"]
    bundle = analysis["generated_bundle"]
    output_dir = Path(state["output_dir"])

    _render_score_cards(analysis, assessment, output_dir)

    overview_tab, risks_tab, assets_tab, ai_tab, report_tab, json_tab = st.tabs(
        ["Overview", "Risks", "Generated Assets", "AI Doctor", "Report", "JSON"]
    )

    with overview_tab:
        col_a, col_b = st.columns([1, 1])
        with col_a:
            st.subheader("Detected Stack")
            st.dataframe(stack_rows(analysis), use_container_width=True, hide_index=True)
        with col_b:
            st.subheader("Score Breakdown")
            st.dataframe(assessment["checks"], use_container_width=True, hide_index=True)

        st.subheader("CI Gaps")
        ci_gaps = analysis.get("ci_gaps", [])
        if ci_gaps:
            st.dataframe(ci_gaps, use_container_width=True, hide_index=True)
        else:
            st.success("No CI gaps detected by static analysis.")

    with risks_tab:
        _render_risk_lanes(assessment)
        rows = risk_rows(analysis)
        if rows:
            st.subheader("Risk Table")
            st.dataframe(rows, use_container_width=True, hide_index=True)
        else:
            st.success("No risks detected by static analysis.")

    with assets_tab:
        _render_assets(bundle, output_dir)

    with ai_tab:
        _render_ai_doctor(analysis)

    with report_tab:
        report_path = output_dir / "ROCM_CI_REPORT.md"
        if report_path.exists():
            report_text = report_path.read_text(encoding="utf-8")
            st.download_button(
                "Download Report",
                data=report_text,
                file_name="ROCM_CI_REPORT.md",
                mime="text/markdown",
                use_container_width=True,
            )
            st.markdown(report_text)
        else:
            st.warning("Report file was not generated.")

    with json_tab:
        st.code(json.dumps(analysis, indent=2, sort_keys=True), language="json")


def _render_score_cards(analysis: dict[str, Any], assessment: dict[str, Any], output_dir: Path) -> None:
    summary = analysis.get("summary", {})
    risk_counts = assessment.get("risk_counts", {})
    score = int(assessment["score"])
    status_label = _short_status_label(score)

    cards = [
        ("High Risks", str(risk_counts.get("high", 0)), "blocking findings"),
        ("CI Gaps", str(summary.get("ci_gap_count", 0)), "workflow coverage"),
        ("Files Scanned", str(summary.get("files_scanned", 0)), "static analysis"),
        ("Generated", str(len(generated_file_paths(analysis["generated_bundle"]))), "bundle assets"),
    ]
    markup = [
        textwrap.dedent(
            f"""
            <div class="chart-section-rule chart-section-rule-tight">
              <span class="hero-index">03 / Diagnosis</span>
              <span class="chart-rule-line"></span>
              <span class="hero-stamp hero-stamp-quiet">CHART OPENED</span>
            </div>
            <section class="result-hero">
              <div class="score-tile {_score_class(score)}">
                <div class="score-tile-corner reg-mark reg-tl"></div>
                <div class="score-tile-corner reg-mark reg-tr"></div>
                <div class="score-tile-corner reg-mark reg-bl"></div>
                <div class="score-tile-corner reg-mark reg-br"></div>
                <div class="score-label">Readiness score</div>
                <div class="score-value">{score}<span>/{assessment['max_score']}</span></div>
                <svg class="score-pulse" viewBox="0 0 240 24" preserveAspectRatio="none" aria-hidden="true">
                  <path d="M0 12 L60 12 L72 4 L84 20 L96 8 L108 18 L120 12 L240 12"
                        fill="none" stroke="currentColor" stroke-width="1.4"
                        stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <div class="score-state">{html.escape(status_label)}</div>
              </div>
              <div class="result-context">
                <div class="result-eyebrow">— Findings, in brief</div>
                <h2>{html.escape(str(analysis.get("repo_name", "repository")))}</h2>
                <p>{html.escape(assessment["label"])}</p>
                <div class="run-summary">
                  <span><em>Subject</em> <code>{html.escape(str(analysis.get("source", "unknown")))}</code></span>
                  <span><em>Bundle</em> <code>{html.escape(output_dir.as_posix())}</code></span>
                </div>
              </div>
            </section>
            <div class="metric-grid">
            """
        ).strip()
    ]
    for index, (label, value, caption) in enumerate(cards, start=1):
        markup.append(
            textwrap.dedent(
                f"""
                <div class="metric-card">
                  <div class="metric-num">{index:02d}</div>
                  <div class="metric-label">{html.escape(label)}</div>
                  <div class="metric-value">{html.escape(value)}</div>
                  <div class="metric-caption">{html.escape(caption)}</div>
                </div>
                """
            ).strip()
        )
    markup.append("</div>")
    _render_html("\n".join(markup))


def _render_assets(bundle: dict[str, Any], output_dir: Path) -> None:
    st.subheader("Generated Bundle")
    _render_asset_cards(bundle)

    if output_dir.exists():
        st.download_button(
            "Download Bundle ZIP",
            data=zip_directory_bytes(output_dir),
            file_name=f"{output_dir.name}.zip",
            mime="application/zip",
            use_container_width=True,
        )

    file_paths = generated_file_paths(bundle)
    if not file_paths:
        st.warning("No generated files found in manifest.")
        return

    selected = st.selectbox("Preview file", file_paths)
    selected_path = output_dir / selected
    if selected_path.exists():
        language = _language_for_path(selected)
        st.code(selected_path.read_text(encoding="utf-8"), language=language)
    else:
        st.warning(f"Generated file is missing: {selected}")


def _render_ai_doctor(analysis: dict[str, Any]) -> None:
    api_key = _qwen_api_key()
    model = _qwen_model()
    configured = qwen_configured(api_key)

    _render_agent_cards(deterministic_agent_steps(analysis))

    status = "Qwen enabled" if configured else "Qwen not configured"
    note = (
        f"Using `{html.escape(model)}` for maintainer summaries and Ask the Doctor."
        if configured
        else "Set `DASHSCOPE_API_KEY` in your shell or enter a session API key in the sidebar to enable Qwen."
    )
    _render_html(
        f"""
        <section class="qwen-status {'qwen-on' if configured else 'qwen-off'}">
          <div>
            <div class="qwen-status-label">{html.escape(status)}</div>
            <div class="qwen-status-copy">{note}</div>
          </div>
          <div class="qwen-badge">qwen-plus</div>
        </section>
        """
    )

    st.markdown(deterministic_summary(analysis))

    summary_key = f"qwen_summary::{analysis.get('source', '')}"
    if st.button("Generate Qwen Maintainer Summary", disabled=not configured, use_container_width=True):
        try:
            with st.spinner("Asking Qwen to summarize the ROCm remediation plan..."):
                response = generate_qwen_summary(analysis, api_key=api_key, model=model)
            st.session_state[summary_key] = response.content
            st.session_state[f"{summary_key}::meta"] = response.model
        except QwenClientError as exc:
            st.error(str(exc))

    if summary_key in st.session_state:
        st.subheader("Qwen Maintainer Summary")
        st.markdown(st.session_state[summary_key])
        model_used = st.session_state.get(f"{summary_key}::meta")
        if model_used:
            st.caption(f"Generated with {model_used}. Deterministic analyzer output remains the source of truth.")

    st.subheader("Ask the Doctor")
    question = st.text_area(
        "Question",
        value="What should I fix first before adding the generated ROCm CI workflow?",
        label_visibility="collapsed",
    )
    ask_key = f"qwen_answer::{analysis.get('source', '')}"
    if st.button("Ask Qwen", disabled=not configured or not question.strip(), use_container_width=True):
        try:
            with st.spinner("Asking Qwen about this analysis..."):
                response = answer_qwen_question(analysis, question, api_key=api_key, model=model)
            st.session_state[ask_key] = response.content
            st.session_state[f"{ask_key}::meta"] = response.model
        except QwenClientError as exc:
            st.error(str(exc))

    if ask_key in st.session_state:
        st.markdown(st.session_state[ask_key])
        model_used = st.session_state.get(f"{ask_key}::meta")
        if model_used:
            st.caption(f"Answered with {model_used}.")


def _render_agent_cards(steps: list[dict[str, str]]) -> None:
    markup = [
        '<div class="chart-section-rule chart-section-rule-tight">'
        '<span class="hero-index">05 / Rounds</span>'
        '<span class="chart-rule-line"></span>'
        '<span class="hero-stamp hero-stamp-quiet">CONSULTING TEAM</span>'
        '</div>',
        '<div class="agent-grid">',
    ]
    for index, step in enumerate(steps, start=1):
        markup.append(
            textwrap.dedent(
                f"""
                <div class="agent-card">
                  <div class="agent-num">{index:02d}</div>
                  <div class="agent-status">{html.escape(step["status"])}</div>
                  <div class="agent-name">{html.escape(step["agent"])}</div>
                  <div class="agent-output">{html.escape(step["output"])}</div>
                </div>
                """
            ).strip()
        )
    markup.append("</div>")
    _render_html("\n".join(markup))


def _language_for_path(path: str) -> str:
    if path.endswith((".yml", ".yaml")):
        return "yaml"
    if path.endswith(".py"):
        return "python"
    if path.endswith(".md"):
        return "markdown"
    if "Dockerfile" in Path(path).name:
        return "dockerfile"
    if path.endswith(".json"):
        return "json"
    return "text"


def _render_header() -> None:
    sidebar_logo_html = ""
    if SIDEBAR_LOGO_PATH.exists():
        sidebar_logo_html = f'<img src="{_image_data_uri(SIDEBAR_LOGO_PATH)}" alt="ROCm CI Doctor mark" />'
    logo_html = ""
    if LOGO_PATH.exists():
        logo_html = f'<img src="{_image_data_uri(LOGO_PATH)}" alt="ROCm CI Doctor logo" />'
    _render_html(
        f"""
        <div class="masthead">
          <div class="masthead-mark">{sidebar_logo_html}
            <div class="masthead-meta">
              <span class="masthead-title">ROCm CI Doctor</span>
              <span class="masthead-sub">Diagnostic Instrument · AMD Readiness</span>
            </div>
          </div>
          <div class="masthead-nav">
            <span><em>01</em>Scan</span>
            <span><em>02</em>Score</span>
            <span><em>03</em>Generate</span>
            <span><em>04</em>Explain</span>
          </div>
        </div>

        <header class="hero">
          <div class="hero-rule">
            <span class="hero-index">00 / Examination</span>
            <svg class="ekg" viewBox="0 0 600 40" preserveAspectRatio="none" aria-hidden="true">
              <path d="M0 20 L120 20 L138 20 L150 6 L168 34 L186 12 L204 28 L222 20 L600 20"
                    fill="none" stroke="currentColor" stroke-width="1.4"
                    stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span class="hero-stamp">REC · LIVE</span>
          </div>
          <div class="hero-grid">
            <div class="hero-copy">
              <div class="hero-eyebrow">A diagnostic instrument for</div>
              <h1>
                <em>AMD</em> readiness,<br/>
                measured like a pulse.
              </h1>
              <p>
                ROCm CI Doctor reads repository structure as <span class="ink-mark">vital signs</span>—
                dependencies, tests, Docker, workflows—and returns a triage score, a maintainer's chart,
                and a validation bundle ready for the AMD Developer Cloud.
              </p>
              <div class="hero-tape">
                <span>STATIC SIGNAL</span>
                <span class="dot"></span>
                <span>READINESS SCORE</span>
                <span class="dot"></span>
                <span>CI BUNDLE</span>
                <span class="dot"></span>
                <span>QWEN ROUNDS</span>
              </div>
            </div>
            <div class="hero-mark">
              <div class="hero-mark-frame">
                <span class="reg-mark reg-tl"></span>
                <span class="reg-mark reg-tr"></span>
                <span class="reg-mark reg-bl"></span>
                <span class="reg-mark reg-br"></span>
                {logo_html}
              </div>
            </div>
          </div>
        </header>
        """
    )


def _render_risk_lanes(assessment: dict[str, Any]) -> None:
    risk_counts = assessment.get("risk_counts", {})
    lanes = [
        ("high", "Acute", "High", risk_counts.get("high", 0), "Fix before treating the repo as AMD-ready."),
        ("medium", "Subacute", "Medium", risk_counts.get("medium", 0), "Review before enabling the PR gate."),
        ("low", "Watch", "Low", risk_counts.get("low", 0), "Track as validation notes."),
    ]
    markup = [
        '<div class="chart-section-rule chart-section-rule-tight">'
        '<span class="hero-index">04 / Triage</span>'
        '<span class="chart-rule-line"></span>'
        '<span class="hero-stamp hero-stamp-quiet">RISK LANES</span>'
        '</div>',
        '<div class="risk-grid">',
    ]
    for css_name, severity, label, count, note in lanes:
        markup.append(
            textwrap.dedent(
                f"""
            <div class="risk-card risk-{css_name}">
              <div class="risk-head">
                <span class="risk-severity">{html.escape(severity)}</span>
                <span class="risk-label">{html.escape(label)}</span>
              </div>
              <div class="risk-count">{count}</div>
              <div class="risk-note">{html.escape(note)}</div>
            </div>
            """
            ).strip()
        )
    markup.append("</div>")
    _render_html("\n".join(markup))


def _render_asset_cards(bundle: dict[str, Any]) -> None:
    files = bundle.get("files", [])
    if not files:
        st.warning("No generated files found in manifest.")
        return
    markup = [
        '<div class="chart-section-rule chart-section-rule-tight">'
        '<span class="hero-index">06 / Discharge</span>'
        '<span class="chart-rule-line"></span>'
        '<span class="hero-stamp hero-stamp-quiet">BUNDLE MANIFEST</span>'
        '</div>',
        '<div class="asset-grid">',
    ]
    for index, file in enumerate(files, start=1):
        path = str(file.get("path", ""))
        size = int(file.get("bytes", 0))
        markup.append(
            textwrap.dedent(
                f"""
            <div class="asset-card">
              <div class="asset-tab">FILE · {index:02d}</div>
              <div class="asset-path">{html.escape(path)}</div>
              <div class="asset-meta">{size:,} bytes</div>
            </div>
            """
            ).strip()
        )
    markup.append("</div>")
    _render_html("\n".join(markup))


def _sidebar_qwen_settings() -> None:
    st.sidebar.markdown("### Qwen Agent")
    st.sidebar.text_input(
        "Qwen API key",
        type="password",
        key="qwen_api_key_input",
        help="Optional. Leave empty to use DASHSCOPE_API_KEY from the shell environment.",
    )
    st.sidebar.text_input(
        "Qwen model",
        value=os.environ.get("QWEN_MODEL", DEFAULT_QWEN_MODEL),
        key="qwen_model_input",
    )


def _qwen_api_key() -> str | None:
    value = st.session_state.get("qwen_api_key_input")
    return str(value).strip() if value else os.environ.get("DASHSCOPE_API_KEY")


def _qwen_model() -> str:
    value = st.session_state.get("qwen_model_input")
    return str(value).strip() if value else os.environ.get("QWEN_MODEL", DEFAULT_QWEN_MODEL)


def _short_status_label(score: int) -> str:
    if score >= 85:
        return "Ready"
    if score >= 65:
        return "Close"
    if score >= 40:
        return "Needs work"
    return "High risk"


def _score_class(score: int) -> str:
    if score >= 85:
        return "score-ready"
    if score >= 65:
        return "score-close"
    if score >= 40:
        return "score-work"
    return "score-risk"


def _image_data_uri(path: Path) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _render_html(markup: str) -> None:
    st.markdown(_dedent_html(markup), unsafe_allow_html=True)


def _dedent_html(markup: str) -> str:
    normalized = textwrap.dedent(markup).strip()
    return "\n".join(line.lstrip() for line in normalized.splitlines())


def _inject_css() -> None:
    st.markdown(
        """
        <style>
        @import url("https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400..700;1,9..144,400..700&family=DM+Sans:ital,opsz,wght@0,9..40,300..700;1,9..40,400..600&family=JetBrains+Mono:wght@400;500;600;700&display=swap");

        :root {
          --paper:      #F4EEE2;
          --paper-2:    #EDE6D5;
          --paper-3:    #E3DBC4;
          --ink:        #15110D;
          --ink-2:      #2C261F;
          --bone:       #D5CAB1;
          --bone-2:     #C7BB9F;
          --steam:      #6E665B;
          --steam-2:    #8C8377;
          --pulse:      #D6282A;
          --pulse-deep: #B11A1C;
          --pulse-soft: #F2D8D8;
          --pulse-glow: rgba(214, 40, 42, 0.22);
          --healthy:    #2D5A3D;
          --healthy-soft:#DCE7DA;
          --caution:    #A86A1F;
          --caution-soft:#EFE0C5;
          --shadow-paper: 0 22px 50px -22px rgba(22, 17, 12, 0.28);
          --shadow-card: 0 10px 24px -14px rgba(22, 17, 12, 0.18);
          /* legacy aliases for any remaining styles */
          --rcd-bg: var(--paper);
          --rcd-panel: var(--paper);
          --rcd-paper: var(--paper-2);
          --rcd-ink: var(--ink);
          --rcd-text: var(--ink);
          --rcd-muted: var(--steam);
          --rcd-border: var(--bone);
          --rcd-red: var(--pulse);
          --rcd-red-dark: var(--pulse-deep);
          --rcd-shadow: var(--shadow-paper);
        }

        header[data-testid="stHeader"],
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        #MainMenu,
        footer {
          display: none !important;
          visibility: hidden !important;
          height: 0 !important;
        }

        .stApp {
          background:
            radial-gradient(circle at 0% 0%, rgba(214, 40, 42, 0.05) 0, transparent 38%),
            radial-gradient(circle at 100% 100%, rgba(45, 90, 61, 0.04) 0, transparent 50%),
            repeating-linear-gradient(0deg, rgba(22, 17, 12, 0.018) 0 1px, transparent 1px 4px),
            var(--paper);
          color: var(--ink);
          font-family: "DM Sans", "Helvetica Neue", Helvetica, Arial, sans-serif;
          font-feature-settings: "ss01";
          font-size: 16px;
          line-height: 1.5;
        }

        [data-testid="stSidebar"] {
          background:
            linear-gradient(180deg, var(--paper-2) 0%, var(--paper) 38%, var(--paper-2) 100%);
          border-right: 1px solid var(--bone);
        }

        [data-testid="stSidebar"] * {
          color: var(--ink-2);
        }

        [data-testid="stSidebar"] section {
          padding-top: 1.2rem;
        }

        [data-testid="stSidebar"] h3 {
          font-family: "Fraunces", "Iowan Old Style", Georgia, serif;
          font-style: italic;
          font-weight: 500;
          font-size: 1.2rem;
          color: var(--ink);
          margin: 1.5rem 0 0.45rem;
          letter-spacing: -0.005em;
        }

        [data-testid="stSidebar"] input,
        [data-testid="stSidebar"] textarea {
          color: var(--ink) !important;
          background: var(--paper) !important;
          border: 1px solid var(--bone) !important;
          border-radius: 2px !important;
          min-height: 44px;
          font-family: "JetBrains Mono", monospace !important;
          font-size: 0.86rem !important;
        }

        [data-testid="stSidebar"] input::placeholder {
          color: var(--steam-2) !important;
        }

        [data-testid="stSidebar"] [role="radiogroup"] label {
          background: var(--paper);
          border: 1px solid var(--bone);
          border-radius: 2px;
          padding: 0.4rem 0.6rem;
          margin-bottom: 0.32rem;
          box-shadow: var(--shadow-card);
          transition: border-color 200ms ease, transform 200ms ease;
        }

        [data-testid="stSidebar"] [role="radiogroup"] label:hover {
          border-color: var(--ink);
          transform: translateX(2px);
        }

        [data-testid="stSidebar"] [data-baseweb="select"] > div {
          background: var(--paper);
          border-color: var(--bone);
          border-radius: 2px;
        }

        [data-testid="stSidebar"] [data-baseweb="radio"] div,
        [data-testid="stSidebar"] [data-baseweb="select"] *,
        [data-testid="stSidebar"] [role="option"] *,
        [data-testid="stSidebar"] label p {
          color: var(--ink-2) !important;
          font-family: "DM Sans", sans-serif !important;
        }

        .sidebar-logo-card {
          position: relative;
          background: linear-gradient(180deg, var(--paper) 0%, var(--paper-2) 100%);
          border: 1px solid var(--ink);
          border-radius: 2px;
          padding: 1.5rem 1rem 1.15rem;
          margin: 0.2rem 0 1.4rem;
          box-shadow: var(--shadow-paper);
        }

        .sidebar-logo-card::before,
        .sidebar-logo-card::after {
          content: "";
          position: absolute;
          width: 9px;
          height: 9px;
          border: 1px solid var(--ink);
        }
        .sidebar-logo-card::before { top: 5px; left: 5px; border-right: 0; border-bottom: 0; }
        .sidebar-logo-card::after  { bottom: 5px; right: 5px; border-left: 0; border-top: 0; }

        .sidebar-logo-card img {
          display: block;
          width: 100%;
          max-height: 200px;
          object-fit: contain;
        }

        .block-container {
          padding-top: 0;
          padding-bottom: 4rem;
          max-width: 1480px;
        }

        /* === Masthead === */
        .masthead {
          display: grid;
          grid-template-columns: minmax(0, 1.3fr) auto;
          align-items: center;
          gap: 1.6rem;
          padding: 1.1rem 0 0.85rem;
          border-bottom: 1px solid var(--ink);
          position: relative;
          animation: paper-rise 700ms cubic-bezier(.2,.8,.2,1) both;
        }
        .masthead::after {
          content: "";
          position: absolute;
          left: 0; right: 0;
          bottom: -3px;
          height: 1px;
          background: var(--ink);
          opacity: 0.45;
        }
        .masthead-mark {
          display: flex;
          align-items: center;
          gap: 0.95rem;
        }
        .masthead-mark img {
          width: 56px;
          height: 56px;
          object-fit: contain;
          display: block;
        }
        .masthead-meta {
          display: flex;
          flex-direction: column;
          gap: 0.18rem;
        }
        .masthead-title {
          font-family: "Fraunces", serif;
          font-style: italic;
          font-weight: 500;
          font-size: 1.55rem;
          color: var(--ink);
          letter-spacing: -0.012em;
          line-height: 1;
          font-variation-settings: "opsz" 144, "SOFT" 50;
        }
        .masthead-sub {
          font-family: "JetBrains Mono", monospace;
          font-size: 0.7rem;
          letter-spacing: 0.2em;
          text-transform: uppercase;
          color: var(--steam);
          line-height: 1;
        }
        .masthead-nav {
          display: flex;
          gap: 1.4rem;
          font-family: "JetBrains Mono", monospace;
          font-size: 0.74rem;
          letter-spacing: 0.16em;
          text-transform: uppercase;
          color: var(--ink-2);
        }
        .masthead-nav em {
          font-style: normal;
          color: var(--pulse);
          font-weight: 700;
          margin-right: 0.4rem;
        }
        /* === Hero === */
        .hero {
          padding: 2.4rem 0 2.6rem;
          border-bottom: 1px solid var(--bone);
          position: relative;
          animation: paper-rise 800ms 100ms cubic-bezier(.2,.8,.2,1) both;
        }
        .hero-rule {
          display: grid;
          grid-template-columns: auto 1fr auto;
          align-items: center;
          gap: 1.1rem;
          margin-bottom: 1.8rem;
          color: var(--steam);
        }
        .hero-index {
          font-family: "JetBrains Mono", monospace;
          font-size: 0.72rem;
          letter-spacing: 0.22em;
          text-transform: uppercase;
          color: var(--ink);
          font-weight: 600;
        }
        .ekg {
          width: 100%;
          height: 30px;
          color: var(--pulse);
          filter: drop-shadow(0 0 6px var(--pulse-glow));
        }
        .ekg path {
          stroke-dasharray: 600;
          stroke-dashoffset: 600;
          animation: ekg-draw 2.6s 0.4s cubic-bezier(.6,0,.2,1) forwards,
                     ekg-pulse 2.4s 3.2s ease-in-out infinite;
        }
        .hero-stamp {
          font-family: "JetBrains Mono", monospace;
          font-size: 0.66rem;
          letter-spacing: 0.24em;
          text-transform: uppercase;
          font-weight: 700;
          color: var(--pulse);
          border: 1px solid var(--pulse);
          padding: 0.3rem 0.55rem;
          border-radius: 2px;
        }
        .hero-stamp::before {
          content: "";
          display: inline-block;
          width: 6px; height: 6px;
          background: var(--pulse);
          border-radius: 50%;
          margin-right: 0.45rem;
          vertical-align: middle;
          animation: pulse-dot 1.8s ease-in-out infinite;
        }
        .hero-stamp-quiet {
          color: var(--ink);
          border-color: var(--ink-2);
        }
        .hero-stamp-quiet::before { background: var(--ink); animation: none; }

        .hero-grid {
          display: grid;
          grid-template-columns: minmax(0, 1.6fr) minmax(0, 1fr);
          gap: 3rem;
          align-items: start;
        }
        .hero-eyebrow {
          font-family: "DM Sans", sans-serif;
          font-style: italic;
          font-size: 1rem;
          color: var(--steam);
          margin-bottom: 0.55rem;
        }
        .hero h1 {
          font-family: "Fraunces", "Iowan Old Style", Georgia, serif;
          font-weight: 400;
          font-size: clamp(3.2rem, 6.6vw, 5.8rem);
          line-height: 0.95;
          letter-spacing: -0.022em;
          color: var(--ink);
          margin: 0 0 1.2rem;
          font-variation-settings: "opsz" 144, "SOFT" 30;
          max-width: 880px;
        }
        .hero h1 em {
          font-style: italic;
          color: var(--pulse);
          font-variation-settings: "opsz" 144, "SOFT" 100;
        }
        .hero p {
          font-size: 1.06rem;
          line-height: 1.58;
          color: var(--ink-2);
          margin: 0 0 1.4rem;
          max-width: 640px;
        }
        .ink-mark {
          background: linear-gradient(180deg, transparent 60%, var(--pulse-soft) 60% 95%, transparent 95%);
          padding: 0 0.15em;
          font-style: italic;
          font-family: "Fraunces", serif;
          color: var(--ink);
        }
        .hero-tape {
          display: flex;
          align-items: center;
          gap: 0.7rem;
          flex-wrap: wrap;
          font-family: "JetBrains Mono", monospace;
          font-size: 0.72rem;
          letter-spacing: 0.18em;
          text-transform: uppercase;
          color: var(--ink);
          padding: 0.7rem 0.9rem;
          border: 1px solid var(--ink);
          background: var(--paper-2);
          border-radius: 2px;
          margin-top: 0.4rem;
          width: fit-content;
        }
        .hero-tape .dot {
          width: 4px;
          height: 4px;
          border-radius: 50%;
          background: var(--pulse);
        }

        .hero-mark {
          display: flex;
          flex-direction: column;
          gap: 0.65rem;
          align-items: center;
        }
        .hero-mark-frame {
          position: relative;
          background: var(--paper);
          border: 1px solid var(--ink);
          padding: 1.8rem 1.6rem 1.4rem;
          width: 100%;
          max-width: 360px;
          box-shadow: var(--shadow-paper);
        }
        .hero-mark-frame img {
          display: block;
          width: 100%;
          max-height: 220px;
          object-fit: contain;
        }
        .reg-mark {
          position: absolute;
          width: 14px;
          height: 14px;
          pointer-events: none;
        }
        .reg-mark::before, .reg-mark::after {
          content: "";
          position: absolute;
          background: var(--ink);
        }
        .reg-mark::before {
          width: 14px; height: 1px;
          top: 50%; left: 0;
          transform: translateY(-50%);
        }
        .reg-mark::after {
          width: 1px; height: 14px;
          left: 50%; top: 0;
          transform: translateX(-50%);
        }
        .reg-tl { top: -7px; left: -7px; }
        .reg-tr { top: -7px; right: -7px; }
        .reg-bl { bottom: -7px; left: -7px; }
        .reg-br { bottom: -7px; right: -7px; }

        /* === Chart (welcome) === */
        .chart {
          padding: 2.4rem 0 1.5rem;
          animation: paper-rise 700ms 200ms cubic-bezier(.2,.8,.2,1) both;
        }
        .chart-section-rule {
          display: grid;
          grid-template-columns: auto 1fr auto;
          align-items: center;
          gap: 1rem;
          margin: 2.4rem 0 1.6rem;
        }
        .chart-section-rule-tight { margin: 1.6rem 0 1rem; }
        .chart-rule-line {
          height: 1px;
          background: linear-gradient(90deg, var(--ink) 0, var(--ink) 24px, var(--bone) 24px, var(--bone) 100%);
          position: relative;
        }
        .chart-rule-line::after {
          content: "";
          position: absolute;
          right: 0; top: 50%;
          width: 6px; height: 6px;
          border-radius: 50%;
          background: var(--pulse);
          transform: translateY(-50%);
        }
        .chart-grid {
          display: grid;
          grid-template-columns: minmax(0, 1.45fr) minmax(0, 0.95fr);
          gap: 2.6rem;
          align-items: start;
        }
        .chart-eyebrow {
          font-family: "Fraunces", serif;
          font-style: italic;
          font-size: 1rem;
          color: var(--steam);
          margin-bottom: 0.75rem;
        }
        .chart-headline h2 {
          font-family: "Fraunces", "Iowan Old Style", Georgia, serif;
          font-weight: 400;
          font-size: clamp(2.6rem, 5.4vw, 4.8rem);
          line-height: 0.96;
          letter-spacing: -0.02em;
          color: var(--ink);
          margin: 0 0 1.1rem;
          font-variation-settings: "opsz" 144;
        }
        .chart-headline h2 em {
          font-style: italic;
          color: var(--pulse);
        }
        .chart-headline p {
          font-size: 1.04rem;
          line-height: 1.55;
          color: var(--ink-2);
          margin: 0 0 1.4rem;
          max-width: 580px;
        }
        .chart-pulse {
          margin-top: 0.5rem;
          color: var(--pulse);
          opacity: 0.9;
        }
        .chart-pulse svg {
          width: 100%;
          max-width: 480px;
          height: 32px;
          display: block;
        }
        .chart-pulse path {
          stroke-dasharray: 480;
          stroke-dashoffset: 480;
          animation: ekg-draw 2.4s 0.6s cubic-bezier(.6,0,.2,1) forwards,
                     ekg-pulse 2.6s 3.4s ease-in-out infinite;
        }

        .chart-card {
          position: relative;
          background: var(--paper);
          border: 1px solid var(--ink);
          padding: 1.4rem 1.5rem 1.2rem;
          box-shadow: var(--shadow-paper);
        }
        .chart-card-tab {
          position: absolute;
          top: -12px; left: 1.2rem;
          background: var(--ink);
          color: var(--paper);
          font-family: "JetBrains Mono", monospace;
          font-size: 0.66rem;
          letter-spacing: 0.24em;
          text-transform: uppercase;
          padding: 0.32rem 0.65rem;
          font-weight: 600;
        }
        .procedure {
          list-style: none;
          margin: 0.8rem 0 1rem;
          padding: 0;
        }
        .procedure li {
          display: grid;
          grid-template-columns: 38px 1fr;
          gap: 0.4rem 0.85rem;
          padding: 0.85rem 0;
          border-bottom: 1px dashed var(--bone-2);
        }
        .procedure li:last-child { border-bottom: 0; }
        .procedure em {
          grid-row: 1 / span 2;
          align-self: start;
          font-family: "JetBrains Mono", monospace;
          font-style: normal;
          font-weight: 600;
          font-size: 0.78rem;
          color: var(--pulse);
          letter-spacing: 0.05em;
          border: 1px solid var(--pulse);
          padding: 0.22rem 0.32rem;
          text-align: center;
          border-radius: 2px;
        }
        .procedure strong {
          font-family: "Fraunces", serif;
          font-style: italic;
          font-weight: 500;
          font-size: 1.18rem;
          color: var(--ink);
          line-height: 1.1;
        }
        .procedure span {
          font-size: 0.92rem;
          color: var(--steam);
          line-height: 1.45;
        }
        .chart-card-foot {
          display: flex;
          flex-direction: column;
          gap: 0.3rem;
          padding-top: 0.75rem;
          border-top: 1px solid var(--ink);
        }
        .chart-card-foot span {
          font-family: "JetBrains Mono", monospace;
          letter-spacing: 0.2em;
          text-transform: uppercase;
          color: var(--steam);
          font-size: 0.66rem;
        }
        .chart-card-foot code {
          background: var(--paper-2);
          border: 1px solid var(--bone);
          border-radius: 2px;
          padding: 0.18rem 0.42rem;
          color: var(--pulse-deep);
          font-size: 0.82rem;
          font-family: "JetBrains Mono", monospace;
          width: fit-content;
        }

        .creed-rule {
          display: grid;
          grid-template-columns: auto 1fr auto;
          align-items: center;
          gap: 1.1rem;
          margin: 2.6rem 0 1.2rem;
        }
        .creed-num {
          font-family: "Fraunces", serif;
          font-style: italic;
          font-size: 2.6rem;
          color: var(--pulse);
          line-height: 1;
          font-weight: 500;
        }
        .creed-line {
          height: 1px;
          background: var(--ink);
        }
        .creed-label {
          font-family: "JetBrains Mono", monospace;
          font-size: 0.72rem;
          letter-spacing: 0.22em;
          text-transform: uppercase;
          color: var(--ink);
        }
        .creed-grid {
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 1.5rem;
        }
        .creed-grid > div {
          position: relative;
          padding-top: 1.05rem;
          border-top: 1px solid var(--ink);
        }
        .creed-grid > div::before {
          content: "";
          position: absolute;
          top: -3.5px; left: 0;
          width: 7px; height: 7px;
          border-radius: 50%;
          background: var(--pulse);
        }
        .creed-grid strong {
          display: block;
          font-family: "Fraunces", serif;
          font-style: italic;
          font-weight: 500;
          font-size: 1.55rem;
          letter-spacing: -0.005em;
          color: var(--ink);
          margin-bottom: 0.5rem;
          line-height: 1.1;
        }
        .creed-grid span {
          color: var(--steam);
          font-size: 0.95rem;
          line-height: 1.5;
        }

        /* === Grids === */
        .metric-grid,
        .risk-grid,
        .asset-grid,
        .agent-grid {
          display: grid;
          gap: 0.85rem;
          margin: 0.85rem 0 1.4rem;
        }
        .metric-grid { grid-template-columns: repeat(4, minmax(0, 1fr)); }
        .risk-grid   { grid-template-columns: repeat(3, minmax(0, 1fr)); }
        .asset-grid  { grid-template-columns: repeat(2, minmax(0, 1fr)); }
        .agent-grid  { grid-template-columns: repeat(4, minmax(0, 1fr)); }

        .metric-card,
        .risk-card,
        .asset-card,
        .agent-card {
          transition: transform 240ms cubic-bezier(.2,.8,.2,1),
                      box-shadow 240ms ease,
                      border-color 240ms ease;
        }
        .metric-card:hover,
        .risk-card:hover,
        .asset-card:hover,
        .agent-card:hover {
          transform: translateY(-3px);
          box-shadow: var(--shadow-paper);
        }

        /* === Metric cards === */
        .metric-card {
          position: relative;
          background: var(--paper);
          border: 1px solid var(--ink);
          padding: 1.05rem 1.15rem 1.1rem;
          min-height: 148px;
          box-shadow: var(--shadow-card);
        }
        .metric-num {
          position: absolute;
          top: 0.75rem; right: 0.95rem;
          font-family: "JetBrains Mono", monospace;
          font-size: 0.72rem;
          letter-spacing: 0.18em;
          color: var(--pulse);
          font-weight: 600;
        }
        .metric-label,
        .risk-label,
        .asset-meta {
          color: var(--steam);
          font-family: "JetBrains Mono", monospace;
          font-size: 0.66rem;
          letter-spacing: 0.22em;
          text-transform: uppercase;
          font-weight: 600;
        }
        .metric-value {
          font-family: "Fraunces", "Iowan Old Style", Georgia, serif;
          font-style: italic;
          font-weight: 500;
          font-size: 2.7rem;
          color: var(--ink);
          margin-top: 0.55rem;
          line-height: 1;
          font-variation-settings: "opsz" 144;
        }

        /* === Result hero === */
        .result-hero {
          display: grid;
          grid-template-columns: 320px minmax(0, 1fr);
          gap: 1rem;
          align-items: stretch;
          margin: 0 0 1.4rem;
          animation: paper-rise 600ms 60ms cubic-bezier(.2,.8,.2,1) both;
        }
        .score-tile {
          position: relative;
          background: var(--ink);
          color: var(--paper);
          padding: 1.5rem 1.4rem 1.4rem;
          min-height: 250px;
          overflow: hidden;
          display: flex;
          flex-direction: column;
          justify-content: space-between;
          box-shadow: var(--shadow-paper);
          transition: transform 240ms cubic-bezier(.2,.8,.2,1), box-shadow 240ms ease;
        }
        .score-tile:hover {
          transform: translateY(-3px);
        }
        .score-tile::after {
          content: "";
          position: absolute;
          inset: 0;
          background: radial-gradient(circle at 80% 20%, rgba(214, 40, 42, 0.18) 0, transparent 42%);
          pointer-events: none;
        }
        .score-tile-corner {
          width: 12px;
          height: 12px;
          z-index: 2;
        }
        .score-tile-corner::before,
        .score-tile-corner::after {
          background: var(--paper);
        }
        .score-tile-corner.reg-tl { top: 8px;    left: 8px;   }
        .score-tile-corner.reg-tr { top: 8px;    right: 8px;  }
        .score-tile-corner.reg-bl { bottom: 8px; left: 8px;   }
        .score-tile-corner.reg-br { bottom: 8px; right: 8px;  }
        .score-label,
        .result-eyebrow {
          font-family: "JetBrains Mono", monospace;
          font-size: 0.7rem;
          letter-spacing: 0.24em;
          text-transform: uppercase;
          color: var(--paper-3);
          font-weight: 500;
          position: relative;
          z-index: 1;
        }
        .score-value {
          font-family: "Fraunces", "Iowan Old Style", Georgia, serif;
          font-style: italic;
          font-weight: 500;
          font-size: 6.4rem;
          line-height: 0.9;
          color: var(--paper);
          letter-spacing: -0.022em;
          margin: 0.65rem 0 0.5rem;
          font-variation-settings: "opsz" 144, "SOFT" 30;
          position: relative;
          z-index: 1;
        }
        .score-value span {
          font-family: "JetBrains Mono", monospace;
          font-style: normal;
          font-size: 1.05rem;
          color: var(--steam-2);
          margin-left: 0.32rem;
          letter-spacing: 0.05em;
        }
        .score-pulse {
          height: 22px;
          width: 100%;
          color: var(--pulse);
          margin-bottom: 0.5rem;
          position: relative;
          z-index: 1;
        }
        .score-pulse path {
          stroke-dasharray: 240;
          stroke-dashoffset: 240;
          animation: ekg-draw 2.2s 0.2s cubic-bezier(.6,0,.2,1) forwards,
                     ekg-pulse 2.4s 2.6s ease-in-out infinite;
        }
        .score-state {
          font-family: "Fraunces", serif;
          font-style: italic;
          font-size: 1.3rem;
          color: var(--paper);
          font-weight: 500;
          position: relative;
          z-index: 1;
        }
        .score-risk  { border-left: 4px solid var(--pulse); }
        .score-close,
        .score-work  { border-left: 4px solid var(--caution); }
        .score-ready { border-left: 4px solid var(--healthy); }

        .result-context {
          position: relative;
          background: var(--paper);
          border: 1px solid var(--ink);
          padding: 1.55rem 1.65rem 1.3rem;
          box-shadow: var(--shadow-paper);
          transition: transform 240ms cubic-bezier(.2,.8,.2,1), box-shadow 240ms ease;
        }
        .result-context:hover {
          transform: translateY(-3px);
        }
        .result-eyebrow {
          font-family: "Fraunces", serif;
          font-style: italic;
          font-size: 1rem;
          color: var(--pulse);
          letter-spacing: 0;
          text-transform: none;
        }
        .result-context h2 {
          font-family: "Fraunces", "Iowan Old Style", Georgia, serif;
          font-style: italic;
          font-weight: 500;
          font-size: 2.7rem;
          letter-spacing: -0.02em;
          line-height: 1.02;
          color: var(--ink);
          margin: 0.35rem 0 0.55rem;
          font-variation-settings: "opsz" 144;
        }
        .result-context p {
          color: var(--ink-2);
          margin: 0 0 1.1rem;
          font-size: 1rem;
          line-height: 1.5;
        }
        .metric-caption,
        .risk-note {
          color: var(--steam);
          font-size: 0.88rem;
          margin-top: 0.5rem;
          line-height: 1.45;
        }
        .metric-caption {
          font-family: "DM Sans", sans-serif;
          font-style: italic;
        }

        .run-summary {
          display: flex;
          flex-wrap: wrap;
          align-items: baseline;
          gap: 1.1rem;
          padding: 0.85rem 0 0;
          border-top: 1px solid var(--bone);
          font-family: "JetBrains Mono", monospace;
          font-size: 0.78rem;
          color: var(--steam);
        }
        .run-summary span {
          display: inline-flex;
          gap: 0.5rem;
          align-items: baseline;
        }
        .run-summary em {
          font-style: normal;
          color: var(--ink);
          letter-spacing: 0.2em;
          font-size: 0.66rem;
          text-transform: uppercase;
          font-weight: 600;
        }
        .run-summary code,
        .empty-copy code {
          color: var(--pulse-deep);
          background: var(--paper-2);
          border: 1px solid var(--bone);
          border-radius: 2px;
          padding: 0.12rem 0.4rem;
          font-family: "JetBrains Mono", monospace;
          font-size: 0.78rem;
        }

        .status-pill {
          background: var(--pulse-soft);
          color: var(--pulse-deep);
          border: 1px solid var(--pulse);
          border-radius: 2px;
          padding: 0.3rem 0.65rem;
          font-family: "JetBrains Mono", monospace;
          font-size: 0.7rem;
          letter-spacing: 0.2em;
          text-transform: uppercase;
          font-weight: 700;
        }

        /* === Risk lanes === */
        .risk-card {
          position: relative;
          padding: 1.2rem 1.2rem 1.2rem;
          background: var(--paper);
          border: 1px solid var(--ink);
          box-shadow: var(--shadow-card);
        }
        .risk-card::before {
          content: "";
          position: absolute;
          top: 0; left: 0; right: 0;
          height: 6px;
        }
        .risk-head {
          display: flex;
          justify-content: space-between;
          align-items: baseline;
          margin: 0.4rem 0 0.4rem;
          gap: 0.8rem;
        }
        .risk-severity {
          font-family: "Fraunces", serif;
          font-style: italic;
          font-size: 1.25rem;
          font-weight: 500;
          color: var(--ink);
        }
        .risk-label {
          font-size: 0.66rem !important;
        }
        .risk-count {
          font-family: "Fraunces", "Iowan Old Style", Georgia, serif;
          font-style: italic;
          font-weight: 500;
          font-size: 3.2rem;
          line-height: 0.9;
          color: var(--ink);
          margin: 0.3rem 0 0.55rem;
          font-variation-settings: "opsz" 144;
        }
        .risk-note {
          font-family: "DM Sans", sans-serif;
        }
        .risk-high::before  { background: var(--pulse); }
        .risk-high           { background: linear-gradient(180deg, var(--pulse-soft) 0%, var(--paper) 60%); }
        .risk-medium::before { background: var(--caution); }
        .risk-medium         { background: linear-gradient(180deg, var(--caution-soft) 0%, var(--paper) 60%); }
        .risk-low::before    { background: var(--healthy); }
        .risk-low            { background: linear-gradient(180deg, var(--healthy-soft) 0%, var(--paper) 60%); }

        /* === Asset cards === */
        .asset-card {
          position: relative;
          background: var(--paper);
          border: 1px solid var(--ink);
          padding: 1.45rem 1.1rem 1rem;
          box-shadow: var(--shadow-card);
        }
        .asset-tab {
          position: absolute;
          top: -10px; left: 0.85rem;
          background: var(--ink);
          color: var(--paper);
          font-family: "JetBrains Mono", monospace;
          font-size: 0.62rem;
          letter-spacing: 0.24em;
          font-weight: 600;
          padding: 0.22rem 0.55rem;
        }
        .asset-path {
          color: var(--ink);
          font-family: "JetBrains Mono", "SFMono-Regular", monospace;
          font-size: 0.94rem;
          font-weight: 500;
          overflow-wrap: anywhere;
          line-height: 1.4;
        }
        .asset-meta {
          margin-top: 0.55rem;
          padding-top: 0.5rem;
          border-top: 1px dashed var(--bone);
          letter-spacing: 0.12em !important;
          font-size: 0.7rem !important;
        }

        /* === Agent cards === */
        .agent-card {
          position: relative;
          background: var(--paper);
          border: 1px solid var(--ink);
          padding: 1.05rem 1.1rem 1rem;
          min-height: 178px;
          box-shadow: var(--shadow-card);
        }
        .agent-card::after {
          content: "";
          position: absolute;
          left: 1.05rem; right: 1.05rem;
          bottom: 0;
          height: 2px;
          background: var(--pulse);
        }
        .agent-num {
          position: absolute;
          top: 0.85rem; right: 1.05rem;
          font-family: "Fraunces", serif;
          font-style: italic;
          font-size: 1.1rem;
          color: var(--pulse);
          font-weight: 500;
        }
        .agent-status {
          color: var(--pulse);
          font-family: "JetBrains Mono", monospace;
          font-size: 0.66rem;
          letter-spacing: 0.24em;
          text-transform: uppercase;
          font-weight: 700;
        }
        .agent-name {
          color: var(--ink);
          font-family: "Fraunces", "Iowan Old Style", Georgia, serif;
          font-style: italic;
          font-size: 1.4rem;
          font-weight: 500;
          line-height: 1.05;
          margin-top: 0.5rem;
          font-variation-settings: "opsz" 144;
        }
        .agent-output {
          color: var(--steam);
          font-size: 0.9rem;
          line-height: 1.5;
          margin-top: 0.65rem;
        }

        /* === Qwen status === */
        .qwen-status {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 1rem;
          padding: 1rem 1.15rem;
          margin: 0.6rem 0 1.2rem;
          background: var(--paper);
          border: 1px solid var(--ink);
          box-shadow: var(--shadow-card);
        }
        .qwen-on  { border-left: 4px solid var(--healthy); }
        .qwen-off { border-left: 4px solid var(--caution); }
        .qwen-status-label {
          font-family: "Fraunces", serif;
          font-style: italic;
          font-weight: 500;
          font-size: 1.2rem;
          color: var(--ink);
        }
        .qwen-status-copy {
          color: var(--steam);
          font-size: 0.92rem;
          margin-top: 0.2rem;
          line-height: 1.45;
        }
        .qwen-badge {
          flex: 0 0 auto;
          background: var(--ink);
          color: var(--paper);
          font-family: "JetBrains Mono", monospace;
          font-size: 0.7rem;
          letter-spacing: 0.22em;
          text-transform: uppercase;
          font-weight: 600;
          padding: 0.42rem 0.78rem;
        }

        /* === Code blocks === */
        div[data-testid="stCodeBlock"],
        .stCodeBlock,
        div[data-testid="stMarkdownContainer"] pre {
          width: 100%;
          max-width: 100%;
          background: #15110D !important;
          border: 1px solid var(--ink) !important;
          border-radius: 2px;
          box-shadow: var(--shadow-paper);
          overflow: hidden;
          position: relative;
        }
        div[data-testid="stCodeBlock"] pre,
        .stCodeBlock pre,
        div[data-testid="stMarkdownContainer"] pre {
          width: 100%;
          max-width: 100%;
          max-height: 720px;
          box-sizing: border-box;
          margin: 0 !important;
          padding: 1.1rem 1.15rem !important;
          background:
            linear-gradient(90deg, var(--pulse) 0, var(--pulse) 3px, transparent 3px),
            #15110D !important;
          color: #E5DDC8 !important;
          border-radius: 2px !important;
          overflow: auto !important;
          white-space: pre !important;
          font-size: 0.88rem !important;
          line-height: 1.6 !important;
        }
        div[data-testid="stCodeBlock"] code,
        .stCodeBlock code,
        div[data-testid="stMarkdownContainer"] pre code {
          color: #E5DDC8 !important;
          background: transparent !important;
          font-family: "JetBrains Mono", "SFMono-Regular", "Cascadia Code", monospace !important;
          font-size: 0.88rem !important;
          line-height: 1.6 !important;
          text-shadow: none !important;
        }
        div[data-testid="stCodeBlock"] span,
        .stCodeBlock span,
        div[data-testid="stMarkdownContainer"] pre span {
          background: transparent !important;
        }
        div[data-testid="stCodeBlock"] button,
        .stCodeBlock button {
          background: var(--paper) !important;
          border: 1px solid var(--bone) !important;
          color: var(--ink) !important;
          border-radius: 2px !important;
          font-family: "JetBrains Mono", monospace !important;
          font-size: 0.74rem !important;
          letter-spacing: 0.1em !important;
        }

        /* === Buttons === */
        div[data-testid="stButton"] > button,
        div[data-testid="stDownloadButton"] > button {
          border-radius: 2px;
          border: 1px solid var(--ink);
          background: var(--ink);
          color: var(--paper);
          font-family: "JetBrains Mono", monospace;
          font-size: 0.78rem;
          letter-spacing: 0.18em;
          text-transform: uppercase;
          font-weight: 600;
          padding: 0.7rem 1.1rem;
          transition: background 200ms ease, transform 200ms ease, border-color 200ms ease;
        }
        div[data-testid="stButton"] > button:hover,
        div[data-testid="stDownloadButton"] > button:hover {
          background: var(--pulse);
          border-color: var(--pulse);
          color: var(--paper);
          transform: translateY(-1px);
        }
        div[data-testid="stButton"] > button[kind="primary"] {
          background: var(--pulse);
          border-color: var(--pulse);
        }
        div[data-testid="stButton"] > button[kind="primary"]:hover {
          background: var(--pulse-deep);
          border-color: var(--pulse-deep);
        }

        /* === Tabs === */
        .stTabs [data-baseweb="tab-list"] {
          gap: 0;
          border-bottom: 1px solid var(--ink);
          margin-bottom: 1.2rem;
        }
        .stTabs [data-baseweb="tab"] {
          border-radius: 0 !important;
          padding: 0.85rem 1.25rem !important;
          font-family: "JetBrains Mono", monospace !important;
          font-size: 0.76rem !important;
          letter-spacing: 0.18em !important;
          text-transform: uppercase !important;
          font-weight: 600 !important;
          color: var(--steam) !important;
          background: transparent !important;
          border-bottom: 2px solid transparent !important;
          transition: color 200ms ease, border-color 200ms ease;
        }
        .stTabs [data-baseweb="tab"]:hover {
          color: var(--ink) !important;
        }
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
          color: var(--ink) !important;
          border-bottom-color: var(--pulse) !important;
        }

        /* === Inline subheaders === */
        .stApp h2,
        [data-testid="stMarkdownContainer"] h2 {
          font-family: "Fraunces", "Iowan Old Style", Georgia, serif;
          font-style: italic;
          font-weight: 500;
          letter-spacing: -0.01em;
          color: var(--ink);
        }
        .stApp h3,
        [data-testid="stMarkdownContainer"] h3 {
          font-family: "Fraunces", "Iowan Old Style", Georgia, serif;
          font-style: italic;
          font-weight: 500;
          font-size: 1.55rem;
          letter-spacing: -0.005em;
          color: var(--ink);
          margin: 1.4rem 0 0.4rem;
          font-variation-settings: "opsz" 144;
        }

        /* === Dataframes === */
        [data-testid="stDataFrame"],
        [data-testid="stTable"] {
          border: 1px solid var(--ink);
          border-radius: 2px;
          overflow: hidden;
          box-shadow: var(--shadow-card);
          font-family: "JetBrains Mono", monospace !important;
          font-size: 0.84rem !important;
        }

        /* === Animations === */
        @keyframes paper-rise {
          from { opacity: 0; transform: translateY(14px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        @keyframes ekg-draw {
          to { stroke-dashoffset: 0; }
        }
        @keyframes ekg-pulse {
          0%, 100% { opacity: 1; }
          50%      { opacity: 0.55; }
        }
        @keyframes pulse-dot {
          0%, 100% { box-shadow: 0 0 0 0 var(--pulse-glow); transform: scale(1); }
          50%      { box-shadow: 0 0 0 8px transparent; transform: scale(1.35); }
        }

        @media (prefers-reduced-motion: reduce) {
          *, *::before, *::after {
            animation-duration: 0.001ms !important;
            animation-iteration-count: 1 !important;
            scroll-behavior: auto !important;
            transition-duration: 0.001ms !important;
          }
        }

        /* === Responsive === */
        @media (max-width: 1100px) {
          .masthead {
            grid-template-columns: 1fr;
            gap: 0.85rem;
          }
          .hero-grid,
          .chart-grid,
          .result-hero { grid-template-columns: 1fr; }
          .metric-grid,
          .risk-grid,
          .asset-grid,
          .agent-grid,
          .creed-grid { grid-template-columns: 1fr; }
          .hero h1 { font-size: 3.2rem; }
          .chart-headline h2 { font-size: 2.6rem; }
          .score-value { font-size: 4.6rem; }
          .hero-mark-frame { max-width: 100%; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
