#!/usr/bin/env python3
import json
import subprocess
from pathlib import Path
from urllib.request import Request, urlopen

OWNER = "obinexusmk2"
ROOT = Path("obix")

FOLDERS = {
    "runtime": ["component-runtime", "holo-core", "runtime", "core"],
    "components": ["component-", "sdk-components"],
    "overlays": ["component-overlays"],
    "navigation": ["component-navigation", "sdk-router"],
    "forms": ["component-forms", "sdk-forms"],
    "feedback": ["component-feedback"],
    "data": ["component-data"],
    "controls": ["component-controls", "component-cursor"],
    "drivers": ["driver-"],
    "configs": ["config-"],
    "bindings": ["binding-"],
    "docs": ["docs"],
    "demos": ["demo", "todoapp"],
    "cli": ["cli", "sdk-cli"],
}


def run(cmd, cwd=None):
    print(">", " ".join(cmd))
    subprocess.run(cmd, cwd=cwd, check=True)


def fetch_repos():
    repos = []
    page = 1

    while True:
        url = (
            "https://api.github.com/search/repositories"
            f"?q=user:{OWNER}+obix&per_page=100&page={page}"
        )

        req = Request(url, headers={"User-Agent": "OBIX Workspace Downloader"})

        with urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))

        items = data.get("items", [])

        if not items:
            break

        repos.extend(items)
        page += 1

    return [
        repo for repo in repos
        if repo["name"] == "obix" or repo["name"].startswith("obix-")
    ]


def classify_repo(name):
    lowered = name.lower()

    priority = [
        "drivers",
        "configs",
        "bindings",
        "overlays",
        "navigation",
        "forms",
        "feedback",
        "data",
        "controls",
        "docs",
        "demos",
        "cli",
        "components",
        "runtime",
    ]

    for folder in priority:
        for pattern in FOLDERS[folder]:
            if pattern in lowered:
                return folder

    return "runtime"


def main():
    ROOT.mkdir(exist_ok=True)

    for folder in FOLDERS:
        (ROOT / folder).mkdir(parents=True, exist_ok=True)

    repos = fetch_repos()

    print(f"Found {len(repos)} OBIX repos")

    for repo in repos:
        name = repo["name"]
        clone_url = repo["clone_url"]
        folder = classify_repo(name)
        target = ROOT / folder / name

        if target.exists():
            print(f"\nUpdating {name}")
            run(["git", "pull"], cwd=target)
        else:
            print(f"\nCloning {name} into obix/{folder}/")
            run(["git", "clone", clone_url, str(target)])

    print("\nDone.")
    print(f"Workspace: {ROOT.resolve()}")


if __name__ == "__main__":
    main()