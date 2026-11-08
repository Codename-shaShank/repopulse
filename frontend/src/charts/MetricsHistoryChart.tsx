import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { Snapshot } from "../api/types";
import { EmptyState } from "../components/Ui";

export function MetricsHistoryChart({ snapshots }: { snapshots: Snapshot[] }) {
  if (snapshots.length === 0) {
    return (
      <EmptyState title="No history yet">
        <p>Snapshots appear here after the first successful sync.</p>
      </EmptyState>
    );
  }

  if (snapshots.length === 1) {
    return (
      <EmptyState title="Only one snapshot so far">
        <p>
          A trend needs at least two successful syncs. Sync again later to start
          plotting stars and forks over time.
        </p>
      </EmptyState>
    );
  }

  const data = snapshots.map((snapshot) => ({
    captured: new Date(snapshot.captured_at).toLocaleDateString(),
    stars: snapshot.stars_count,
    forks: snapshot.forks_count,
  }));

  return (
    <div className="chart">
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey="captured" tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip />
          <Legend />
          <Line
            type="monotone"
            dataKey="stars"
            name="Stars"
            stroke="#2563eb"
            strokeWidth={2}
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="forks"
            name="Forks"
            stroke="#059669"
            strokeWidth={2}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
