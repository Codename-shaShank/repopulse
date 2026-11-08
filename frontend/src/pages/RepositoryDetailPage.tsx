import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { ApiError } from "../api/client";
import {
  deleteRepository,
  getRepository,
  listSnapshots,
  listSyncRuns,
  syncRepository,
} from "../api/repositories";
import type { RepositoryDetail, Snapshot, SyncRun } from "../api/types";
import { LanguageBreakdownChart } from "../charts/LanguageBreakdownChart";
import { MetricsHistoryChart } from "../charts/MetricsHistoryChart";
import { SyncHistory } from "../components/SyncHistory";
import {
  ConfirmDialog,
  ErrorBanner,
  KpiCard,
  Loading,
  SuccessBanner,
  formatDateTime,
  formatNumber,
} from "../components/Ui";

export function RepositoryDetailPage() {
  const { repositoryId } = useParams<{ repositoryId: string }>();
  const navigate = useNavigate();

  const [repository, setRepository] = useState<RepositoryDetail | null>(null);
  const [snapshots, setSnapshots] = useState<Snapshot[]>([]);
  const [runs, setRuns] = useState<SyncRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const load = useCallback(async (id: string) => {
    try {
      const [detail, history, syncRuns] = await Promise.all([
        getRepository(id),
        listSnapshots(id),
        listSyncRuns(id),
      ]);
      setRepository(detail);
      setSnapshots(history);
      setRuns(syncRuns);
      setError(null);
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : "Could not load this repository.",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (repositoryId) {
      void load(repositoryId);
    }
  }, [load, repositoryId]);

  async function handleSync() {
    if (!repositoryId) {
      return;
    }
    setSyncing(true);
    setError(null);
    setNotice(null);
    try {
      const result = await syncRepository(repositoryId);
      setNotice(
        `Synced. Stored a snapshot with ${formatNumber(
          result.snapshot.stars_count,
        )} stars and ${result.languages.length} language rows.`,
      );
      await load(repositoryId);
    } catch (caught) {
      if (caught instanceof ApiError) {
        setError(
          caught.status === 429
            ? `${caught.message} Existing history is unchanged.`
            : `${caught.message} The failure was recorded and no snapshot was written.`,
        );
      } else {
        setError("The sync failed for an unknown reason.");
      }
      await load(repositoryId);
    } finally {
      setSyncing(false);
    }
  }

  async function handleDelete() {
    if (!repositoryId) {
      return;
    }
    setDeleting(true);
    try {
      await deleteRepository(repositoryId);
      navigate("/");
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : "Could not delete this repository.",
      );
      setDeleting(false);
      setConfirmOpen(false);
    }
  }

  if (loading) {
    return <Loading label="Loading repository" />;
  }

  if (!repository) {
    return (
      <div className="stack">
        {error ? <ErrorBanner message={error} /> : null}
        <p>
          <Link to="/">Back to the dashboard</Link>
        </p>
      </div>
    );
  }

  return (
    <div className="stack">
      <section className="panel">
        <div className="panel-header">
          <div>
            <h2>{repository.full_name}</h2>
            <p className="muted">{repository.description ?? "No description"}</p>
            <p className="muted">
              Owner {repository.owner} ·{" "}
              <a href={repository.html_url} target="_blank" rel="noreferrer">
                View on GitHub
              </a>{" "}
              · Primary language {repository.primary_language ?? "unknown"}
            </p>
            <p className="muted">
              Last synced {formatDateTime(repository.last_synced_at)}
            </p>
          </div>
          <div className="button-row">
            <button
              type="button"
              className="primary"
              onClick={handleSync}
              disabled={syncing}
            >
              {syncing ? "Syncing…" : "Sync now"}
            </button>
            <button
              type="button"
              className="danger"
              onClick={() => setConfirmOpen(true)}
              disabled={syncing || deleting}
            >
              Delete
            </button>
          </div>
        </div>
      </section>

      {error ? <ErrorBanner message={error} onDismiss={() => setError(null)} /> : null}
      {notice ? <SuccessBanner message={notice} /> : null}

      <section className="kpi-row">
        <KpiCard label="Stars" value={formatNumber(repository.stars_count)} />
        <KpiCard label="Forks" value={formatNumber(repository.forks_count)} />
        <KpiCard
          label="Open issues"
          value={formatNumber(repository.open_issues_count)}
        />
        <KpiCard
          label="Watchers"
          value={formatNumber(repository.watchers_count)}
          hint="GitHub watchers_count, not stars"
        />
      </section>

      <section className="panel">
        <h2>Stars and forks over time</h2>
        <MetricsHistoryChart snapshots={snapshots} />
      </section>

      <section className="panel">
        <h2>Language breakdown</h2>
        <p className="muted">From the most recent successful sync.</p>
        <LanguageBreakdownChart languages={repository.languages} />
      </section>

      <section className="panel">
        <h2>Recent sync attempts</h2>
        <SyncHistory runs={runs} />
      </section>

      <p>
        <Link to="/">Back to the dashboard</Link>
      </p>

      {confirmOpen ? (
        <ConfirmDialog
          title="Delete this repository?"
          body={`${repository.full_name}, its ${repository.snapshot_count} snapshot(s), language rows and sync history will be removed. This cannot be undone.`}
          confirmLabel="Delete"
          onConfirm={handleDelete}
          onCancel={() => setConfirmOpen(false)}
          busy={deleting}
        />
      ) : null}
    </div>
  );
}
