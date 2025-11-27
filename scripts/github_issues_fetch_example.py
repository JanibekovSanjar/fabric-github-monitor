"""
Example script: fetch issues and pull requests from a GitHub repository.

In Fabric, this logic would live inside a notebook. Here it is written as a
standalone Python script for reference and local testing.

Monitored repo: microsoft/fabric-samples
"""

import os
import requests
import pandas as pd

GITHUB_API_BASE = "https://api.github.com"
# Set this as an environment variable, not hardcoded in real use
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

OWNER = "microsoft"
REPO = "fabric-samples"


def github_headers(token: str | None) -> dict:
    headers = {
        "Accept": "application/vnd.github+json"
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def fetch_all_issues(owner: str, repo: str, token: str | None = None) -> list[dict]:
    issues: list[dict] = []
    page = 1

    while True:
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues"
        params = {
            "state": "all",
            "per_page": 100,
            "page": page,
        }
        response = requests.get(url, headers=github_headers(token), params=params)
        response.raise_for_status()
        batch = response.json()

        if not batch:
            break

        issues.extend(batch)
        page += 1

    return issues


def normalize_issues(raw_issues: list[dict], owner: str, repo: str) -> pd.DataFrame:
    rows = []

    for item in raw_issues:
        is_pr = "pull_request" in item

        labels = [lbl.get("name") for lbl in item.get("labels", [])]

        row = {
            "repo": f"{owner}/{repo}",
            "external_id": item.get("id"),
            "number": item.get("number"),
            "type": "pr" if is_pr else "issue",
            "state": item.get("state"),
            "title": item.get("title"),
            "author": (item.get("user") or {}).get("login"),
            "assignee": (item.get("assignee") or {}).get("login")
            if item.get("assignee")
            else None,
            "created_at": item.get("created_at"),
            "closed_at": item.get("closed_at"),
            # merged_at is not included in the issues endpoint response by default.
            # In Fabric you can optionally call the pulls API for more details.
            "merged_at": None,
            "labels": ",".join(labels),
        }

        rows.append(row)

    df = pd.DataFrame(rows)
    return df


def main():
    if not GITHUB_TOKEN:
        print("Warning: GITHUB_TOKEN is not set. You will be rate-limited by GitHub.")

    raw = fetch_all_issues(OWNER, REPO, GITHUB_TOKEN)
    df = normalize_issues(raw, OWNER, REPO)

    print(f"Fetched {len(df)} rows from {OWNER}/{REPO}")
    print(df.head())

    # In Fabric, instead of writing CSV, you would write df into a Lakehouse table.
    # For local testing, this can be useful:
    df.to_csv("fabric_samples_issues_preview.csv", index=False)


if __name__ == "__main__":
    main()
