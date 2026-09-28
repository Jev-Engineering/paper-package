"""Real Git fixtures exercise PR/push scope, renames and conservative fallback."""
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import ci_scope


class ScopeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.repository = Path(self.temporary.name)
        self.git("init", "-q")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("config", "user.name", "Routing fixture")
        self.git("config", "commit.gpgsign", "false")
        self.write(".github/README.md", "original documentation")
        self.write("graph_synthesis/core.py", "original code")
        self.base = self.commit()

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.repository, check=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.decode().strip()

    def write(self, name, content="changed"):
        path = self.repository / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def commit(self):
        self.git("add", "-A")
        self.git("commit", "-qm", "fixture")
        return self.git("rev-parse", "HEAD")

    def decision(self, base=None, head=None, event="pull_request"):
        before, after = base or self.base, head or self.git("rev-parse", "HEAD")
        payload = {"pull_request": {"base": {"sha": before}, "head": {"sha": after}}}
        if event == "push":
            payload = {"before": before, "after": after}
        return ci_scope.classify(event, payload, self.repository)

    def test_documentation_only_pr_and_push_skip_research_steps(self):
        self.write(".github/README.md")
        self.commit()
        for event in ("pull_request", "push"):
            with self.subTest(event=event):
                self.assertFalse(self.decision(event=event)["run_research"])

    def test_mixed_documentation_and_code_runs_research(self):
        self.write(".github/README.md")
        self.write("graph_synthesis/core.py")
        self.commit()
        self.assertTrue(self.decision()["run_research"])

    def test_pr_uses_merge_base_and_excludes_changes_only_on_target_branch(self):
        self.write(".github/README.md")
        head = self.commit()
        self.git("checkout", "-q", "--detach", self.base)
        self.write("graph_synthesis/core.py", "target branch change")
        advanced_base = self.commit()
        self.assertFalse(self.decision(base=advanced_base, head=head)["run_research"])
        self.assertTrue(self.decision(base=advanced_base, head=head, event="push")["run_research"])

    def test_rename_from_code_into_allowlisted_document_still_runs_research(self):
        self.git("mv", "graph_synthesis/core.py", "CURRENT_REPRODUCTION.md")
        self.commit()
        result = self.decision()
        self.assertTrue(result["run_research"])
        self.assertIn("graph_synthesis/core.py", result["paths"])
        self.assertIn("CURRENT_REPRODUCTION.md", result["paths"])

    def test_deleting_code_runs_research(self):
        self.git("rm", "graph_synthesis/core.py")
        self.commit()
        self.assertTrue(self.decision()["run_research"])

    def test_deleting_only_standalone_documentation_skips_research(self):
        self.git("rm", ".github/README.md")
        self.commit()
        self.assertFalse(self.decision()["run_research"])

    def test_source_evidence_requirements_and_workflows_are_not_plain_docs(self):
        for name in ("README.md", "REPRODUCE.md", "MANIFEST.json", "CURRENT_RESULTS.md",
                     "manuscript/paper-current.md", "reproduction/results/jev/run-20260918/calls.jsonl",
                     "scripts/datasets.json", "graph_synthesis/datasets.py", "graph_synthesis/requirements-verification.txt",
                     "graph_synthesis/render_current_paper.py", "graph_synthesis/adaptive/PROTOCOL.md",
                     ".github/workflows/graph-synthesis.yml", ".github/actions/research-scope/action.yml",
                     ".github/ci_scope.py", "new-unknown-path.md"):
            with self.subTest(path=name), patch.object(ci_scope, "changed_files", return_value=[name]):
                self.assertTrue(ci_scope.classify("pull_request", {}, self.repository)["run_research"])

    def test_allowlist_contains_no_original_archive_files(self):
        repository = Path(__file__).resolve().parents[1]
        manifest = json.loads((repository / "MANIFEST.json").read_text(encoding="utf-8"))
        archived = {row["path"] for row in manifest["files"]}
        self.assertFalse(ci_scope.DOCUMENTATION_ONLY & archived)

    def test_new_branch_missing_commit_manual_event_and_empty_diff_run_research(self):
        events = [
            ("push", {"before": "0" * 40, "after": self.base}),
            ("push", {"created": True, "before": self.base, "after": self.base}),
            ("push", {"deleted": True, "before": self.base, "after": self.base}),
            ("push", {"before": "a" * 40, "after": self.base}),
            ("push", {"before": "--output=unsafe", "after": self.base}),
            ("workflow_dispatch", {}),
            ("pull_request", {}),
        ]
        for name, event in events:
            with self.subTest(event=event):
                self.assertTrue(ci_scope.classify(name, event, self.repository)["run_research"])
        self.assertTrue(self.decision()["run_research"])

    def test_classifier_failure_retains_full_coverage(self):
        with patch.object(ci_scope, "changed_files", side_effect=OSError("git unavailable")):
            result = ci_scope.classify("pull_request", {}, self.repository)
        self.assertTrue(result["run_research"])
        self.assertIn("git unavailable", result["reason"])

    def shallow_clone(self):
        destination = self.repository / "clone"
        subprocess.run(["git", "clone", "-q", "--depth=1", self.repository.as_uri(), str(destination)],
                       check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return destination

    def test_shallow_pr_checkout_fetches_comparison_history_and_skips_docs(self):
        self.write(".github/README.md")
        head = self.commit()
        clone = self.shallow_clone()
        payload = {"pull_request": {"base": {"sha": self.base}, "head": {"sha": head}}}
        self.assertFalse(ci_scope.classify("pull_request", payload, clone)["run_research"])

    def test_shallow_merge_checkout_fetches_divergent_base_and_head_by_sha(self):
        self.git("checkout", "-qb", "feature")
        self.write(".github/README.md")
        head = self.commit()
        self.git("checkout", "-qb", "integration", self.base)
        self.write("graph_synthesis/core.py", "target branch change")
        advanced_base = self.commit()
        self.git("merge", "-q", "--no-ff", "-m", "PR merge fixture", "feature")
        clone = self.shallow_clone()
        payload = {"pull_request": {"base": {"sha": advanced_base}, "head": {"sha": head}}}
        with patch.object(ci_scope.subprocess, "run", wraps=subprocess.run) as run:
            self.assertFalse(ci_scope.classify("pull_request", payload, clone)["run_research"])
        fetches = [call.args[0] for call in run.call_args_list if call.args[0][:2] == ["git", "fetch"]]
        self.assertEqual(len(fetches), 1)
        self.assertEqual(fetches[0][-2:], [advanced_base, head])

    def test_shallow_push_checkout_fetches_previous_tree_and_skips_docs(self):
        self.write(".github/README.md")
        head = self.commit()
        clone = self.shallow_clone()
        self.assertFalse(ci_scope.classify("push", {"before": self.base, "after": head}, clone)["run_research"])

    def test_shallow_history_beyond_bound_runs_research(self):
        # Use a small test bound to exercise the same boundary without 64 commits.
        for index in range(4):
            self.write(".github/README.md", str(index))
            head = self.commit()
        clone = self.shallow_clone()
        payload = {"pull_request": {"base": {"sha": self.base}, "head": {"sha": head}}}
        with patch.object(ci_scope, "PR_FETCH_DEPTH", 2):
            self.assertTrue(ci_scope.classify("pull_request", payload, clone)["run_research"])

    def test_failed_shallow_fetch_runs_research(self):
        self.write(".github/README.md")
        head = self.commit()
        clone = self.shallow_clone()
        subprocess.run(["git", "remote", "remove", "origin"], cwd=clone, check=True)
        self.assertTrue(ci_scope.classify("push", {"before": self.base, "after": head}, clone)["run_research"])

    def test_comparison_fetch_timeout_runs_research(self):
        failures = [subprocess.CalledProcessError(128, ["git", "diff"]),
                    subprocess.TimeoutExpired(["git", "fetch"], ci_scope.FETCH_TIMEOUT_SECONDS)]
        with patch.object(ci_scope.subprocess, "run", side_effect=failures):
            self.assertTrue(self.decision(head=self.base)["run_research"])

    def test_missing_event_file_outputs_full_coverage(self):
        output = self.repository / "output.txt"
        with patch.dict(os.environ, {"GITHUB_EVENT_PATH": str(self.repository / "missing.json"),
                                    "GITHUB_OUTPUT": str(output), "GITHUB_STEP_SUMMARY": ""}):
            with contextlib.redirect_stdout(io.StringIO()):
                ci_scope.main()
        self.assertEqual(output.read_text(), "run_research=true\n")


if __name__ == "__main__":
    unittest.main()
