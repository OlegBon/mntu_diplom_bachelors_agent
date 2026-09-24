from pathlib import Path

from scripts.check_doc_links import find_broken_links


def test_documentation_has_no_broken_local_markdown_links():
    repository_root = Path(__file__).resolve().parents[2]

    assert find_broken_links(repository_root / "docs") == []
