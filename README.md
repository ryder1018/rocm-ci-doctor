---
title: ROCm CI Doctor
colorFrom: red
colorTo: gray
sdk: streamlit
sdk_version: 1.45.0
app_file: app.py
pinned: false
license: mit
---

# ROCm CI Doctor

ROCm CI Doctor is an agentic developer workflow for keeping AI repositories AMD/ROCm-ready. It analyzes a Python/PyTorch repository, scores ROCm CI readiness, generates a reviewable validation bundle, and uses Qwen to help maintainers understand what to fix first.

Instead of doing one-time CUDA-to-ROCm migration, ROCm CI Doctor focuses on the workflow maintainers need after every pull request: continuous validation through CI, smoke tests, benchmark scripts, and evidence captured on AMD Developer Cloud.

## Current Phase

Phase 1 through Phase 6 are implemented. Phase 7 packaging is in progress. Phase 5 hardware validation was run on AMD Developer Cloud using the generated validation bundle. Phase 6 adds an optional Qwen-powered explanation layer while keeping deterministic analysis as the source of truth.

- Accept a local repository path or public GitHub URL.
- Clone public GitHub repositories into a temporary directory.
- Scan relevant source, dependency, Docker, and GitHub Actions files.
- Detect Python, PyTorch, Transformers, vLLM, SGLang, Docker, and CI usage.
- Detect common CUDA/NVIDIA-specific patterns.
- Return structured JSON with stack detection, risks, CI gaps, and recommended assets.
- Calculate a transparent 0-100 AMD readiness score.
- Categorize risks by severity and recommended fix category.
- Generate `ROCM_CI_REPORT.md` from structured analyzer output.
- Generate a complete ROCm CI asset bundle:
  - `.github/workflows/rocm-ci.yml`
  - `Dockerfile.rocm`
  - `tests/test_rocm_smoke.py`
  - `benchmarks/benchmark_rocm.py`
  - `ROCM_CI_REPORT.md`
  - `ASSET_MANIFEST.json`
- Run a local Streamlit UI for repository analysis, risk review, generated asset previews, and bundle export.
- Generate AMD Developer Cloud validation handoff assets:
  - `AMD_CLOUD_VALIDATION.md`
  - `scripts/run_rocm_validation.sh`
  - `evidence/README.md`
- Capture AMD Developer Cloud proof in `evidence/amd-cloud/`.
- Provide an agentic explanation workflow with optional Qwen summaries and an Ask the Doctor panel.

## Why Track 1: AI Agents & Agentic Workflows

ROCm CI Doctor fits the AMD Developer Hackathon's AI Agents & Agentic Workflows track because it coordinates multiple bounded agents around a real developer workflow:

1. **Repo Inspector Agent** scans source files, dependencies, Dockerfiles, and workflows for CUDA/ROCm signals.
2. **CI Architect Agent** decides which ROCm CI assets should be generated.
3. **Validation Agent** creates the smoke test, benchmark script, and AMD Developer Cloud evidence runner.
4. **Report Agent** writes the readiness report, score breakdown, and next-step plan.
5. **Qwen AI Doctor** summarizes findings and answers maintainer questions using the deterministic analysis context.

The deterministic analyzer is the source of truth. Qwen is used for explanation, prioritization, and interactive maintainer guidance, not for unchecked code generation.

## Business Value

Many AI repositories are developed against CUDA-first environments. Even when their code can run on AMD GPUs, maintainers often lack a repeatable way to prove ROCm compatibility after future changes.

ROCm CI Doctor turns ROCm support into a reviewable pull-request gate:

- Identify CUDA-specific assumptions before they break an AMD deployment.
- Generate the CI, Docker, smoke test, benchmark, and report files maintainers need.
- Capture AMD Developer Cloud evidence once and reuse it in demos, reviews, and project documentation.
- Keep ROCm compatibility from regressing after migration work is complete.

## Demo Script

Recommended 2-3 minute demo flow:

1. Start the Streamlit app and select `samples/cuda_heavy_repo`.
2. Run analysis and show the readiness score plus top risks.
3. Open Generated Assets and preview `.github/workflows/rocm-ci.yml`, `Dockerfile.rocm`, `tests/test_rocm_smoke.py`, and `benchmarks/benchmark_rocm.py`.
4. Open AI Doctor and show the deterministic agent cards.
5. Click `Generate Qwen Maintainer Summary` and ask: "What should I fix first for ROCm CI readiness?"
6. Show AMD Developer Cloud proof in `evidence/amd-cloud/PHASE5_PROOF.md`.
7. Close with the message: ROCm CI Doctor is not a migration script; it is a continuous AMD readiness gate.

## Conda Setup

```bash
conda env create -f environment.yml
conda activate rocm-ci-doctor
```

If the environment already exists:

```bash
conda env update -f environment.yml --prune
conda activate rocm-ci-doctor
```

## Usage

Run the local UI:

```bash
streamlit run app.py
```

Analyze a local sample repository:

```bash
python -m rocm_ci_doctor analyze samples/cuda_heavy_repo
```

Analyze a public GitHub repository:

```bash
python -m rocm_ci_doctor analyze https://github.com/pytorch/examples
```

Write JSON output to a file:

```bash
python -m rocm_ci_doctor analyze samples/simple_pytorch_repo --json-out outputs/simple.json
```

Generate a markdown report:

```bash
python -m rocm_ci_doctor analyze samples/cuda_heavy_repo --report-out outputs/ROCM_CI_REPORT.md
```

Generate both JSON and markdown:

```bash
python -m rocm_ci_doctor analyze samples/cuda_heavy_repo \
  --json-out outputs/cuda-heavy.json \
  --report-out outputs/ROCM_CI_REPORT.md
```

Generate a complete ROCm CI asset bundle:

```bash
python -m rocm_ci_doctor analyze samples/cuda_heavy_repo \
  --json-out outputs/cuda-heavy.json \
  --report-out outputs/ROCM_CI_REPORT.md \
  --generate-out outputs/cuda-heavy-bundle
```

The generated bundle is written outside the analyzed repository by default, so you can review the files before copying them into a branch or pull request.

## Phase 5 AMD Developer Cloud Validation

ROCm CI Doctor now generates a Phase 5 validation runner inside each bundle. After creating a bundle, copy it into the target repository root on an AMD Developer Cloud instance and run:

```bash
chmod +x scripts/run_rocm_validation.sh
./scripts/run_rocm_validation.sh evidence/amd-cloud
```

The script captures:

- ROCm/PyTorch environment metadata in `evidence/amd-cloud/environment.json`
- Smoke test output in `evidence/amd-cloud/smoke.json`
- Benchmark output in `evidence/amd-cloud/benchmark.json`
- A demo-friendly summary in `evidence/amd-cloud/SUMMARY.md`

Real Phase 5 proof must include a non-empty `torch.version.hip`, visible ROCm GPU access, and successful `status: "ok"` results for both smoke test and benchmark. CPU dry-runs are useful for debugging but do not count as AMD/ROCm hardware proof.

Current captured evidence:

- `evidence/amd-cloud/PHASE5_PROOF.md`
- `evidence/amd-cloud/SUMMARY.md`
- `evidence/amd-cloud/environment.json`
- `evidence/amd-cloud/smoke.json`
- `evidence/amd-cloud/benchmark.json`
- `evidence/amd-cloud/rocm-smi.txt`

For the exact manual workflow, see `PHASE5_AMD_CLOUD_RUNBOOK.md`.

## AMD Developer Cloud Proof

The generated validation bundle was executed on AMD Developer Cloud in a PyTorch ROCm container. Captured proof is stored in `evidence/amd-cloud/`.

Summary:

- ROCm/HIP: `7.0.51831-a3e329ad8`
- PyTorch: `2.9.0.dev20250821+rocm7.0.0.git125803b7`
- GPU visible through PyTorch: `torch.cuda.is_available() == true`
- GPU count: `1`
- Smoke test: `ok`
- Benchmark: `ok`

See `evidence/amd-cloud/PHASE5_PROOF.md` for the full evidence summary.

## Phase 6 Qwen Agent Layer

The local UI includes an `AI Doctor` tab with four deterministic agents:

- Repo Inspector Agent
- CI Architect Agent
- Validation Agent
- Report Agent

If Qwen is configured, the same tab can generate a maintainer-facing remediation summary and answer questions about the report.

Set the Qwen API key in your shell:

```bash
export DASHSCOPE_API_KEY="sk-..."
```

Or create a local `.env` file. `.env` is ignored by git:

```bash
printf 'DASHSCOPE_API_KEY=sk-your-qwen-api-key\nQWEN_MODEL=qwen-plus\n' > .env
```

You can also enter the key into the Streamlit sidebar for the current local session. The default model is `qwen-plus`; override it with:

```bash
export QWEN_MODEL="qwen-plus"
```

The Qwen layer only rewrites, summarizes, and answers from the deterministic analysis context. It does not replace the static analyzer or readiness score.

## Public Demo Deployment

The app can be deployed as a Streamlit app on Hugging Face Spaces or another Streamlit-compatible host.

Minimum files for a Space:

- `app.py`
- `requirements.txt`
- `rocm_ci_doctor/`
- `samples/`
- `assets/`
- `evidence/amd-cloud/PHASE5_PROOF.md`

Set `DASHSCOPE_API_KEY` as a private Space secret if live Qwen responses are desired. The app still works without the secret by showing deterministic agent cards and deterministic summaries.

For deployment steps, see `DEPLOYMENT.md`.

## Verification

```bash
python -m pytest -q
python -m rocm_ci_doctor analyze samples/cuda_heavy_repo --generate-out outputs/submission-check-bundle --compact
bash -n outputs/submission-check-bundle/scripts/run_rocm_validation.sh
```
