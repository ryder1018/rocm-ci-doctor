import os
from pathlib import Path
import tempfile
import unittest

from rocm_ci_doctor.env_loader import load_dotenv


class EnvLoaderTests(unittest.TestCase):
    def test_load_dotenv_reads_values_without_overriding_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text(
                "\n".join(
                    [
                        "DASHSCOPE_API_KEY=sk-test",
                        'QWEN_MODEL="qwen3.6-plus"',
                        "# ignored",
                    ]
                ),
                encoding="utf-8",
            )

            old_key = os.environ.pop("DASHSCOPE_API_KEY", None)
            old_model = os.environ.get("QWEN_MODEL")
            os.environ["QWEN_MODEL"] = "already-set"
            try:
                self.assertTrue(load_dotenv(env_file))
                self.assertEqual(os.environ["DASHSCOPE_API_KEY"], "sk-test")
                self.assertEqual(os.environ["QWEN_MODEL"], "already-set")
            finally:
                if old_key is None:
                    os.environ.pop("DASHSCOPE_API_KEY", None)
                else:
                    os.environ["DASHSCOPE_API_KEY"] = old_key
                if old_model is None:
                    os.environ.pop("QWEN_MODEL", None)
                else:
                    os.environ["QWEN_MODEL"] = old_model

    def test_load_dotenv_can_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("QWEN_MODEL=qwen-plus\n", encoding="utf-8")
            old_model = os.environ.get("QWEN_MODEL")
            os.environ["QWEN_MODEL"] = "already-set"
            try:
                self.assertTrue(load_dotenv(env_file, override=True))
                self.assertEqual(os.environ["QWEN_MODEL"], "qwen-plus")
            finally:
                if old_model is None:
                    os.environ.pop("QWEN_MODEL", None)
                else:
                    os.environ["QWEN_MODEL"] = old_model


if __name__ == "__main__":
    unittest.main()
