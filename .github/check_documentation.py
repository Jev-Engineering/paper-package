"""Check repository-local links in standalone public documentation, offline."""
from __future__ import annotations

import argparse
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit


DOCUMENTS = (".github/README.md", ".github/CI.md", "CURRENT_REPRODUCTION.md", "graph_synthesis/DATASETS.md")


def check_documentation(repository: Path, documents=DOCUMENTS) -> list[str]:
    repository = repository.resolve()
    errors = []
    for name in documents:
        source = repository / name
        if not source.is_file():
            errors.append(f"Missing documentation file: {name}")
            continue
        text = source.read_text(encoding="utf-8")
        text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
        for match in re.finditer(r"!?\[[^\]]*\]\((<[^>]+>|[^\s)]+)(?:\s+\"[^\"]*\")?\)", text):
            link = urlsplit(match.group(1).strip("<>"))
            if link.scheme or link.netloc or not link.path:
                continue
            target = (source.parent / unquote(link.path)).resolve()
            if link.path.startswith("/"):
                target = (repository / unquote(link.path).lstrip("/")).resolve()
            if not target.is_relative_to(repository) or not target.exists():
                errors.append(f"{name}: missing or outside repository: {match.group(1)}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    errors = check_documentation(args.repository)
    if errors:
        print("\n".join(errors))
        return 1
    print(f"Verified local link destinations in {len(DOCUMENTS)} standalone documentation files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
