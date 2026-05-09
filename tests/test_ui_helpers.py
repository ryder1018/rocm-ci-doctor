from pathlib import Path
import tempfile
import unittest
import zipfile

from rocm_ci_doctor.ui_helpers import (
    default_bundle_dir,
    generated_file_paths,
    list_sample_repositories,
    risk_rows,
    slugify_source,
    stack_rows,
    zip_directory_bytes,
)


class UIHelperTests(unittest.TestCase):
    def test_sample_repositories_are_listed(self) -> None:
        samples = dict(list_sample_repositories())
        self.assertIn("Cuda Heavy Repo", samples)
        self.assertEqual(samples["Cuda Heavy Repo"], "samples/cuda_heavy_repo")

    def test_slugify_source_and_default_bundle_dir(self) -> None:
        self.assertEqual(slugify_source("https://github.com/pypa/sampleproject"), "https-github-com-pypa-sampleproject")
        self.assertEqual(default_bundle_dir("samples/cuda_heavy_repo").as_posix(), "outputs/ui-bundles/samples-cuda-heavy-repo")

    def test_stack_and_risk_rows(self) -> None:
        analysis = {
            "detected_stack": {"python": True, "docker": False},
            "assessment": {
                "risks_by_severity": {
                    "high": [
                        {
                            "id": "pattern:cuda_package",
                            "count": 2,
                            "fix_category": "dependency portability",
                            "recommended_fix": "Use ROCm-compatible dependencies.",
                        }
                    ],
                    "medium": [],
                    "low": [],
                }
            },
        }
        self.assertEqual(
            stack_rows(analysis),
            [{"Signal": "Dockerfile", "Detected": "No"}, {"Signal": "Python", "Detected": "Yes"}],
        )
        risks = risk_rows(analysis)
        self.assertEqual(len(risks), 1)
        self.assertEqual(risks[0]["Severity"], "High")
        self.assertEqual(risks[0]["Risk ID"], "pattern:cuda_package")
        self.assertEqual(risks[0]["Findings"], 2)

    def test_zip_directory_bytes_excludes_pycache(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "a.txt").write_text("hello", encoding="utf-8")
            (root / "__pycache__").mkdir()
            (root / "__pycache__" / "ignored.pyc").write_bytes(b"ignored")

            archive_bytes = zip_directory_bytes(root)
            archive_path = root / "bundle.zip"
            archive_path.write_bytes(archive_bytes)
            with zipfile.ZipFile(archive_path) as archive:
                self.assertEqual(archive.namelist(), ["a.txt"])

    def test_generated_file_paths(self) -> None:
        manifest = {"files": [{"path": "Dockerfile.rocm"}, {"path": "ROCM_CI_REPORT.md"}]}
        self.assertEqual(generated_file_paths(manifest), ["Dockerfile.rocm", "ROCM_CI_REPORT.md"])


if __name__ == "__main__":
    unittest.main()
