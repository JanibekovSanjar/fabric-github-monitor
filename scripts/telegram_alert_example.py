"""
Example script: compute GitHub metrics and send Telegram alerts.

This mirrors the alert logic that would run inside a Fabric notebook:
1) Too many open issues
2) Too many open / old PRs
3) No activity for X days

In this standalone example:
- We read data from a local CSV file `tasks.csv` which should have the same
  columns as the Lakehouse `Tasks` table.
- In Fabric, you would replace the CSV load with reading from the Lakehouse.
"""

import os
from datetime import datetime, timezone

import pandas as pd
import requests

# --------------------
# Config
# --------------------
MONITORED_REPO = "microsoft/fabric-samples"

ISSUE_THRESHOLD = int(os.getenv("ALERT_ISSUE_THRESHOLD", "80"))
PR_THRESHOLD = int(os.getenv("ALERT_PR_THRESHOLD", "20"))
OLD_PR_DAYS = int(os.getenv("ALERT_OLD_PR_DAYS", "7"))
NO_ACTIVITY_DAYS = int(os.getenv("ALERT_NO_ACTIVITY_DAYS", "3"))

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

TASKS_CSV_PATH = os.getenv("TASKS_CSV_PATH", "tasks.csv")


def send_telegram_message(text: str) -> None:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        raise RuntimeError("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set")

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
    }
    resp = requests.post(url, json=payload)
    resp.raise_for_status()


def load_tasks() -> pd.DataFrame:
    """
    Load tasks from a CSV file.

    Expected columns:
    - repo
    - type ('issue' / 'pr')
    - state ('open' / 'closed')
    - created_at
    - closed_at
    - merged_at (optional for PRs)
    """
    if not os.path.exists(TASKS_CSV_PATH):
        raise FileNotFoundError(
            f"{TASKS_CSV_PATH} not found. Export your Tasks table or adjust TASKS_CSV_PATH."
        )

    df = pd.read_csv(TASKS_CSV_PATH)

    # Filter to the monitored repo
    df = df[df["repo"] == MONITORED_REPO].copy()

    # Parse timestamps
    for col in ["created_at", "closed_at", "merged_at"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce", utc=True)

    return df


def compute_and_send_alerts(tasks: pd.DataFrame) -> int:
    """
    Compute metrics and send the three types of alerts via Telegram.
    Returns the number of alerts sent.
    """
    alerts_sent = 0
    now = datetime.now(timezone.utc)

    # --------------------
    # 1) Too many open issues
    # --------------------
    open_issues = len(
        tasks[
            (tasks["type"] == "issue")
            & (tasks["state"] == "open")
        ]
    )

    if open_issues > ISSUE_THRESHOLD:
        msg = (
            f"🚨 *GitHub Alert – Too many open issues*\n"
            f"Repo: `{MONITORED_REPO}`\n"
            f"Open issues: *{open_issues}* (threshold: {ISSUE_THRESHOLD})"
        )
        send_telegram_message(msg)
        alerts_sent += 1

    # --------------------
    # 2a) Too many open PRs
    # --------------------
    open_prs_df = tasks[
        (tasks["type"] == "pr")
        & (tasks["state"] == "open")
    ]
    open_prs = len(open_prs_df)

    if open_prs > PR_THRESHOLD:
        msg = (
            f"⚠️ *GitHub Alert – Too many open PRs*\n"
            f"Repo: `{MONITORED_REPO}`\n"
            f"Open PRs: *{open_prs}* (threshold: {PR_THRESHOLD})"
        )
        send_telegram_message(msg)
        alerts_sent += 1

    # --------------------
    # 2b) Old PRs
    # --------------------
    if "created_at" in open_prs_df.columns:
        open_prs_df = open_prs_df.copy()
        open_prs_df["age_days"] = (now - open_prs_df["created_at"]).dt.days
        old_prs_df = open_prs_df[open_prs_df["age_days"] > OLD_PR_DAYS]
        count_old_prs = len(old_prs_df)

        if count_old_prs > 0:
            # Show up to 3 PR numbers in the message
            sample = old_prs_df.sort_values("age_days", ascending=False).head(3)
            lines = [
                f"- PR #{int(row['number'])} – {int(row['age_days'])} days open"
                for _, row in sample.iterrows()
                if not pd.isna(row.get("number"))
            ]
            pr_details = "\n".join(lines)

            msg = (
                f"🐢 *GitHub Alert – Old PRs*\n"
                f"Repo: `{MONITORED_REPO}`\n"
                f"Open PRs older than *{OLD_PR_DAYS}* days: *{count_old_prs}*"
            )
            if pr_details:
                msg += "\n" + pr_details

            send_telegram_message(msg)
            alerts_sent += 1

    # --------------------
    # 3) No activity for X days
    # --------------------
    # Last activity is max(created_at, closed_at, merged_at) across all rows
    candidates = []
    for col in ["created_at", "closed_at", "merged_at"]:
        if col in tasks.columns:
            candidates.append(tasks[col])

    if candidates:
        last_activity_series = pd.concat(candidates, axis=1).max(axis=1)
        repo_last_activity = last_activity_series.max()

        if pd.notna(repo_last_activity):
            inactivity_days = (now - repo_last_activity).days

            if inactivity_days > NO_ACTIVITY_DAYS:
                msg = (
                    f"🕒 *GitHub Alert – No recent activity*\n"
                    f"Repo: `{MONITORED_REPO}`\n"
                    f"No new issues or PR merges in the last *{inactivity_days}* days.\n"
                    f"Last activity: `{repo_last_activity}`"
                )
                send_telegram_message(msg)
                alerts_sent += 1

    return alerts_sent


def main():
    tasks = load_tasks()
    alerts_sent = compute_and_send_alerts(tasks)
    print(f"Alerts sent: {alerts_sent}")


if __name__ == "__main__":
    main()
