from pathlib import Path
import unittest

from rocm_ci_doctor.analyzer import analyze_repository


ROOT = Path(__file__).resolve().parents[1]


class AnalyzerSampleTests(unittest.TestCase):
    def test_simple_pytorch_repo_detects_pytorch(self) -> None:
        result = analyze_repository(ROOT / "samples/simple_pytorch_repo")
        self.assertTrue(result["detected_stack"]["python"])
        self.assertTrue(result["detected_stack"]["pytorch"])
        self.assertTrue(result["detected_stack"]["transformers"])
        self.assertFalse(result["detected_stack"]["docker"])
        self.assertIn("tests/test_rocm_smoke.py", _asset_paths(result))

    def test_cuda_heavy_repo_reports_cuda_risks(self) -> None:
        result = analyze_repository(ROOT / "samples/cuda_heavy_repo")
        pattern_ids = {occurrence["id"] for occurrence in result["gpu_patterns"]}
        self.assertIn("cuda_base_image", pattern_ids)
        self.assertIn("cuda_method", pattern_ids)
        self.assertIn("nvidia_smi", pattern_ids)
        self.assertIn("Dockerfile.rocm", _asset_paths(result))

    def test_plain_python_repo_does_not_detect_pytorch(self) -> None:
        result = analyze_repository(ROOT / "samples/plain_python_repo")
        self.assertTrue(result["detected_stack"]["python"])
        self.assertFalse(result["detected_stack"]["pytorch"])
        self.assertIn("ROCM_CI_REPORT.md", _asset_paths(result))


def _asset_paths(result: dict) -> set[str]:
    return {asset["path"] for asset in result["recommended_assets"]}


if __name__ == "__main__":
    unittest.main()
