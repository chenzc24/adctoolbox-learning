"""Search toolbox-wiki with dependency-free keyword matching.

Examples:

    python tools/search_wiki.py calibration
    python tools/search_wiki.py "rank deficiency" --raw
    python tools/search_wiki.py sndr --context 2 --limit 20

By default this searches the synthesized wiki and maintenance files first,
leaving raw sources out to keep results focused.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SEARCH_ROOTS = (
    ROOT / "index.md",
    ROOT / "progress.md",
    ROOT / "coverage_matrix.md",
    ROOT / "open_questions.md",
    ROOT / "wiki",
    ROOT / "schema",
    ROOT / "audits",
)
RAW_ROOT = ROOT / "raw"


@dataclass
class Match:
    path: Path
    line_no: int
    score: int
    line: str


def iter_markdown_files(include_raw: bool) -> list[Path]:
    paths: list[Path] = []
    for root in DEFAULT_SEARCH_ROOTS:
        if root.is_file():
            paths.append(root)
        elif root.exists():
            paths.extend(root.rglob("*.md"))
    if include_raw and RAW_ROOT.exists():
        paths.extend(RAW_ROOT.rglob("*.md"))
        paths.extend(RAW_ROOT.rglob("*.txt"))
    return sorted(set(paths))


def score_line(line_lower: str, terms: list[str]) -> int:
    return sum(line_lower.count(term) for term in terms)


def search(query: str, include_raw: bool) -> list[Match]:
    terms = [term.lower() for term in query.split() if term.strip()]
    if not terms:
        return []

    matches: list[Match] = []
    for path in iter_markdown_files(include_raw):
        text = path.read_text(encoding="utf-8", errors="replace").splitlines()
        for idx, line in enumerate(text, start=1):
            line_lower = line.lower()
            score = score_line(line_lower, terms)
            if score:
                matches.append(Match(path=path, line_no=idx, score=score, line=line.strip()))
    matches.sort(key=lambda item: (-item.score, str(item.path), item.line_no))
    return matches


def print_context(path: Path, line_no: int, context: int) -> None:
    if context <= 0:
        return
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    start = max(1, line_no - context)
    end = min(len(lines), line_no + context)
    for idx in range(start, end + 1):
        prefix = ">" if idx == line_no else " "
        print(f"  {prefix} {idx}: {lines[idx - 1]}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Search toolbox-wiki markdown files.")
    parser.add_argument("query", help="Keyword query. Quote multi-word queries.")
    parser.add_argument("--raw", action="store_true", help="Include raw Markdown/text sources.")
    parser.add_argument("--limit", type=int, default=30, help="Maximum matches to print.")
    parser.add_argument("--context", type=int, default=0, help="Context lines around each match.")
    args = parser.parse_args()

    matches = search(args.query, include_raw=args.raw)
    if not matches:
        print("No matches")
        return 1

    for item in matches[: args.limit]:
        rel = item.path.relative_to(ROOT)
        print(f"{rel}:{item.line_no}: score={item.score}: {item.line}")
        print_context(item.path, item.line_no, args.context)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
