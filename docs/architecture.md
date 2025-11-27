# Architecture

## Overview

This project monitors activity in a GitHub repository (`microsoft/fabric-samples`) using Microsoft Fabric, Power BI, and Telegram alerts.

The solution has four main parts:

1. **Data ingestion from GitHub**
2. **Storage and transformation in Microsoft Fabric (Lakehouse)**
3. **Analytics in Power BI**
4. **Alerting via Telegram**

## Data flow

1. **GitHub → Fabric notebook**

   - A Fabric notebook uses Python to call the GitHub REST API:
     - `GET /repos/{owner}/{repo}/issues?state=all`
   - Handles pagination using the `page` and `per_page` parameters.
   - Distinguishes issues and pull requests using the `pull_request` field in the JSON payload.
   - Normalizes the JSON into tabular rows and writes to a Lakehouse table `Tasks`.

2. **Fabric notebook → Lakehouse table**

   The notebook writes to a Delta table with approximate schema:

   - `repo` (string)
   - `external_id` (bigint)
   - `number` (int)
   - `type` (string: `issue` / `pr`)
   - `state` (string: `open` / `closed`)
   - `title` (string)
   - `author` (string)
   - `assignee` (string)
   - `created_at` (timestamp)
   - `closed_at` (timestamp)
   - `merged_at` (timestamp, PRs only)
   - `labels` (string or array)
   - `raw_json` (string or variant)

3. **Fabric pipeline (scheduling)**

   - A Fabric pipeline has an activity that runs the ingestion notebook.
   - The pipeline is scheduled (for example, every 6 or 12 hours).
   - On each run, the notebook:
     - Pulls the latest issues and pull requests.
     - Performs upserts or overwrites the `Tasks` table (depending on design).

4. **Power BI**

   - Power BI connects to the Lakehouse or its SQL endpoint.
   - The `Tasks` table is used as the main fact table.
   - Measures are created for:
     - Open issues / open PRs
     - Issues/PRs created per day
     - Issues/PRs closed per day
     - Average cycle time (created → closed)
     - Average PR merge time (created → merged)
   - Visuals:
     - KPI cards for key metrics
     - Line chart for created vs closed over time
     - Bar chart of open work by assignee
     - Table of recent issues and pull requests

5. **Alerts**

   A secondary notebook or pipeline step evaluates metrics for the monitored repository and triggers alerts via Telegram when conditions are met. The main alert types are:

   1. **Too many open issues**
      - Condition: `open_issues > issue_threshold`
   2. **Too many open / old pull requests**
      - Condition A: `open_prs > pr_threshold`
      - Condition B: count of open PRs with `age_days > old_pr_days` > 0
   3. **No activity for X days**
      - Compute `last_activity` as the max of `created_at`, `closed_at`, `merged_at` across all tasks.
      - Condition: `current_date - last_activity > no_activity_days`.

   When a condition is met, the Fabric notebook (or a Web Activity) calls the Telegram Bot API to send a notification to a configured chat.

## Technologies

- **GitHub**
  - REST API
  - Repository: `microsoft/fabric-samples`

- **Microsoft Fabric**
  - Notebooks (Python)
  - Pipelines
  - Lakehouse / Warehouse (Delta tables)

- **Power BI**
  - Semantic model on top of `Tasks`
  - Dashboard for GitHub activity

- **Telegram**
  - Bot API for sending alert messages

## Possible extensions

- Support multiple repositories (e.g., additional Fabric-related repos).
- Store alert events in a separate Lakehouse table for historical analysis.
- Add more metrics such as:
  - Time from issue creation to first response
  - PR review times
  - Breakdown by label and area.
