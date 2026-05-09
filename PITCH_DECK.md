# ROCm CI Doctor Pitch Deck

9-slide deck for the lablab.ai submission. Each slide is structured as:

- **Headline** — the one quotable sentence
- **Body** — 3-5 short bullets
- **Visual** — exact screenshot or asset to use
- **Speaker notes** — 2-3 sentences for the presenter (or for a written walkthrough)

Export to PDF when finished. Aspect ratio: 16:9 widescreen.

---

## Slide 1 — Problem

**Title:** AI repos quietly regress to CUDA-only

**Headline:**
> Most AI repositories are CUDA-first, and every new pull request is a chance to silently break AMD/ROCm support — until somebody on AMD hardware tries to build it.

**Body:**

- 90%+ of public PyTorch repos are written and tested only against NVIDIA CUDA.
- Even after a successful one-time ROCm migration, the next PR can hardcode `cuda`, drop a CUDA-only dependency, or skip the AMD container — without anyone noticing.
- Maintainers don't have a repeatable AMD readiness gate that runs on every PR.
- Migration tools fix code once. They do not protect compatibility over time.

**Visual:** Screenshot of `samples/cuda_heavy_repo` analysis with the black hero card showing **`READINESS SCORE 30/100 · High risk`** and the 4 KPI tiles (`HIGH RISKS 1`, `CI GAPS 4`, `FILES SCANNED 120`, `GENERATED 8`).

**Speaker notes:** This is the gap the product fills. We're showing a real CUDA-heavy repository scoring 30 out of 100 — judges should immediately see that even a "supported" repo can be one PR away from breaking ROCm. The problem is structural, not a one-time migration task.

---

## Slide 2 — Solution

**Title:** A continuous AMD readiness gate for AI repositories

**Headline:**
> ROCm CI Doctor scans a repo, scores its AMD/ROCm readiness, generates a reviewable CI validation bundle, and explains the result through a Qwen-powered AI Doctor — verified end-to-end on AMD Developer Cloud.

**Body:**

- **Scan** the repository structure, dependencies, Dockerfiles, and existing CI.
- **Score** AMD readiness on a transparent 0-100 scale with explainable risk lanes.
- **Generate** a complete ROCm CI bundle: workflow, Dockerfile, smoke test, benchmark, runner, and report.
- **Explain** the findings with Qwen — maintainer summary plus free-form Q&A.

**Visual:** Top section of the AI Doctor tab showing the four green `COMPLETE` agent cards (Repo Inspector → CI Architect → Validation → Report) plus the `Qwen enabled · qwen-plus` status banner.

**Speaker notes:** This slide answers "what is it" in one sentence. The four-step verb flow — scan, score, generate, explain — is also the structure of the demo. Everything else in the deck is detail underneath these four words.

---

## Slide 3 — Agentic Workflow

**Title:** Four deterministic agents plus a Qwen explanation layer

**Headline:**
> Each agent is a small, auditable pipeline stage — same input, same output — and Qwen sits on top for human-friendly explanations, never replacing the deterministic source of truth.

**Body:**

1. **Repo Inspector Agent** — walks source files, dependencies, Dockerfiles, and existing workflows. Detects CUDA assumptions and CI gaps.
2. **CI Architect Agent** — designs the ROCm validation gate (workflow target, container base, test surface).
3. **Validation Agent** — generates the smoke test, benchmark, AMD Cloud runner, and evidence checklist.
4. **Report Agent** — writes the readiness report, score breakdown, and remediation plan.
5. **Qwen AI Doctor (overlay)** — turns the deterministic findings into a maintainer summary and answers free-form questions. The deterministic analyzer remains the source of truth.

**Visual:** Same AI Doctor screenshot from Slide 2, with one extra arrow-callout from the four agent cards down to the Qwen `Generate Maintainer Summary` button.

**Speaker notes:** The deterministic layer is what makes this auditable: judges can re-run any sample and reproduce the same score and the same generated files. Qwen is layered on top for prioritization and Q&A — it does not invent risks. This separation is intentional and a key trust property.

---

## Slide 4 — Generated ROCm CI Bundle

**Title:** Reviewable files a maintainer can drop straight into a pull request

**Headline:**
> The output is not a recommendation document — it is six concrete files ready to commit, review, and merge.

**Body:**

| File | What it does |
|---|---|
| `.github/workflows/rocm-ci.yml` | GitHub Actions workflow targeting a self-hosted AMD GPU runner |
| `Dockerfile.rocm` | ROCm container starter (PyTorch ROCm base image) |
| `tests/test_rocm_smoke.py` | Pytest smoke test: import torch, detect device, run a tiny tensor op |
| `benchmarks/benchmark_rocm.py` | Matrix multiply benchmark with timing |
| `scripts/run_rocm_validation.sh` | One-command runner for AMD Developer Cloud |
| `ROCM_CI_REPORT.md` | Consolidated readiness report with score, risks, and next steps |

**Visual:** Generated Assets tab in the UI, with `.github/workflows/rocm-ci.yml` open on the right pane, the `runs-on: [self-hosted, amd-gpu]` line visible.

**Speaker notes:** This is the maintainer's deliverable. Instead of a vague "you should add CI", we hand over six files that already pass syntax checks and are designed to be diffed in a pull request. This is what makes the workflow agentic-but-shippable.

---

## Slide 5 — External Validation

**Title:** Same analyzer holds up on four very different public repos — and got better in the process

**Headline:**
> We ran ROCm CI Doctor against four real public GitHub projects to verify that scores, risk counts, and the generated bundle behave consistently outside our own sample data. The exercise also surfaced two calibration bugs, which we fixed in-product before this submission.

**Body — Final results (after calibration fix):**

| Repository | Detected stack | Score | Key signals | Verdict |
|---|---|---|---|---|
| `karpathy/nanoGPT` | Python · PyTorch · transformers | **30/100** | 3× hardcoded `cuda` device, 9× `torch.cuda` API, no CI / tests / Dockerfile | ✅ Matches reality (research-grade CUDA repo, no CI) |
| `CompVis/stable-diffusion` | Python · PyTorch · transformers · tests | **40/100** | **18× hardcoded `cuda`**, 7× `.cuda()` calls, no GitHub Actions, no Dockerfile | ✅ Matches reality (classic CUDA AI codebase with a test suite) |
| `ROCm/HIP-Examples` | **`rocm_native`** | **55/100** | 8× `nvcc` references, no GitHub Actions, no Dockerfile | ✅ Now correctly identified as ROCm-native (was 45/100, no stack detected before fix) |
| `psf/requests` | Python · tests · GitHub Actions | **75/100** | Only 1 low-severity risk (`missing_dockerfile`) | ✅ Clean signal (was 75/100 with a false-positive `missing_rocm_workflow` high risk before fix) |

**Two calibration fixes triggered by external testing:**

1. **`rocm_native` stack detection** — added a strong-signal detector (`.hip` source files, or `hipcc` / `find_package(HIP)` / `<hip/hip_runtime.h>` in `Makefile` / `CMakeLists.txt` / `*.cmake`). When detected, the analyzer treats the repository as a ROCm-aware codebase and credits the `Portable GPU codebase` score check accordingly. Before the fix, `ROCm/HIP-Examples` returned an empty `detected_stack` and a misleading mid-range score.
2. **GPU-relevance gate on `missing_rocm_workflow`** — that risk is now only flagged when the repository actually shows GPU signals (PyTorch / vLLM / sglang / `rocm_native` / any GPU-related source pattern). Before the fix, a pure HTTP library like `psf/requests` would surface a `high`-severity "missing ROCm workflow" risk that had no operational meaning.

**What this confirms:**

- **Pattern detection is accurate**: stable-diffusion's 18 hardcoded `cuda` references and `.cuda()` count match the actual codebase.
- **Scoring ranks repositories correctly** within scope: nanoGPT (30) < stable-diffusion (40) < HIP-Examples (55) < requests (75). The deltas line up with real differences (tests, ROCm-native, full CI).
- **Generation works** on every Python/PyTorch repo tested — same 8-file bundle, customized to each repo's name and detected stack.
- **Engineering loop is real**: external testing surfaced two scope bugs; the fixes ship in this submission with `pytest -q` green (23/23 tests pass).

**Visual:** The table rendered as a clean 4-row comparison card. No screenshot needed — this is the credibility slide.

**Speaker notes:** This slide answers the skeptical question — "does this thing actually work on code you didn't write?" — with numbers from four public repos. It also tells judges something stronger: when external testing exposed two calibration edges (a ROCm-native C++ repo getting a misleading mid score, a non-GPU Python lib raising a meaningless high-severity ROCm warning), we shipped the fixes, kept tests green, and re-ran the validation before submitting. That iteration loop is the difference between a hackathon prototype and a tool a maintainer would actually adopt.

---

## Slide 6 — AMD Developer Cloud Proof

**Title:** Generated assets ran on real ROCm hardware

**Headline:**
> The validation bundle was executed on AMD Developer Cloud in a PyTorch ROCm 7 container. The numbers below are committed in the repo for independent verification.

**Body:**

- **ROCm/HIP:** `7.0.51831-a3e329ad8`
- **PyTorch:** `2.9.0.dev20250821+rocm7.0.0.git125803b7`
- **GPU visible through PyTorch:** ✅ (`torch.cuda.is_available() == true`, device count `1`)
- **Smoke test:** `ok` in **502.992 ms**
- **Benchmark:** `ok` — 2048×2048 matmul, 10 iterations, **0.196 ms mean** (`0.19 ms median`)
- **Evidence files:** `evidence/amd-cloud/PHASE5_PROOF.md`, `smoke.json`, `benchmark.json`, `rocm-smi.txt`

**Visual:** Side-by-side: left = `evidence/amd-cloud/PHASE5_PROOF.md` Run Summary section, right = `rocm-smi.txt` showing real GPU output. Or just the GitHub view of `PHASE5_PROOF.md`.

**Speaker notes:** This is what separates the project from a static report generator. We executed the generated bundle on AMD Developer Cloud, captured the runtime evidence, and committed it. Judges can clone the repo and verify every number in this slide.

---

## Slide 7 — Qwen Integration

**Title:** Qwen-plus turns the analysis into maintainer language

**Headline:**
> The deterministic analyzer produces structured findings; Qwen-plus turns them into a clear maintainer summary and answers free-form questions in the maintainer's own context.

**Body:**

- **Model:** `qwen-plus` via Alibaba Cloud Model Studio (DashScope API).
- **Two surfaces:**
  - *Generate Qwen Maintainer Summary* — prose summary of the readiness report, prioritized.
  - *Ask the Doctor* — free-form Q&A grounded on the deterministic findings (e.g. *"What should I fix first before adding the generated ROCm CI workflow?"*).
- **Trust boundary:** the deterministic score and risk list are the source of truth. Qwen is an explanation, prioritization, and Q&A layer — not a re-evaluator.
- **Graceful fallback:** if no API key is configured, the deterministic agents and generated bundle still work end-to-end.

**Visual:** AI Doctor tab scrolled to show the Qwen Maintainer Summary output, plus the Ask the Doctor input box with the default question pre-filled.

**Speaker notes:** Submitted under the Qwen track. The product was designed so Qwen has a real, scoped job — explanation and prioritization on top of structured analysis — instead of being bolted on as a chatbot. That separation is what makes the AI layer trustworthy for engineering use.

---

## Slide 8 — Why This Is Different

**Title:** Continuous gate, not a one-shot migration

**Headline:**
> Migration tools help code move from CUDA to ROCm once. ROCm CI Doctor keeps it there, pull request after pull request.

**Body:**

| | Migration tools | ROCm CI Doctor |
|---|---|---|
| **When it runs** | Once, manually | Every PR, automatically |
| **Output** | Patched code | Reviewable CI assets + readiness score |
| **Catches regressions** | No | Yes |
| **Hardware-validated** | Optional | AMD Developer Cloud evidence built in |
| **Maintainer experience** | "Trust me, I rewrote it" | "Here's the score, the risks, and the bundle to review" |

**Target users:**

- Open-source maintainers of Python/PyTorch repos.
- ML infrastructure teams evaluating AMD as a second backend.
- Startups assessing AMD Developer Cloud for production workloads.
- Developer-relations teams who need shippable AMD readiness templates.

**Visual:** Single horizontal flow image: `Analyze repo → Generate CI assets → Validate on AMD Cloud → Qwen guidance`. Render this as a clean Keynote/Slides shape diagram.

**Speaker notes:** Most ROCm-related hackathon ideas are migration scripts. We are deliberately positioned downstream of migration — we exist *because* migration alone doesn't keep AMD support healthy. That positioning is what makes us a workflow product, not a one-time tool.

---

## Slide 9 — Submission Summary & Links

**Title:** ROCm CI Doctor

**Headline:**
> Continuous AMD readiness gate · Qwen-augmented · AMD Developer Cloud verified.

**Body:**

- **GitHub repo:** `github.com/ryder1018/rocm-ci-doctor`
- **Live demo (HF Space):** `huggingface.co/spaces/lablab-ai-amd-developer-hackathon/rocm-ci-doctor`
- **Demo video:** *(link from lablab submission)*
- **Submitted under:** Qwen track
- **Hardware proof:** `evidence/amd-cloud/PHASE5_PROOF.md`
- **Tech stack:** Python, PyTorch ROCm, Streamlit, Qwen-plus (DashScope), Hugging Face Spaces, AMD Developer Cloud, GitHub Actions, Docker

**Visual:** Static end card matching the demo video's closing frame — black background, three centered lines (`ROCm CI Doctor` / two URLs / `Qwen · AMD Developer Cloud · ROCm 7`).

**Speaker notes:** Mirror this card with the demo video's end frame so the submission feels coherent across artifacts. If a judge only ever sees this slide, they should walk away with the repo URL, the demo URL, and the one-sentence positioning.
