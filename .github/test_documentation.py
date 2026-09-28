import json
from pathlib import Path
import tempfile
import unittest

from check_documentation import DOCUMENTS, check_documentation


class DocumentationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.repository = Path(self.temporary.name)
        (self.repository / ".github").mkdir()
        self.document = self.repository / ".github/README.md"

    def check(self, text):
        self.document.write_text(text, encoding="utf-8")
        return check_documentation(self.repository, (".github/README.md",))

    def test_existing_relative_root_and_directory_destinations(self):
        (self.repository / "file with spaces.md").write_text("text")
        self.assertEqual(self.check("[relative](../file%20with%20spaces.md#section) "
                                    "[root](/file%20with%20spaces.md) [directory](../.github/)"), [])

    def test_broken_link_is_reported(self):
        errors = self.check("[missing](../missing.md)")
        self.assertEqual(len(errors), 1)
        self.assertIn("../missing.md", errors[0])

    def test_external_urls_and_fragments_are_not_fetched(self):
        self.assertEqual(self.check("[web](https://example.invalid/missing) [anchor](#section) "
                                    "[mail](mailto:contact@example.invalid)"), [])

    def test_code_examples_do_not_create_false_broken_links(self):
        self.assertEqual(self.check("```md\n[example](nonexistent.md)\n```"), [])

    def test_missing_document_is_reported(self):
        self.assertIn("Missing documentation file", check_documentation(self.repository, ("missing.md",))[0])

    def test_outside_repository_destination_is_rejected(self):
        self.assertIn("outside repository", self.check("[outside](../../outside.md)")[0])

    def test_standalone_docs_do_not_exclude_frozen_archive(self):
        repository = Path(__file__).resolve().parents[1]
        manifest = json.loads((repository / "MANIFEST.json").read_text(encoding="utf-8"))
        self.assertFalse(set(DOCUMENTS) & {row["path"] for row in manifest["files"]})


if __name__ == "__main__":
    unittest.main()
