# GitHub Activity Monitor with Microsoft Fabric & Power BI

This repository contains documentation and example code for a small analytics solution that monitors activity in a GitHub repository using **Microsoft Fabric**, **Power BI**, and **Telegram alerts**.

The main monitored repository is:

- `microsoft/fabric-samples`

Data is ingested from the GitHub REST API into a **Fabric Lakehouse** using notebooks and pipelines. A **Power BI report** on top of the Lakehouse shows issue and pull request metrics such as:

- Open issues and pull requests
- Issues and PRs created/closed over time
- Average issue cycle time (created → closed)
- Average PR merge time
- Activity per assignee

Fabric pipelines also trigger **Telegram alerts** when certain conditions are met:

1. **Too many open issues**  
2. **Too many open / old pull requests**  
3. **No activity for X days**  

> Note: The actual Fabric notebooks and pipelines live in a Fabric workspace. This repository tracks the design, example Python snippets, and Power BI configuration.

---

## Architecture overview

High-level flow:

1. **GitHub API (source)**  
   - Repository: `microsoft/fabric-samples`  
   - Endpoint: `/repos/{owner}/{repo}/issues?state=all`  
   - Issues and pull requests are fetched on a schedule.

2. **Microsoft Fabric (data & orchestration)**  
   - **Notebook** calls GitHub API, normalizes JSON, and writes to a Lakehouse table `Tasks`.  
   - **Pipeline** schedules the notebook (e.g., every 6 or 12 hours).  
   - A second notebook or pipeline activity evaluates metrics and triggers Telegram alerts.

3. **Power BI (analytics)**  
   - Connects to the Lakehouse / Warehouse.  
   - Uses `Tasks` as the main fact table.  
   - Provides a dashboard with KPIs and charts for GitHub activity.

4. **Telegram (alerts)**  
   - A Fabric pipeline step (notebook or Web Activity) calls the Telegram Bot API.  
   - Sends alerts such as:  
     - "Too many open issues"  
     - "Too many open or old PRs"  
     - "No activity in the last X days"

More detailed diagrams and descriptions are in `docs/architecture.md`.

---

## Components

- `config/monitored_repos.example.json`  
  Example configuration for monitored repositories and alert thresholds.

- `scripts/github_issues_fetch_example.py`  
  Standalone Python example of how the Fabric notebook calls the GitHub API and handles pagination.

- `scripts/telegram_alert_example.py`  
  Standalone Python example of how alert logic can be implemented using the same conditions as the Fabric notebook and sent to Telegram.

- `docs/architecture.md`  
  Architecture description, data model, and metric definitions.

- `powerbi/dashboard_layout.md`  
  Description of the Power BI report layout and key measures.

---

## Data model (Lakehouse)

The Fabric Lakehouse uses a simplified `Tasks` table with one row per GitHub issue or pull request:

- `repo` – repository name (e.g., `microsoft/fabric-samples`)
- `external_id` – GitHub numeric ID
- `number` – issue/PR number
- `type` – `"issue"` or `"pr"`
- `state` – `"open"` or `"closed"`
- `title`
- `author`
- `assignee`
- `created_at`
- `closed_at`
- `merged_at` (for PRs)
- `labels` (flattened, if needed)
- `raw_json` (optional, for debugging)

From this table, Power BI computes:

- Open issues / open PRs
- Issues/PRs created and closed per day
- Average cycle time (days)
- Average PR merge time (hours)
- Activity per assignee and per repo

---

## Prerequisites

To reproduce the full solution you need:

- A Microsoft Fabric workspace with:
  - Lakehouse or Warehouse
  - Ability to create notebooks and pipelines
- Power BI (for building the dashboard)
- A GitHub Personal Access Token with read access to public repositories
- A Telegram bot and chat ID (for alerts)

Secrets such as tokens and chat IDs should be stored in Fabric credentials or environment variables, not committed to this repository.

---

## Typical implementation steps

1. **GitHub ingestion**
   - Implement a Fabric notebook based on `scripts/github_issues_fetch_example.py`.
   - Write the normalized data into a Lakehouse table `Tasks`.

2. **Scheduling**
   - Create a Fabric pipeline that executes the ingestion notebook on a schedule.

3. **Power BI report**
   - Connect Power BI to the Lakehouse.
   - Implement the dashboard described in `powerbi/dashboard_layout.md`.

4. **Alerts**
   - Implement alert logic similar to `scripts/telegram_alert_example.py` inside a Fabric notebook (or SQL + Web Activity).
   - Trigger Telegram messages when:
     - Open issues exceed a threshold
     - Open PRs / old PRs exceed thresholds
     - No activity has occurred in the last X days

This repository is the documentation and reference code for the solution, not the runtime environment itself.

This isn't enough
