export interface LanguageStat {
  language: string;
  bytes_of_code: number;
}

export interface Snapshot {
  id: string;
  stars_count: number;
  forks_count: number;
  open_issues_count: number;
  watchers_count: number;
  captured_at: string;
}

export interface SyncRun {
  id: string;
  status: "in_progress" | "success" | "failed";
  started_at: string;
  finished_at: string | null;
  records_processed: number;
  error_message: string | null;
}

export interface Repository {
  id: string;
  owner: string;
  name: string;
  full_name: string;
  html_url: string;
  description: string | null;
  primary_language: string | null;
  stars_count: number;
  forks_count: number;
  open_issues_count: number;
  watchers_count: number;
  github_created_at: string | null;
  last_synced_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface RepositoryDetail extends Repository {
  languages: LanguageStat[];
  snapshot_count: number;
}

export interface SyncResult {
  repository: Repository;
  snapshot: Snapshot;
  languages: LanguageStat[];
  sync_run: SyncRun;
}

export interface RecentlySynced {
  id: string;
  full_name: string;
  last_synced_at: string | null;
  stars_count: number;
  forks_count: number;
}

export interface AnalyticsSummary {
  tracked_repositories: number;
  total_stars: number;
  total_forks: number;
  total_open_issues: number;
  total_snapshots: number;
  recently_synced: RecentlySynced[];
}
