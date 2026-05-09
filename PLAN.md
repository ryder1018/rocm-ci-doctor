# ROCm CI Doctor - Project Plan

## 1. Project Summary

**Project name:** ROCm CI Doctor  
**Hackathon:** AMD Developer Hackathon by lablab.ai  
**Primary track:** Track 1 - AI Agents & Agentic Workflows  
**Secondary fit:** AMD Developer Cloud / ROCm developer tooling  
**Recommended positioning:** A GitHub PR gate that keeps AI repositories AMD-ready over time.

ROCm CI Doctor is a developer tool that analyzes an AI repository and generates the files needed to continuously validate AMD/ROCm compatibility through CI. Instead of focusing on one-time CUDA-to-ROCm code migration, it helps maintainers add repeatable checks, smoke tests, benchmark scripts, Docker configuration, and a clear AMD readiness report.

The project should be demoable locally without an AMD GPU. Local execution will analyze repositories, generate CI assets, and produce reports. AMD Developer Cloud should be used at least once to run a generated smoke test or benchmark on real ROCm hardware, then the captured logs/results can be used in the final demo.

## 2. Problem

Many open-source AI repositories are built and tested mainly on NVIDIA CUDA environments. Even when the code can run on AMD GPUs, maintainers often do not have a simple way to verify that compatibility continuously.

Common problems:

- CI pipelines rarely test ROCm compatibility.
- Repositories often contain implicit CUDA assumptions.
- Dockerfiles and dependency files are frequently NVIDIA-specific.
- Maintainers do not know which small smoke tests should be run on AMD GPUs.
- One-time migration reports become stale after future pull requests.

The hackathon already has several projects focused on code migration. ROCm CI Doctor should avoid competing directly with those tools by focusing on continuous verification and maintainer workflows.

## 3. Purpose

The purpose of ROCm CI Doctor is to make AMD GPU compatibility visible, repeatable, and maintainable for AI repositories.

The tool should answer:

- Is this repository likely to run on AMD ROCm?
- What CI files should be added to validate that?
- What smoke test should run on an AMD GPU?
- What benchmark should be run on AMD Developer Cloud?
- What issues should maintainers fix before calling the project AMD-ready?

## 4. Target Users

Primary users:

- Maintainers of open-source AI repositories.
- ML infrastructure engineers.
- Hackathon participants deploying AI workloads on AMD GPUs.
- Developer relations teams helping projects support ROCm.

Secondary users:

- AI startups evaluating AMD Developer Cloud.
- Researchers publishing PyTorch projects.
- Teams moving inference workloads from CUDA-only environments to portable GPU stacks.

## 5. Core Value Proposition

ROCm CI Doctor turns a repository into an AMD-ready project by generating:

- ROCm-aware GitHub Actions workflow.
- ROCm Dockerfile or Docker recommendations.
- PyTorch ROCm smoke test.
- Optional vLLM/SGLang benchmark script.
- AMD readiness score.
- Maintainer-friendly compatibility report.
- Runbook for executing the generated workflow on AMD Developer Cloud.

## 6. Differentiation

This project must not be presented as a CUDA-to-ROCm migration tool.

Differentiation from likely competing submissions:

- Focuses on CI/CD instead of code conversion.
- Focuses on ongoing PR validation instead of one-time migration.
- Generates maintainer workflow assets, not only patches.
- Produces a repeatable AMD readiness gate.
- Can be used after migration tools to keep compatibility from regressing.

Suggested tagline:

> ROCm CI Doctor helps maintainers keep AI repositories AMD-ready with generated CI, smoke tests, benchmarks, and readiness reports.

## 7. Track 1 Submission Strategy

Primary submission category:

- **AI Agents & Agentic Workflows**

Why this track fits:

- The product coordinates multiple bounded agents to inspect a repository, reason about ROCm readiness, generate validation assets, and explain remediation steps.
- The core workflow automates a developer task that is normally manual: checking CUDA assumptions, designing an AMD/ROCm CI gate, writing smoke tests, preparing benchmark scripts, and producing a maintainer-facing report.
- Qwen is integrated as the optional natural-language agent layer that turns deterministic analysis into clearer maintainer guidance and answers repo-specific questions.
- AMD Developer Cloud evidence proves that the generated validation path is not only a static report; it can run on real ROCm hardware.

Track 1 positioning statement:

> ROCm CI Doctor is an agentic developer workflow that turns any Python/PyTorch AI repository into a reviewable AMD/ROCm CI validation plan, then uses Qwen to help maintainers understand and prioritize the fixes.

Agentic workflow shown in the demo:

1. **Repo Inspector Agent** scans files, dependencies, Dockerfiles, and workflows for CUDA/ROCm signals.
2. **CI Architect Agent** decides which CI and container assets should be generated.
3. **Validation Agent** creates a smoke test, benchmark script, and AMD Developer Cloud evidence runner.
4. **Report Agent** writes the readiness report, score breakdown, and next-step plan.
5. **Qwen AI Doctor** summarizes the findings and answers maintainer questions using the deterministic analysis context.

Judging alignment:

- **Application of Technology:** show Qwen integration, ROCm-aware static analysis, generated GitHub Actions, generated Dockerfile, generated smoke test, generated benchmark, and AMD Developer Cloud validation evidence.
- **Business Value:** frame the tool as a PR-readiness gate for maintainers and AI infrastructure teams, not as a one-off migration script.
- **Originality:** emphasize continuous ROCm validation after migration, which is different from CUDA-to-HIP code conversion projects.
- **Presentation:** use the live UI plus saved AMD Cloud evidence so the project remains demoable even without live GPU access.

Submission checklist for this track:

- Public GitHub repository with README, PLAN, and evidence files.
- Demo URL, preferably Hugging Face Space or another public Streamlit deployment.
- 2-3 minute video showing repo analysis, generated assets, Qwen AI Doctor, and AMD Cloud proof.
- Slide or README section titled "Why Track 1" explaining the agent workflow above.
- Clear note that deterministic analysis is the source of truth and Qwen is used for explanation, prioritization, and interactive maintainer guidance.
- Mention Qwen Special Reward eligibility by highlighting `qwen-plus` usage in the AI Doctor tab.

## 8. MVP Scope

The MVP should support Python/PyTorch repositories only.

In scope:

- Analyze a public GitHub repository URL or local folder.
- Detect common Python project files:
  - `requirements.txt`
  - `pyproject.toml`
  - `setup.py`
  - `Dockerfile`
  - `.github/workflows/*.yml`
- Detect GPU-related patterns:
  - `torch.cuda`
  - `.cuda()`
  - `device="cuda"`
  - `nvidia-smi`
  - CUDA base images
  - CUDA-specific packages
  - vLLM or SGLang usage
- Generate:
  - `.github/workflows/rocm-ci.yml`
  - `Dockerfile.rocm`
  - `tests/test_rocm_smoke.py`
  - `benchmarks/benchmark_rocm.py`
  - `ROCM_CI_REPORT.md`
- Produce an AMD readiness score.
- Provide copy-paste run instructions for AMD Developer Cloud.
- Provide a local web UI or CLI demo.

Out of scope for MVP:

- Fully automatic code migration.
- Supporting every framework.
- Running real ROCm jobs locally.
- Managing cloud credentials automatically.
- Opening GitHub pull requests automatically.
- Training or fine-tuning models.

## 9. Suggested Tech Stack

Frontend:

- Streamlit for fastest demo, or Next.js if there is enough time.

Backend:

- Python.
- FastAPI if building a frontend/backend split.
- Plain Python CLI if using Streamlit only.

Repository analysis:

- Git clone for public repos.
- `pathlib`, `tomllib`, `yaml`, and regex-based scanners.
- Optional GitHub API for metadata.

LLM/agent layer:

- Qwen model through an API or local inference endpoint.
- Agent roles can be implemented simply without heavy orchestration.
- Optional CrewAI/LangChain only if they reduce implementation time.

Generated assets:

- Jinja2 templates for workflow, Dockerfile, smoke test, benchmark, and report.

Deployment:

- Hugging Face Space for demo.
- GitHub repo for source code.
- AMD Developer Cloud for one real ROCm validation run.

## 10. Architecture

High-level flow:

1. User enters GitHub repository URL or uploads/selects local repo.
2. Repo Fetcher clones or reads the project.
3. Static Analyzer scans files and dependencies.
4. Compatibility Classifier identifies ROCm risks and CI gaps.
5. Template Generator creates ROCm CI assets.
6. Report Writer creates a maintainer-facing report.
7. UI shows readiness score, generated files, warnings, and runbook.

Suggested internal modules:

- `app.py` - Streamlit UI or main web app.
- `src/repo_loader.py` - clone/read repository.
- `src/analyzer.py` - file and pattern scanning.
- `src/scoring.py` - readiness score rules.
- `src/generator.py` - generate CI/Docker/test/benchmark files.
- `src/report.py` - generate markdown report.
- `templates/rocm-ci.yml.j2`
- `templates/Dockerfile.rocm.j2`
- `templates/test_rocm_smoke.py.j2`
- `templates/benchmark_rocm.py.j2`
- `templates/ROCM_CI_REPORT.md.j2`
- `examples/` - sample repos or generated outputs.

## 11. Agent Design

Keep agents pragmatic and bounded. The product can present agentic behavior even if the implementation is a structured pipeline.

Recommended agents:

### 11.1 Repo Inspector Agent

Responsibilities:

- Identify project type.
- Find GPU-related files.
- Detect PyTorch, Transformers, vLLM, SGLang, CUDA, Docker, and CI usage.
- Summarize compatibility risks.

### 11.2 CI Architect Agent

Responsibilities:

- Decide which workflow template is appropriate.
- Generate GitHub Actions YAML.
- Generate Dockerfile recommendations.
- Produce AMD Developer Cloud run instructions.

### 11.3 Smoke Test Agent

Responsibilities:

- Generate a minimal PyTorch ROCm smoke test.
- Include checks for `torch.cuda.is_available()`.
- Print device name and memory info.
- Run a small tensor operation.
- Optionally run a tiny model inference if dependencies suggest Transformers.

### 11.4 Benchmark Agent

Responsibilities:

- Generate a benchmark script for model loading or tensor throughput.
- Keep benchmark safe and small for hackathon credits.
- Emit JSON or markdown benchmark results.

### 11.5 Report Agent

Responsibilities:

- Create `ROCM_CI_REPORT.md`.
- Explain risks in maintainer language.
- Show readiness score.
- List generated files.
- Provide next steps.

## 12. Readiness Scoring

Use a simple transparent score from 0 to 100.

Suggested scoring:

- +20 if project uses PyTorch in a portable way.
- +15 if dependencies are not CUDA-pinned.
- +15 if Dockerfile is not NVIDIA/CUDA-only.
- +15 if no hard-coded `torch.cuda` assumptions are found.
- +10 if CI already exists.
- +10 if tests exist.
- +10 if inference or training entrypoints are discoverable.
- +5 if README has environment setup instructions.

Subtract points for:

- Hard-coded CUDA device usage.
- `nvidia-smi` in scripts.
- CUDA-only base images.
- CUDA-specific packages without alternatives.
- No tests or unclear entrypoint.

The score should not claim correctness. It should be framed as a static readiness estimate.

## 13. Generated Files

### 13.1 `.github/workflows/rocm-ci.yml`

Purpose:

- Defines a ROCm validation workflow.
- Designed for self-hosted AMD GPU runner or AMD Developer Cloud execution.
- Runs dependency install, smoke test, and optional benchmark.

Must include:

- Clear comments for runner requirements.
- Python setup.
- Dependency installation.
- `python tests/test_rocm_smoke.py`.
- Artifact upload for benchmark/report outputs.

### 13.2 `Dockerfile.rocm`

Purpose:

- Provides a ROCm-compatible container starting point.
- Uses an AMD ROCm/PyTorch image when appropriate.

Must include:

- Base image placeholder.
- Workdir setup.
- Dependency installation.
- Smoke test command.

### 13.3 `tests/test_rocm_smoke.py`

Purpose:

- Minimal runtime validation on AMD ROCm.

Must test:

- Python imports.
- PyTorch import.
- GPU availability through PyTorch.
- Device name.
- Simple tensor operation.
- Optional tiny inference path if supported.

### 13.4 `benchmarks/benchmark_rocm.py`

Purpose:

- Small benchmark suitable for AMD Developer Cloud.

Must measure:

- Device information.
- Warmup time.
- Simple matrix multiply timing.
- Optional model inference latency.

### 13.5 `ROCM_CI_REPORT.md`

Purpose:

- Human-readable report for maintainers.

Must include:

- Readiness score.
- Detected stack.
- Detected ROCm risks.
- Generated files.
- How to run locally where possible.
- How to run on AMD Developer Cloud.
- Next recommended fixes.

## 14. Demo Strategy

The demo should be designed to work even if live AMD GPU access is unavailable during presentation.

Live local demo:

1. Start the app locally.
2. Paste a GitHub repo URL or select an included sample repo.
3. Run analysis.
4. Show detected CUDA/ROCm risks.
5. Generate CI files.
6. Preview generated workflow, Dockerfile, test, benchmark, and report.
7. Download or show the generated patch bundle.

Recorded/proof demo:

1. Use AMD Developer Cloud.
2. Run generated `tests/test_rocm_smoke.py`.
3. Run generated `benchmarks/benchmark_rocm.py`.
4. Capture terminal logs.
5. Include the result in README and presentation.

Final presentation story:

1. "AI repos often say they support GPUs, but they rarely test AMD compatibility."
2. "ROCm CI Doctor turns compatibility into a repeatable CI gate."
3. "Here is a repo before analysis."
4. "Here are the risks."
5. "Here are generated ROCm CI assets."
6. "Here is proof running on AMD Developer Cloud."
7. "This helps maintainers keep AMD support from regressing."

## 15. Implementation Phases

### Phase 0 - Setup and Scope Lock

Goal:

- Create repository structure and lock MVP scope.

Status:

- Completed. The repository now has a README, Python package structure, Streamlit UI, sample repositories, tests, generated asset templates, and a locked Python/PyTorch MVP scope.

Tasks:

- [x] Create project README.
- [x] Choose UI approach: Streamlit recommended.
- [x] Create Python project structure.
- [x] Add lightweight tests and syntax checks.
- [x] Add sample repository fixtures.
- [x] Define exact generated file templates.

Exit criteria:

- [x] Project runs locally with a working UI and CLI.
- [x] Scope is limited to Python/PyTorch repositories.

### Phase 1 - Repository Analyzer

Goal:

- Build deterministic repo scanning.

Status:

- Completed in the current Phase 1 implementation.

Tasks:

- [x] Accept GitHub URL or local path.
- [x] Clone public repo into temp directory.
- [x] List relevant files.
- [x] Parse dependency files when present.
- [x] Detect Python, PyTorch, Transformers, vLLM, SGLang, Docker, and GitHub Actions.
- [x] Detect CUDA/NVIDIA-specific patterns.
- [x] Return structured JSON analysis result.

Exit criteria:

- [x] Analyzer can scan at least 3 sample repos.
- [x] Output includes detected stack, risks, and recommended generated assets.

Verification:

- `conda run -n rocm-ci-doctor python -m unittest discover -s tests`
- `conda run -n rocm-ci-doctor python -m rocm_ci_doctor analyze samples/simple_pytorch_repo --compact`
- `conda run -n rocm-ci-doctor python -m rocm_ci_doctor analyze https://github.com/pypa/sampleproject --compact`

### Phase 2 - Readiness Scoring and Risk Report

Goal:

- Convert analyzer output into a useful maintainer-facing assessment.

Status:

- Completed in the current Phase 2 implementation.

Tasks:

- [x] Implement transparent 0-100 scoring.
- [x] Categorize risks as high/medium/low.
- [x] Add explanations for each risk.
- [x] Add recommended fix categories.
- [x] Generate markdown report from structured data.

Exit criteria:

- [x] `ROCM_CI_REPORT.md` can be generated from analyzer output.
- [x] Score and risks are explainable without LLM dependency.

Verification:

- `conda run -n rocm-ci-doctor python -m unittest discover -s tests`
- `conda run -n rocm-ci-doctor python -m rocm_ci_doctor analyze samples/cuda_heavy_repo --json-out outputs/cuda-heavy.json --report-out outputs/ROCM_CI_REPORT.md --compact`

### Phase 3 - CI Asset Generator

Goal:

- Generate files that maintainers can copy into their repo.

Status:

- Completed in the current Phase 3 implementation.

Tasks:

- [x] Create GitHub Actions workflow template.
- [x] Create ROCm Dockerfile template.
- [x] Create PyTorch smoke test template.
- [x] Create benchmark script template.
- [x] Write generated files to an output directory.
- [x] Show previews through the generated bundle manifest and CLI JSON output.

Exit criteria:

- [x] Running the CLI produces a complete output bundle.
- [x] Generated Python files are syntactically valid.

Verification:

- `conda run -n rocm-ci-doctor python -m unittest discover -s tests`
- `conda run -n rocm-ci-doctor python -m rocm_ci_doctor analyze samples/cuda_heavy_repo --json-out outputs/cuda-heavy.json --report-out outputs/ROCM_CI_REPORT.md --generate-out outputs/cuda-heavy-bundle --compact`
- `conda run -n rocm-ci-doctor python -m py_compile outputs/cuda-heavy-bundle/tests/test_rocm_smoke.py outputs/cuda-heavy-bundle/benchmarks/benchmark_rocm.py`

### Phase 4 - Local UI Demo

Goal:

- Make the product understandable in under 3 minutes.

Status:

- Completed in the current Phase 4 implementation.

Tasks:

- [x] Build Streamlit UI.
- [x] Add repo URL input.
- [x] Add sample repo selector.
- [x] Show readiness score.
- [x] Show risk table.
- [x] Show generated file previews.
- [x] Add export/download for generated bundle.

Exit criteria:

- [x] A judge can understand the product without reading the code.
- [x] The local demo does not require AMD GPU access.

Verification:

- `conda run -n rocm-ci-doctor python -m unittest discover -s tests`
- `conda run -n rocm-ci-doctor python -m py_compile app.py rocm_ci_doctor/*.py tests/*.py`
- `conda run -n rocm-ci-doctor streamlit run app.py --server.headless true --server.port 8501`

### Phase 5 - AMD Developer Cloud Validation

Goal:

- Prove that generated assets can run on AMD ROCm hardware.

Status:

- Completed. The generated bundle includes a cloud validation guide, an evidence directory guide, and a runnable evidence capture script.
- Hardware proof was captured on AMD Developer Cloud with ROCm/HIP 7.0, PyTorch ROCm, one visible GPU, successful smoke test, and successful benchmark.

Tasks:

- [x] Start AMD Developer Cloud instance.
- [x] Confirm ROCm/PyTorch environment.
- [x] Run generated smoke test.
- [x] Run generated benchmark.
- [x] Save logs and benchmark output.
- [x] Generate `AMD_CLOUD_VALIDATION.md` with cloud run instructions.
- [x] Generate `scripts/run_rocm_validation.sh` to collect environment, smoke test, and benchmark evidence.
- [x] Generate `evidence/README.md` describing expected proof files.
- [x] Add proof section to README.
- [x] Include screenshots or terminal output in final demo.

Exit criteria:

- Project-side: generated bundles include a repeatable AMD/ROCm validation runner and evidence checklist.
- Hardware-side: at least one generated smoke test has real AMD/ROCm execution proof.
- Demo can show saved evidence even if live cloud access fails.

Verification:

- `conda run -n rocm-ci-doctor python -m unittest discover -s tests`
- `conda run -n rocm-ci-doctor python -m rocm_ci_doctor analyze samples/cuda_heavy_repo --generate-out outputs/cuda-heavy-bundle --compact`
- `bash -n outputs/cuda-heavy-bundle/scripts/run_rocm_validation.sh`
- `cat evidence/amd-cloud/PHASE5_PROOF.md`

### Phase 6 - Optional LLM/Agent Enhancement

Goal:

- Add agentic behavior without making the system fragile.

Status:

- Completed. The UI now includes an `AI Doctor` tab with deterministic agent workflow cards and optional Qwen-powered maintainer summaries and Q&A.
- Qwen uses `DASHSCOPE_API_KEY` or a session-only sidebar key. The deterministic analyzer remains the source of truth.
- Live `qwen-plus` access has been tested successfully after Model Studio billing/free-trial activation.

Tasks:

- [x] Use Qwen to rewrite risk explanations in clearer maintainer language.
- [x] Use Qwen to summarize generated CI plan.
- [x] Add an "Ask the Doctor" panel for questions about the report.
- [x] Keep deterministic analyzer as the source of truth.
- [x] Add deterministic agent workflow cards so the demo still works without an API key.
- [x] Support `.env` loading for `DASHSCOPE_API_KEY` and `QWEN_MODEL`.
- [x] Confirm live Qwen calls can return both summary and Q&A responses.

Exit criteria:

- [x] LLM improves presentation quality but is not required for core functionality.
- [x] UI remains usable without `DASHSCOPE_API_KEY`.
- [x] Qwen requests are only triggered by explicit button clicks.
- [x] Track 1 story is visible in the UI through Repo Inspector, CI Architect, Validation, Report, and Qwen AI Doctor agents.

Verification:

- `conda run -n rocm-ci-doctor python -m unittest discover -s tests`
- `conda run -n rocm-ci-doctor python -m py_compile app.py rocm_ci_doctor/*.py tests/*.py`
- `python -m pytest -q`
- Manual live check: generate a Qwen summary and Ask the Doctor answer with `QWEN_MODEL=qwen-plus`.

### Phase 7 - Packaging and Submission

Goal:

- Prepare a hackathon-ready public delivery package that makes the Track 1 story clear without requiring the judge to read the code.

Status:

- In progress. Local packaging, README positioning, demo script, deployment guide, submission draft, secret hygiene checks, generated bundle verification, GitHub publishing, Hugging Face Space deployment, Streamlit compatibility fixes, and Qwen live checks are complete. Remaining work is video recording, final public browser verification, optional Space secrets, and final lablab submission.

Tasks:

- [x] Run a secret scan before publishing:
  - `git status --short`
  - `rg -n "sk-|DASHSCOPE_API_KEY|API_KEY|TOKEN|SECRET|PASSWORD" . -g '!outputs/**' -g '!evidence/**' -g '!.git/**'`
  - Confirm `.env` is ignored and no real API key appears in tracked files.
- [x] Clean generated noise before publishing:
  - Keep curated example outputs only if they help the demo.
  - Do not publish local caches, temporary bundles, or credential files.
- [x] Publish the GitHub repository with:
  - `README.md`
  - `PLAN.md`
  - `PHASE5_AMD_CLOUD_RUNBOOK.md`
  - `evidence/amd-cloud/PHASE5_PROOF.md`
  - sample repo fixtures
  - source code and tests
- [x] Prepare clean local submission archive:
  - `outputs/rocm-ci-doctor-submission.tar.gz`
- [x] Add a README section titled `Why Track 1: AI Agents & Agentic Workflows`.
- [x] Add a README section titled `AMD Developer Cloud Proof` that links to `evidence/amd-cloud/PHASE5_PROOF.md`.
- [x] Add a README section titled `Qwen Integration` that explains `qwen-plus` powers summary and Q&A while deterministic analysis remains the source of truth.
- [x] Add a README section titled `Demo Script` with the exact flow:
  1. Select `samples/cuda_heavy_repo`.
  2. Run analysis.
  3. Show readiness score and top risks.
  4. Open generated ROCm CI assets.
  5. Open `AI Doctor` and click `Generate Qwen Maintainer Summary`.
  6. Ask Qwen what to fix first.
  7. Show AMD Cloud evidence.
- [x] Deploy a public demo:
  - Preferred: Hugging Face Space with Streamlit.
  - Fallback: another public Streamlit host or a recorded local demo if deployment blocks submission.
- [x] Add public demo deployment preparation files:
  - `requirements.txt`
  - `DEPLOYMENT.md`
- [ ] If using Hugging Face Space:
  - [x] Join the event Hugging Face organization.
  - [ ] Add required environment secret `DASHSCOPE_API_KEY` only through Space secrets, never in code.
  - [ ] Confirm the Space can run without the secret using deterministic mode.
- [x] Prepare `DEMO_SCRIPT.md` for a 2-3 minute demo video:
  - 0:00-0:20 problem statement: AI repos regress to CUDA-only without CI.
  - 0:20-0:55 analyze sample repo and show readiness score.
  - 0:55-1:25 show generated GitHub Actions, Dockerfile, smoke test, and benchmark.
  - 1:25-1:55 show Qwen AI Doctor summary and Q&A.
  - 1:55-2:25 show AMD Developer Cloud smoke/benchmark proof.
  - 2:25-2:45 close with maintainer workflow and business value.
- [x] Prepare short pitch deck or submission screenshots:
  - Slide 1: problem and target user.
  - Slide 2: agentic workflow.
  - Slide 3: generated ROCm CI assets.
  - Slide 4: AMD Cloud proof.
  - Slide 5: why this is different from migration tools.
- [x] Prepare `SUBMISSION.md` draft for lablab.ai with:
  - project name
  - public repo link
  - demo link
  - video link
  - Track 1 explanation
  - Qwen usage explanation
  - AMD Developer Cloud proof summary

Exit criteria:

- [ ] Submission includes working demo link, repo link, video, and clear Track 1 explanation.
- [ ] A judge can understand the value in under 3 minutes after the video is recorded.
- [ ] The project still works if Qwen API access is unavailable.
- [x] The project includes real AMD/ROCm validation evidence.

Verification:

- [x] `python -m pytest -q`
- [x] `python -m rocm_ci_doctor analyze samples/cuda_heavy_repo --generate-out outputs/submission-check-bundle --compact`
- [x] `bash -n outputs/submission-check-bundle/scripts/run_rocm_validation.sh`
- [x] `streamlit run app.py --server.headless true --server.port 8502`
- [x] Manual/API check: Qwen summary and Qwen Q&A return successfully with `qwen-plus`.
- [ ] Manual browser check after final public deployment: sample analysis, generated asset preview, AI Doctor deterministic cards, Qwen summary, Qwen Q&A.

### Phase 8 - Build in Public Extra Challenge

Goal:

- Qualify for the extra challenge with minimal extra work.

Status:

- Planned. This should be done after Phase 7 content is mostly stable so posts can point to the public repo or demo.

Tasks:

- [ ] Publish technical update 1 on X or LinkedIn:
  - Topic: why CUDA-heavy AI repos need continuous ROCm CI, not only one-time migration.
  - Include architecture image or short UI screenshot.
  - Mention the agent workflow: Repo Inspector, CI Architect, Validation Agent, Report Agent, Qwen AI Doctor.
  - Tag lablab and AMD accounts required by the hackathon page.
- [ ] Publish technical update 2 on X or LinkedIn:
  - Topic: generated ROCm CI assets ran successfully on AMD Developer Cloud.
  - Include the smoke test and benchmark result summary.
  - Mention ROCm/HIP version and PyTorch ROCm proof.
  - Tag lablab and AMD accounts required by the hackathon page.
- [ ] Write product feedback for AMD Developer Cloud:
  - What worked well: fast MI300X access, ready PyTorch ROCm container, easy evidence capture.
  - What was confusing: PyTorch was only available inside Docker, device name returned empty, billing/access activation steps were not obvious.
  - What would help developers: clearer first-run checklist, explicit ROCm container instructions, sample CI runner docs.
- [ ] Publish a technical walkthrough:
  - Problem.
  - Architecture.
  - How the analyzer works.
  - How the generated CI bundle works.
  - AMD Developer Cloud validation result.
  - How Qwen is used safely.
- [ ] Link the posts and walkthrough in the README or submission notes.

Exit criteria:

- [ ] At least two public technical updates exist.
- [ ] Required lablab and AMD accounts are tagged.
- [ ] Feedback is concrete enough to be useful to AMD Developer Cloud or ROCm maintainers.
- [ ] The project is open source or has a published technical walkthrough.

Verification:

- Public links open in an incognito/private browser.
- Tags are visible.
- README or submission notes contain the post links.

### Phase 9 - Final Submission Audit and Demo Lock

Goal:

- Freeze a reliable submission package and remove avoidable judge-facing risks.

Status:

- Planned. Run this after Phase 7 and Phase 8, immediately before final submission.

Tasks:

- [ ] Verify repository hygiene:
  - No `.env` or secrets in tracked files.
  - No large unnecessary generated artifacts.
  - README setup commands work from a clean clone.
- [ ] Verify local commands:
  - `python -m pytest -q`
  - `python -m rocm_ci_doctor analyze samples/cuda_heavy_repo --compact`
  - `python -m rocm_ci_doctor analyze samples/cuda_heavy_repo --generate-out outputs/final-check-bundle --compact`
- [ ] Verify UI demo:
  - Streamlit starts.
  - Sample repo analysis works.
  - Generated assets render clearly.
  - AI Doctor tab shows deterministic agents.
  - Qwen summary and Q&A work if the key is configured.
- [ ] Verify public links:
  - GitHub repo.
  - Public demo.
  - Demo video.
  - Build in Public posts.
  - Hugging Face Space if used.
- [ ] Verify submission narrative:
  - Track 1 is the primary track.
  - Qwen usage is explicit.
  - AMD Developer Cloud proof is explicit.
  - Differentiation from migration tools is explicit.
  - Business value for maintainers is explicit.
- [ ] Prepare fallback plan:
  - If live Qwen fails, use deterministic AI Doctor cards and mention optional Qwen layer.
  - If live demo fails, use recorded video.
  - If AMD Cloud is unavailable, use saved evidence in `evidence/amd-cloud/`.

Exit criteria:

- [ ] Final lablab submission has no missing links.
- [ ] Demo can be shown from either the public URL or the recorded video.
- [ ] The project can be explained with one sentence, one screenshot, and one proof artifact.

Verification:

- Run the full final checklist once without editing code.
- Record any remaining known limitations in README or submission notes.

## 16. Suggested Timeline

### 24-hour version

- Hours 0-2: Scope lock, repo setup, templates outline.
- Hours 2-7: Analyzer and scoring.
- Hours 7-11: File generation.
- Hours 11-15: Streamlit UI.
- Hours 15-18: Sample repos and polish.
- Hours 18-21: AMD Developer Cloud validation.
- Hours 21-23: README, Track 1 story, demo video.
- Hours 23-24: final audit and lablab submission.

### 48-hour version

- Day 1 morning: Project setup and analyzer.
- Day 1 afternoon: Scoring, report generation, CI templates.
- Day 1 night: UI and sample demo.
- Day 2 morning: AMD Developer Cloud validation.
- Day 2 afternoon: LLM explanation layer and export bundle.
- Day 2 night: README, Track 1 packaging, video, Hugging Face Space, final audit, submission.

### 1-week version

- Day 1: Analyzer and scoring.
- Day 2: Template generator.
- Day 3: UI and export workflow.
- Day 4: AMD Developer Cloud validation.
- Day 5: LLM/agent enhancements.
- Day 6: README, public deployment, demo video, submission screenshots.
- Day 7: Build-in-public content, final audit, lablab submission.

## 17. Testing Plan

Local tests:

- Analyzer detects files correctly.
- Pattern scanner catches common CUDA assumptions.
- Scoring is deterministic.
- Generated YAML is parseable.
- Generated Python smoke test is syntactically valid.
- Report generation works without LLM.

Manual tests:

- Test on a simple PyTorch repo.
- Test on a repo with no GPU usage.
- Test on a repo with CUDA-specific patterns.
- Test export bundle.

AMD Cloud tests:

- Run smoke test on ROCm PyTorch environment.
- Run benchmark script.
- Capture device info and timing output.

## 18. Success Metrics

MVP success:

- User can analyze a repo locally.
- User can generate ROCm CI assets.
- User can understand risks and next steps.
- At least one generated smoke test is validated on AMD Developer Cloud.

Hackathon success:

- Demo is complete and reliable.
- AMD/ROCm relevance is obvious.
- The product is clearly different from migration-agent submissions.
- Presentation explains business value for maintainers and AI infrastructure teams.

## 19. Risks and Mitigations

### Risk: Looks too similar to migration tools

Mitigation:

- Avoid code patching as the main feature.
- Use CI/CD language throughout the product.
- Show GitHub Actions and PR gate as the core output.

### Risk: No live AMD GPU during demo

Mitigation:

- Make local demo independent of AMD GPU.
- Capture AMD Developer Cloud logs ahead of time.
- Include saved benchmark output in README/demo.

### Risk: Generated CI cannot run on GitHub-hosted runners

Mitigation:

- Clearly state self-hosted AMD GPU runner or AMD Developer Cloud requirement.
- Generate a runbook instead of pretending standard GitHub runners have AMD GPUs.

### Risk: Static analysis gives false confidence

Mitigation:

- Call the score a readiness estimate.
- Separate static risks from runtime validation.
- Recommend actual ROCm smoke test execution.

### Risk: Too much agent framework complexity

Mitigation:

- Implement deterministic pipeline first.
- Add LLM only for summaries and explanations.
- Do not let LLM be required for core generation.

## 20. Final Deliverables

Required:

- Working local demo.
- GitHub repository.
- `README.md`.
- `PLAN.md` with Track 1 strategy and submission phases.
- Generated sample output bundle.
- Demo video.
- AMD Developer Cloud validation log or screenshot.
- Hackathon submission page.

Recommended:

- Hugging Face Space.
- Build-in-public posts.
- Technical walkthrough.
- Example PR showing generated ROCm CI files.
- Short pitch deck or submission screenshot set.

## 21. Current Completion Checklist

Completed product work:

- [x] Create project skeleton.
- [x] Implement repo loader.
- [x] Implement analyzer.
- [x] Implement scoring.
- [x] Create templates.
- [x] Generate output bundle.
- [x] Build UI.
- [x] Add sample repo.
- [x] Run local tests.
- [x] Run AMD Cloud validation.
- [x] Add Qwen AI Doctor layer.
- [x] Add Track 1 submission strategy.

Remaining submission work:

- [x] Polish README for Track 1, Qwen, and AMD Cloud proof.
- [ ] Secret-scan and publish GitHub repository.
- [x] Prepare reliable recorded-demo script and deployment guide.
- [ ] Deploy public demo.
- [ ] Record demo video.
- [ ] Publish Build in Public updates if pursuing the extra challenge.
- [ ] Run final submission audit.
- [ ] Submit on lablab.ai.
