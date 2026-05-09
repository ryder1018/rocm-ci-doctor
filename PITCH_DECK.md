# ROCm CI Doctor Pitch Deck Outline

Use this as a 5-slide deck or as screenshot captions in the lablab.ai submission.

## Slide 1 - Problem

**Title:** AI repositories regress to CUDA-only without CI

Key points:

- Many Python/PyTorch projects are developed against NVIDIA CUDA.
- Even when ROCm works once, future pull requests can silently break AMD compatibility.
- Maintainers need a repeatable AMD readiness gate, not only one-time migration advice.

Suggested visual:

- Screenshot of `samples/cuda_heavy_repo` analysis with low readiness score.

## Slide 2 - Agentic Workflow

**Title:** Five agents turn repo signals into a validation plan

Agents:

- Repo Inspector Agent: scans code, dependencies, Dockerfiles, workflows.
- CI Architect Agent: selects CI/container validation assets.
- Validation Agent: generates smoke test, benchmark, and AMD Cloud evidence runner.
- Report Agent: writes readiness report and next-step plan.
- Qwen AI Doctor: summarizes and answers maintainer questions.

Suggested visual:

- AI Doctor tab with agent cards.

## Slide 3 - Generated ROCm CI Bundle

**Title:** Reviewable files maintainers can put in a pull request

Generated assets:

- `.github/workflows/rocm-ci.yml`
- `Dockerfile.rocm`
- `tests/test_rocm_smoke.py`
- `benchmarks/benchmark_rocm.py`
- `ROCM_CI_REPORT.md`
- `scripts/run_rocm_validation.sh`

Suggested visual:

- Generated Assets tab showing syntax-highlighted file previews.

## Slide 4 - AMD Developer Cloud Proof

**Title:** Generated validation ran on real ROCm infrastructure

Evidence:

- ROCm/HIP: `7.0.51831-a3e329ad8`
- PyTorch ROCm: `2.9.0.dev20250821+rocm7.0.0.git125803b7`
- GPU visible through PyTorch.
- Smoke test: `ok`
- Benchmark: `ok`

Suggested visual:

- `evidence/amd-cloud/PHASE5_PROOF.md`.

## Slide 5 - Why This Is Different

**Title:** Not migration. Continuous AMD readiness.

Positioning:

- Migration tools help code move once.
- ROCm CI Doctor helps maintainers keep ROCm compatibility healthy after every PR.
- The product is useful for open-source maintainers, ML infra teams, startups evaluating AMD Developer Cloud, and developer relations workflows.

Suggested visual:

- One-line flow: Analyze repo -> Generate CI assets -> Validate on AMD Cloud -> Qwen remediation guidance.
