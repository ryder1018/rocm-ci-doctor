"""Minimal .env loader used for local demo secrets."""

from __future__ import annotations

import os
from pathlib import Path


_LOADED_PATHS: set[Path] = set()


def load_dotenv(path: Path | str = ".env", *, override: bool = False) -> bool:
    """Load KEY=VALUE pairs from a .env file into os.environ.

    This intentionally supports only the small subset needed for local demo
    configuration. Existing environment variables win unless override=True.
    """

    env_path = Path(path)
    if not env_path.exists():
        return False

    resolved = env_path.resolve()
    if resolved in _LOADED_PATHS and not override:
        return True

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        value = _strip_quotes(value.strip())
        if override or key not in os.environ:
            os.environ[key] = value

    _LOADED_PATHS.add(resolved)
    return True


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value
