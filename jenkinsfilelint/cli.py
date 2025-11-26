#!/usr/bin/env python3
"""Command-line interface for jenkinsfilelint."""

import sys
import argparse
import fnmatch
import io
from .linter import JenkinsfileLinter
from . import __version__


def should_skip_file(filepath: str, skip_patterns: list) -> bool:
    """Check if a file should be skipped based on the provided patterns.

    Args:
        filepath: Path to the file to check
        skip_patterns: List of glob patterns to match against

    Returns:
        True if the file should be skipped, False otherwise
    """
    if not skip_patterns:
        return False

    for pattern in skip_patterns:
        if fnmatch.fnmatch(filepath, pattern):
            return True
    return False


def main():
    """Main entry point for the CLI."""
    # Ensure stdout and stderr use UTF-8 encoding on Windows
    # Only wrap if not already wrapped to avoid issues in tests
    if sys.platform == "win32":
        if (
            not isinstance(sys.stdout, io.TextIOWrapper)
            or sys.stdout.encoding.lower() != "utf-8"
        ):
            sys.stdout = io.TextIOWrapper(
                sys.stdout.buffer, encoding="utf-8", errors="replace"
            )
        if (
            not isinstance(sys.stderr, io.TextIOWrapper)
            or sys.stderr.encoding.lower() != "utf-8"
        ):
            sys.stderr = io.TextIOWrapper(
                sys.stderr.buffer, encoding="utf-8", errors="replace"
            )

    parser = argparse.ArgumentParser(
        description="Validate Jenkinsfiles using Jenkins API"
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "jenkinsfile",
        nargs="+",
        help="Path to Jenkinsfile(s) to validate",
    )
    parser.add_argument(
        "--jenkins-url",
        help="Jenkins server URL (can also be set via JENKINS_URL env var)",
    )
    parser.add_argument(
        "--username",
        help="Jenkins username (can also be set via JENKINS_USER env var)",
    )
    parser.add_argument(
        "--token",
        help="Jenkins API token (can also be set via JENKINS_TOKEN env var)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose output",
    )
    parser.add_argument(
        "--skip",
        action="append",
        default=[],
        metavar="PATTERN",
        help="Glob pattern(s) for files to skip. Can be used multiple times. "
        "Example: --skip '*/src/*.groovy' --skip 'vars/*.groovy'",
    )

    args = parser.parse_args()

    # Create linter instance
    linter = JenkinsfileLinter(
        jenkins_url=args.jenkins_url,
        username=args.username,
        token=args.token,
    )

    # Validate all provided files
    all_valid = True
    for jenkinsfile in args.jenkinsfile:
        # Check if file should be skipped
        if should_skip_file(jenkinsfile, args.skip):
            if args.verbose:
                print(f"⊘ {jenkinsfile}: Skipped (matches skip pattern)")
            continue

        if args.verbose:
            print(f"Validating {jenkinsfile}...")

        is_valid, message = linter.validate(jenkinsfile)

        if is_valid:
            # Show valid status for multiple files or when verbose
            if args.verbose or len(args.jenkinsfile) > 1:
                print(f"✓ {jenkinsfile}: Valid")
            if args.verbose and message:
                print(f"  {message}")
        else:
            print(f"✗ {jenkinsfile}: Invalid", file=sys.stderr)
            print(f"  {message}", file=sys.stderr)
            all_valid = False

    # Exit with appropriate code
    sys.exit(0 if all_valid else 1)


if __name__ == "__main__":
    main()
