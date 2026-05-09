"""Command-line interface for ROCm CI Doctor."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from .analyzer import analyze_repository
from .generator import generate_asset_bundle
from .report import generate_markdown_report
from .repo_loader import RepoLoadError, load_repository
from .scoring import assess_repository


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rocm-ci-doctor",
        description="Analyze AI repositories for AMD/ROCm CI readiness.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser(
        "analyze",
        help="Analyze a local repository path or public GitHub URL.",
    )
    analyze.add_argument(
        "source",
        help="Local path or public GitHub URL to analyze.",
    )
    analyze.add_argument(
        "--json-out",
        type=Path,
        help="Optional path to write the structured JSON result.",
    )
    analyze.add_argument(
        "--report-out",
        type=Path,
        help="Optional path to write a ROCm CI markdown report.",
    )
    analyze.add_argument(
        "--generate-out",
        type=Path,
        help="Optional directory to write generated ROCm CI assets.",
    )
    analyze.add_argument(
        "--compact",
        action="store_true",
        help="Print compact JSON instead of pretty formatted JSON.",
    )
    return parser


def run_analyze(args: argparse.Namespace) -> int:
    try:
        with load_repository(args.source) as loaded_repo:
            result = analyze_repository(
                loaded_repo.path,
                source=args.source,
                loaded_from=loaded_repo.loaded_from,
            )
    except RepoLoadError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    result["assessment"] = assess_repository(result)

    if args.generate_out:
        result["generated_bundle"] = generate_asset_bundle(result, args.generate_out)

    indent = None if args.compact else 2
    output = json.dumps(result, indent=indent, sort_keys=True)
    print(output)

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(output + "\n", encoding="utf-8")

    if args.report_out:
        args.report_out.parent.mkdir(parents=True, exist_ok=True)
        args.report_out.write_text(generate_markdown_report(result), encoding="utf-8")

    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "analyze":
        return run_analyze(args)

    parser.error(f"unknown command: {args.command}")
    return 2
