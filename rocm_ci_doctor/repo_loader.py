"""Load local and remote repositories for analysis."""

from __future__ import annotations

import contextlib
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


class RepoLoadError(RuntimeError):
    """Raised when a repository cannot be loaded."""


@dataclass(frozen=True)
class LoadedRepo:
    """Repository path loaded for analysis."""

    source: str
    path: Path
    loaded_from: str


GITHUB_URL_RE = re.compile(
    r"^(https://github\.com/[^/\s]+/[^/\s]+(?:\.git)?/?|git@github\.com:[^/\s]+/[^/\s]+(?:\.git)?)$"
)


def is_github_url(source: str) -> bool:
    """Return whether the source looks like a GitHub repository URL."""

    return bool(GITHUB_URL_RE.match(source.strip()))


def _clone_repository(source: str, destination: Path) -> None:
    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", source, str(destination)],
            check=True,
            capture_output=True,
            text=True,
            timeout=180,
        )
    except FileNotFoundError as exc:
        raise RepoLoadError("git is required to clone GitHub repositories") from exc
    except subprocess.TimeoutExpired as exc:
        raise RepoLoadError(f"timed out while cloning {source}") from exc
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip() or exc.stdout.strip() or "unknown git error"
        raise RepoLoadError(f"failed to clone {source}: {stderr}") from exc


@contextlib.contextmanager
def load_repository(source: str) -> Iterator[LoadedRepo]:
    """Load a local path or public GitHub repository URL."""

    clean_source = source.strip()
    if not clean_source:
        raise RepoLoadError("source is empty")

    if is_github_url(clean_source):
        temp_dir = Path(tempfile.mkdtemp(prefix="rocm-ci-doctor-"))
        repo_dir = temp_dir / "repo"
        try:
            _clone_repository(clean_source, repo_dir)
            yield LoadedRepo(source=clean_source, path=repo_dir, loaded_from="github")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
        return

    path = Path(clean_source).expanduser().resolve()
    if not path.exists():
        raise RepoLoadError(f"local path does not exist: {path}")
    if not path.is_dir():
        raise RepoLoadError(f"local path is not a directory: {path}")

    yield LoadedRepo(source=clean_source, path=path, loaded_from="local")
