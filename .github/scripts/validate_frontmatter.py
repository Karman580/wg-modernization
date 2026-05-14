#!/usr/bin/env python3
"""
Validates YAML frontmatter for framework/ documents against the schema
defined in CONTENT_SCHEMA.md.

Usage:
    python validate_frontmatter.py <file1.md> [file2.md ...]

Exit codes:
    0 — all files pass
    1 — one or more validation errors found
    2 — script invocation error
"""

import re
import sys

try:
    import frontmatter
except ImportError:
    print("error: python-frontmatter is not installed (pip install python-frontmatter)")
    sys.exit(2)


ALLOWED_DOMAINS = {
    "applications",
    "data",
    "operations",
    "interoperability",
    "security",
}

ALLOWED_STATUSES = {"draft", "review", "approved"}

# Matches MAJOR.MINOR — e.g. "0.1", "1.0"
VERSION_RE = re.compile(r"^\d+\.\d+$")

# Matches ISO-8601 calendar date — e.g. "2024-06-01"
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# Fields requiring non-empty values once a document leaves draft
STRICT_STATUSES = {"review", "approved"}


def validate(path: str) -> list[str]:
    errors = []

    try:
        with open(path, encoding="utf-8") as fh:
            post = frontmatter.load(fh)
    except Exception as exc:
        return [f"{path}: malformed frontmatter — {exc}"]

    meta = post.metadata

    # --- Fields required at every lifecycle stage ---

    title = meta.get("title", "")
    if not isinstance(title, str) or not title.strip():
        errors.append(
            f"{path}: 'title' must be a non-empty string — got {title!r}"
        )

    domain = meta.get("domain", "")
    if domain not in ALLOWED_DOMAINS:
        errors.append(
            f"{path}: 'domain' invalid — got {domain!r}, "
            f"expected one of: {', '.join(sorted(ALLOWED_DOMAINS))}"
        )

    status = meta.get("status", "")
    if status not in ALLOWED_STATUSES:
        errors.append(
            f"{path}: 'status' invalid — got {status!r}, "
            f"expected one of: {', '.join(sorted(ALLOWED_STATUSES))}"
        )

    version = str(meta.get("version", ""))
    if not VERSION_RE.match(version):
        errors.append(
            f"{path}: 'version' must match MAJOR.MINOR (e.g. '0.1') — got {version!r}"
        )

    # --- Additional fields required for review and approved documents ---

    if status in STRICT_STATUSES:
        authors = meta.get("authors", [])
        if not isinstance(authors, list) or len(authors) == 0:
            errors.append(
                f"{path}: 'authors' must be a non-empty list "
                f"when status is {status!r} — got {authors!r}"
            )

        last_updated = str(meta.get("last-updated", ""))
        if not DATE_RE.match(last_updated):
            errors.append(
                f"{path}: 'last-updated' must be a valid ISO-8601 date (YYYY-MM-DD) "
                f"when status is {status!r} — got {last_updated!r}"
            )

    return errors


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: validate_frontmatter.py <file> [file ...]")
        sys.exit(2)

    paths = sys.argv[1:]
    all_errors: list[str] = []

    for path in paths:
        file_errors = validate(path)
        all_errors.extend(file_errors)

    if all_errors:
        print("Frontmatter validation failed:\n")
        for err in all_errors:
            print(f"  ✗ {err}")
        print(f"\n{len(all_errors)} error(s) found.")
        sys.exit(1)

    print(f"Frontmatter validation passed ({len(paths)} file(s) checked).")


if __name__ == "__main__":
    main()
