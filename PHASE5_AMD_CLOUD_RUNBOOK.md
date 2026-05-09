# Phase 5 AMD Developer Cloud Runbook

This runbook explains the only manual step left in Phase 5: running the generated validation bundle on real AMD/ROCm hardware.

## What Is Already Implemented

ROCm CI Doctor now generates:

- `AMD_CLOUD_VALIDATION.md`
- `scripts/run_rocm_validation.sh`
- `evidence/README.md`
- `tests/test_rocm_smoke.py`
- `benchmarks/benchmark_rocm.py`

The validation script collects ROCm/PyTorch environment metadata, runs the smoke test, runs the benchmark, and writes a demo-ready evidence summary.

## What You Need To Do

You need access to an AMD Developer Cloud instance or any AMD GPU machine with ROCm and PyTorch installed.

No API key is needed by this project itself. You only need whatever login, SSH key, or web console access AMD Developer Cloud gives you.

## Local Preparation

From this repository:

```bash
conda run -n rocm-ci-doctor python -m rocm_ci_doctor analyze samples/cuda_heavy_repo \
  --json-out outputs/phase5-check.json \
  --report-out outputs/phase5-ROCM_CI_REPORT.md \
  --generate-out outputs/phase5-check-bundle \
  --compact
```

Optional archive for upload:

```bash
tar -czf outputs/phase5-check-bundle.tar.gz -C outputs phase5-check-bundle
```

## AMD Developer Cloud Steps

Upload or clone the generated bundle onto the AMD/ROCm machine, then run:

```bash
cd phase5-check-bundle
chmod +x scripts/run_rocm_validation.sh
./scripts/run_rocm_validation.sh evidence/amd-cloud
```

Expected output files:

- `evidence/amd-cloud/SUMMARY.md`
- `evidence/amd-cloud/environment.json`
- `evidence/amd-cloud/smoke.json`
- `evidence/amd-cloud/benchmark.json`
- `evidence/amd-cloud/benchmark.stdout.log`

## Proof Checklist

The evidence counts as real Phase 5 proof when:

- `environment.json` has a non-empty `torch.hip_version`.
- `environment.json` shows at least one GPU device.
- `smoke.json` has `"status": "ok"`.
- `benchmark.json` has `"status": "ok"`.
- `SUMMARY.md` names the device and benchmark mean time.

CPU dry-runs are useful for debugging, but they do not count as AMD/ROCm proof.

## Bring Evidence Back

After the run, copy `evidence/amd-cloud/` back into this project, for example:

```bash
mkdir -p evidence
scp -r <your-amd-cloud-host>:~/phase5-check-bundle/evidence/amd-cloud evidence/
```

Then use `evidence/amd-cloud/SUMMARY.md` and the JSON files in the final demo if live cloud access is unavailable.
