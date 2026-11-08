# BigQuery Sandbox analytics

RepoPulse stores one snapshot per successful sync. These steps load that history
into BigQuery Sandbox so it can be queried with SQL. The application itself never
calls Google Cloud — this is a manual, batch workflow and is entirely optional.

## 1. Export the CSV files

With the backend running, download both exports:

```bash
curl -O http://localhost:8000/api/v1/exports/repository-snapshots.csv
curl -O http://localhost:8000/api/v1/exports/language-stats.csv
```

You can also use the download buttons on the dashboard.

Both files are UTF-8, carry a header row, and use ISO-8601 UTC timestamps so
BigQuery types `captured_at` as a `TIMESTAMP` automatically.

| File | Columns |
|---|---|
| `repository_snapshots.csv` | `snapshot_id`, `repository_id`, `repository_full_name`, `owner`, `name`, `stars_count`, `forks_count`, `open_issues_count`, `watchers_count`, `captured_at` |
| `language_stats.csv` | `repository_full_name`, `snapshot_id`, `captured_at`, `language`, `bytes_of_code` |

## 2. Create a Sandbox project

1. Open <https://console.cloud.google.com/bigquery> and sign in.
2. Accept the BigQuery Sandbox prompt. No billing account is required.
3. Note the project ID — the SQL files use `PROJECT_ID` as a placeholder for it.

## 3. Create the dataset

In the BigQuery console, select your project, choose **Create dataset**, and use:

- Dataset ID: `repopulse`
- Location: whichever region is closest to you (keep it consistent)

## 4. Upload each CSV as a table

For each file, choose **Create table** inside the `repopulse` dataset and set:

- Create table from: **Upload**
- File: the CSV you downloaded
- File format: **CSV**
- Table name: `repository_snapshots`, then `language_stats`
- Schema: **Auto detect**
- Advanced options → Header rows to skip: **1**

Re-uploading later with write preference **Overwrite table** replaces the data
with a fresh export.

## 5. Run the queries

Open a SQL workspace and run the scripts in this folder, replacing `PROJECT_ID`
with your project ID:

- [`repository_trends.sql`](repository_trends.sql) — latest metrics per
  repository, star and fork growth between the earliest and latest snapshot, top
  repositories by stars with a daily star rate, and daily snapshot coverage.
- [`language_popularity.sql`](language_popularity.sql) — most common languages,
  per-repository language shares, each repository's dominant language, and how a
  language mix shifted over time.

Each file holds several independent statements. Run them one at a time; the
BigQuery console executes the statement under the cursor.

## Sandbox limitations

- Sandbox tables expire after 60 days and the dataset has a storage cap.
- There is no streaming insert and no scheduled query without billing enabled.
- Growth queries need at least two snapshots per repository, so sync a few times
  across different days before expecting a useful trend.

Never commit service-account keys, credentials or exported data to this
repository.
