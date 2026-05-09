# Phase 5 AMD Developer Cloud Proof

ROCm CI Doctor successfully ran its generated validation bundle on AMD Developer Cloud.

## Run Summary

- Repository analyzed: `cuda_heavy_repo`
- Evidence captured at: `2026-05-08T08:30:12Z`
- Runtime location: DigitalOcean / AMD Developer Cloud PyTorch ROCm container
- Kernel: `Linux 6.8.0-84-generic x86_64 GNU/Linux`
- Python: `3.10.12`
- PyTorch: `2.9.0.dev20250821+rocm7.0.0.git125803b7`
- ROCm/HIP: `7.0.51831-a3e329ad8`
- PyTorch GPU API available: `true`
- GPU device count: `1`

## Validation Results

- Smoke test status: `ok`
- Smoke test elapsed time: `502.992 ms`
- Benchmark status: `ok`
- Benchmark workload: `2048 x 2048` matrix multiply
- Benchmark iterations: `10`
- Benchmark mean time: `0.196 ms`
- Benchmark median time: `0.19 ms`

## Evidence Files

- `SUMMARY.md`
- `environment.json`
- `smoke.json`
- `benchmark.json`
- `benchmark.stdout.log`
- `rocm-smi.txt`

## Notes

The DigitalOcean PyTorch ROCm image returned an empty string for `torch.cuda.get_device_name(0)`, but the run still provides ROCm hardware proof through:

- non-empty `torch.version.hip`
- `torch.cuda.is_available() == true`
- `torch.cuda.device_count() == 1`
- successful ROCm smoke test
- successful ROCm benchmark
- successful `rocm-smi` output in `rocm-smi.txt`
