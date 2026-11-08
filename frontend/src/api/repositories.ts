import { request } from "./client";
import type {
  AnalyticsSummary,
  Repository,
  RepositoryDetail,
  Snapshot,
  SyncResult,
  SyncRun,
} from "./types";

export function listRepositories(q?: string): Promise<Repository[]> {
  const query = q && q.trim() ? `?q=${encodeURIComponent(q.trim())}` : "";
  return request<Repository[]>(`/api/v1/repositories${query}`);
}

export function addRepository(
  owner: string,
  name: string,
): Promise<RepositoryDetail> {
  return request<RepositoryDetail>("/api/v1/repositories", {
    method: "POST",
    body: JSON.stringify({ owner, name }),
  });
}

export function getRepository(id: string): Promise<RepositoryDetail> {
  return request<RepositoryDetail>(`/api/v1/repositories/${id}`);
}

export function syncRepository(id: string): Promise<SyncResult> {
  return request<SyncResult>(`/api/v1/repositories/${id}/sync`, {
    method: "POST",
  });
}

export function listSnapshots(id: string): Promise<Snapshot[]> {
  return request<Snapshot[]>(`/api/v1/repositories/${id}/snapshots`);
}

export function listSyncRuns(id: string): Promise<SyncRun[]> {
  return request<SyncRun[]>(`/api/v1/repositories/${id}/sync-runs`);
}

export function deleteRepository(id: string): Promise<void> {
  return request<void>(`/api/v1/repositories/${id}`, { method: "DELETE" });
}

export function getSummary(): Promise<AnalyticsSummary> {
  return request<AnalyticsSummary>("/api/v1/analytics/summary");
}
