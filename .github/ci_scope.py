"""Skip expensive research steps only for an audited set of standalone docs.

Unknown changes or incomplete Git/event information always retain full coverage.
The original jobs and matrix check names remain present on documentation changes.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import time


DOCUMENTATION_ONLY = frozenset({
    ".github/README.md",
    ".github/CI.md",
    "CURRENT_REPRODUCTION.md",
    "graph_synthesis/DATASETS.md",
})
PR_FETCH_DEPTH = 64
FETCH_TIMEOUT_SECONDS = 45


def checked_sha(value: object) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", value):
        raise ValueError("Missing or invalid commit SHA")
    if set(value) == {"0"}:
        raise ValueError("No previous commit for a new or deleted branch")
    return value


def changed_files(event_name: str, event: dict, repository: Path) -> list[str]:
    if not isinstance(event, dict):
        raise ValueError("Event payload is not an object")
    if event_name == "pull_request":
        request = event["pull_request"]
        before = checked_sha(request["base"]["sha"])
        after = checked_sha(request["head"]["sha"])
        comparison = f"{before}...{after}"
    elif event_name == "push":
        if event.get("created") or event.get("deleted"):
            raise ValueError("New or deleted branch requires full coverage")
        before = checked_sha(event["before"])
        after = checked_sha(event["after"])
        comparison = f"{before}..{after}"
    else:
        raise ValueError(f"Full coverage for event {event_name!r}")
    command = ["git", "diff", "--no-ext-diff", "--no-textconv", "--name-only", "--no-renames", "-z", comparison, "--"]

    def diff():
        return subprocess.run(command, cwd=repository, check=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    try:
        result = diff()
    except subprocess.CalledProcessError:
        # Hosted checkout usually has depth 1. Fetch only comparison refs, not
        # all branches/history or blobs; PRs also need a common ancestor.
        depth = PR_FETCH_DEPTH if event_name == "pull_request" else 1
        started = time.monotonic()
        try:
            subprocess.run(
                ["git", "fetch", "--no-tags", "--filter=blob:none", f"--depth={depth}", "origin", before, after],
                cwd=repository, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                timeout=FETCH_TIMEOUT_SECONDS,
            )
        finally:
            print(json.dumps({"comparison_fetch_depth": depth,
                              "comparison_fetch_seconds": round(time.monotonic() - started, 3)}))
        # If 64 commits do not reach the common ancestor, retain full coverage.
        result = diff()
    # Rename detection is disabled so both the removed and added paths are seen.
    return sorted(set(os.fsdecode(path) for path in result.stdout.split(b"\0") if path))


def classify(event_name: str, event: dict, repository: Path) -> dict:
    try:
        paths = changed_files(event_name, event, repository)
        if paths and all(path in DOCUMENTATION_ONLY for path in paths):
            return {"run_research": False, "reason": "Only standalone documentation changed", "paths": paths}
        return {"run_research": True, "reason": "Research inputs changed or the diff is empty", "paths": paths}
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        return {"run_research": True, "reason": f"Full coverage: classification unavailable ({error})", "paths": None}


def main() -> None:
    try:
        event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text(encoding="utf-8"))
        result = classify(os.environ.get("GITHUB_EVENT_NAME", ""), event, Path.cwd())
    except (OSError, ValueError, KeyError, TypeError) as error:
        result = {"run_research": True, "reason": f"Full coverage: event unavailable ({error})", "paths": None}
    print(json.dumps(result, sort_keys=True))
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as stream:
            stream.write(f"run_research={str(result['run_research']).lower()}\n")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as stream:
            stream.write("Research step routing: " + json.dumps(result, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
