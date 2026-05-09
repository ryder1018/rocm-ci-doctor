from pathlib import Path
import json
import py_compile
import tempfile
import unittest

from rocm_ci_doctor.analyzer import analyze_repository
from rocm_ci_doctor.generator import generate_asset_bundle
from rocm_ci_doctor.scoring import assess_repository


ROOT = Path(__file__).resolve().parents[1]


class GeneratorTests(unittest.TestCase):
    def test_generate_asset_bundle_writes_expected_files(self) -> None:
        analysis = analyze_repository(ROOT / "samples/cuda_heavy_repo")
        analysis["assessment"] = assess_repository(analysis)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "bundle"
            manifest = generate_asset_bundle(analysis, output_dir)

            expected_paths = {
                ".github/workflows/rocm-ci.yml",
                "AMD_CLOUD_VALIDATION.md",
                "Dockerfile.rocm",
                "ROCM_CI_REPORT.md",
                "benchmarks/benchmark_rocm.py",
                "evidence/README.md",
                "scripts/run_rocm_validation.sh",
                "tests/test_rocm_smoke.py",
            }
            self.assertEqual(expected_paths, {file["path"] for file in manifest["files"]})

            for relative_path in expected_paths:
                self.assertTrue((output_dir / relative_path).exists(), relative_path)
            self.assertTrue((output_dir / "ASSET_MANIFEST.json").exists())

            self.assertIn("runs-on: [self-hosted, linux, x64, rocm]", (output_dir / ".github/workflows/rocm-ci.yml").read_text())
            self.assertIn("ARG ROCM_PYTORCH_IMAGE", (output_dir / "Dockerfile.rocm").read_text())
            self.assertIn("Readiness Score", (output_dir / "ROCM_CI_REPORT.md").read_text())
            self.assertIn("AMD Developer Cloud", (output_dir / "AMD_CLOUD_VALIDATION.md").read_text())
            self.assertIn("run_rocm_validation.sh", (output_dir / "evidence/README.md").read_text())

    def test_generated_python_assets_are_syntactically_valid(self) -> None:
        analysis = analyze_repository(ROOT / "samples/simple_pytorch_repo")
        analysis["assessment"] = assess_repository(analysis)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "bundle"
            generate_asset_bundle(analysis, output_dir)

            py_compile.compile(str(output_dir / "tests/test_rocm_smoke.py"), doraise=True)
            py_compile.compile(str(output_dir / "benchmarks/benchmark_rocm.py"), doraise=True)

    def test_generated_validation_script_is_syntactically_valid_bash(self) -> None:
        analysis = analyze_repository(ROOT / "samples/simple_pytorch_repo")
        analysis["assessment"] = assess_repository(analysis)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "bundle"
            generate_asset_bundle(analysis, output_dir)

            import subprocess

            completed = subprocess.run(
                ["bash", "-n", str(output_dir / "scripts/run_rocm_validation.sh")],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_manifest_file_is_valid_json(self) -> None:
        analysis = analyze_repository(ROOT / "samples/plain_python_repo")
        analysis["assessment"] = assess_repository(analysis)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "bundle"
            generate_asset_bundle(analysis, output_dir)
            manifest = json.loads((output_dir / "ASSET_MANIFEST.json").read_text(encoding="utf-8"))

            self.assertEqual(manifest["generator_version"], "phase5")
            self.assertEqual(manifest["repo_name"], "plain_python_repo")
            self.assertTrue(manifest["manifest_file"].endswith("ASSET_MANIFEST.json"))


if __name__ == "__main__":
    unittest.main()
