import type { SyncRun } from "../api/types";
import { EmptyState, formatDateTime } from "./Ui";

export function SyncHistory({ runs }: { runs: SyncRun[] }) {
  if (runs.length === 0) {
    return (
      <EmptyState title="No sync attempts yet">
        <p>Use Sync now to fetch the latest metrics from GitHub.</p>
      </EmptyState>
    );
  }

  return (
    <table className="table">
      <thead>
        <tr>
          <th scope="col">Started</th>
          <th scope="col">Status</th>
          <th scope="col">Rows written</th>
          <th scope="col">Detail</th>
        </tr>
      </thead>
      <tbody>
        {runs.map((run) => (
          <tr key={run.id}>
            <td>{formatDateTime(run.started_at)}</td>
            <td>
              <span className={`status status-${run.status}`}>{run.status}</span>
            </td>
            <td>{run.records_processed}</td>
            <td className="muted">{run.error_message ?? "—"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
