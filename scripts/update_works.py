import json
import os
import sys
import urllib.error
import urllib.request


OWNER = os.environ.get("GITHUB_OWNER", "dgtwzd1")
README_PATH = os.environ.get("README_PATH", "README.md")
START_MARKER = "<!-- works:start -->"
END_MARKER = "<!-- works:end -->"


def github_get(path):
    token = os.environ.get("GITHUB_TOKEN", "")
    request = urllib.request.Request(
        f"https://api.github.com{path}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "dgtwzd1-profile-works-updater",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    if token:
        request.add_header("Authorization", f"Bearer {token}")

    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def github_get_optional(path):
    try:
        return github_get(path)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise


def escape_cell(value):
    text = str(value or "").replace("\n", " ").strip()
    return text.replace("|", "\\|")


def repo_status(repo):
    if repo.get("archived"):
        return "`parked`"

    latest_release = github_get_optional(f"/repos/{OWNER}/{repo['name']}/releases/latest")
    if latest_release and latest_release.get("tag_name"):
        return f"`{escape_cell(latest_release['tag_name'])} — live`"

    return "`in progress`"


def build_table():
    repos = github_get(f"/users/{OWNER}/repos?per_page=100&type=owner&sort=updated")
    visible_repos = [
        repo for repo in repos
        if not repo.get("fork") and repo.get("name") != OWNER
    ]

    rows = [
        START_MARKER,
        "<!-- generated; do not edit by hand -->",
        "| Project | What it does | Status |",
        "|---|---|---|",
    ]

    if not visible_repos:
        rows.append("| _No public project repos yet._ |  |  |")
    else:
        for repo in visible_repos:
            name = escape_cell(repo["name"])
            url = repo["html_url"]
            description = escape_cell(repo.get("description") or "No description yet.")
            rows.append(f"| [{name}]({url}) | {description} | {repo_status(repo)} |")

    rows.append(END_MARKER)
    return "\n".join(rows)


def update_readme():
    with open(README_PATH, "r", encoding="utf-8") as handle:
        readme = handle.read()

    start = readme.find(START_MARKER)
    end = readme.find(END_MARKER)
    if start == -1 or end == -1 or end < start:
        raise RuntimeError("README markers are missing or out of order.")

    end += len(END_MARKER)
    updated = readme[:start] + build_table() + readme[end:]

    with open(README_PATH, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(updated)


if __name__ == "__main__":
    try:
        update_readme()
    except Exception as exc:
        print(f"Failed to update works list: {exc}", file=sys.stderr)
        raise
