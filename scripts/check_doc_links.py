"""Validate local Markdown links in the tracked documentation.

The active backlog intentionally contains only unfinished tasks.  Completed
task files are removed, so a relative Markdown link to one is always stale.
This small dependency-free check keeps the roadmap and durable guides honest.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse


MARKDOWN_LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)(?:\s+[^)]*)?\)")
IGNORED_SCHEMES = {"http", "https", "mailto", "tel"}


def find_broken_links(docs_root: Path) -> list[str]:
    """Return local Markdown links whose target is absent from the repository."""
    errors: list[str] = []
    for source in sorted(docs_root.rglob("*.md")):
        text = source.read_text(encoding="utf-8")
        for target in MARKDOWN_LINK.findall(text):
            parsed = urlparse(target)
            if parsed.scheme.lower() in IGNORED_SCHEMES or target.startswith("#"):
                continue
            target_path = unquote(parsed.path)
            if not target_path:
                continue
            resolved = (source.parent / target_path).resolve()
            if not resolved.exists():
                errors.append(f"{source.relative_to(docs_root.parent)} -> {target}")
    return errors


def main() -> int:
    repository_root = Path(__file__).resolve().parents[1]
    errors = find_broken_links(repository_root / "docs")
    if errors:
        print("Broken local Markdown links:")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    print("Documentation links: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
