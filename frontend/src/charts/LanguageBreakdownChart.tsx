import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { LanguageStat } from "../api/types";
import { EmptyState, formatNumber } from "../components/Ui";

const COLORS = [
  "#2563eb",
  "#059669",
  "#d97706",
  "#7c3aed",
  "#db2777",
  "#0891b2",
  "#65a30d",
];

export function LanguageBreakdownChart({
  languages,
}: {
  languages: LanguageStat[];
}) {
  if (languages.length === 0) {
    return (
      <EmptyState title="No language data">
        <p>
          GitHub reported no language bytes for this repository at the latest
          sync.
        </p>
      </EmptyState>
    );
  }

  const total = languages.reduce((sum, item) => sum + item.bytes_of_code, 0);
  const data = languages.slice(0, 7).map((item) => ({
    language: item.language,
    bytes: item.bytes_of_code,
    share: total > 0 ? ((item.bytes_of_code / total) * 100).toFixed(1) : "0.0",
  }));

  return (
    <>
      <div className="chart">
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={data} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="language" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip
              formatter={(value: number) => [`${formatNumber(value)} bytes`, "Size"]}
            />
            <Bar dataKey="bytes" name="Bytes of code">
              {data.map((entry, index) => (
                <Cell key={entry.language} fill={COLORS[index % COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <ol className="language-list">
        {data.map((item) => (
          <li key={item.language}>
            <span>{item.language}</span>
            <span className="muted">
              {formatNumber(item.bytes)} bytes · {item.share}%
            </span>
          </li>
        ))}
      </ol>
    </>
  );
}
