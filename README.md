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

A continuous AMD/ROCm readiness gate for Python/PyTorch repositories. Point it at a repo, get a readiness score, generated CI assets ready to drop into a pull request, and an explanation layer that prioritizes what to fix first.

**Live demo:** https://huggingface.co/spaces/lablab-ai-amd-developer-hackathon/rocm-ci-doctor

## What it does

Most AI repositories are written and tested against NVIDIA CUDA. Even after a successful one-time port to AMD ROCm, future pull requests can hardcode CUDA assumptions and silently break AMD compatibility. ROCm CI Doctor closes that loop.

Given a local path or a public GitHub URL, the tool:

- Scans source files, dependencies, Dockerfiles, and existing GitHub Actions.
- Detects CUDA/NVIDIA-specific patterns (`.cuda()` calls, hardcoded `cuda` device strings, CUDA-only packages, `nvidia-smi`, `nvcc`, CUDA base images, TensorRT references, etc.).
- Calculates a transparent 0–100 readiness score with an explainable breakdown.
- Generates a complete ROCm CI bundle ready for review in a pull request.
- Provides an optional AI Doctor layer (powered by Qwen) that turns the structured findings into a maintainer-facing summary and answers free-form questions.

The deterministic analyzer is always the source of truth. The Qwen layer is opt-in and never overrides the score or risk list.

## Try it without installing

Open the live Hugging Face Space and paste any public GitHub URL into the sidebar:

```
https://huggingface.co/spaces/lablab-ai-amd-developer-hackathon/rocm-ci-doctor
```

Or run any of the bundled sample repositories:

- `samples/cuda_heavy_repo` (intentionally CUDA-heavy, low score)
- `samples/simple_pytorch_repo` (a small portable PyTorch repo)
- `samples/plain_python_repo` (no GPU code, high score)

## Local install

```bash
conda env create -f environment.yml
conda activate rocm-ci-doctor
```

If the environment already exists, update it:

```bash
conda env update -f environment.yml --prune
conda activate rocm-ci-doctor
```

## Using the Streamlit UI

```bash
streamlit run app.py
```

The sidebar accepts three source modes:

| Mode | When to use |
|------|-------------|
| `Sample repository` | Pick a bundled fixture for quick experimentation. |
| `Local path` | Analyze a working copy on your own machine. |
| `GitHub URL` | Clone a public repo into a temporary directory and analyze it. |

After you click `Run Analysis`, six tabs appear:

- **Overview** — detected stack, score breakdown, and CI gaps.
- **Risks** — every finding grouped by severity, with line numbers.
- **Generated Assets** — preview every file in the generated ROCm CI bundle and download the whole bundle as a zip.
- **AI Doctor** — four deterministic agent cards summarizing the run. If `DASHSCOPE_API_KEY` is set, a Qwen-powered Maintainer Summary and an Ask the Doctor Q&A panel become available.
- **Report** — the rendered `ROCM_CI_REPORT.md` with the score, risks, remediation plan, and validation commands.
- **JSON** — raw analyzer output for downstream tooling.

## Using the CLI

Analyze a local path:

```bash
python -m rocm_ci_doctor analyze samples/cuda_heavy_repo
```

Analyze a public GitHub repository:

```bash
python -m rocm_ci_doctor analyze https://github.com/pytorch/examples
```

Write structured JSON to disk:

```bash
python -m rocm_ci_doctor analyze samples/simple_pytorch_repo --json-out outputs/simple.json
```

Render a Markdown report:

```bash
python -m rocm_ci_doctor analyze samples/cuda_heavy_repo --report-out outputs/ROCM_CI_REPORT.md
```

Generate a full ROCm CI asset bundle in one command:

```bash
python -m rocm_ci_doctor analyze samples/cuda_heavy_repo \
  --json-out outputs/cuda-heavy.json \
  --report-out outputs/ROCM_CI_REPORT.md \
  --generate-out outputs/cuda-heavy-bundle
```

The generated bundle is written outside the analyzed repository by default, so you can review the files before copying them into a feature branch.

Pass `--compact` to emit single-line JSON suitable for piping into other tools.

## What the bundle contains

Each generated bundle is a self-contained set of files designed to be diffed in a pull request:

```
outputs/<bundle-name>/
├── .github/workflows/rocm-ci.yml      GitHub Actions workflow for a self-hosted AMD GPU runner
├── Dockerfile.rocm                    ROCm-compatible container starter (PyTorch ROCm base image)
├── tests/test_rocm_smoke.py           Smoke test: import torch, detect AMD GPU, run a tensor op
├── benchmarks/benchmark_rocm.py       Small matrix multiply benchmark with timing
├── scripts/run_rocm_validation.sh     One-command runner for AMD Developer Cloud
├── ROCM_CI_REPORT.md                  Readiness report (score, risks, remediation plan)
├── AMD_CLOUD_VALIDATION.md            How to capture hardware evidence on AMD Developer Cloud
├── evidence/README.md                 Reserved directory for runner output
└── ASSET_MANIFEST.json                Machine-readable manifest of every generated file
```

Every asset is deterministic. The same input repository always produces the same bundle.

## Running validation on AMD hardware

After generating a bundle, copy it into the target repository root on an AMD Developer Cloud instance (or any host with a ROCm-capable AMD GPU and PyTorch ROCm installed) and run:

```bash
chmod +x scripts/run_rocm_validation.sh
./scripts/run_rocm_validation.sh evidence/amd-cloud
```

The runner produces:

- `evidence/amd-cloud/environment.json` — ROCm/PyTorch environment metadata
- `evidence/amd-cloud/smoke.json` — smoke test result with elapsed time
- `evidence/amd-cloud/benchmark.json` — benchmark result with mean and median time
- `evidence/amd-cloud/SUMMARY.md` — readable summary suitable for sharing or attaching to a PR

A successful run must include a non-empty `torch.version.hip`, `torch.cuda.is_available() == true`, and `status: "ok"` for both the smoke test and the benchmark. CPU-only dry runs are useful for debugging but do not count as hardware proof.

## Reference AMD Developer Cloud run

A reference run is committed in `evidence/amd-cloud/`. It used the bundled sample (`cuda_heavy_repo`) to validate the generated runner end-to-end on real ROCm hardware. Summary:

| Field | Value |
|-------|-------|
| ROCm/HIP | `7.0.51831-a3e329ad8` |
| PyTorch | `2.9.0.dev20250821+rocm7.0.0.git125803b7` |
| `torch.cuda.is_available()` | `true` |
| GPU count | `1` |
| Smoke test | `ok` (`502.992 ms`) |
| Benchmark | `ok` (2048×2048 matmul, `0.196 ms` mean) |

The full proof, including `smoke.json`, `benchmark.json`, `environment.json`, and `rocm-smi.txt`, is in `evidence/amd-cloud/`.

## Enabling the Qwen AI Doctor

The AI Doctor is optional. The analyzer, scoring, and bundle generation all work without it.

Set your DashScope API key in the shell:

```bash
export DASHSCOPE_API_KEY="sk-..."
```

Or create a local `.env` file (already gitignored):

```bash
printf 'DASHSCOPE_API_KEY=sk-your-key\nQWEN_MODEL=qwen-plus\n' > .env
```

You can also paste the key directly into the Streamlit sidebar for a single session. The default model is `qwen-plus`; override it with the `QWEN_MODEL` environment variable.

If the AI Doctor is enabled, the tab gains two surfaces:

- **Generate Qwen Maintainer Summary** — a prose summary of the readiness report, prioritized for the maintainer.
- **Ask the Doctor** — free-form Q&A grounded on the deterministic findings (defaults to *"What should I fix first before adding the generated ROCm CI workflow?"*).

The Qwen layer is strictly an explanation and prioritization layer. The deterministic score, risk list, and generated bundle are produced before Qwen runs.

## Repository layout

```
rocm_ci_doctor/        Analyzer, scoring, generator, Qwen agent, CLI
app.py                 Streamlit UI
samples/               Bundled sample repositories for testing
evidence/amd-cloud/    Reference AMD Developer Cloud run output
tests/                 Unit tests (23 tests)
environment.yml        Conda environment definition
requirements.txt       Pip-installable dependencies (for HF Spaces)
.env.example           Template for local Qwen configuration
```

## Verification

```bash
python -m pytest -q
python -m rocm_ci_doctor analyze samples/cuda_heavy_repo --generate-out outputs/check-bundle --compact
bash -n outputs/check-bundle/scripts/run_rocm_validation.sh
```

All 23 unit tests should pass and the generated runner script should pass `bash -n` syntax validation.

## License

MIT.
