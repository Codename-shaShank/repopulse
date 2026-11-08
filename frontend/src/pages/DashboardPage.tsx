import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { ApiError, exportUrl } from "../api/client";
import { addRepository, getSummary, listRepositories } from "../api/repositories";
import type { AnalyticsSummary, Repository } from "../api/types";
import { AddRepositoryForm } from "../components/AddRepositoryForm";
import { RepositoryList } from "../components/RepositoryList";
import {
  EmptyState,
  ErrorBanner,
  KpiCard,
  Loading,
  SuccessBanner,
  formatDateTime,
  formatNumber,
} from "../components/Ui";

export function DashboardPage() {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const load = useCallback(async (query: string) => {
    try {
      const [summaryData, repositoryData] = await Promise.all([
        getSummary(),
        listRepositories(query),
      ]);
      setSummary(summaryData);
      setRepositories(repositoryData);
      setError(null);
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : "Something went wrong loading the dashboard.",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void load(search);
    }, 250);
    return () => window.clearTimeout(timer);
  }, [load, search]);

  async function handleAdd(owner: string, name: string) {
    setAdding(true);
    setError(null);
    setNotice(null);
    try {
      const created = await addRepository(owner, name);
      setNotice(`${created.full_name} is now tracked and synced.`);
      await load(search);
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : "Could not add that repository.",
      );
    } finally {
      setAdding(false);
    }
  }

  const nothingTracked = !loading && summary?.tracked_repositories === 0;

  return (
    <div className="stack">
      <section className="panel">
        <h2>Add a public repository</h2>
        <AddRepositoryForm onAdd={handleAdd} busy={adding} />
      </section>

      {error ? <ErrorBanner message={error} onDismiss={() => setError(null)} /> : null}
      {notice ? <SuccessBanner message={notice} /> : null}

      {loading ? (
        <Loading label="Loading dashboard" />
      ) : nothingTracked ? (
        <EmptyState title="Nothing tracked yet">
          <p>
            Add a public repository with its owner and name above. RepoPulse
            fetches its current metrics and starts a history you can chart and
            export.
          </p>
        </EmptyState>
      ) : (
        <>
          <section className="kpi-row">
            <KpiCard
              label="Tracked repositories"
              value={formatNumber(summary?.tracked_repositories ?? 0)}
            />
            <KpiCard
              label="Total stars"
              value={formatNumber(summary?.total_stars ?? 0)}
              hint="Latest known value per repository"
            />
            <KpiCard
              label="Total forks"
              value={formatNumber(summary?.total_forks ?? 0)}
            />
            <KpiCard
              label="Stored snapshots"
              value={formatNumber(summary?.total_snapshots ?? 0)}
              hint="One per successful sync"
            />
          </section>

          <section className="panel">
            <h2>Recently synced</h2>
            {summary && summary.recently_synced.length > 0 ? (
              <ul className="recent-list">
                {summary.recently_synced.map((item) => (
                  <li key={item.id}>
                    <Link to={`/repositories/${item.id}`}>{item.full_name}</Link>
                    <span className="muted">
                      {formatDateTime(item.last_synced_at)}
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="muted">No successful sync has run yet.</p>
            )}
          </section>

          <RepositoryList
            repositories={repositories}
            search={search}
            onSearchChange={setSearch}
          />
        </>
      )}

      <section className="panel">
        <h2>Analytics exports</h2>
        <p className="muted">
          Download the history as CSV, then upload it into BigQuery Sandbox. See{" "}
          <Link to="/analytics">the analytics guide</Link> for the steps.
        </p>
        <div className="button-row">
          <a
            className="button"
            href={exportUrl("repository-snapshots.csv")}
            download
          >
            repository_snapshots.csv
          </a>
          <a className="button" href={exportUrl("language-stats.csv")} download>
            language_stats.csv
          </a>
        </div>
      </section>
    </div>
  );
}
