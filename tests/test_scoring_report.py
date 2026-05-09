from pathlib import Path
import contextlib
import io
import tempfile
import unittest

from rocm_ci_doctor.analyzer import analyze_repository
from rocm_ci_doctor.cli import main
from rocm_ci_doctor.report import generate_markdown_report
from rocm_ci_doctor.scoring import assess_repository


ROOT = Path(__file__).resolve().parents[1]


class ScoringAndReportTests(unittest.TestCase):
    def test_simple_repo_scores_higher_than_cuda_heavy_repo(self) -> None:
        simple = analyze_repository(ROOT / "samples/simple_pytorch_repo")
        cuda_heavy = analyze_repository(ROOT / "samples/cuda_heavy_repo")

        simple_assessment = assess_repository(simple)
        cuda_assessment = assess_repository(cuda_heavy)

        self.assertGreater(simple_assessment["score"], cuda_assessment["score"])
        self.assertEqual(simple_assessment["max_score"], 100)
        self.assertEqual(cuda_assessment["max_score"], 100)

    def test_cuda_heavy_risks_are_enriched_and_categorized(self) -> None:
        analysis = analyze_repository(ROOT / "samples/cuda_heavy_repo")
        assessment = assess_repository(analysis)

        high_risk_ids = {risk["id"] for risk in assessment["risks_by_severity"]["high"]}
        self.assertIn("pattern:cuda_package", high_risk_ids)
        self.assertIn("gap:missing_rocm_smoke_test", high_risk_ids)

        cuda_package = next(
            risk
            for risk in assessment["risks_by_severity"]["high"]
            if risk["id"] == "pattern:cuda_package"
        )
        self.assertEqual(cuda_package["fix_category"], "dependency portability")
        self.assertIn("CUDA-specific", cuda_package["explanation"])

    def test_markdown_report_contains_phase2_sections(self) -> None:
        analysis = analyze_repository(ROOT / "samples/cuda_heavy_repo")
        analysis["assessment"] = assess_repository(analysis)
        report = generate_markdown_report(analysis)

        self.assertIn("# ROCm CI Report:", report)
        self.assertIn("## Readiness Score", report)
        self.assertIn("## Risks By Severity", report)
        self.assertIn("pattern:cuda_package", report)
        self.assertIn("## AMD Developer Cloud Runbook", report)

    def test_cli_can_write_json_and_report_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            json_out = Path(tmpdir) / "analysis.json"
            report_out = Path(tmpdir) / "ROCM_CI_REPORT.md"

            with contextlib.redirect_stdout(io.StringIO()):
                exit_code = main(
                    [
                        "analyze",
                        str(ROOT / "samples/simple_pytorch_repo"),
                        "--json-out",
                        str(json_out),
                        "--report-out",
                        str(report_out),
                        "--compact",
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertTrue(json_out.exists())
            self.assertTrue(report_out.exists())
            self.assertIn("assessment", json_out.read_text(encoding="utf-8"))
            self.assertIn("ROCm CI Report", report_out.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
