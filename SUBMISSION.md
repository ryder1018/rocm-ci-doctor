# ROCm CI Doctor Hackathon Submission Draft

Use this as the source text for the lablab.ai submission form. Replace bracketed links before submitting.

## Project Name

ROCm CI Doctor

## Short Description

An agentic developer workflow that analyzes AI repositories, scores AMD/ROCm CI readiness, generates ROCm validation assets, and uses Qwen to help maintainers understand what to fix first.

## Primary Track

AI Agents & Agentic Workflows

## Long Description

ROCm CI Doctor helps maintainers keep Python/PyTorch AI repositories AMD-ready over time.

Many AI projects are developed and tested primarily on CUDA. Even when a project can run on AMD GPUs, maintainers often do not have a repeatable way to validate ROCm compatibility after every pull request. ROCm CI Doctor solves that workflow problem.

The tool scans a repository, detects CUDA/NVIDIA assumptions, calculates a transparent AMD readiness score, and generates a complete validation bundle:

- `.github/workflows/rocm-ci.yml`
- `Dockerfile.rocm`
- `tests/test_rocm_smoke.py`
- `benchmarks/benchmark_rocm.py`
- `ROCM_CI_REPORT.md`
- AMD Developer Cloud validation runner and evidence checklist

The product is organized as a practical agentic workflow:

1. Repo Inspector Agent scans repository files and dependency signals.
2. CI Architect Agent designs the ROCm validation gate.
3. Validation Agent creates smoke test, benchmark, and AMD Cloud evidence runner.
4. Report Agent writes the readiness report and remediation plan.
5. Qwen AI Doctor summarizes the findings and answers maintainer questions from the deterministic analysis context.

ROCm CI Doctor is intentionally not a one-time migration script. It is a continuous AMD readiness gate for maintainers and ML infrastructure teams.

## Qwen Usage

Qwen powers the optional AI Doctor layer. The deterministic analyzer remains the source of truth, while Qwen turns the analysis into clearer maintainer-facing summaries and answers questions such as "What should I fix first for ROCm CI readiness?"

The implemented model configuration uses `qwen-plus` through Alibaba Cloud Model Studio.

## AMD Developer Cloud Proof

The generated validation bundle was run on AMD Developer Cloud in a PyTorch ROCm container.

Captured evidence:

- ROCm/HIP: `7.0.51831-a3e329ad8`
- PyTorch: `2.9.0.dev20250821+rocm7.0.0.git125803b7`
- `torch.cuda.is_available() == true`
- GPU count: `1`
- Smoke test: `ok`
- Benchmark: `ok`

Evidence file: `evidence/amd-cloud/PHASE5_PROOF.md`

## Business Value

ROCm CI Doctor gives maintainers a practical path to keep AMD support healthy:

- Detect portability risks early.
- Generate reviewable CI assets instead of vague recommendations.
- Run a small ROCm smoke test and benchmark on AMD Developer Cloud.
- Store evidence for future PR validation and project documentation.

## Originality

Most ROCm/CUDA hackathon ideas focus on code migration. ROCm CI Doctor focuses on what happens after migration: preventing regressions with repeatable CI validation.

## Demo Links

- GitHub repository: `https://github.com/ryder1018/rocm-ci-doctor`
- Public demo: `https://huggingface.co/spaces/lablab-ai-amd-developer-hackathon/rocm-ci-doctor`
- Demo video: `[add link]`
- Build in Public post 1: `[add link]`
- Build in Public post 2: `[add link]`

## Demo Flow

1. Analyze `samples/cuda_heavy_repo`.
2. Show readiness score and detected CUDA risks.
3. Preview generated ROCm CI workflow, Dockerfile, smoke test, and benchmark.
4. Show AI Doctor deterministic agents and Qwen summary/Q&A.
5. Show AMD Developer Cloud proof.

## Known Limitations

- The MVP focuses on Python/PyTorch repositories.
- Generated GitHub Actions require a self-hosted AMD GPU runner or AMD Developer Cloud workflow; standard GitHub-hosted runners do not provide AMD Instinct GPUs.
- Static analysis is a readiness estimate, not a substitute for real ROCm runtime validation.
