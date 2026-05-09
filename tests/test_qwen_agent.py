from pathlib import Path
import unittest
from unittest import mock

from rocm_ci_doctor.analyzer import analyze_repository
from rocm_ci_doctor.qwen_agent import (
    DEFAULT_QWEN_MODEL,
    QwenResponse,
    answer_qwen_question,
    deterministic_agent_steps,
    deterministic_summary,
    generate_qwen_summary,
    qwen_configured,
)
from rocm_ci_doctor.scoring import assess_repository
import rocm_ci_doctor.qwen_agent as qwen_agent


ROOT = Path(__file__).resolve().parents[1]


class QwenAgentTests(unittest.TestCase):
    def _analysis(self) -> dict:
        analysis = analyze_repository(ROOT / "samples/cuda_heavy_repo")
        analysis["assessment"] = assess_repository(analysis)
        analysis["generated_bundle"] = {
            "files": [
                {"path": ".github/workflows/rocm-ci.yml"},
                {"path": "tests/test_rocm_smoke.py"},
            ]
        }
        return analysis

    def test_qwen_configured_checks_key(self) -> None:
        with mock.patch.object(qwen_agent, "load_dotenv", return_value=False), mock.patch.dict(
            "os.environ",
            {"DASHSCOPE_API_KEY": ""},
            clear=False,
        ):
            self.assertFalse(qwen_configured(""))
            self.assertTrue(qwen_configured("sk-test"))

    def test_deterministic_agent_steps_are_present(self) -> None:
        steps = deterministic_agent_steps(self._analysis())
        self.assertEqual(
            [step["agent"] for step in steps],
            [
                "Repo Inspector Agent",
                "CI Architect Agent",
                "Validation Agent",
                "Report Agent",
            ],
        )
        self.assertTrue(all(step["status"] == "Complete" for step in steps))

    def test_deterministic_summary_mentions_score_and_risks(self) -> None:
        summary = deterministic_summary(self._analysis())
        self.assertIn("Deterministic Agent Summary", summary)
        self.assertIn("10/100", summary)
        self.assertIn("pattern:cuda_package", summary)

    def test_qwen_summary_uses_mocked_client(self) -> None:
        with mock.patch("rocm_ci_doctor.qwen_agent.call_qwen") as call_qwen:
            call_qwen.return_value = QwenResponse("summary", DEFAULT_QWEN_MODEL)
            response = generate_qwen_summary(self._analysis(), api_key="sk-test")

        self.assertEqual(response.content, "summary")
        messages = call_qwen.call_args.args[0]
        self.assertIn("maintainer-facing", messages[1]["content"])
        self.assertIn("cuda_heavy_repo", messages[1]["content"])

    def test_qwen_question_uses_mocked_client(self) -> None:
        with mock.patch("rocm_ci_doctor.qwen_agent.call_qwen") as call_qwen:
            call_qwen.return_value = QwenResponse("answer", DEFAULT_QWEN_MODEL)
            response = answer_qwen_question(self._analysis(), "What first?", api_key="sk-test")

        self.assertEqual(response.content, "answer")
        messages = call_qwen.call_args.args[0]
        self.assertIn("Question: What first?", messages[1]["content"])


if __name__ == "__main__":
    unittest.main()
