import { Link } from "react-router-dom";

import type { Repository } from "../api/types";
import { EmptyState, formatDateTime, formatNumber } from "./Ui";

export function RepositoryList({
  repositories,
  search,
  onSearchChange,
}: {
  repositories: Repository[];
  search: string;
  onSearchChange: (value: string) => void;
}) {
  return (
    <section className="panel">
      <div className="panel-header">
        <h2>Tracked repositories</h2>
        <div className="field inline">
          <label htmlFor="search">Search</label>
          <input
            id="search"
            value={search}
            onChange={(event) => onSearchChange(event.target.value)}
            placeholder="owner or name"
            autoComplete="off"
          />
        </div>
      </div>

      {repositories.length === 0 ? (
        <EmptyState title="No repositories match">
          <p>
            Add a public repository above, or clear the search to see everything
            you track.
          </p>
        </EmptyState>
      ) : (
        <table className="table">
          <thead>
            <tr>
              <th scope="col">Repository</th>
              <th scope="col">Language</th>
              <th scope="col">Stars</th>
              <th scope="col">Forks</th>
              <th scope="col">Open issues</th>
              <th scope="col">Last synced</th>
            </tr>
          </thead>
          <tbody>
            {repositories.map((repository) => (
              <tr key={repository.id}>
                <td>
                  <Link to={`/repositories/${repository.id}`}>
                    {repository.full_name}
                  </Link>
                </td>
                <td>{repository.primary_language ?? "—"}</td>
                <td>{formatNumber(repository.stars_count)}</td>
                <td>{formatNumber(repository.forks_count)}</td>
                <td>{formatNumber(repository.open_issues_count)}</td>
                <td>{formatDateTime(repository.last_synced_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
