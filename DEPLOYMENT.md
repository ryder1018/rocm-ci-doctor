# ROCm CI Doctor Deployment Guide

This guide prepares the project for Phase 7 public delivery.

## Local Verification

Run these before publishing:

```bash
python -m pytest -q
python -m rocm_ci_doctor analyze samples/cuda_heavy_repo --generate-out outputs/submission-check-bundle --compact
bash -n outputs/submission-check-bundle/scripts/run_rocm_validation.sh
streamlit run app.py --server.headless true --server.port 8501
```

Open `http://localhost:8501` and verify:

- Sample repository analysis works.
- Generated asset previews render.
- AI Doctor deterministic cards render.
- Qwen summary and Q&A work if `DASHSCOPE_API_KEY` is configured.

## Secret Hygiene

Before publishing:

```bash
git check-ignore -v .env
rg -n "sk-|DASHSCOPE_API_KEY|API_KEY|TOKEN|SECRET|PASSWORD" . \
  -g '!.env' \
  -g '!.env.*' \
  -g '!outputs/**' \
  -g '!evidence/**' \
  -g '!.git/**'
```

Expected:

- `.env` is ignored.
- `.env.example` contains only placeholder values.
- Real API keys do not appear in tracked files.

## GitHub Repository

Recommended public repository contents:

- `README.md`
- `PLAN.md`
- `DEMO_SCRIPT.md`
- `SUBMISSION.md`
- `DEPLOYMENT.md`
- `PHASE5_AMD_CLOUD_RUNBOOK.md`
- `app.py`
- `requirements.txt`
- `environment.yml`
- `rocm_ci_doctor/`
- `tests/`
- `samples/`
- `assets/`
- `evidence/amd-cloud/PHASE5_PROOF.md`

Do not publish:

- `.env`
- local logs
- local process IDs
- temporary generated bundles unless intentionally curated as examples

## Hugging Face Space

Recommended Space settings:

- SDK: `Streamlit`
- App file: `app.py`
- Python dependencies: `requirements.txt`
- Visibility: public for the hackathon submission

Required files:

- `app.py`
- `requirements.txt`
- `rocm_ci_doctor/`
- `samples/`
- `assets/`
- `evidence/amd-cloud/PHASE5_PROOF.md`

Optional Space secret:

- `DASHSCOPE_API_KEY`

The app must remain usable without `DASHSCOPE_API_KEY`. In that mode, the deterministic analyzer and deterministic AI Doctor cards still work.

## lablab.ai Submission Fields

Use `SUBMISSION.md` as the source for:

- Project title.
- Short description.
- Long description.
- Track 1 explanation.
- Qwen usage.
- AMD Developer Cloud proof.
- Demo script.
- Links.
