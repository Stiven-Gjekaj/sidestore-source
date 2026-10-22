"""Tests of build.py. Run them with: python3 -m unittest discover scripts"""

import json
import tempfile
import unittest
from pathlib import Path

import build

CONFIG = {
    "repository": "owner/app",
    "asset": "App.ipa",
    "changelog": "CHANGELOG.md",
    "app": {"name": "App", "bundleIdentifier": "test.app", "minOSVersion": "16.0"},
}

CHANGELOG = """# Changelog

## 1.1.0 (2026-10-22)

- Adds a filter.
- Fixes a long
  line.

## 1.0.0 (2026-10-21)

- The first version.
"""


def release(tag, assets=("App.ipa",), **extra):
    return {
        "tag_name": tag,
        "published_at": "2026-10-21T10:00:00Z",
        "body": "Notes",
        "assets": [{"name": n, "size": 1000, "browser_download_url": f"https://x.test/{tag}/{n}"} for n in assets],
        **extra,
    }


class ChangelogSectionTests(unittest.TestCase):
    def test_gives_the_items_of_one_version_and_joins_a_wrapped_line(self):
        self.assertEqual(build.changelog_section(CHANGELOG, "1.1.0"), "- Adds a filter.\n- Fixes a long line.")

    def test_stops_at_the_next_heading(self):
        self.assertEqual(build.changelog_section(CHANGELOG, "1.0.0"), "- The first version.")

    def test_a_version_with_no_heading_gives_no_text(self):
        self.assertEqual(build.changelog_section(CHANGELOG, "2.0.0"), "")
        self.assertEqual(build.changelog_section(None, "1.0.0"), "")

    def test_one_version_does_not_match_a_longer_one(self):
        self.assertEqual(build.changelog_section("## 1.0.10\n\n- Ten\n\n## 1.0.1\n\n- One\n", "1.0.1"), "- One")


class VersionsTests(unittest.TestCase):
    def test_each_release_with_the_asset_becomes_a_version_newest_first(self):
        releases = [release("v1.0.0"), release("v1.10.0"), release("v1.2.0")]
        found = build.versions(CONFIG, releases, lambda tag: CHANGELOG)
        self.assertEqual([v["version"] for v in found], ["1.10.0", "1.2.0", "1.0.0"])
        self.assertEqual(found[2]["downloadURL"], "https://x.test/v1.0.0/App.ipa")
        self.assertEqual(found[2]["size"], 1000)
        self.assertEqual(found[2]["localizedDescription"], "- The first version.")

    def test_drafts_prereleases_and_releases_with_no_asset_are_left_out(self):
        releases = [release("v1.0.0", draft=True), release("v1.1.0", prerelease=True), release("v1.2.0", assets=("Other.ipa",))]
        self.assertEqual(build.versions(CONFIG, releases, lambda tag: None), [])

    def test_the_release_notes_take_the_place_of_a_missing_changelog_entry(self):
        found = build.versions(CONFIG, [release("v3.0.0")], lambda tag: CHANGELOG)
        self.assertEqual(found[0]["localizedDescription"], "Notes")


class BuildTests(unittest.TestCase):
    def test_build_writes_each_app_that_has_a_release(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "apps").mkdir()
            (root / "source.json").write_text(json.dumps({"name": "Source"}))
            (root / "apps" / "app.json").write_text(json.dumps(CONFIG))
            other = dict(CONFIG, repository="owner/none")
            (root / "apps" / "none.json").write_text(json.dumps(other))
            answers = {
                "https://api.github.com/repos/owner/app/releases?per_page=100": json.dumps([release("v1.0.0")]),
                # A repository with no release yet gives an empty list.
                "https://api.github.com/repos/owner/none/releases?per_page=100": "[]",
                "https://raw.githubusercontent.com/owner/app/v1.0.0/CHANGELOG.md": CHANGELOG,
            }
            source = build.build(root, answers.get)
        self.assertEqual(source["name"], "Source")
        self.assertEqual([a["name"] for a in source["apps"]], ["App"])
        self.assertNotIn("minOSVersion", source["apps"][0])
        self.assertEqual(source["apps"][0]["versions"][0]["minOSVersion"], "16.0")
        self.assertEqual(source["news"], [])

    def test_no_answer_or_an_error_answer_stops_the_build(self):
        for answer in (None, '{"message": "Not Found"}'):
            with tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                (root / "apps").mkdir()
                (root / "source.json").write_text(json.dumps({"name": "Source"}))
                (root / "apps" / "app.json").write_text(json.dumps(CONFIG))
                with self.assertRaises(SystemExit):
                    build.build(root, lambda url, answer=answer: answer)


if __name__ == "__main__":
    unittest.main()
