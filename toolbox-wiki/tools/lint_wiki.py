"""Lightweight lint checks for toolbox-wiki.

Run from the repository root or from anywhere:

    python learning/adctoolbox-learning/toolbox-wiki/tools/lint_wiki.py

The script is intentionally dependency-free so future agents can run it before
and after wiki maintenance.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WIKI_DIR = ROOT / "wiki"
RAW_DIR = ROOT / "raw"
LOG_FILE = ROOT / "logs" / "log.md"
WIKI_INDEX = WIKI_DIR / "index.md"

LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
LOG_HEADING_RE = re.compile(r"^## \[\d{4}-\d{2}-\d{2}\] [a-z0-9_-]+ \| .+")

REQUIRED_METADATA = (
    "stage_link:",
    "source_links:",
    "rigor:",
    "status:",
    "last_updated:",
    "confidence:",
)

ALLOWED_STATUS = {"draft", "usable", "stable", "deprecated"}


def markdown_files() -> list[Path]:
    return sorted(ROOT.rglob("*.md"))


def generated_wiki_pages() -> list[Path]:
    return [
        path
        for path in sorted(WIKI_DIR.rglob("*.md"))
        if path.name != "index.md"
    ]


def is_external_link(target: str) -> bool:
    return bool(re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target))


def strip_anchor(target: str) -> str:
    return target.split("#", 1)[0]


def lint_links(errors: list[str]) -> None:
    for path in markdown_files():
        text = path.read_text(encoding="utf-8", errors="replace")
        for match in LINK_RE.finditer(text):
            target = strip_anchor(match.group(1).strip())
            if not target or is_external_link(target):
                continue
            resolved = (path.parent / target).resolve()
            if not resolved.exists():
                rel = path.relative_to(ROOT)
                errors.append(f"broken link: {rel} -> {target}")


def lint_metadata(errors: list[str]) -> None:
    for path in generated_wiki_pages():
        text = path.read_text(encoding="utf-8", errors="replace")
        rel = path.relative_to(ROOT)
        for key in REQUIRED_METADATA:
            if key not in text:
                errors.append(f"missing metadata {key} in {rel}")
        status_match = re.search(r"^status:\s*([a-zA-Z0-9_-]+)\s*$", text, flags=re.MULTILINE)
        if status_match and status_match.group(1) not in ALLOWED_STATUS:
            errors.append(f"invalid status {status_match.group(1)!r} in {rel}")


def lint_index(errors: list[str]) -> None:
    if not WIKI_INDEX.exists():
        errors.append("missing wiki/index.md")
        return
    index_text = WIKI_INDEX.read_text(encoding="utf-8", errors="replace")
    for path in generated_wiki_pages():
        rel = path.relative_to(WIKI_DIR).as_posix()
        if rel not in index_text:
            errors.append(f"page not listed in wiki/index.md: {rel}")


def lint_log(errors: list[str]) -> None:
    if not LOG_FILE.exists():
        errors.append("missing logs/log.md")
        return
    headings = [
        line
        for line in LOG_FILE.read_text(encoding="utf-8", errors="replace").splitlines()
        if line.startswith("## ")
    ]
    if not headings:
        errors.append("logs/log.md has no operation entries")
    for line in headings:
        if not LOG_HEADING_RE.match(line):
            errors.append(f"malformed log heading: {line}")


def lint_raw_integrity(errors: list[str]) -> None:
    if not RAW_DIR.exists():
        errors.append("missing raw/ directory")


def main() -> int:
    errors: list[str] = []
    lint_raw_integrity(errors)
    lint_links(errors)
    lint_metadata(errors)
    lint_index(errors)
    lint_log(errors)

    if errors:
        print("toolbox-wiki lint failed:")
        for item in errors:
            print(f"- {item}")
        return 1

    print("toolbox-wiki lint passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
