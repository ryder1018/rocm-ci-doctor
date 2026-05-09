# ROCm CI Doctor Demo Script

Use this as a step-by-step shooting script for a 2:30-2:45 hackathon submission video.

## Pitch in one sentence

ROCm CI Doctor is an agentic developer workflow that turns a CUDA-heavy AI repository into a reviewable AMD/ROCm CI validation plan, with real AMD Developer Cloud evidence and Qwen-powered maintainer summaries.

---

## Pre-recording checklist

Do all of this **before** hitting record so the take is clean:

- [ ] Open public Space and confirm Qwen status reads `Qwen enabled`:
  `https://huggingface.co/spaces/lablab-ai-amd-developer-hackathon/rocm-ci-doctor`
- [ ] In the sidebar, set source to **Sample repository** → **Cuda Heavy Repo**.
- [ ] Click `Run Analysis` once now so the bundle is cached and the rerun in the recording is instant.
- [ ] Open these tabs in order in the browser so you can swipe through them:
  1. The HF Space (analysis already loaded)
  2. GitHub repo: `https://github.com/ryder1018/rocm-ci-doctor`
  3. AMD Cloud evidence: `https://github.com/ryder1018/rocm-ci-doctor/blob/main/evidence/amd-cloud/PHASE5_PROOF.md`
- [ ] Close anything personal: email, Slack, other tabs, secret values, terminal history.
- [ ] Hide bookmarks bar and any browser extensions that show notifications.
- [ ] Set screen recorder to 1920x1080, 30 fps, system audio off, mic on.
- [ ] Test mic level on a 5-second throwaway take.

If recording locally instead of on the Space:

```bash
export DASHSCOPE_API_KEY="sk-..."
export QWEN_MODEL="qwen-plus"
streamlit run app.py
```

Never let the API key appear on screen — keep the terminal off-frame.

---

## Recording flow

Total target: **2:30-2:45**. Each beat is structured as:

- **Frame** — exactly what fills the screen at the start of the beat (the opening shot)
- **Action** — what to click or scroll during the beat
- **Say** — voiceover, read at a calm pace
- **Beat tip** — pacing or recovery note

### 0:00-0:20 — Hook and problem

**Frame:**
- Browser at 100% zoom on the HF Space URL.
- Top hero panel fully visible: the black `READINESS SCORE 30 / 100 · High risk` card on the left, the `repo / High-risk for ROCm CI` panel on the right with `SUBJECT` showing `samples/cuda_heavy_repo` and `BUNDLE` showing the outputs path.
- Cursor parked outside the score card (top-right corner of the page).
- Bookmarks bar hidden, no other browser tab visible.

**Action:** None — hold the frame still for the full 20 seconds.

**Say:**
> Many AI repositories are CUDA-first. Even after a one-time migration, future pull requests can quietly break AMD ROCm support. ROCm CI Doctor is an agentic workflow that keeps every PR honest about ROCm compatibility — and ships generated CI assets a maintainer can actually merge.

**Beat tip:** Do not move the cursor. Let the score "30 / 100" and the red "High risk" label do the selling.

---

### 0:20-0:55 — Run the analysis

**Frame opens on:** the same hero panel, now with the sidebar visible on the left edge of the screen.

**Action:**

1. Move cursor to the sidebar. Hover the `Sample repository` selector showing `Cuda Heavy Repo`. (~2 s)
2. Click `Run Analysis`. (~1 s)
3. Once results render, scroll up so the four KPI tiles fill the frame: `HIGH RISKS 1`, `CI GAPS 4`, `FILES SCANNED 120`, `GENERATED 8`. Hold ~3 s. (~5 s)
4. Click the **Risks** tab. Center the **Top risks** bullet list in the frame. Slowly hover the cursor down each row so judges can read them: `gap:missing_rocm_smoke_test` → `gap:missing_github_actions` → `gap:missing_tests` → `pattern:cuda_method` → `pattern:hardcoded_cuda_device`. (~20 s)

**Say:**
> The Repo Inspector Agent walks the source tree, dependencies, Dockerfiles, and existing workflows. For this CUDA-heavy sample it finds 120 files, scores readiness 30 out of 100, and surfaces five concrete risks — a missing ROCm smoke test, no AMD CI workflow, no test suite, and hardcoded `cuda` device calls.

**Beat tip:** Slow scroll. Each risk label needs roughly one second on screen for a judge to read. Do not click the risks open — keep the list compact.

---

### 0:55-1:30 — Generated ROCm CI assets

**Frame opens on:** the **Generated Assets** tab, with the file list visible on the left and the first file's contents filling most of the frame.

**Action:**

1. Click **Generated Assets** tab. (~1 s)
2. Click each of the four files below in order. Each file's content should fill the right-hand pane; hold for ~6 s with the cursor parked on a meaningful line (the workflow's `runs-on` line, the Dockerfile's `FROM` line, etc.). (~24 s total)
   - `.github/workflows/rocm-ci.yml` → cursor on the `runs-on:` line
   - `Dockerfile.rocm` → cursor on the `FROM rocm/...` line
   - `tests/test_rocm_smoke.py` → cursor on the `torch.cuda.is_available()` assertion
   - `scripts/run_rocm_validation.sh` → cursor on the smoke + benchmark invocation lines
3. Quick swipe to the **Report** tab — let `ROCM_CI_REPORT.md` render for ~4 s, do not scroll. (~4 s)

**Say:**
> The CI Architect and Validation Agents generate the files a maintainer can review in a pull request: a ROCm GitHub Actions workflow targeting an AMD GPU runner, a ROCm container Dockerfile, a torch-based smoke test, and a benchmark harness. Every asset is deterministic — same input, same output — so the analyzer is auditable, not a black box.

**Beat tip:** This section is the core of Track 1 — do not rush. If you must cut to make 2:45, cut from the Phase 5 evidence beat, not from here.

---

### 1:30-2:00 — AI Doctor with Qwen

**Frame opens on:** the **AI Doctor** tab. Visible: the four green `COMPLETE` agent cards (Repo Inspector → CI Architect → Validation → Report) in a single row, with the `Qwen enabled` status banner directly below them showing the `qwen-plus` model name.

**Action:**

1. Hold on the four agent cards for ~3 s. (~3 s)
2. Click the **Generate Qwen Maintainer Summary** button. (~1 s)
3. Wait for the spinner. As text streams in, scroll so the rendered summary fills the frame, cursor parked at the start of the first bullet. Hold ~10 s. (~12 s)
4. Scroll down to **Ask the Doctor**. The text area is pre-filled: *"What should I fix first before adding the generated ROCm CI workflow?"* — do not edit it. Click **Ask Qwen**. (~2 s)
5. Once the answer renders, scroll so the answer fills the frame. Cursor parked at the first numbered item. Hold ~10 s. (~12 s)

**Say:**
> Qwen — running on `qwen-plus` — is layered on top of the deterministic analyzer. It does not replace the score or the risk list. It explains them in maintainer language and prioritizes what to fix first, so the engineer doesn't have to read the whole report to act.

**Beat tip:** If Qwen takes more than ~6 s on either call, narrate the four agent cards while waiting. If Qwen errors, stay on the deterministic summary above the button and add the fallback line — see Fallbacks.

---

### 2:00-2:25 — AMD Developer Cloud proof

**Frame opens on:** the GitHub view of `evidence/amd-cloud/PHASE5_PROOF.md`, scrolled so the **Run Summary** and **Validation Results** headings are both visible. URL bar visible at top showing the `github.com/ryder1018/rocm-ci-doctor/blob/main/...` path.

**Action:**

1. Drag-select these four lines in order, ~3 s each. Use mouse-drag-select so the highlight stays on screen, not just cursor hover. (~12 s)
   - `PyTorch: 2.9.0.dev20250821+rocm7.0.0.git125803b7`
   - `ROCm/HIP: 7.0.51831-a3e329ad8`
   - `Smoke test status: ok` and `Smoke test elapsed time: 502.992 ms`
   - `Benchmark status: ok` and `Benchmark mean time: 0.196 ms`
2. (Optional) Click into `rocm-smi.txt` for ~3 s to flash real GPU output, then back. (~6 s)

**Say:**
> The generated bundle was executed on AMD Developer Cloud, in a PyTorch ROCm 7 container. The smoke test passed in 502 milliseconds, and a 2K matmul benchmark ran clean with a 0.196 millisecond mean. This evidence is committed in the repo — judges can verify the run is real, not synthetic.

**Beat tip:** Drag-select the values — do not just hover. The text highlight is what makes the proof feel concrete on video.

---

### 2:25-2:45 — Close and CTA

**Frame opens on:** a static end card filling the full screen — black background, three white text blocks centered. No browser, no UI.

**End-card template (full-screen image, generate before recording):**

```
ROCm CI Doctor

github.com/ryder1018/rocm-ci-doctor
huggingface.co/spaces/lablab-ai-amd-developer-hackathon/rocm-ci-doctor

Track 1 · AMD Developer Cloud · Qwen
```

**Action:** Hold the end card still for the full 20 seconds.

**Say:**
> ROCm CI Doctor is not a CUDA-to-ROCm rewriter. It's a continuous AMD readiness gate, built for the maintainers of AI repositories that need ROCm support to stay green after every pull request. Track 1, agentic workflow, AMD Cloud verified, Qwen-augmented. Links in the description.

**Beat tip:** If you don't have time to make a static end card, fall back to a clean browser frame with both URLs visible (one tab title for GitHub, URL bar showing the HF Space). Hold still — no clicking.

---

## Fallbacks

| If this fails… | Do this instead |
|---|---|
| HF Space cold-starts >30s on click | Use the pre-warmed tab from the checklist; never click `Run Analysis` from a cold load on camera. |
| Qwen returns an error mid-take | Stay on the AI Doctor tab, narrate the deterministic agent cards, and say "Qwen is optional — the four deterministic agents are the source of truth." Cut and re-take only the Qwen beat. |
| Space is fully down | Record locally with `streamlit run app.py` and the local `DASHSCOPE_API_KEY`. Keep the terminal off-frame. |
| GitHub evidence page is slow | Show the same file from a local VS Code preview of `evidence/amd-cloud/PHASE5_PROOF.md`. |

---

## Post-recording checklist

- [ ] Total length is between 2:15 and 2:50 (lablab tolerance).
- [ ] No API key, email, or local username visible in any frame.
- [ ] Audio is clear, no background noise, no mouth clicks at cuts.
- [ ] First 3 seconds show the readiness score — that's the thumbnail-worthy frame.
- [ ] Description includes: GitHub repo URL, HF Space URL, Track 1 line, AMD + lablab tags.
- [ ] Captions/subtitles attached (optional but recommended for international judges).
- [ ] Upload to YouTube *unlisted* first; share the unlisted link in `SUBMISSION.md`. Flip to public only after the lablab submission is locked in.
