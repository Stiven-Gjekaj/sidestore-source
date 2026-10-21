"""Writes apps.json, the source that SideStore and AltStore read.

Each file in apps/ names one app and the GitHub repository of its releases.
Each release with the IPA asset becomes one version of the app, newest first.
The text of a version comes from the changelog of the app at the tag of the
release.

Run it from the root of the repository:

    python3 scripts/build.py

The GITHUB_TOKEN variable is used when it is set, so that the requests are not
limited to 60 in each hour.
"""

import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

API = "https://api.github.com"
RAW = "https://raw.githubusercontent.com"


def fetch(url, token=None):
    """Gets the body of a URL as text. A missing file gives None."""
    request = urllib.request.Request(url, headers={"User-Agent": "sidestore-source"})
    if token and url.startswith(API):
        request.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return None
        raise


def version_of(tag):
    """Gives the version of a tag, such as 1.2.0 for v1.2.0."""
    return tag[1:] if tag.startswith("v") else tag


def changelog_section(text, version):
    """Gives the lines under the heading of one version, such as "## 1.2.0 (2026-10-21)".

    The text stops at the next heading of the same level. Each list item becomes
    one line, and the lines of an item that wraps join with a space.
    """
    if not text:
        return ""
    heading = re.compile(r"^##\s+v?" + re.escape(version) + r"(\s|$)")
    lines = text.splitlines()
    start = next((i for i, line in enumerate(lines) if heading.match(line)), None)
    if start is None:
        return ""
    items = []
    for line in lines[start + 1:]:
        if line.startswith("## "):
            break
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("- "):
            items.append(stripped)
        elif items:
            items[-1] += " " + stripped
        else:
            items.append(stripped)
    return "\n".join(items)


def versions(config, releases, changelog_at):
    """Makes the versions of one app from its releases, newest first.

    `changelog_at` gives the changelog text at a tag, or None.
    """
    found = []
    for release in releases:
        if release.get("draft") or release.get("prerelease"):
            continue
        asset = next((a for a in release.get("assets", []) if a.get("name") == config["asset"]), None)
        if asset is None:
            continue
        tag = release["tag_name"]
        version = version_of(tag)
        text = changelog_section(changelog_at(tag), version) or (release.get("body") or "").strip()
        found.append({
            "version": version,
            "buildVersion": version,
            "date": release["published_at"],
            "localizedDescription": text,
            "downloadURL": asset["browser_download_url"],
            "size": asset["size"],
            "minOSVersion": config["app"].get("minOSVersion", "16.0"),
        })
    found.sort(key=lambda v: [int(p) if p.isdigit() else 0 for p in re.split(r"[.\-]", v["version"])], reverse=True)
    return found


def app_entry(config, releases, changelog_at):
    """Makes the entry of one app. An app with no release is left out."""
    found = versions(config, releases, changelog_at)
    if not found:
        return None
    entry = dict(config["app"])
    entry.pop("minOSVersion", None)
    entry["versions"] = found
    return entry


def build(root, get):
    """Makes the full source. `get` reads a URL, as `fetch` does."""
    source = json.loads((root / "source.json").read_text())
    apps = []
    for path in sorted((root / "apps").glob("*.json")):
        config = json.loads(path.read_text())
        repository = config["repository"]
        releases = json.loads(get(f"{API}/repos/{repository}/releases?per_page=100") or "[]")
        changelog = config.get("changelog")

        def changelog_at(tag, repository=repository, changelog=changelog):
            return get(f"{RAW}/{repository}/{tag}/{changelog}") if changelog else None

        entry = app_entry(config, releases, changelog_at)
        if entry:
            apps.append(entry)
    source["apps"] = apps
    source["news"] = []
    return source


def main():
    root = Path(__file__).resolve().parent.parent
    token = os.environ.get("GITHUB_TOKEN")
    source = build(root, lambda url: fetch(url, token))
    text = json.dumps(source, indent=2, ensure_ascii=False) + "\n"
    target = root / "apps.json"
    if target.exists() and target.read_text() == text:
        print("apps.json has no change")
        return 0
    target.write_text(text)
    print(f"apps.json has {len(source['apps'])} apps")
    return 0


if __name__ == "__main__":
    sys.exit(main())
