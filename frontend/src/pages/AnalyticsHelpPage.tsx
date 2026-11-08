import { Link } from "react-router-dom";

import { exportUrl } from "../api/client";

export function AnalyticsHelpPage() {
  return (
    <div className="stack">
      <section className="panel">
        <h2>Analysing the history in BigQuery Sandbox</h2>
        <p>
          RepoPulse stores every successful sync as a snapshot. The two CSV
          exports below carry that history in a flat shape with stable column
          names and ISO-8601 UTC timestamps, so BigQuery can infer the schema on
          upload.
        </p>

        <ol className="steps">
          <li>
            Download the exports:{" "}
            <a href={exportUrl("repository-snapshots.csv")} download>
              repository_snapshots.csv
            </a>{" "}
            and{" "}
            <a href={exportUrl("language-stats.csv")} download>
              language_stats.csv
            </a>
            .
          </li>
          <li>
            Open the BigQuery console and start a Sandbox project. No billing
            account is needed.
          </li>
          <li>
            Create a dataset named <code>repopulse</code> in a region close to
            you.
          </li>
          <li>
            Create a table from each CSV upload. Use table names{" "}
            <code>repository_snapshots</code> and <code>language_stats</code>,
            enable auto-detect schema, and set the header rows to skip to 1.
          </li>
          <li>
            Run the queries bundled in the repository under{" "}
            <code>analytics/bigquery/</code>:{" "}
            <code>repository_trends.sql</code> and{" "}
            <code>language_popularity.sql</code>.
          </li>
        </ol>

        <p className="muted">
          BigQuery is an analysis destination only. The application never calls
          Google Cloud at runtime and works fully without it.
        </p>
      </section>

      <p>
        <Link to="/">Back to the dashboard</Link>
      </p>
    </div>
  );
}
