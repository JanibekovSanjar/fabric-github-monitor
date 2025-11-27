# Power BI Dashboard Layout

This document describes the layout and key measures used in the Power BI report
for the GitHub activity monitor.

## Data

Main table: `Tasks` (from the Lakehouse)

Key columns:

- `repo`
- `type` (`issue` / `pr`)
- `state` (`open` / `closed`)
- `created_at`
- `closed_at`
- `merged_at`
- `assignee`
- `title`
- `labels`

## Page: Overview

### KPIs (top row)

1. **Open Issues**
   - Count of tasks where `type = "issue"` and `state = "open"`.

2. **Open PRs**
   - Count of tasks where `type = "pr"` and `state = "open"`.

3. **Average Issue Cycle Time (days)**
   - Average of `closed_at - created_at` (in days) for closed issues.

4. **Average PR Merge Time (hours)**
   - Average of `merged_at - created_at` (in hours) for merged PRs.

### Time series chart (center)

- Visual: Line chart
- Axis: Date (based on `created_at`)
- Series:
  - Issues created
  - Issues closed
  - PRs opened
  - PRs merged (optional, if not too noisy)

### Open work by assignee (bottom left)

- Visual: Bar chart
- Axis: Assignee
- Value: Count of open tasks (issues + PRs)
- Optional: Legend for type (`issue` vs `pr`)

### Recent items table (bottom right)

- Visual: Table
- Columns:
  - Type
  - Title
  - Assignee
  - State
  - Created date
  - Closed/Merged date
  - Cycle time (days)

### Slicers (side panel)

- Repo (e.g., `microsoft/fabric-samples`)
- Type (`issue` / `pr`)
- Assignee
- Date range (based on `created_at`)

## Example DAX measures (conceptual)

Open Issues:

```DAX
Open Issues =
CALCULATE (
    COUNTROWS ( Tasks ),
    Tasks[type] = "issue",
    Tasks[state] = "open"
)
Open PRs =
CALCULATE (
    COUNTROWS ( Tasks ),
    Tasks[type] = "pr",
    Tasks[state] = "open"
)
Avg Issue Cycle Time (Days) =
VAR ClosedIssues =
    FILTER ( Tasks, Tasks[type] = "issue" && NOT ISBLANK ( Tasks[closed_at] ) )
RETURN
    AVERAGEX (
        ClosedIssues,
        DATEDIFF ( Tasks[created_at], Tasks[closed_at], DAY )
    )
Avg PR Merge Time (Hours) =
VAR MergedPRs =
    FILTER ( Tasks, Tasks[type] = "pr" && NOT ISBLANK ( Tasks[merged_at] ) )
RETURN
    AVERAGEX (
        MergedPRs,
        DATEDIFF ( Tasks[created_at], Tasks[merged_at], HOUR )
    )
new change
