# ROCm CI Doctor Demo Script

Use this script for a 2-3 minute hackathon video.

## Goal

Show that ROCm CI Doctor is an agentic developer workflow for turning a CUDA-heavy AI repository into a reviewable AMD/ROCm CI validation plan.

## Setup

Start the app:

```bash
streamlit run app.py
```

Optional Qwen setup:

```bash
export DASHSCOPE_API_KEY="sk-..."
export QWEN_MODEL="qwen-plus"
```

Do not show the API key in the recording.

## Recording Flow

### 0:00-0:20 - Problem

Say:

> Many AI repositories are CUDA-first. Even after a migration, future pull requests can quietly break AMD/ROCm compatibility. ROCm CI Doctor turns that into a repeatable CI validation workflow.

Show:

- App home screen.
- Product name.
- Sidebar with sample repository selected.

### 0:20-0:55 - Analyze a CUDA-heavy repo

Action:

1. Select `Cuda Heavy Repo`.
2. Click `Run Analysis`.
3. Show readiness score and top risks.

Say:

> The Repo Inspector Agent scans source files, dependencies, Dockerfiles, and workflows. This sample is intentionally CUDA-heavy, so the score is low and the risks are easy to understand.

### 0:55-1:25 - Show generated ROCm CI assets

Action:

1. Open `Generated Assets`.
2. Show `.github/workflows/rocm-ci.yml`.
3. Show `Dockerfile.rocm`.
4. Show `tests/test_rocm_smoke.py`.
5. Show `benchmarks/benchmark_rocm.py`.

Say:

> The CI Architect and Validation Agents generate the files a maintainer can review in a pull request: a ROCm workflow, ROCm container starter, smoke test, benchmark, and report.

### 1:25-1:55 - Show Qwen AI Doctor

Action:

1. Open `AI Doctor`.
2. Show deterministic agent cards.
3. Click `Generate Qwen Maintainer Summary` if the API key is configured.
4. Ask: `What should I fix first for ROCm CI readiness?`

Say:

> Qwen is used for explanation and prioritization. It does not replace the deterministic analyzer; it helps maintainers understand the report and decide what to do first.

### 1:55-2:25 - Show AMD Developer Cloud proof

Action:

1. Open `evidence/amd-cloud/PHASE5_PROOF.md`.
2. Show ROCm/HIP version, PyTorch ROCm version, smoke test `ok`, benchmark `ok`.

Say:

> The generated validation bundle was run on AMD Developer Cloud in a PyTorch ROCm container. The saved evidence proves this is more than a static report.

### 2:25-2:45 - Close

Say:

> ROCm CI Doctor is not a CUDA migration script. It is a continuous AMD readiness gate for AI repositories, built for maintainers who want ROCm compatibility to stay healthy after every pull request.

## Fallbacks

- If live Qwen fails, show deterministic agent cards and explain that Qwen is optional.
- If live deployment fails, use local Streamlit and the recorded video.
- If AMD Developer Cloud is unavailable, show saved evidence in `evidence/amd-cloud/`.
